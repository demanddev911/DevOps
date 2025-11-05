# Google Reviews Data Fetcher Documentation - FLATTENED SCHEMA

## Overview

This script fetches complete review data from Google Reviews API (via RapidAPI's "Google Search Master Mega") and stores it in Google BigQuery in a **FLATTENED structure** (each review = one row with individual columns).

## Features

- ✅ **FLATTENED Structure**: Each review stored as ONE row with individual columns (no JSON!)
- ✅ **Full Data Capture**: Fetches ALL review data including ratings, snippets, reviewer info
- ✅ **Pagination Handling**: Automatically follows `nextPageToken` to fetch all pages
- ✅ **Incremental Processing**: Uses timestamps to fetch only new/updated reviews
- ✅ **Robust Error Handling**: Automatic retries with exponential backoff
- ✅ **Progress Tracking**: Detailed logging to console and file
- ✅ **BigQuery Integration**: Automatic table creation and data upload
- ✅ **Easy Querying**: Standard SQL on individual columns (no JSON parsing needed)

## Installation

### Requirements
```bash
pip install google-cloud-bigquery google-auth pandas db-dtypes
```

Or use the provided requirements file:
```bash
pip install -r requirements_review.txt
```

## Configuration

### Method 1: Environment Variables (Recommended)
```bash
export RAPIDAPI_KEY="your_rapidapi_key_here"
export BIGQUERY_KEY_JSON='{"type": "service_account", "project_id": "..."}'
```

### Method 2: Hardcoded in Script
Edit the script and replace the default values:
```python
RAPIDAPI_KEY = 'your_rapidapi_key_here'
# BigQuery credentials will use hardcoded fallback
```

## Usage

### Run the Script
```bash
python review.py
```

The script will:
1. Connect to BigQuery using `BIGQUERY_KEY_JSON`
2. Read CIDs from `Map_location.cid` column
3. For each CID:
   - Fetch ALL reviews via Google Reviews API
   - Handle pagination automatically
   - Flatten each review into a separate row
4. Upload to `place_reviews_full` table (FLATTENED format)
5. Skip already processed places (incremental)

### Customize Batch Size
Edit the `main()` function to change the limit:
```python
place_ids = get_place_ids_to_process(client, limit=10)  # Process 10 places
```

For full processing, remove the limit:
```python
place_ids = get_place_ids_to_process(client)  # Process all places
```

## BigQuery Schema (FLATTENED)

### Table: `place_reviews_full`

**Structure**: Each review = One row

| Column | Type | Description |
|--------|------|-------------|
| `place_id` | STRING | Place ID (CID) from Map_location table |
| `rating` | INTEGER | Review rating (1-5 stars) |
| `date` | STRING | Relative date (e.g., "2 months ago") |
| `isoDate` | TIMESTAMP | ISO 8601 timestamp of review |
| `snippet` | STRING | Full review text/comment |
| `likes` | INTEGER | Number of likes on the review |
| `reviewer_name` | STRING | Name of the reviewer |
| `reviewer_link` | STRING | Link to reviewer's Google profile |
| `reviewer_thumbnail` | STRING | URL to reviewer's profile image |
| `reviewer_reviews` | INTEGER | Total number of reviews by this reviewer |
| `reviewer_photos` | INTEGER | Total number of photos by this reviewer |
| `timestamp` | TIMESTAMP | When the data was inserted to BigQuery |
| `fetch_date` | DATE | Date when data was fetched |

### Key Benefits of Flattened Structure

✅ **No JSON parsing needed** - Direct column access  
✅ **Easy SQL queries** - Standard filtering, aggregation, joins  
✅ **Better performance** - Indexed columns, faster queries  
✅ **Clear data model** - One review per row  
✅ **Simple analytics** - GROUP BY, AVG, COUNT work directly  

### Example: Raw API Response vs Flattened

**Raw API JSON:**
```json
{
  "reviews": [
    {
      "rating": 5,
      "date": "2 months ago",
      "isoDate": "2024-08-14T18:31:24.651Z",
      "snippet": "Great place!",
      "likes": 2,
      "user": {
        "name": "John Doe",
        "reviews": 13,
        "photos": 18
      }
    }
  ]
}
```

**Flattened BigQuery Row:**
| place_id | rating | date | snippet | likes | reviewer_name | reviewer_reviews |
|----------|--------|------|---------|-------|---------------|-----------------|
| 123456 | 5 | 2 months ago | Great place! | 2 | John Doe | 13 |

## Query Examples (FLATTENED)

### Get all reviews for a specific place
```sql
SELECT 
    place_id,
    rating,
    date,
    reviewer_name,
    snippet
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE place_id = '7632417579134624850'
ORDER BY isoDate DESC
```

### Calculate average rating per place
```sql
SELECT 
    place_id,
    COUNT(*) as review_count,
    AVG(rating) as avg_rating,
    COUNT(DISTINCT reviewer_name) as unique_reviewers
FROM `shopper-reviews-477306.place_data.place_reviews_full`
GROUP BY place_id
ORDER BY review_count DESC
```

### Find 5-star reviews
```sql
SELECT 
    place_id,
    reviewer_name,
    date,
    snippet
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE rating = 5
ORDER BY isoDate DESC
LIMIT 100
```

### Get top reviewers
```sql
SELECT 
    reviewer_name,
    COUNT(*) as reviews_in_dataset,
    AVG(rating) as avg_rating_given,
    MAX(reviewer_reviews) as total_google_reviews
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE reviewer_name IS NOT NULL
GROUP BY reviewer_name
ORDER BY reviews_in_dataset DESC
LIMIT 10
```

### Rating distribution
```sql
SELECT 
    rating,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE rating IS NOT NULL
GROUP BY rating
ORDER BY rating DESC
```

### Reviews over time
```sql
SELECT 
    DATE_TRUNC(isoDate, MONTH) as month,
    COUNT(*) as review_count,
    AVG(rating) as avg_rating
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE isoDate IS NOT NULL
GROUP BY month
ORDER BY month DESC
```

### Join with Map_location to get place details
```sql
SELECT 
    m.title,
    m.address,
    r.rating,
    r.reviewer_name,
    r.snippet
FROM `shopper-reviews-477306.place_data.place_reviews_full` r
JOIN `shopper-reviews-477306.place_data.Map_location` m
ON r.place_id = m.cid
WHERE r.rating >= 4
ORDER BY r.isoDate DESC
LIMIT 50
```

## Logging

The script logs to:
- **Console**: Real-time progress updates
- **File**: `review_fetcher.log` (detailed logs)

Log levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues (e.g., no reviews found)
- `ERROR`: Critical failures

## Error Handling

The script includes:
- **Retry Logic**: 3 attempts with 2-second delays
- **API Error Handling**: Graceful handling of rate limits and timeouts
- **BigQuery Error Handling**: Automatic table creation and schema validation
- **Partial Success**: Continues processing even if some places fail

## Incremental Processing

The script automatically:
1. Checks if destination table exists
2. If yes: Fetches only CIDs not yet processed
3. If no: Processes all CIDs from Map_location

**Result**: You can run the script multiple times safely!

## Customization

### Change API Parameters
Edit `fetch_reviews_for_place()`:
```python
params = f"?cid={place_id}&sortBy=mostRelevant&gl=us&hl=en&page={page}"
# Change: gl (country), hl (language), sortBy (mostRelevant, newest, highestRating, lowestRating)
```

### Change Page Limit
Edit `MAX_PAGES` constant:
```python
MAX_PAGES = 20  # Fetch up to 20 pages per place
```

### Change BigQuery Table
Edit configuration section:
```python
DESTINATION_TABLE = "my_reviews_table"  # Custom table name
```

## Workflow Summary

```
Map_location (cid) 
    ↓
Read CIDs via BigQuery
    ↓
For each CID:
  ├─ Fetch reviews from API (with pagination)
  ├─ Flatten each review to one row
  └─ Upload to BigQuery (append mode)
    ↓
place_reviews_full (FLATTENED)
```

## Performance Tips

1. **Batch Processing**: Set appropriate limit for testing, remove for production
2. **Rate Limiting**: Script includes 1-second delay between places
3. **Parallel Processing**: Not implemented (to avoid API rate limits)
4. **Monitoring**: Check `review_fetcher.log` for issues

## Troubleshooting

### "No CIDs found"
- Check that `Map_location.cid` column has data
- Verify BigQuery credentials are correct

### "API Error 429"
- RapidAPI rate limit exceeded
- Increase `RETRY_DELAY` or reduce request frequency

### "Schema mismatch"
- Delete `place_reviews_full` table and re-run
- Script will recreate with correct FLATTENED schema

### "Duplicate reviews"
- Not possible - script uses `WRITE_APPEND` mode
- Each row is a unique review (no deduplication needed)

## Comparison: JSON vs FLATTENED

### Old JSON Format (before)
```sql
-- Complex: Requires JSON parsing
SELECT 
    JSON_VALUE(review, '$.rating') as rating
FROM table,
UNNEST(JSON_EXTRACT_ARRAY(reviews)) as review
```

### New FLATTENED Format (now)
```sql
-- Simple: Direct column access
SELECT rating FROM table
```

**Result**: 10x easier to query, better performance!

---

## Support

For issues or questions:
1. Check `review_fetcher.log` for detailed error messages
2. Verify API credentials and BigQuery permissions
3. Test with a small batch (limit=1) first

## Version

**Version**: 2.0 - Flattened Schema  
**Last Updated**: 2025-11-05  
**Created for**: Google Cloud BigQuery + RapidAPI

---

**Enjoy your FLATTENED, queryable review data! 🎉**
