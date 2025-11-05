-- ============================================
-- QUICK CHECKS FOR DUPLICATES & API WASTE
-- ============================================

-- 1. Check for duplicate reviews
-- (Should show duplicates = 0 if protection working)
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT review_id) as unique_reviews,
    COUNT(*) - COUNT(DISTINCT review_id) as duplicates,
    CASE 
        WHEN COUNT(*) - COUNT(DISTINCT review_id) = 0 THEN '✅ NO DUPLICATES'
        ELSE '⚠️ DUPLICATES FOUND'
    END as status
FROM `shopper-reviews-477306.place_data.place_reviews_full`;

-- 2. Check for places that will be processed
-- (Should show 0 if all places already processed)
SELECT 
    COUNT(DISTINCT cid) as unprocessed_places,
    CASE 
        WHEN COUNT(DISTINCT cid) = 0 THEN '✅ NO API CALLS NEEDED'
        ELSE CONCAT('💰 ', CAST(COUNT(DISTINCT cid) AS STRING), ' places = ~', CAST(COUNT(DISTINCT cid) * 3 AS STRING), ' API calls')
    END as api_cost_estimate
FROM `shopper-reviews-477306.place_data.Map_location`
WHERE cid IS NOT NULL
AND cid NOT IN (
    SELECT DISTINCT place_id 
    FROM `shopper-reviews-477306.place_data.place_reviews_full`
    WHERE place_id IS NOT NULL
);

-- 3. Check for old data without review_id
-- (Should show 0 rows - old data will cause issues)
SELECT 
    COUNT(*) as rows_without_review_id,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ ALL ROWS HAVE review_id'
        ELSE '⚠️ OLD DATA DETECTED - RECREATE TABLE'
    END as status
FROM `shopper-reviews-477306.place_data.place_reviews_full`
WHERE review_id IS NULL;

-- 4. Review count per place
-- (Shows which places have reviews and how many)
SELECT 
    place_id,
    COUNT(DISTINCT review_id) as unique_reviews,
    COUNT(*) as total_rows,
    COUNT(*) - COUNT(DISTINCT review_id) as duplicates_per_place,
    MIN(fetch_date) as first_fetch,
    MAX(fetch_date) as last_fetch,
    CASE 
        WHEN COUNT(*) - COUNT(DISTINCT review_id) > 0 THEN '⚠️ HAS DUPLICATES'
        ELSE '✅ NO DUPLICATES'
    END as status
FROM `shopper-reviews-477306.place_data.place_reviews_full`
GROUP BY place_id
ORDER BY duplicates_per_place DESC, unique_reviews DESC
LIMIT 20;

-- 5. Summary statistics
SELECT 
    'Total Places' as metric,
    COUNT(DISTINCT place_id) as value
FROM `shopper-reviews-477306.place_data.place_reviews_full`
UNION ALL
SELECT 
    'Total Reviews (unique)',
    COUNT(DISTINCT review_id)
FROM `shopper-reviews-477306.place_data.place_reviews_full`
UNION ALL
SELECT 
    'Total Rows',
    COUNT(*)
FROM `shopper-reviews-477306.place_data.place_reviews_full`
UNION ALL
SELECT 
    'Duplicate Rows',
    COUNT(*) - COUNT(DISTINCT review_id)
FROM `shopper-reviews-477306.place_data.place_reviews_full`;
