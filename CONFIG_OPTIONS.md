# ⚙️ Configuration Options

## Quick Reference

```python
# In review.py or Review_Fetcher_Colab.ipynb

# ===== PAGINATION =====
MAX_PAGES = None      # Fetch ALL reviews (recommended)
# MAX_PAGES = 10      # Limit to 10 pages for testing
# MAX_PAGES = 50      # Limit to 50 pages for cost control

# ===== API SETTINGS =====
RETRY_ATTEMPTS = 3    # Retry failed API calls 3 times
RETRY_DELAY = 2       # Wait 2 seconds between retries

# ===== DATA PROCESSING =====
# Deduplication: Automatic (can't disable - prevents duplicates!)
# review_id generation: Automatic
```

## Option Details

### MAX_PAGES
**What it does:** Limits how many pages to fetch per place

| Value | Result | Use Case |
|-------|--------|----------|
| `None` | Fetch ALL pages | Production - complete data ✅ |
| `10` | Max 10 pages (~100 reviews) | Testing |
| `50` | Max 50 pages (~500 reviews) | Cost control |

**Recommendation:** `None` (get all reviews)

### RETRY_ATTEMPTS
**What it does:** How many times to retry failed API calls

| Value | Result |
|-------|--------|
| `1` | No retries (fail fast) |
| `3` | Retry 3 times (recommended) |
| `5` | Retry 5 times (for unstable connection) |

### RETRY_DELAY
**What it does:** Seconds to wait before retrying

| Value | Result |
|-------|--------|
| `1` | Fast retry (may hit rate limit) |
| `2` | Balanced (recommended) |
| `5` | Slow retry (for rate limit issues) |

## Batch Processing Options

```python
# In main() function:
place_ids = get_place_ids_to_process(client, limit=5)
```

| Limit | Result |
|-------|--------|
| `None` | Process ALL places |
| `5` | Process 5 places (testing) |
| `100` | Process 100 places (production batch) |

## Cost Optimization

### Low Cost (Testing):
```python
MAX_PAGES = 2
limit = 5
# = 5 places × 2 pages = 10 API calls
```

### Balanced (Production):
```python
MAX_PAGES = None  # Get all reviews
limit = None      # Process all places
# = X places × avg 3-5 pages = depends on data
```

### High Cost (Large Dataset):
```python
MAX_PAGES = None
limit = None
# = 1000 places × avg 20 pages = ~20,000 API calls
```

**Recommendation:** Start with low cost for testing, then use balanced for production.
