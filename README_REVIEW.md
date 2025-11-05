# Google Reviews Data Fetcher - FLATTENED with Deduplication

## Overview

Fetches complete review data from Google Reviews API and stores it in BigQuery with **FLATTENED structure** and **automatic deduplication** using unique `review_id`.

## Features

- ✅ **FLATTENED Structure**: Each review = ONE row with individual columns (no JSON!)
- ✅ **Unique review_id**: Each review gets a unique identifier
- ✅ **Automatic Deduplication**: No duplicate reviews - safe to re-run!
- ✅ **Full Data Capture**: Fetches ALL review data including ratings, snippets, reviewer info
- ✅ **Pagination Handling**: Automatically follows `nextPageToken` to fetch all pages
- ✅ **Incremental Processing**: Uses timestamps to fetch only new/updated reviews
- ✅ **Robust Error Handling**: Automatic retries with exponential backoff
- ✅ **Progress Tracking**: Detailed logging to console and file
- ✅ **BigQuery Integration**: Automatic table creation and data upload
- ✅ **Easy Querying**: Standard SQL on individual columns (no JSON parsing needed)

## Installation

```bash
pip install google-cloud-bigquery google-auth pandas db-dtypes
```

Or use requirements file:
```bash
pip install -r requirements_review.txt
```

## Configuration

### Environment Variables (Recommended)
```bash
export RAPIDAPI_KEY="your_key_here"
export BIGQUERY_KEY_JSON='{"type": "service_account", ...}'
```

### Hardcoded (Fallback)
Edit script and replace default values.

## Usage

```bash
python review.py
```

The script will:
1. Connect to BigQuery
2. Read CIDs from `Map_location.cid`
3. Fetch ALL reviews with pagination
4. **Generate unique review_id** for each review
5. **Check for duplicates** before upload
6. Upload only new reviews to BigQuery

## BigQuery Schema (FLATTENED with review_id)

### Table: `place_reviews_full`

**Structure**: Each review = One row with unique review_id

| Column | Type | Description |
|--------|------|-------------|
| **`review_id`** | **STRING** | **Unique review identifier (prevents duplicates)** |
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

### 🔑 About review_id

**What is it?**  
A unique 16-character hash generated from:
- `place_id` + `isoDate` + `reviewer_name` + `snippet` (first 100 chars)

**Why?**  
- Same review always gets same ID
- **Automatic duplicate prevention**
- Safe to re-run script multiple times
- No duplicate reviews in database

**How it works:**
```python
unique_string = f"{place_id}_{iso_date}_{reviewer_name}_{snippet[:100]}"
review_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]
```

## Key Benefits

✅ **No JSON parsing needed** - Direct column access  
✅ **No duplicates** - Unique review_id prevents duplicate reviews  
✅ **Easy SQL queries** - Standard filtering, aggregation, joins  
✅ **Better performance** - Indexed columns, faster queries  
✅ **Clear data model** - One review per row  
✅ **Simple analytics** - GROUP BY, AVG, COUNT work directly  
✅ **Safe re-runs** - Can run script multiple times without duplicating data  

## Deduplication Process

1. **Generate review_id**: Hash of place_id + isoDate + reviewer_name + snippet
2. **Query existing IDs**: Get all review_ids from BigQuery
3. **Filter duplicates**: Remove reviews that already exist
4. **Upload only new**: Insert only new reviews

**Result**: No duplicate reviews, even if you run the script multiple times! 🎉

### Example Flow

```
Fetch 100 reviews from API
  ↓
Generate review_id for each
  ↓
Query BigQuery: 50 review_ids already exist
  ↓
Filter: Remove 50 duplicates
  ↓
Upload: Only 50 new reviews
```

## Query Examples (FLATTENED)

### Get all reviews for a place
```sql
SELECT review_id, rating, reviewer_name, snippet
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE place_id = '7632417579134624850'
ORDER BY isoDate DESC
```

### Calculate average rating per place
```sql
SELECT 
    place_id,
    COUNT(DISTINCT review_id) as review_count,
    AVG(rating) as avg_rating
FROM `shopper-reviews-477306.place_data.place_reviews_full`
GROUP BY place_id
ORDER BY review_count DESC
```

### Find 5-star reviews
```sql
SELECT review_id, place_id, reviewer_name, snippet
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE rating = 5
ORDER BY isoDate DESC
LIMIT 100
```

### Check for duplicates (shouldn't find any!)
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT review_id) as unique_reviews,
    COUNT(*) - COUNT(DISTINCT review_id) as duplicates
FROM `shopper-reviews-477306.place_data.place_reviews_full`
```

### Get top reviewers
```sql
SELECT 
    reviewer_name,
    COUNT(DISTINCT review_id) as reviews_in_dataset,
    AVG(rating) as avg_rating_given
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
    COUNT(DISTINCT review_id) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE rating IS NOT NULL
GROUP BY rating
ORDER BY rating DESC
```

## Logging

The script logs to:
- **Console**: Real-time progress
- **File**: `review_fetcher.log` (detailed logs)

Log messages:
- `📊 Found X existing review IDs` - Deduplication check
- `🔍 Removed X duplicate(s)` - Duplicates found and skipped
- `📤 X new review(s)` - New reviews to upload
- `✅ Uploaded X new review(s)` - Upload successful

## Error Handling

- **Retry Logic**: 3 attempts with 2-second delays
- **API Errors**: Graceful handling of rate limits
- **BigQuery Errors**: Automatic table creation
- **Duplicates**: Automatically filtered before upload
- **Partial Success**: Continues even if some places fail

## Incremental Processing

The script:
1. Checks if destination table exists
2. If yes: Processes only new places (CIDs not yet in table)
3. If no: Processes all CIDs
4. **For each place**: Only uploads new reviews (filters out duplicates)

**Result**: Safe to run multiple times!

## Troubleshooting

### "Duplicates still appearing"
- Check if old data exists without review_id column
- Delete table and re-run to use new schema
- Query: `SELECT * FROM table WHERE review_id IS NULL`

### "No CIDs found"
- Verify `Map_location.cid` has data
- Check BigQuery credentials

### "All reviews already exist"
- This is normal! Deduplication is working
- Script skips existing reviews automatically

### "Performance slow"
- Script checks all existing review_ids on each place
- For large datasets, consider batching or indexing

## Comparison: Before vs After

### Before (JSON format)
```sql
-- Complex: Requires JSON parsing
SELECT JSON_VALUE(review, '$.rating') FROM table
```

### After (Flattened with review_id)
```sql
-- Simple: Direct column access + no duplicates
SELECT rating FROM table WHERE review_id = 'abc123'
```

**Benefits:**
- 10x easier queries
- No duplicates
- Better performance
- Clear data model

## Version

**Version**: 3.0 - Flattened with review_id & Deduplication  
**Last Updated**: 2025-11-05  
**Key Feature**: Unique review_id prevents ALL duplicates

---

**Enjoy duplicate-free, queryable review data! 🎉**
