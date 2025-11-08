# Mistral API Rate Limiter - User Guide

## Overview

The Enhanced Mistral API Rate Limiter provides intelligent request management to prevent rate limits and timeouts when using the Mistral API. It includes advanced features like token bucket rate limiting, circuit breakers, exponential backoff, and intelligent key health tracking.

## Key Features

### 1. **Token Bucket Rate Limiting**
- Prevents exceeding API rate limits by controlling request frequency
- Each API key has its own token bucket
- Configurable capacity and refill rate
- Automatically queues requests when bucket is empty

### 2. **Circuit Breaker Pattern**
- Protects against cascading failures
- Three states: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing)
- Automatically opens after 5 consecutive failures
- Self-healing: attempts recovery after cooldown period

### 3. **Intelligent Key Health Tracking**
- Monitors success/failure rates for each API key
- Calculates health scores (0-100) for optimal key selection
- Tracks response times and performance metrics
- Automatically rotates to healthiest keys

### 4. **Exponential Backoff with Jitter**
- Gradually increases wait time between retries
- Adds random jitter to prevent thundering herd
- Maximum delay cap to prevent excessive waiting

### 5. **Automatic Cooldown Management**
- Rate-limited keys: 60-second cooldown
- Timeout errors: 10-second cooldown
- Circuit breaker open: 120-second cooldown
- Authentication errors: 1-hour cooldown

## Configuration

### Basic Setup

```python
from mistral_rate_limiter import EnhancedMistralAnalyzer

# Initialize with your API keys
analyzer = EnhancedMistralAnalyzer(
    api_keys=["key1", "key2", "key3"],
    api_url="https://api.mistral.ai/v1/chat/completions",
    model="mistral-large-latest",
    temperature=0.3,
    max_tokens=4000,
    rate_limit_per_key=5,  # Requests per minute per key
    timeout=60  # Request timeout in seconds
)
```

### Configuration Parameters

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `api_keys` | List of Mistral API keys | Required | 3+ keys for resilience |
| `api_url` | Mistral API endpoint | mistral.ai/v1/chat/completions | - |
| `model` | Model to use | mistral-large-latest | - |
| `temperature` | Response creativity | 0.3 | 0.1-0.7 |
| `max_tokens` | Max response length | 4000 | 1000-8000 |
| `rate_limit_per_key` | Requests/minute/key | 5 | 3-10 |
| `timeout` | Request timeout (seconds) | 60 | 30-120 |

## Usage Examples

### Single Request

```python
# Simple analysis
result = analyzer.analyze(
    prompt="What is the capital of France?",
    max_tokens=500,
    max_retries=10
)

if result:
    print(f"Response: {result}")
else:
    print("Request failed after all retries")
```

### Batch Processing

```python
# Process multiple prompts in parallel
prompts = [
    ("summary", "Summarize this text...", 1000),
    ("sentiment", "Analyze sentiment...", 500),
    ("topics", "Extract main topics...", 800)
]

results = analyzer.analyze_batch(
    prompts=prompts,
    max_workers=3  # Parallel threads
)

for section_key, content in results.items():
    print(f"{section_key}: {content}")
```

### Health Monitoring

```python
# Get health report for all keys
health_report = analyzer.get_health_report()

for key_id, stats in health_report.items():
    print(f"\nKey {key_id}:")
    print(f"  Health Score: {stats['health_score']:.1f}/100")
    print(f"  Success Rate: {stats['success_rate']:.1f}%")
    print(f"  Rate Limit Hits: {stats['rate_limit_hits']}")
    print(f"  Circuit State: {stats['circuit_state']}")
    print(f"  Avg Response Time: {stats['average_response_time']:.2f}s")
```

### Reset Cooldowns (Emergency Use)

```python
# Reset all cooldowns and circuit breakers
# Use only when you're sure rate limits have been lifted
analyzer.reset_all_cooldowns()
```

## Error Handling

The analyzer handles various error types automatically:

### 1. Rate Limit (429)
- **Action**: Key marked as rate-limited
- **Cooldown**: 60 seconds
- **Behavior**: Switches to next available key

### 2. Timeout
- **Action**: Key marked as slow
- **Cooldown**: 10 seconds
- **Behavior**: Switches to next available key

### 3. Server Error (500-504)
- **Action**: Temporary failure
- **Cooldown**: None (but affects health score)
- **Behavior**: Exponential backoff and retry

### 4. Authentication Error (401/403)
- **Action**: Invalid key
- **Cooldown**: 1 hour
- **Behavior**: Key disabled temporarily

### 5. Circuit Breaker Opens
- **Trigger**: 5 consecutive failures
- **Cooldown**: 120 seconds
- **Behavior**: Key completely blocked until recovery

## Best Practices

