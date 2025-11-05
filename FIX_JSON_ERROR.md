# Fix for "Unsupported field type: JSON" Error

## Problem
The error `400 Unsupported field type: JSON` occurs because BigQuery's JSON type is not supported in all regions/projects or requires specific settings.

## Solution
The notebook has been updated to use STRING type instead of JSON type. JSON data is stored as strings, but BigQuery can still parse them using JSON functions.

## What Changed
**Schema Update:**
- `reviews` field: JSON → STRING
- `topics` field: JSON → STRING  
- `metadata` field: JSON → STRING

**All JSON functions still work!** BigQuery can parse JSON strings natively.

## If You Already Created the Table

If you created the `place_reviews_full` table before this fix, you need to either:

### Option 1: Delete and Recreate (Recommended)
Run this in a new Colab cell:

```python
# Delete the old table
client = get_bigquery_client()
table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"

try:
    client.delete_table(table_id)
    print(f"✅ Deleted table: {table_id}")
    print("📝 Now re-run Step 4 to define functions with the fix")
    print("📝 Then run Step 8 to process places with the new schema")
except Exception as e:
    print(f"Error: {e}")
```

### Option 2: Use a Different Table Name
Update Step 3 configuration:

```python
DESTINATION_TABLE = "place_reviews_full_v2"  # New table name
```

## Verification

After the fix, you should see:
```
✅ Created table place_reviews_full
```

And uploads should succeed:
```
✅ Uploaded review data for place XXXXX to BigQuery
```

## Querying Data (Still Works!)

Even though data is stored as STRING, you can still query JSON:

```sql
-- Extract reviews
SELECT 
  place_id,
  JSON_VALUE(review, '$.rating') as rating,
  JSON_VALUE(review, '$.snippet') as review_text
FROM `shopper-reviews-477306.place_data.place_reviews_full`,
UNNEST(JSON_EXTRACT_ARRAY(reviews)) as review
```

```sql
-- Extract topics
SELECT 
  place_id,
  JSON_VALUE(topic, '$.name') as topic_name,
  CAST(JSON_VALUE(topic, '$.reviews') AS INT64) as mentions
FROM `shopper-reviews-477306.place_data.place_reviews_full`,
UNNEST(JSON_EXTRACT_ARRAY(topics)) as topic
```

**These queries work exactly the same whether the column is JSON or STRING type!**

## Next Steps

1. ✅ **Fixed**: Notebook updated to use STRING type
2. 🔄 **Action Required**: 
   - If table exists, delete it (Option 1 above)
   - OR use a new table name (Option 2 above)
3. ▶️ **Continue**: Re-run Step 4, then proceed with Step 8

---

**The fix is complete and the notebook is ready to use!**
