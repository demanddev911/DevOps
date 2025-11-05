#!/usr/bin/env python3
"""
Google Reviews Data Fetcher and BigQuery Uploader - FLATTENED SCHEMA

Fetches full review data from Google Reviews API and stores in BigQuery.
Each review is stored as ONE row with individual columns (no JSON).

Features:
- FLATTENED structure: Each review = One row
- Incremental processing (timestamp-based)
- Pagination handling (nextPageToken)
- Robust error handling and retries
- Progress tracking and logging
"""

import os
import json
import logging
import time
import http.client
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

# ==================== CONFIGURATION ====================

# Load secrets from environment variables or hardcode for testing
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', 'ac0025f410mshd0c260cb60f3db6p18c4b0jsnc9b7413cd574')
BIGQUERY_CREDENTIALS_JSON = os.getenv('BIGQUERY_KEY_JSON', None)

# BigQuery configuration
PROJECT_ID = "shopper-reviews-477306"
DATASET_ID = "place_data"
SOURCE_TABLE = "Map_location"  # Source table (reads from 'cid' column)
DESTINATION_TABLE = "place_reviews_full"  # FLATTENED table

# API configuration
API_HOST = "google-search-master-mega.p.rapidapi.com"
API_ENDPOINT = "/reviews"
MAX_PAGES = 10  # Maximum pages to fetch per place (safety limit)
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# ==================== LOGGING SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('review_fetcher.log')
    ]
)
logger = logging.getLogger(__name__)

# ==================== BIGQUERY CLIENT ====================

def get_bigquery_client() -> Optional[bigquery.Client]:
    """Creates and returns a BigQuery client with proper credentials."""
    try:
        if BIGQUERY_CREDENTIALS_JSON:
            credentials_dict = json.loads(BIGQUERY_CREDENTIALS_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        else:
            # Fallback to hardcoded credentials
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
        logger.info(f"✅ Connected to BigQuery project: {PROJECT_ID}")
        return client
        
    except Exception as e:
        logger.error(f"❌ Error creating BigQuery client: {e}")
        return None

# ==================== API FUNCTIONS ====================

def fetch_reviews_for_place(place_id: str, page: int = 1) -> Optional[Dict[str, Any]]:
    """Fetches review data for a single page from Google Reviews API."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            conn = http.client.HTTPSConnection(API_HOST)
            
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': API_HOST
            }
            
            params = f"?cid={place_id}&sortBy=mostRelevant&gl=us&hl=en&page={page}"
            endpoint = API_ENDPOINT + params
            
            logger.info(f"📡 Fetching page {page} for CID {place_id}...")
            
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                result = json.loads(data.decode("utf-8"))
                logger.info(f"✅ Page {page} fetched successfully")
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
    """Fetches ALL reviews for a place by following pagination."""
    all_reviews = []
    all_topics = []
    metadata = {}
    page = 1
    
    logger.info(f"🔍 Fetching all reviews for CID {place_id}...")
    
    while page <= MAX_PAGES:
        result = fetch_reviews_for_place(place_id, page)
        
        if not result:
            logger.warning(f"⚠️ No data for page {page}, stopping")
            break
        
        reviews = result.get('reviews', [])
        all_reviews.extend(reviews)
        
        if page == 1:
            all_topics = result.get('topics', [])
            metadata = {
                'searchParameters': result.get('searchParameters', {}),
                'credits': result.get('credits', 0),
            }
        
        logger.info(f"✅ Page {page}: {len(reviews)} reviews")
        
        next_page_token = result.get('nextPageToken')
        if not next_page_token or len(reviews) == 0:
            logger.info(f"✅ All pages fetched (stopped at page {page})")
            break
        
        page += 1
        time.sleep(0.5)
    
    logger.info(f"🎉 Total: {len(all_reviews)} reviews, {len(all_topics)} topics")
    
    return {
        'place_id': place_id,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
        'topics': all_topics,
        'metadata': metadata,
        'pages_fetched': page
    }

# ==================== DATA FLATTENING ====================

def flatten_reviews_to_rows(review_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Flattens review data into individual rows.
    Each review becomes ONE row with all fields as separate columns.
    
    Args:
        review_data: Dictionary containing review data from API
        
    Returns:
        DataFrame with flattened review rows (one row per review)
    """
    place_id = review_data['place_id']
    reviews = review_data['reviews']
    current_time = datetime.now(timezone.utc)
    current_date = current_time.date()
    
    rows = []
    
    for review in reviews:
        # Extract user data safely
        user = review.get('user', {})
        
        # Parse ISO date
        iso_date = review.get('isoDate')
        try:
            iso_timestamp = datetime.fromisoformat(iso_date.replace('Z', '+00:00')) if iso_date else None
        except:
            iso_timestamp = None
        
        # Create flattened row - each review = one row
        row = {
            'place_id': place_id,
            'rating': review.get('rating'),
            'date': review.get('date'),
            'isoDate': iso_timestamp,
            'snippet': review.get('snippet'),
            'likes': review.get('likes'),
            'reviewer_name': user.get('name'),
            'reviewer_link': user.get('link'),
            'reviewer_thumbnail': user.get('thumbnail'),
            'reviewer_reviews': user.get('reviews'),
            'reviewer_photos': user.get('photos'),
            'timestamp': current_time,
            'fetch_date': current_date,
        }
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    logger.info(f"✅ Flattened {len(rows)} reviews into individual rows")
    return df

# ==================== BIGQUERY OPERATIONS ====================

def get_place_ids_to_process(client: bigquery.Client, limit: int = None) -> List[str]:
    """
    Retrieves CIDs from the source table (Map_location) that need reviews fetched.
    Reads from 'cid' column.
    """
    source_table = f"{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}"
    
    try:
        dest_table = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
        
        try:
            client.get_table(dest_table)
            # Table exists, exclude already processed places
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
            logger.info("📊 Reading 'cid' column from Map_location table...")
        except:
            # Table doesn't exist yet, process all
            query = f"""
            SELECT DISTINCT cid as place_id
            FROM `{source_table}`
            WHERE cid IS NOT NULL
            """
            if limit:
                query += f" LIMIT {limit}"
            logger.info("📊 Destination table doesn't exist, reading all CIDs from Map_location...")
        
        result = client.query(query).to_dataframe()
        place_ids = result['place_id'].tolist()
        
        logger.info(f"✅ Found {len(place_ids)} CID(s) to process from 'cid' column")
        return place_ids
        
    except Exception as e:
        logger.error(f"❌ Error fetching CIDs from 'cid' column: {e}")
        return []


def create_reviews_table_if_not_exists(client: bigquery.Client) -> bool:
    """
    Creates the place_reviews_full table with FLATTENED structure.
    Each review is stored as a separate row with individual columns.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        # Check if table exists
        try:
            client.get_table(table_id)
            logger.info(f"✅ Table {DESTINATION_TABLE} already exists")
            return True
        except:
            pass
        
        # Create FLATTENED table schema - each review is a separate row
        schema = [
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
        table = client.create_table(table)
        
        logger.info(f"✅ Created FLATTENED table {DESTINATION_TABLE} (each review = one row)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        return False


def upload_review_data_to_bigquery(client: bigquery.Client, review_data: Dict[str, Any]) -> bool:
    """
    Uploads FLATTENED review data to BigQuery.
    Each review is stored as a separate row.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        # Flatten reviews into individual rows
        df = flatten_reviews_to_rows(review_data)
        
        if df.empty:
            logger.warning("No reviews to upload")
            return False
        
        # Upload to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        )
        
        logger.info(f"Uploading {len(df)} review row(s) for place {review_data['place_id']}...")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for job to complete
        
        logger.info(f"✅ Uploaded {len(df)} review row(s) for place {review_data['place_id']} to BigQuery")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error uploading to BigQuery: {e}")
        return False

# ==================== MAIN EXECUTION ====================

def process_single_place(client: bigquery.Client, place_id: str) -> bool:
    """Process reviews for a single place."""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"📍 Processing CID: {place_id}")
        logger.info(f"{'='*60}")
        
        # Fetch all reviews
        review_data = fetch_all_reviews_for_place(place_id)
        
        if review_data['total_reviews'] == 0:
            logger.warning("⚠️ No reviews found, skipping")
            return False
        
        # Upload to BigQuery (flattened format)
        if upload_review_data_to_bigquery(client, review_data):
            logger.info(f"✅ Success: {review_data['total_reviews']} review rows uploaded")
            return True
        else:
            logger.error("❌ Upload failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error processing place {place_id}: {e}")
        return False


