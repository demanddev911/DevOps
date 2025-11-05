# 🚨 How to Avoid Duplicates & Wasted API Calls

## Quick Answer

**Duplicates happen because Google's API returns the SAME reviews every time.**

**Solution: 3-layer protection system (already built-in!)**

---

## ✅ Protection System (Auto-Enabled)

### 1. Before Fetching (Saves API $$)
```
Script checks: "Did we already fetch this place?"
If YES → Skip API call (save money!)
If NO → Fetch reviews
```

### 2. Before Uploading (Prevents Duplicates)
```
Script checks: "Does this review_id already exist?"
If YES → Skip this review
If NO → Upload review
```

### 3. Result:
- **No duplicate reviews** in database ✅
- **No wasted API calls** for already-processed places ✅

---

## 🔍 How to Check if Protection is Working

### Run these queries in BigQuery:

```sql
-- 1. Check for duplicates (should show 0)
SELECT 
    COUNT(*) - COUNT(DISTINCT review_id) as duplicates
FROM `shopper-reviews-477306.place_data.place_reviews_full`;

-- 2. Check how many NEW places to process (should decrease over time)
SELECT COUNT(DISTINCT cid) as new_places
FROM `shopper-reviews-477306.place_data.Map_location`
WHERE cid NOT IN (
    SELECT DISTINCT place_id 
    FROM `shopper-reviews-477306.place_data.place_reviews_full`
);
```

**Expected Results:**
- Query 1: `duplicates = 0` ✅
- Query 2: First run = many places, second run = 0 places ✅

---

## 📊 What You Should See in Logs

### First Run (New Places):
```
✅ Found 100 NEW place(s) to process
💰 This will make ~300 API calls (avg 3 pages/place)
📍 Place 1/100: 123456
🔍 Fetching reviews...
✅ Uploaded 50 new review(s)
```

### Second Run (All Processed):
```
✅ All places already processed! No API calls needed.
💰 No API calls needed - saving your credits!
```

### If You Accidentally Re-run Same Place:
```
📍 Place 1/1: 123456
⚠️ Place 123456 already has 50 reviews in BigQuery!
⚠️ SKIPPING API call to avoid wasting credits
```

---

## 🚨 If You're STILL Getting Duplicates

### Possible Cause 1: Old Data Without review_id

**Check:**
```sql
SELECT COUNT(*) FROM place_reviews_full WHERE review_id IS NULL
```

**If result > 0:**
You have old data. Fix it:
```sql
-- Backup first!
CREATE TABLE place_reviews_full_backup AS 
SELECT * FROM place_reviews_full;

-- Delete old table
DROP TABLE place_reviews_full;

-- Re-run script (will recreate with review_id column)
```

---

### Possible Cause 2: Testing Same Place Multiple Times

**Problem:**
```python
# DON'T DO THIS:
test_place = "123456"
fetch_reviews(test_place)  # API call!
fetch_reviews(test_place)  # API call AGAIN! (waste!)
```

**Solution:**
Use the batch process - it has built-in protection:
```python
python review.py  # Automatically skips already-processed places
```

---

### Possible Cause 3: Manual Upload Without Deduplication

**Problem:**
```python
# DON'T DO THIS:
df = flatten_reviews_to_rows(review_data)
# Missing: df = remove_duplicate_reviews(df, client)  ← IMPORTANT!
upload_to_bigquery(df)  # Will insert duplicates!
```

**Solution:**
Use the `upload_review_data_to_bigquery()` function - it has deduplication built-in.

---

## 💡 Best Practices

### ✅ DO:
1. Run the script normally: `python review.py`
2. Check logs for "already processed" messages
3. Run these check queries regularly (see above)
4. Let the script handle everything automatically

### ❌ DON'T:
1. Don't manually fetch same place twice
2. Don't bypass the protection functions
3. Don't remove the `review_id` column
4. Don't ignore warning logs

---

## 💰 API Cost Savings

### Without Protection:
```
Run 1: 100 places × 3 calls = 300 API calls 💸
Run 2: 100 places × 3 calls = 300 API calls 💸 (SAME DATA!)
Total: 600 calls
Wasted: 300 calls (50%!)
```

### With Protection:
```
Run 1: 100 places × 3 calls = 300 API calls 💸
Run 2: 0 places × 0 calls = 0 API calls ✅ (all already processed)
Total: 300 calls
Wasted: 0 calls
Savings: 300 API calls! 🎉
```

---

## 📋 Quick Checklist

Before running script:
- [ ] Check how many NEW places exist (query #2 above)
- [ ] Check for duplicates in current data (query #1 above)
- [ ] Check logs from previous run

After running script:
- [ ] Verify log says "X new review(s)" (not total)
- [ ] Verify log shows "Removed X duplicate(s)"
- [ ] Run duplicate check query (should show 0)

---

## 🆘 Still Having Issues?

1. **Check the DUPLICATE_PREVENTION_GUIDE.md** for detailed explanation
2. **Run QUICK_CHECK.sql** queries in BigQuery for diagnostics
3. **Check script logs** - they tell you exactly what's happening

**The protection system is automatic - if you run the script normally, it should just work!** ✅
