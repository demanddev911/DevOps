#!/usr/bin/env python3
"""
Google Reviews Data Fetcher and BigQuery Uploader
Fetches full review data for places from Google Reviews API and stores in BigQuery.

Features:
- Incremental processing (timestamp-based)
- Pagination handling (nextPageToken)
- Full data capture (reviews, topics, metadata)
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
SOURCE_TABLE = "Map_location"  # Table with place_ids
DESTINATION_TABLE = "place_reviews_full"  # Table to store reviews

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
    """
    Creates and returns a BigQuery client with proper credentials.
    
    Returns:
        BigQuery client or None on error
    """
    try:
        if BIGQUERY_CREDENTIALS_JSON:
            # Load from environment variable (JSON string)
            credentials_dict = json.loads(BIGQUERY_CREDENTIALS_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        else:
            # Load from hardcoded credentials (fallback)
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

# ==================== DATA FETCHING ====================

def fetch_reviews_for_place(place_id: str, page: int = 1) -> Optional[Dict[str, Any]]:
    """
    Fetches review data for a single place from Google Reviews API.
    
    Args:
        place_id: The place CID to fetch reviews for
        page: Page number to fetch (for pagination)
        
    Returns:
        Dictionary containing full API response or None on error
    """
    for attempt in range(RETRY_ATTEMPTS):
        try:
            conn = http.client.HTTPSConnection(API_HOST)
            
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': API_HOST
            }
            
            # Build query parameters
            params = f"?cid={place_id}&sortBy=mostRelevant&gl=us&hl=en&page={page}"
            endpoint = API_ENDPOINT + params
            
            logger.info(f"📡 Fetching page {page} for place {place_id}...")
            
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                result = json.loads(data.decode("utf-8"))
                logger.info(f"✅ Successfully fetched page {page} for place {place_id}")
                return result
            else:
                logger.warning(f"⚠️ API returned status {res.status} for place {place_id}, attempt {attempt + 1}/{RETRY_ATTEMPTS}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)
                    
        except Exception as e:
            logger.error(f"❌ Error fetching reviews for place {place_id}, attempt {attempt + 1}/{RETRY_ATTEMPTS}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
    
    return None


def fetch_all_reviews_for_place(place_id: str) -> Dict[str, Any]:
    """
    Fetches ALL reviews for a place by following pagination.
    
    Args:
        place_id: The place CID to fetch reviews for
        
    Returns:
        Dictionary containing aggregated review data:
        {
            'place_id': str,
            'total_reviews': int,
            'reviews': list of all reviews,
            'topics': list of topics,
            'metadata': dict of API metadata,
            'pages_fetched': int
        }
    """
    all_reviews = []
    all_topics = []
    metadata = {}
    page = 1
    
    logger.info(f"🔍 Starting to fetch all reviews for place {place_id}...")
    
    while page <= MAX_PAGES:
        result = fetch_reviews_for_place(place_id, page)
        
        if not result:
            logger.warning(f"⚠️ No data received for page {page}, stopping pagination")
            break
        
        # Extract reviews from this page
        reviews = result.get('reviews', [])
        all_reviews.extend(reviews)
        
        # Extract topics (usually same across pages, take from first page)
        if page == 1:
            all_topics = result.get('topics', [])
            metadata = {
                'searchParameters': result.get('searchParameters', {}),
                'credits': result.get('credits', 0),
            }
        
        logger.info(f"✅ Page {page}: {len(reviews)} reviews fetched")
        
        # Check for next page
        next_page_token = result.get('nextPageToken')
        if not next_page_token or len(reviews) == 0:
            logger.info(f"✅ No more pages available, stopping at page {page}")
            break
        
        page += 1
        time.sleep(0.5)  # Rate limiting
    
    logger.info(f"🎉 Completed fetching for place {place_id}: {len(all_reviews)} total reviews, {len(all_topics)} topics")
    
    return {
        'place_id': place_id,
        'total_reviews': len(all_reviews),
        'reviews': all_reviews,
        'topics': all_topics,
        'metadata': metadata,
        'pages_fetched': page,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

# ==================== BIGQUERY OPERATIONS ====================

def get_place_ids_to_process(client: bigquery.Client) -> List[str]:
    """
    Retrieves place IDs from the source table that need review data fetched.
    
    Args:
        client: BigQuery client
        
    Returns:
        List of place_id strings
    """
    source_table = f"{PROJECT_ID}.{DATASET_ID}.{SOURCE_TABLE}"
    
    try:
        # Check if destination table exists to find already processed places
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
            logger.info("📊 Fetching place_ids that haven't been processed yet...")
        except:
            # Table doesn't exist yet, process all
            query = f"""
            SELECT DISTINCT cid as place_id
            FROM `{source_table}`
            WHERE cid IS NOT NULL
            """
            logger.info("📊 Destination table doesn't exist, fetching all place_ids...")
        
        result = client.query(query).to_dataframe()
        place_ids = result['place_id'].tolist()
        
        logger.info(f"✅ Found {len(place_ids)} place(s) to process")
        return place_ids
        
    except Exception as e:
        logger.error(f"❌ Error fetching place IDs: {e}")
        return []


def create_reviews_table_if_not_exists(client: bigquery.Client) -> bool:
    """
    Creates the place_reviews_full table if it doesn't exist.
    
    Args:
        client: BigQuery client
        
    Returns:
        True if successful, False otherwise
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
        
        # Create table with schema (using STRING for JSON compatibility)
        schema = [
            bigquery.SchemaField("place_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("total_reviews", "INTEGER"),
            bigquery.SchemaField("pages_fetched", "INTEGER"),
            bigquery.SchemaField("reviews", "STRING"),  # JSON stored as STRING
            bigquery.SchemaField("topics", "STRING"),   # JSON stored as STRING
            bigquery.SchemaField("metadata", "STRING"), # JSON stored as STRING
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("fetch_date", "DATE"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        
        logger.info(f"✅ Created table {DESTINATION_TABLE}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        return False


def upload_review_data_to_bigquery(client: bigquery.Client, review_data: Dict[str, Any]) -> bool:
    """
    Uploads review data to BigQuery.
    
    Args:
        client: BigQuery client
        review_data: Dictionary containing review data
        
    Returns:
        True if successful, False otherwise
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{DESTINATION_TABLE}"
    
    try:
        # Prepare data for upload
        row = {
            'place_id': review_data['place_id'],
            'total_reviews': review_data['total_reviews'],
            'pages_fetched': review_data['pages_fetched'],
            'reviews': json.dumps(review_data['reviews']),
            'topics': json.dumps(review_data['topics']),
            'metadata': json.dumps(review_data['metadata']),
            'timestamp': datetime.now(timezone.utc),
            'fetch_date': datetime.now(timezone.utc).date(),
        }
        
        # Create DataFrame
        df = pd.DataFrame([row])
        
        # Upload to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for job to complete
        
        logger.info(f"✅ Uploaded review data for place {review_data['place_id']} to BigQuery")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error uploading to BigQuery: {e}")
        return False

# ==================== MAIN WORKFLOW ====================

def main():
    """
    Main workflow:
    1. Connect to BigQuery
    2. Get place IDs to process
    3. For each place ID:
       - Fetch all reviews (with pagination)
       - Upload to BigQuery
    4. Report summary
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Google Reviews Data Fetcher")
    logger.info("=" * 60)
    
    # Step 1: Connect to BigQuery
    client = get_bigquery_client()
    if not client:
        logger.error("❌ Failed to connect to BigQuery, exiting")
        return
    
    # Step 2: Create destination table if needed
    if not create_reviews_table_if_not_exists(client):
        logger.error("❌ Failed to create destination table, exiting")
        return
    
    # Step 3: Get place IDs to process
    place_ids = get_place_ids_to_process(client)
    
    if not place_ids:
        logger.info("✅ No new places to process, exiting")
        return
    
    logger.info(f"📊 Processing {len(place_ids)} place(s)...")
    
    # Step 4: Process each place
    successful = 0
    failed = 0
    
    for idx, place_id in enumerate(place_ids, 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"📍 Processing place {idx}/{len(place_ids)}: {place_id}")
        logger.info(f"{'=' * 60}")
        
        try:
            # Fetch all review data
            review_data = fetch_all_reviews_for_place(place_id)
            
            if review_data['total_reviews'] == 0:
                logger.warning(f"⚠️ No reviews found for place {place_id}, skipping")
                continue
            
            # Upload to BigQuery
            if upload_review_data_to_bigquery(client, review_data):
                successful += 1
                logger.info(f"✅ Successfully processed place {place_id}")
                logger.info(f"   📊 {review_data['total_reviews']} reviews, {len(review_data['topics'])} topics")
            else:
                failed += 1
                logger.error(f"❌ Failed to upload data for place {place_id}")
                
        except Exception as e:
            failed += 1
            logger.error(f"❌ Error processing place {place_id}: {e}")
        
        # Rate limiting between places
        if idx < len(place_ids):
            time.sleep(1)
    
    # Step 5: Report summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Total processed: {successful + failed}/{len(place_ids)}")
    logger.info("=" * 60)
    logger.info("🎉 Google Reviews Data Fetcher completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
