# 🛡️ Duplicate Prevention & API Cost Savings Guide

## ⚠️ Why Duplicates Happen

### The Core Issue:
**Google's API returns the SAME reviews every time you call it for the same place.**

```
Call 1: API(place_123) → Reviews [A, B, C, D, E]
Call 2: API(place_123) → Reviews [A, B, C, D, E]  (SAME REVIEWS!)
Call 3: API(place_123) → Reviews [A, B, C, D, E]  (SAME REVIEWS!)
```

### Without Protection:
```
Run Script → Fetch Reviews → Insert to BigQuery
Run Script → Fetch Reviews → Insert to BigQuery (DUPLICATES!)
Run Script → Fetch Reviews → Insert to BigQuery (MORE DUPLICATES!)
```

**Result:**
- 💸 Wasted API credits (you're paying for the same data!)
- 🗄️ Duplicate reviews in database
- 📊 Incorrect analytics (reviews counted multiple times)

---

## ✅ Our 3-Layer Protection System

### Layer 1: Place-Level Filter (BEFORE API Call) 💰
**Purpose:** Don't fetch places already processed (saves API $$)

```python
# Query: Get only NEW places
SELECT cid FROM Map_location 
WHERE cid NOT IN (
    SELECT DISTINCT place_id FROM place_reviews_full
)
```

**What it does:**
- Checks which places already have reviews in BigQuery
- **Skips API calls** for already-processed places
- **Saves money!** No wasted API credits

**Example:**
```
Map_location has: [Place_A, Place_B, Place_C, Place_D]
place_reviews_full has reviews for: [Place_A, Place_B]

Script fetches: [Place_C, Place_D] only ✅
API calls: 2 places (not 4!) 💰
```

---

### Layer 2: Double-Check Before API Call ⚠️
**Purpose:** Extra safety check (in case Layer 1 fails)

```python
if check_if_place_already_processed(client, place_id):
    logger.warning("⚠️ Place already processed - SKIPPING API call")
    skipped += 1
    continue
```

**What it does:**
- Before each API call, checks if place has reviews
- If yes: **Skips API call entirely**
- Prevents accidental re-fetching

---

### Layer 3: Review-Level Deduplication (AFTER API Call) 🔑
**Purpose:** Even if same reviews fetched, don't insert duplicates

```python
# Generate unique review_id for each review
review_id = hash(place_id + isoDate + reviewer_name + snippet)

# Check which reviews already exist
existing_ids = get_existing_review_ids()

# Filter out duplicates
df_new = df[~df['review_id'].isin(existing_ids)]

# Upload only new reviews
upload(df_new)
```

**What it does:**
- Every review gets a unique `review_id` (hash-based)
- Before upload, checks which review_ids already exist
- **Filters out duplicates** before inserting
- Only uploads genuinely new reviews

**Example:**
```
API returns: 100 reviews
Already in DB: 80 reviews (matched by review_id)
Will upload: 20 new reviews only ✅
Duplicates prevented: 80 ✅
```

---

## 📊 How It Works: Complete Flow

```
START
  ↓
1. Get list of ALL places from Map_location
  ↓
2. FILTER: Remove places already in place_reviews_full
  Result: Only NEW places
  ↓
3. For each NEW place:
  ├─ Double-check: Does this place already have reviews?
  ├─ If YES: SKIP (no API call) 💰
  └─ If NO: Continue
      ↓
  4. Make API call to fetch reviews 💸
      ↓
  5. Generate review_id for each review
      ↓
  6. Query: Which review_ids already exist in BigQuery?
      ↓
  7. FILTER: Remove reviews with existing review_ids
      ↓
  8. Upload ONLY new reviews
      ↓
END

Summary:
- Layer 1 & 2: Prevent unnecessary API calls (save $$)
- Layer 3: Prevent duplicate inserts (data integrity)
```

---

## 🚨 Common Causes of Duplicates & Solutions

### Cause 1: Testing with Same Place Multiple Times
**Problem:**
```python
# In notebook - testing:
test_place_id = "123456"
review_data = fetch_all_reviews_for_place(test_place_id)  # API call!
upload_review_data_to_bigquery(client, review_data)

# Run again:
review_data = fetch_all_reviews_for_place(test_place_id)  # API call AGAIN!
upload_review_data_to_bigquery(client, review_data)  # Tries to insert (filtered by review_id)
```

**Solution:**
- Use the batch process (it has built-in checks)
- Don't manually test same place twice
- Check logs: "⚠️ Place already processed - SKIPPING"

---

### Cause 2: Old Data Without review_id
**Problem:**
```sql
-- Your table has old data:
SELECT * FROM place_reviews_full WHERE review_id IS NULL
-- Returns rows! (old data without review_id column)
```

**Solution:**
Delete old data and re-run:
```sql
-- Backup first!
CREATE TABLE place_reviews_full_backup AS 
SELECT * FROM place_reviews_full;

-- Delete old table
DROP TABLE place_reviews_full;

-- Re-run script (will create table with review_id column)
```

---

### Cause 3: Incorrect Limit in Testing
**Problem:**
```python
place_ids = get_place_ids_to_process(client, limit=5)
# Returns [Place_A, Place_B, Place_C, Place_D, Place_E]

# Run again:
place_ids = get_place_ids_to_process(client, limit=5)
# SHOULD return [] (all processed)
# BUT if query is wrong, might return same places!
```

**Solution:**
Check the query results:
```sql
-- This should return ZERO if all places processed:
SELECT COUNT(DISTINCT cid) 
FROM Map_location 
WHERE cid NOT IN (
    SELECT DISTINCT place_id 
    FROM place_reviews_full
)
```

---

## 💰 API Cost Optimization

### Current Costs Per Place:
```
1 place = ~3-5 pages (depends on review count)
1 page = 1 API call = 1 credit

Average: 3 credits per place
```

### How Script Saves Money:

**Without Protection:**
```
Run 1: Process 100 places = 300 API calls 💸
Run 2: Process 100 places = 300 API calls 💸 (SAME DATA!)
Run 3: Process 100 places = 300 API calls 💸 (SAME DATA!)

Total: 900 API calls
Wasted: 600 API calls (66%!)
```

**With Protection:**
```
Run 1: Process 100 places = 300 API calls 💸
Run 2: Process 0 places = 0 API calls ✅ (all already processed)
Run 3: Process 0 places = 0 API calls ✅ (all already processed)

Total: 300 API calls
Wasted: 0 API calls
Savings: 600 API calls saved! 🎉
```

---

## 🔍 How to Verify Protection is Working

### 1. Check for NEW Places
```sql
-- Should return 0 if all places processed:
SELECT COUNT(*) as unprocessed_places
FROM `shopper-reviews-477306.place_data.Map_location`
WHERE cid NOT IN (
    SELECT DISTINCT place_id 
    FROM `shopper-reviews-477306.place_data.place_reviews_full`
)
```

### 2. Check for Duplicates
```sql
-- Should show duplicates = 0:
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT review_id) as unique_reviews,
    COUNT(*) - COUNT(DISTINCT review_id) as duplicates
FROM `shopper-reviews-477306.place_data.place_reviews_full`
```

### 3. Check Script Logs
Look for these messages:
```
✅ Found 0 NEW place(s) to process          ← Good! No unnecessary API calls
💰 No API calls needed - saving credits!     ← Good! Money saved
⚠️ Place 123 already processed - SKIPPING    ← Good! Protection working
🔍 Removed 80 duplicate(s)                   ← Good! Duplicates filtered
📤 20 new review(s)                          ← Good! Only new data uploaded
```

---

## 📋 Best Practices

### ✅ DO:
1. **Run batch process normally** - it has all protections built-in
2. **Check logs** - look for "already processed" messages
3. **Verify before re-running** - query to see if places already have reviews
4. **Use incremental mode** - process only new places
5. **Monitor API usage** - check RapidAPI dashboard

### ❌ DON'T:
1. **Don't manually test same place twice** - wastes API credits
2. **Don't bypass the `get_place_ids_to_process()` function** - it has protection
3. **Don't remove the `review_id` column** - it prevents duplicates
4. **Don't run full batch twice** - second run should process 0 places
5. **Don't ignore warning logs** - they tell you when protection activates

---

## 🎯 Summary

### Protection Layers:
1. **Layer 1**: Query filters out already-processed places (saves API $$)
2. **Layer 2**: Double-check before each API call (extra safety)
3. **Layer 3**: review_id prevents duplicate inserts (data integrity)

### Cost Savings:
- **Before**: Wasting 60-90% of API calls on duplicate data
- **After**: 0% waste - only fetch NEW places, only insert NEW reviews

### Data Quality:
- **Before**: Multiple copies of same review in database
- **After**: Each review appears exactly once (enforced by review_id)

---

## 🆘 Troubleshooting

### "I'm still seeing duplicates!"

**Step 1: Check if old data exists**
```sql
SELECT COUNT(*) FROM place_reviews_full WHERE review_id IS NULL
```
If > 0: You have old data. Delete table and re-run.

**Step 2: Check script logs**
Look for: "⚠️ Place already processed"
If missing: Protection not activating. Check query.

**Step 3: Verify review_id exists**
```sql
SELECT review_id FROM place_reviews_full LIMIT 1
```
If NULL or error: Schema issue. Recreate table.

### "API calls still being made for old places!"

**Check the query:**
```python
# This query should exclude processed places:
place_ids = get_place_ids_to_process(client)
print(f"Found: {len(place_ids)}")  # Should be 0 if all processed
```

**Manual check:**
```sql
-- This should match the script's query:
SELECT cid FROM Map_location 
WHERE cid NOT IN (
    SELECT DISTINCT place_id FROM place_reviews_full
)
```

---

**Questions? Check the logs - they tell you exactly what's happening!** 📊
