#!/usr/bin/env python3
"""
Google Reviews Data Fetcher - FLATTENED SCHEMA with DEDUPLICATION

Fetches reviews from Google Reviews API and stores in BigQuery.
Features:
- Each review = one row with unique review_id
- Automatic deduplication (no duplicate reviews)
- Pagination handling
- Robust error handling
"""

import os
import json
import logging
import time
import hashlib
import http.client
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

# ==================== CONFIGURATION ====================

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', 'ac0025f410mshd0c260cb60f3db6p18c4b0jsnc9b7413cd574')
BIGQUERY_CREDENTIALS_JSON = os.getenv('BIGQUERY_KEY_JSON', None)

PROJECT_ID = "shopper-reviews-477306"
DATASET_ID = "place_data"
SOURCE_TABLE = "Map_location"
DESTINATION_TABLE = "place_reviews_full"

API_HOST = "google-search-master-mega.p.rapidapi.com"
API_ENDPOINT = "/reviews"
MAX_PAGES = 10
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

# ==================== LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('review_fetcher.log')]
)
logger = logging.getLogger(__name__)

# ==================== BIGQUERY CLIENT ====================

def get_bigquery_client() -> Optional[bigquery.Client]:
    """Creates BigQuery client with credentials."""
    try:
        if BIGQUERY_CREDENTIALS_JSON:
            credentials_dict = json.loads(BIGQUERY_CREDENTIALS_JSON)
        else:
            credentials_dict = {
                "type": "service_account",
                "project_id": "shopper-reviews-477306",
                "private_key_id": "679b00310997262ff77901f080075b509eb9c770",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCPrVXmepJWx8A8\nXLqDARbLqqmgPwQ4NEmCCOmAZ019aFToc0Yho0/hDyMhRhsW6z/5h8YVEbheb2oR\nmFK6/v3UEN1Mf6oJWag9pBngM6IO96QAzozjXjCmIVYJku1HWi+7b4mX7La8p77N\n5fJdOh30ceC6cJSDA51r2xGJDmchRPNhRR8CS9u3xAeZZeB/pgShwJcLM4WY4L3P\niwc7qkQb91NPbB2/p3hL/JJAtCvVKf61xlWGOKEGW3pIwBUUcF2/OJ3FTuWrY7P8\n1c/Kz9LUYOZpztK9zjFCNcnCQvvVAow9bqg3fw6xqE172dQT1FG6AieFSCyUib5B\nXxwNu0phAgMBAAECggEAET1ThPqIxqA54RmgnjQqP7k0Q0XBxDCvRUq7zIFuBdyC\nm6Wr8OtUnAT3Snh2qv2tSSFRKO6zDaRsDhJrPYQigX3zNR5Nu8jQlseIUfjqusWy\nHbqq+GPb4y3gJ06Zk/8uolyUHkZJTZe0cvuNZOxNSIBwM6QV3dE4OVx+3SV88GZ/\nOkAMCUpPRLJux6vJo+l0Qcfe074qjRYPv3XUaGXyHXeOZXmze/lLF6wsEzZmP1A+\nE9xZmP4ucM3ybrYi3ipRu6YwuR2mRASLy8VFMtcYCvNZGv6ODkjF2xmpucHwX78S\nzO3mGFES3Hnknjzoif5sJuBewNSztXJcQqKgtSpDhQKBgQDCS6bYj1VR691J5wxA\n5/fl2MwY4ALIKqW4RtJyNRBZ7+WDAVkq99R6lz+AmQsb6QyiZ/yTZHSUI61Bjn0p\nd2MD/fpQle7ZOMyR1gKZk5fE5lvmfA5sK+Aax3dRI7xjPBXJYI4hiCMAxgYdhgtI\nG1C/Nf6O2HoE/W2qLEnLZadpowKBgQC9Tl+/9Eq9Q/DI74CG78U0+s2aRq19vsXZ\n+wCIUm54TcN9xw4nPKYbT24nTVwTrOu2bxEgDVmuAqtWlKGad16LqZFTZ2aUaEFC\ni1HL8UKSy5XmNcum8mrKL5+MvwExcQUSmalE3PEQDRjV65QNld0EbQ6JNz74025z\nm+3ISpIEKwKBgADf5E1fP8wRmrplbtmv8Z64PhryjzCleH9+2h2nfX5aJRdU3zjh\nSrSOj7uddL5YazUj8LAdKKUuD+6WnJueLPTspL7OHfgeWFVjuDlGv80kGE/OSSZV\ngDm+ohvcZFGyCIsSgzFFcprjSU3Ct7RIYzGpJY8xDEOPfHninyZqO7mvAoGAIsog\ndppikd3Ghmbda+7sgwwEdPHAOHeyzJiARI1BmAJShu7p/vP6YtJ6H+broQIKX4CR\n2R4a+QusiUDPYh/F1EzZVEaQZ32xYJVR9vTjky6u4ZvJTWkHjxipbag8g+WNVRnA\nLdOcyaJeihG9J7H+6C1Smoz4manhhoWFcWWi5/kCgYEAssgWnlZCygCjEQ/XDVtZ\nC8/uelJnMHO93U4yF6Xk61gazKYpXpKjNkD3xfxAyQ3zkBkWo7CXg1env8pT9ld1\nraWCeCmH/w8i0ww3Cmplks5mXIYPrPPuUCEW5D6B8hIyNC1VIoaOlva8+FgJYPIv\nC5AqN3hBRDOUbophIQmAe5I=\n-----END PRIVATE KEY-----\n",
                "client_email": "demand@shopper-reviews-477306.iam.gserviceaccount.com",
                "client_id": "100956109416744224832",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/demand%40shopper-reviews-477306.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com"
            }
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        logger.info(f"✅ Connected to BigQuery: {PROJECT_ID}")
        return client
        
    except Exception as e:
        logger.error(f"❌ BigQuery client error: {e}")
        return None

