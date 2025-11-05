# Google Reviews Data Fetcher

A production-ready Python script that fetches full Google Reviews data from RapidAPI and stores it in BigQuery.

## Features

✅ **Complete Data Capture**
- Reviews (rating, date, snippet, likes, user details)
- Topics (name, reviews count, ID)
- Metadata (search parameters, credits, tokens)

✅ **Smart Incremental Processing**
- Only processes places that haven't been fetched yet
- Timestamp-based tracking
- Resume-friendly (can run multiple times)

✅ **Robust Pagination**
- Automatically follows `nextPageToken`
- Fetches all available pages (up to safety limit)
- Rate limiting between requests

✅ **Production Features**
- Comprehensive error handling with retries
- Detailed logging (console + file)
- Progress tracking
- Graceful failure handling

## Installation

```bash
# Install dependencies
pip install -r requirements_review.txt
```

## Configuration

### Option 1: Environment Variables (Recommended)
```bash
export RAPIDAPI_KEY="your_rapidapi_key"
export BIGQUERY_KEY_JSON='{"type": "service_account", ...}'
```

### Option 2: Edit Script
Edit `review.py` and update the credentials at the top:
- `RAPIDAPI_KEY`
- `BIGQUERY_CREDENTIALS_JSON` or hardcoded credentials dict

## Usage

### Basic Run
```bash
python review.py
```

### What It Does

1. **Connects to BigQuery**
   - Authenticates using provided credentials
   - Validates connection

2. **Creates Destination Table** (if needed)
   - Table: `shopper-reviews-477306.place_data.place_reviews_full`
   - Schema: place_id, total_reviews, reviews (JSON), topics (JSON), metadata (JSON), timestamp

3. **Fetches Place IDs**
   - Reads from `Map_location` table
   - Excludes already-processed places (incremental)

4. **Processes Each Place**
   - Fetches all review pages via pagination
   - Aggregates reviews, topics, and metadata
   - Uploads to BigQuery

5. **Reports Summary**
   - Success/failure counts
   - Total reviews fetched
   - Processing time

## Output

### BigQuery Table: `place_reviews_full`

| Column | Type | Description |
|--------|------|-------------|
| `place_id` | STRING | Place CID (required) |
| `total_reviews` | INTEGER | Total number of reviews fetched |
| `pages_fetched` | INTEGER | Number of pages processed |
| `reviews` | JSON | Full array of all reviews with user data |
| `topics` | JSON | Array of topics mentioned in reviews |
| `metadata` | JSON | API metadata (searchParameters, credits, etc.) |
| `timestamp` | TIMESTAMP | When data was fetched (UTC) |
| `fetch_date` | DATE | Date of fetch |

### Review JSON Structure
```json
{
  "rating": 5,
  "date": "2 months ago",
  "isoDate": "2024-08-14T18:31:24.651Z",
  "snippet": "Great Vibes. Nice People...",
  "likes": 0,
  "user": {
    "name": "Skyler Jenkins",
    "thumbnail": "https://...",
    "link": "https://...",
    "reviews": 13,
    "photos": 18
  }
}
```

### Topics JSON Structure
```json
{
  "name": "studying",
  "reviews": 37,
  "id": "/m/075xv0"
}
```

## Logging

Logs are written to:
- **Console**: Real-time progress
- **File**: `review_fetcher.log` (persistent record)

### Log Levels
- `INFO`: Normal operations
- `WARNING`: Recoverable issues
- `ERROR`: Failed operations

### Example Output
```
2025-11-05 10:30:00 - INFO - 🚀 Starting Google Reviews Data Fetcher
2025-11-05 10:30:01 - INFO - ✅ Connected to BigQuery project: shopper-reviews-477306
2025-11-05 10:30:02 - INFO - 📊 Found 25 place(s) to process
2025-11-05 10:30:05 - INFO - 📍 Processing place 1/25: 17602107806865671526
2025-11-05 10:30:06 - INFO - 📡 Fetching page 1 for place 17602107806865671526...
2025-11-05 10:30:07 - INFO - ✅ Successfully fetched page 1 for place 17602107806865671526
2025-11-05 10:30:08 - INFO - ✅ Page 1: 8 reviews fetched
2025-11-05 10:30:09 - INFO - 🎉 Completed fetching for place 17602107806865671526: 8 total reviews, 10 topics
2025-11-05 10:30:10 - INFO - ✅ Uploaded review data for place 17602107806865671526 to BigQuery
```