def main():
    """Main entry point for the script."""
    logger.info("🚀 Starting Google Reviews Data Fetcher")
    logger.info(f"📊 Source: {PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE} (cid column)")
    logger.info(f"📊 Destination: {PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE} (FLATTENED)")
    logger.info(f"🗂️ Schema: Each review = One row with individual columns")
    
    # Get BigQuery client
    client = get_bigquery_client()
    if not client:
        logger.error("❌ Failed to create BigQuery client")
        return
    
    # Create destination table if needed
    if not create_reviews_table_if_not_exists(client):
        logger.error("❌ Failed to create destination table")
        return
    
    # Get places to process
    place_ids = get_place_ids_to_process(client, limit=5)  # Remove limit for full run
    
    if not place_ids:
        logger.info("✅ No new places to process!")
        return
    
    logger.info(f"\n📊 Processing {len(place_ids)} place(s)...\n")
    
    # Process each place
    successful = 0
    failed = 0
    skipped = 0
    total_review_rows = 0
    
    for idx, place_id in enumerate(place_ids, 1):
        try:
            logger.info(f"\n📍 Place {idx}/{len(place_ids)}: {place_id}")
            
            review_data = fetch_all_reviews_for_place(place_id)
            
            if review_data['total_reviews'] == 0:
                logger.warning("⚠️ No reviews found, skipping")
                skipped += 1
                continue
            
            if upload_review_data_to_bigquery(client, review_data):
                successful += 1
                total_review_rows += review_data['total_reviews']
                logger.info(f"✅ Success: {review_data['total_reviews']} review rows uploaded")
            else:
                failed += 1
                logger.error("❌ Upload failed")
                
        except KeyboardInterrupt:
            logger.info(f"\n⚠️ Interrupted by user. Progress: {successful} done, {failed} failed")
            break
            
        except Exception as e:
            failed += 1
            logger.error(f"❌ Error: {e}")
        
        # Rate limiting
        if idx < len(place_ids):
            time.sleep(1)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 FINAL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successful: {successful} places")
    logger.info(f"❌ Failed: {failed} places")
    logger.info(f"⏭️ Skipped: {skipped} places")
    logger.info(f"📊 Total Review Rows: {total_review_rows:,}")
    if successful > 0:
        logger.info(f"📊 Avg Reviews/Place: {total_review_rows/successful:.1f}")
    logger.info(f"{'='*60}")
    logger.info("✅ Script completed!")


if __name__ == "__main__":
    main()