# ==================== API FUNCTIONS ====================

def fetch_reviews_for_place(place_id: str, page: int = 1) -> Optional[Dict[str, Any]]:
    """Fetches one page of reviews from API."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            conn = http.client.HTTPSConnection(API_HOST)
            headers = {'x-rapidapi-key': RAPIDAPI_KEY, 'x-rapidapi-host': API_HOST}
            params = f"?cid={place_id}&sortBy=mostRelevant&gl=us&hl=en&page={page}"
            
            logger.info(f"📡 Fetching page {page} for CID {place_id}...")
            
            conn.request("GET", API_ENDPOINT + params, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                result = json.loads(data.decode("utf-8"))
                logger.info(f"✅ Page {page} fetched")
                return result
            else:
                logger.warning(f"⚠️ API status {res.status}, attempt {attempt + 1}/{RETRY_ATTEMPTS}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)
                    
        except Exception as e:
            logger.error(f"❌ Error: {e}, attempt {attempt + 1}/{RETRY_ATTEMPTS}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
    
    return None


def fetch_all_reviews_for_place(place_id: str) -> Dict[str, Any]:
    """Fetches ALL reviews with pagination."""
    all_reviews = []
    page = 1
    
    logger.info(f"🔍 Fetching reviews for CID {place_id}...")
    
    while page <= MAX_PAGES:
        result = fetch_reviews_for_place(place_id, page)
        
        if not result:
            break
        
        reviews = result.get('reviews', [])
        all_reviews.extend(reviews)
        
        logger.info(f"✅ Page {page}: {len(reviews)} reviews")
        
        if not result.get('nextPageToken') or len(reviews) == 0:
            break
        
        page += 1
        time.sleep(0.5)
    
    logger.info(f"🎉 Total: {len(all_reviews)} reviews")
    
    return {
        'place_id': place_id,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
        'pages_fetched': page
    }

# ==================== DATA PROCESSING ====================

def generate_review_id(place_id: str, iso_date: str, reviewer_name: str, snippet: str) -> str:
    """Generates unique review ID using hash."""
    unique_string = f"{place_id}_{iso_date}_{reviewer_name}_{snippet[:100]}"
    review_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:16]
    return review_id


def flatten_reviews_to_rows(review_data: Dict[str, Any]) -> pd.DataFrame:
    """Flattens reviews with unique review_id for each row."""
    place_id = review_data['place_id']
    reviews = review_data['reviews']
    current_time = datetime.now(timezone.utc)
    current_date = current_time.date()
    
    rows = []
    
    for review in reviews:
        user = review.get('user', {})
        iso_date = review.get('isoDate', '')
        
        try:
            iso_timestamp = datetime.fromisoformat(iso_date.replace('Z', '+00:00')) if iso_date else None
        except:
            iso_timestamp = None
        
        reviewer_name = user.get('name', '')
        snippet = review.get('snippet', '')
        
        # Generate unique review_id
        review_id = generate_review_id(place_id, iso_date, reviewer_name, snippet)
        
        row = {
            'review_id': review_id,
            'place_id': place_id,
            'rating': review.get('rating'),
            'date': review.get('date'),
            'isoDate': iso_timestamp,
            'snippet': snippet,
            'likes': review.get('likes'),
            'reviewer_name': reviewer_name,
            'reviewer_link': user.get('link'),
            'reviewer_thumbnail': user.get('thumbnail'),
            'reviewer_reviews': user.get('reviews'),
            'reviewer_photos': user.get('photos'),
            'timestamp': current_time,
            'fetch_date': current_date,
        }
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    logger.info(f"✅ Flattened {len(rows)} reviews with unique review_ids")
    return df

# ==================== BIGQUERY OPERATIONS ====================

def get_existing_review_ids(client: bigquery.Client) -> set:
    """Gets existing review_ids to prevent duplicates."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        client.get_table(table_id)
        
        query = f"""
        SELECT DISTINCT review_id
        FROM `{table_id}`
        WHERE review_id IS NOT NULL
        """
        
        result = client.query(query).to_dataframe()
        existing_ids = set(result['review_id'].tolist())
        
        logger.info(f"📊 Found {len(existing_ids)} existing review IDs")
        return existing_ids
        
    except Exception:
        logger.info("No existing reviews found")
        return set()