### 1. **API Key Management**
- Use at least 3 API keys for resilience
- Rotate keys regularly for security
- Monitor key health and replace failing keys

### 2. **Rate Limit Configuration**
- Set `rate_limit_per_key` based on your API plan
- Start conservative (3-5 req/min) and adjust
- Monitor rate limit hits in health reports

### 3. **Timeout Settings**
- Set timeout based on expected response times
- Use longer timeouts (90-120s) for complex prompts
- Use shorter timeouts (30-60s) for simple queries

### 4. **Batch Processing**
- Use `analyze_batch()` for multiple prompts
- Limit `max_workers` to avoid overwhelming API
- Recommended: 3-5 workers for optimal performance

### 5. **Monitoring**
- Check health reports regularly
- Watch for keys with low health scores
- Investigate high rate limit hit counts

### 6. **Error Recovery**
- Let the system handle retries automatically
- Don't reset cooldowns unless necessary
- Log failures for debugging

## Performance Optimization

### Token Bucket Tuning

```python
# High-volume scenario (many keys, tight rate limits)
analyzer = EnhancedMistralAnalyzer(
    api_keys=api_keys,
    rate_limit_per_key=3,  # Conservative
    timeout=45  # Shorter timeout
)

# Low-volume scenario (few keys, loose rate limits)
analyzer = EnhancedMistralAnalyzer(
    api_keys=api_keys,
    rate_limit_per_key=10,  # Aggressive
    timeout=90  # Longer timeout
)
```

### Parallel Processing

```python
# For CPU-bound tasks
max_workers = min(len(api_keys) * 2, 10)

# For I/O-bound tasks (recommended)
max_workers = min(len(api_keys), 5)
```

## Troubleshooting

### Issue: All Keys Exhausted
**Symptoms**: "No available API keys found" warning
**Solutions**:
1. Wait for cooldowns to expire
2. Check key validity
3. Reduce request rate
4. Add more API keys

### Issue: Slow Responses
**Symptoms**: High average response times
**Solutions**:
1. Reduce `max_tokens` parameter
2. Simplify prompts
3. Check network connectivity
4. Increase timeout setting

### Issue: Frequent Rate Limits
**Symptoms**: Many rate limit hits in health report
**Solutions**:
1. Decrease `rate_limit_per_key`
2. Add more API keys
3. Reduce parallel workers
4. Implement request queuing

### Issue: Circuit Breakers Opening
**Symptoms**: Keys stuck in OPEN state
**Solutions**:
1. Wait for 120-second cooldown
2. Check API service status
3. Verify API keys are valid
4. Review error logs for root cause

## Integration with Streamlit

```python
import streamlit as st
from mistral_rate_limiter import EnhancedMistralAnalyzer

# Initialize in session state
if 'mistral_analyzer' not in st.session_state:
    st.session_state.mistral_analyzer = EnhancedMistralAnalyzer(
        api_keys=MISTRAL_KEYS,
        rate_limit_per_key=5
    )

# Use throughout the app
result = st.session_state.mistral_analyzer.analyze(
    prompt=user_input
)

# Display health status
if st.sidebar.checkbox("Show API Health"):
    health = st.session_state.mistral_analyzer.get_health_report()
    st.sidebar.json(health)
```

## Advanced Features

### Custom Logging

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

# All rate limiter operations will be logged
analyzer = EnhancedMistralAnalyzer(api_keys=keys)
```

### Health Score Algorithm

Health score is calculated as:
```
base_score = (successful_requests / total_requests) * 100
penalty = (rate_limit_hits * 5) + (timeout_count * 2)
bonus = 10 if last_success < 60 seconds ago else 0
final_score = min(100, max(0, base_score - penalty + bonus))
```

### Circuit Breaker States

- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: All requests blocked, key in cooldown
- **HALF_OPEN**: Testing recovery, single request allowed

## API Reference

### EnhancedMistralAnalyzer

#### Methods

##### `analyze(prompt, max_tokens, max_retries, priority)`
Analyze a single prompt with intelligent retry logic.

##### `analyze_batch(prompts, max_workers)`
Process multiple prompts in parallel.

##### `get_health_report()`
Get detailed health metrics for all API keys.

##### `reset_all_cooldowns()`
Reset all cooldowns and circuit breakers (use with caution).

#### Properties

- `key_health`: Dictionary of KeyHealth objects
- `token_buckets`: Dictionary of TokenBucket objects
- `session`: Requests session with retry strategy

## Changelog

### Version 1.0
- Initial release
- Token bucket rate limiting
- Circuit breaker pattern
- Health tracking
- Exponential backoff
- Automatic key rotation

## License

MIT License - See main project license for details.

## Support

For issues or questions:
- Check the troubleshooting section
- Review health reports for insights
- Check application logs
- Open an issue on GitHub