## Error Handling

### Automatic Retries
- API failures: 3 attempts with 2-second delays
- Graceful degradation on persistent failures

### Rate Limiting
- 0.5 seconds between pages
- 1 second between places

### Failure Recovery
- Failed places are logged but don't stop the process
- Can re-run script to retry failed places

## Customization

### Configuration Options (in script)

```python
# API configuration
MAX_PAGES = 10              # Maximum pages per place
RETRY_ATTEMPTS = 3          # Number of retries
RETRY_DELAY = 2             # Seconds between retries

# Table names
SOURCE_TABLE = "Map_location"          # Your source table
DESTINATION_TABLE = "place_reviews_full"  # Reviews table
```

### API Parameters

To modify search parameters, edit the `fetch_reviews_for_place()` function:
```python
params = f"?cid={place_id}&sortBy=mostRelevant&gl=us&hl=en&page={page}"
```

Available sort options:
- `mostRelevant`
- `newest`
- `highestRating`
- `lowestRating`

## Incremental Processing

The script automatically:
1. Checks which places already have reviews
2. Only processes new places
3. Skips re-fetching existing data

To **force re-fetch** for a place, delete its record from `place_reviews_full`.

## Querying Reviews in BigQuery

### Get all reviews for a place
```sql
SELECT 
  place_id,
  total_reviews,
  JSON_EXTRACT_ARRAY(reviews) as reviews_array,
  JSON_EXTRACT_ARRAY(topics) as topics_array
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE place_id = '17602107806865671526'
```

### Extract individual reviews
```sql
SELECT 
  place_id,
  JSON_VALUE(review, '$.rating') as rating,
  JSON_VALUE(review, '$.date') as date,
  JSON_VALUE(review, '$.snippet') as snippet,
  JSON_VALUE(review, '$.user.name') as reviewer_name
FROM `shopper-reviews-477306.place_data.place_reviews_full`,
UNNEST(JSON_EXTRACT_ARRAY(reviews)) as review
WHERE place_id = '17602107806865671526'
```

### Get topic summary
```sql
SELECT 
  place_id,
  JSON_VALUE(topic, '$.name') as topic_name,
  CAST(JSON_VALUE(topic, '$.reviews') AS INT64) as review_count
FROM `shopper-reviews-477306.place_data.place_reviews_full`,
UNNEST(JSON_EXTRACT_ARRAY(topics)) as topic
ORDER BY review_count DESC
```

## Monitoring

### Check Processing Status
```sql
SELECT 
  COUNT(DISTINCT place_id) as places_processed,
  SUM(total_reviews) as total_reviews,
  AVG(total_reviews) as avg_reviews_per_place,
  MAX(timestamp) as last_fetch
FROM `shopper-reviews-477306.place_data.place_reviews_full`
```

### Find Places Needing Processing
```sql
SELECT cid
FROM `shopper-reviews-477306.place_data.Map_location`
WHERE cid NOT IN (
  SELECT place_id 
  FROM `shopper-reviews-477306.place_data.place_reviews_full`
)
```

## Troubleshooting

### Issue: "No place IDs found"
- Check that `Map_location` table has `cid` column
- Verify credentials have read access

### Issue: "API rate limit exceeded"
- Increase `RETRY_DELAY` value
- Reduce batch size (process fewer places at once)

### Issue: "BigQuery upload failed"
- Check credentials have write access
- Verify project/dataset names are correct
- Check BigQuery quotas

## Performance

### Typical Performance
- ~2-3 seconds per page
- ~5-10 seconds per place (average)
- ~100 places per hour

### Optimization Tips
- Run during off-peak hours
- Process in batches
- Monitor API quotas

## License & Credits

- Uses RapidAPI's Google Search Master Mega API
- BigQuery integration via Google Cloud SDK
- Built for incremental, production-grade data fetching

## Support

For issues or questions:
1. Check logs in `review_fetcher.log`
2. Verify API credentials
3. Test with a single place ID first
4. Review BigQuery table schema

---

**Last Updated:** 2025-11-05  
**Version:** 1.0.0