def remove_duplicate_reviews(df: pd.DataFrame, client: bigquery.Client) -> pd.DataFrame:
    """Removes reviews that already exist in BigQuery."""
    if df.empty:
        return df
    
    original_count = len(df)
    existing_ids = get_existing_review_ids(client)
    
    if not existing_ids:
        logger.info("✅ No existing reviews, uploading all")
        return df
    
    df_filtered = df[~df['review_id'].isin(existing_ids)].copy()
    
    duplicates_removed = original_count - len(df_filtered)
    
    if duplicates_removed > 0:
        logger.info(f"🔍 Removed {duplicates_removed} duplicate(s)")
        logger.info(f"📤 {len(df_filtered)} new review(s)")
    else:
        logger.info(f"✅ All {original_count} review(s) are new")
    
    return df_filtered


def create_reviews_table_if_not_exists(client: bigquery.Client) -> bool:
    """Creates table with review_id as primary key."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        try:
            client.get_table(table_id)
            logger.info(f"✅ Table exists: {DESTINATION_TABLE}")
            return True
        except:
            pass
        
        schema = [
            bigquery.SchemaField("review_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("place_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("rating", "INTEGER"),
            bigquery.SchemaField("date", "STRING"),
            bigquery.SchemaField("isoDate", "TIMESTAMP"),
            bigquery.SchemaField("snippet", "STRING"),
            bigquery.SchemaField("likes", "INTEGER"),
            bigquery.SchemaField("reviewer_name", "STRING"),
            bigquery.SchemaField("reviewer_link", "STRING"),
            bigquery.SchemaField("reviewer_thumbnail", "STRING"),
            bigquery.SchemaField("reviewer_reviews", "INTEGER"),
            bigquery.SchemaField("reviewer_photos", "INTEGER"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("fetch_date", "DATE"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        
        logger.info(f"✅ Created table: {DESTINATION_TABLE} (with review_id)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table creation error: {e}")
        return False


def get_place_ids_to_process(client: bigquery.Client, limit: int = None) -> List[str]:
    """Gets CIDs from Map_location that need processing."""
    source_table = f"{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}"
    
    try:
        dest_table = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
        
        try:
            client.get_table(dest_table)
            query = f"""
            SELECT DISTINCT cid as place_id
            FROM `{source_table}`
            WHERE cid IS NOT NULL
            AND cid NOT IN (
                SELECT DISTINCT place_id
                FROM `{dest_table}`
                WHERE place_id IS NOT NULL
            )
            """
            if limit:
                query += f" LIMIT {limit}"
            logger.info("📊 Reading 'cid' column...")
        except:
            query = f"""
            SELECT DISTINCT cid as place_id
            FROM `{source_table}`
            WHERE cid IS NOT NULL
            """
            if limit:
                query += f" LIMIT {limit}"
            logger.info("📊 Reading all CIDs...")
        
        result = client.query(query).to_dataframe()
        place_ids = result['place_id'].tolist()
        
        logger.info(f"✅ Found {len(place_ids)} CID(s)")
        return place_ids
        
    except Exception as e:
        logger.error(f"❌ Error fetching CIDs: {e}")
        return []


def upload_review_data_to_bigquery(client: bigquery.Client, review_data: Dict[str, Any]) -> bool:
    """Uploads reviews with automatic deduplication."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        df = flatten_reviews_to_rows(review_data)
        
        if df.empty:
            logger.warning("No reviews")
            return False
        
        # Remove duplicates
        df = remove_duplicate_reviews(df, client)
        
        if df.empty:
            logger.info("⚠️ All reviews already exist, skipping")
            return True
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        
        logger.info(f"Uploading {len(df)} new review(s)...")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Uploaded {len(df)} new review(s)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        return False

