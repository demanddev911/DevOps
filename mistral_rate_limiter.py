"""
Enhanced Mistral API Rate Limiter and Timeout Handler
Version: 1.0

Features:
- Token bucket rate limiting per API key
- Circuit breaker pattern for fault tolerance
- Exponential backoff with jitter
- Intelligent key health tracking and rotation
- Request queue management
- Adaptive timeout handling
- Comprehensive error recovery
"""

import time
import random
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int = 10  # Maximum tokens
    refill_rate: float = 1.0  # Tokens per second
    tokens: float = 10.0  # Current tokens
    last_refill: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def wait_for_token(self, timeout: float = 30.0) -> bool:
        """Wait for a token to become available"""
        start = time.time()
        while time.time() - start < timeout:
            if self.consume():
                return True
            time.sleep(0.1)
        return False


@dataclass
class KeyHealth:
    """Track health metrics for each API key"""
    key: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0
    timeout_count: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    cooldown_until: Optional[float] = None
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_failure_count: int = 0
    circuit_last_attempt: Optional[float] = None
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=10))

    def record_success(self, response_time: float):
        """Record a successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.last_success = time.time()
        self.response_times.append(response_time)
        self.average_response_time = sum(self.response_times) / len(self.response_times)

        # Reset circuit breaker on success
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.circuit_failure_count = 0
            logger.info(f"Circuit breaker closed for key ending in ...{self.key[-8:]}")

    def record_failure(self, error_type: str):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure = time.time()

        if error_type == "rate_limit":
            self.rate_limit_hits += 1
            # Cooldown for rate limits: 60 seconds
            self.cooldown_until = time.time() + 60.0
            logger.warning(f"Rate limit hit for key ending in ...{self.key[-8:]}, cooling down for 60s")
        elif error_type == "timeout":
            self.timeout_count += 1
            # Shorter cooldown for timeouts: 10 seconds
            self.cooldown_until = time.time() + 10.0

        # Update circuit breaker
        self.circuit_failure_count += 1
        if self.circuit_failure_count >= 5:
            self.circuit_state = CircuitState.OPEN
            self.cooldown_until = time.time() + 120.0  # 2 minutes
            logger.error(f"Circuit breaker opened for key ending in ...{self.key[-8:]}")

    def is_available(self) -> bool:
        """Check if key is available for use"""
        now = time.time()

        # Check cooldown
        if self.cooldown_until and now < self.cooldown_until:
            return False

        # Check circuit breaker
        if self.circuit_state == CircuitState.OPEN:
            # Try to transition to half-open after cooldown
            if self.cooldown_until and now >= self.cooldown_until:
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker half-open for key ending in ...{self.key[-8:]}")
                return True
            return False

        return True

    def get_health_score(self) -> float:
        """Calculate health score (0-100)"""
        if self.total_requests == 0:
            return 100.0

        success_rate = (self.successful_requests / self.total_requests) * 100

        # Penalize for rate limits and timeouts
        penalty = (self.rate_limit_hits * 5) + (self.timeout_count * 2)
        score = max(0, success_rate - penalty)

        # Bonus for recent success
        if self.last_success:
            time_since_success = time.time() - self.last_success
            if time_since_success < 60:
                score += 10

        return min(100.0, score)


class EnhancedMistralAnalyzer:
    """
    Enhanced Mistral API analyzer with comprehensive rate limiting and error handling
    """

    def __init__(
        self,
        api_keys: List[str],
        api_url: str = "https://api.mistral.ai/v1/chat/completions",
        model: str = "mistral-large-latest",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        rate_limit_per_key: int = 5,  # Requests per minute per key
        timeout: int = 60
    ):
        self.api_keys = api_keys
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Initialize key health tracking
        self.key_health: Dict[str, KeyHealth] = {
            key: KeyHealth(key=key) for key in api_keys
        }

        # Initialize token buckets for each key
        # rate_limit_per_key requests per minute = rate_limit_per_key/60 per second
        tokens_per_second = rate_limit_per_key / 60.0
        self.token_buckets: Dict[str, TokenBucket] = {
            key: TokenBucket(
                capacity=rate_limit_per_key,
                refill_rate=tokens_per_second,
                tokens=rate_limit_per_key
            ) for key in api_keys
        }

        # Create session with retry strategy
        self.session = self._create_session()

        # Lock for thread-safe key selection
        self.key_lock = threading.Lock()

        logger.info(f"EnhancedMistralAnalyzer initialized with {len(api_keys)} keys")

    def _create_session(self) -> requests.Session:
        """Create optimized requests session"""
        session = requests.Session()

        # Retry strategy for server errors only
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=40,
            pool_block=False
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _select_best_key(self) -> Optional[Tuple[str, TokenBucket, KeyHealth]]:
        """Select the best available API key based on health scores"""
        with self.key_lock:
            available_keys = []

            for key in self.api_keys:
                health = self.key_health[key]
                bucket = self.token_buckets[key]

                if health.is_available():
                    score = health.get_health_score()
                    available_keys.append((key, bucket, health, score))

            if not available_keys:
                logger.warning("No available API keys found")
                return None

            # Sort by health score (highest first)
            available_keys.sort(key=lambda x: x[3], reverse=True)

            # Return the healthiest key
            key, bucket, health, _ = available_keys[0]
            return key, bucket, health

    def _exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 32.0) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0, delay * 0.1)  # Add 10% jitter
        return delay + jitter

    def analyze(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        max_retries: int = 10,
        priority: str = "normal"
    ) -> Optional[str]:
        """
        Analyze prompt with intelligent rate limiting and error handling

        Args:
            prompt: The prompt to analyze
            max_tokens: Maximum tokens for response (uses default if None)
            max_retries: Maximum number of retry attempts
            priority: Request priority ("low", "normal", "high")

        Returns:
            Analysis result or None if all attempts failed
        """
        tokens = max_tokens or self.max_tokens

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": tokens
        }

        for attempt in range(max_retries):
            # Select best available key
            key_data = self._select_best_key()
            if not key_data:
                # No keys available, wait and retry
                wait_time = self._exponential_backoff(attempt, base_delay=2.0)
                logger.warning(f"No keys available, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                continue

            key, bucket, health = key_data

            # Wait for token bucket
            if not bucket.wait_for_token(timeout=30.0):
                logger.warning(f"Token bucket timeout for key ending in ...{key[-8:]}")
                continue

            # Make request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }

            start_time = time.time()

            try:
                response = self.session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    # Success!
                    health.record_success(response_time)
                    try:
                        result = response.json()['choices'][0]['message']['content']
                        logger.info(f"✓ Request successful with key ending in ...{key[-8:]} ({response_time:.2f}s)")
                        return result
                    except (KeyError, ValueError, json.JSONDecodeError) as e:
                        logger.error(f"JSON parsing error: {e}")
                        health.record_failure("parse_error")
                        continue

                elif response.status_code == 429:
                    # Rate limit hit
                    logger.warning(f"Rate limit (429) for key ending in ...{key[-8:]}")
                    health.record_failure("rate_limit")

                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = float(retry_after)
                            health.cooldown_until = time.time() + wait_time
                            logger.info(f"Retry-After header: {wait_time}s")
                        except ValueError:
                            pass

                    continue

                elif response.status_code >= 500:
                    # Server error
                    logger.warning(f"Server error ({response.status_code}) for key ending in ...{key[-8:]}")
                    health.record_failure("server_error")
                    wait_time = self._exponential_backoff(attempt)
                    time.sleep(wait_time)
                    continue

                elif response.status_code == 401 or response.status_code == 403:
                    # Invalid key
                    logger.error(f"Authentication error ({response.status_code}) for key ending in ...{key[-8:]}")
                    health.record_failure("auth_error")
                    health.cooldown_until = time.time() + 3600  # Cool down for 1 hour
                    continue

                else:
                    # Other error
                    logger.warning(f"HTTP error {response.status_code} for key ending in ...{key[-8:]}")
                    health.record_failure("http_error")
                    continue

            except requests.exceptions.Timeout:
                # Timeout
                response_time = time.time() - start_time
                logger.warning(f"Timeout ({response_time:.1f}s) for key ending in ...{key[-8:]}")
                health.record_failure("timeout")
                continue

            except requests.exceptions.ConnectionError as e:
                # Connection error
                logger.error(f"Connection error for key ending in ...{key[-8:]}: {str(e)[:100]}")
                health.record_failure("connection_error")
                wait_time = self._exponential_backoff(attempt)
                time.sleep(wait_time)
                continue

            except requests.exceptions.RequestException as e:
                # Other request error
                logger.error(f"Request error for key ending in ...{key[-8:]}: {str(e)[:100]}")
                health.record_failure("request_error")
                continue

            except Exception as e:
                # Unknown error
                logger.error(f"Unknown error for key ending in ...{key[-8:]}: {str(e)[:100]}")
                health.record_failure("unknown_error")
                continue

        logger.error(f"All {max_retries} retry attempts exhausted")
        return None

    def analyze_batch(
        self,
        prompts: List[Tuple[str, str, int]],
        max_workers: int = 3
    ) -> Dict[str, str]:
        """
        Analyze multiple prompts in parallel with rate limiting

        Args:
            prompts: List of (section_key, prompt, max_tokens) tuples
            max_workers: Maximum parallel workers

        Returns:
            Dictionary mapping section_key to analysis result
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        def process_single(section_key: str, prompt: str, max_tokens: int):
            content = self.analyze(prompt, max_tokens=max_tokens)
            return section_key, content

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single, sk, p, mt): sk
                for sk, p, mt in prompts
            }

            for future in as_completed(futures):
                try:
                    section_key, content = future.result(timeout=180)
                    if content:
                        results[section_key] = content
                        logger.info(f"✓ Batch result for {section_key}")
                except Exception as e:
                    section_key = futures[future]
                    logger.error(f"Batch error for {section_key}: {str(e)[:100]}")

        return results

    def get_health_report(self) -> Dict[str, dict]:
        """Get health report for all API keys"""
        report = {}
        for key, health in self.key_health.items():
            key_suffix = f"...{key[-8:]}"
            report[key_suffix] = {
                "health_score": health.get_health_score(),
                "total_requests": health.total_requests,
                "success_rate": (health.successful_requests / health.total_requests * 100)
                                if health.total_requests > 0 else 0,
                "rate_limit_hits": health.rate_limit_hits,
                "timeout_count": health.timeout_count,
                "circuit_state": health.circuit_state.value,
                "average_response_time": health.average_response_time,
                "is_available": health.is_available()
            }
        return report

    def reset_all_cooldowns(self):
        """Reset all cooldowns (use with caution)"""
        for health in self.key_health.values():
            health.cooldown_until = None
            health.circuit_state = CircuitState.CLOSED
            health.circuit_failure_count = 0
        logger.info("All cooldowns reset")


# Example usage and testing
if __name__ == "__main__":
    # Example with dummy keys (replace with real keys)
    api_keys = [
        "key1_placeholder",
        "key2_placeholder",
        "key3_placeholder"
    ]

    analyzer = EnhancedMistralAnalyzer(
        api_keys=api_keys,
        rate_limit_per_key=5  # 5 requests per minute per key
    )

    # Single analysis
    result = analyzer.analyze("What is the capital of France?")
    if result:
        print(f"Result: {result}")

    # Get health report
    health_report = analyzer.get_health_report()
    print("\nHealth Report:")
    for key, stats in health_report.items():
        print(f"\nKey {key}:")
        print(f"  Health Score: {stats['health_score']:.1f}")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Circuit State: {stats['circuit_state']}")