# ==================== MAIN ====================

def main():
    """Main entry point."""
    logger.info("🚀 Starting Review Fetcher")
    logger.info(f"📊 Source: {SOURCE_TABLE} (cid)")
    logger.info(f"📊 Destination: {DESTINATION_TABLE} (with review_id + deduplication)")
    
    client = get_bigquery_client()
    if not client:
        return
    
    if not create_reviews_table_if_not_exists(client):
        return
    
    place_ids = get_place_ids_to_process(client, limit=5)
    
    if not place_ids:
        logger.info("✅ No new places!")
        return
    
    logger.info(f"\n📊 Processing {len(place_ids)} place(s)...\n")
    
    successful = 0
    failed = 0
    skipped = 0
    total_new_reviews = 0
    
    for idx, place_id in enumerate(place_ids, 1):
        try:
            logger.info(f"\n📍 Place {idx}/{len(place_ids)}: {place_id}")
            
            review_data = fetch_all_reviews_for_place(place_id)
            
            if review_data['total_reviews'] == 0:
                logger.warning("⚠️ No reviews, skipping")
                skipped += 1
                continue
            
            if upload_review_data_to_bigquery(client, review_data):
                successful += 1
                # Count only new reviews (after deduplication)
                df = flatten_reviews_to_rows(review_data)
                df_new = remove_duplicate_reviews(df, client)
                total_new_reviews += len(df_new)
                logger.info(f"✅ Success")
            else:
                failed += 1
                
        except KeyboardInterrupt:
            logger.info(f"\n⚠️ Interrupted! Progress: {successful} done")
            break
            
        except Exception as e:
            failed += 1
            logger.error(f"❌ Error: {e}")
        
        if idx < len(place_ids):
            time.sleep(1)
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⏭️ Skipped: {skipped}")
    logger.info(f"📊 New Reviews Added: {total_new_reviews}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
