#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map Location Data Collector
Fetches location data from RapidAPI and uploads to BigQuery
"""

# --- IMPORTS ---
import os
import sys
import re
import json
import logging
import argparse
import requests
import pandas as pd
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError
from pathlib import Path

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 3. IN-MEMORY CACHE ---
API_CACHE: Dict[str, Any] = {}

# --- CONFIGURATION ---
# Load from environment variables
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
BIGQUERY_CREDENTIALS_PATH = os.getenv('BIGQUERY_CREDENTIALS_PATH')
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'shopper-reviews-477306')
DATASET_ID = os.getenv('GCP_DATASET_ID', 'place_data')
TABLE_ID = os.getenv('GCP_TABLE_ID', 'Map_location')

logger = logging.getLogger(__name__)

# --- FUNCTIONS FOR PART 1 ---

def search_by_place_name(place_name: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Fetches data for a *single* query from the RapidAPI.
    
    Args:
        place_name: The place to search for
        api_key: RapidAPI key (uses global RAPIDAPI_KEY if not provided)
    
    Returns:
        Dictionary containing place data or None on error
    """
    if place_name in API_CACHE:
        logger.info(f"Loading '{place_name}' from cache")
        return API_CACHE[place_name]

    logger.info(f"Calling API for '{place_name}'")

    api_key = api_key or RAPIDAPI_KEY
    API_HOST = "google-search-master-mega.p.rapidapi.com"

    if not api_key:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return None

    url = f"https://{API_HOST}/maps"
    querystring = {"q": place_name, "hl": "en", "page": "1"}
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": API_HOST}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)

        if response.status_code == 200:
            data = response.json()
            API_CACHE[place_name] = data
            logger.info(f"Successfully fetched data for '{place_name}'")
            return data
        else:
            logger.error(f"API returned status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for '{place_name}': {e}")
        return None

def collect_places_for_query(query: str) -> Optional[pd.DataFrame]:
    """
    Collects place data for a single query.
    
    Args:
        query: The place name to search for
    
    Returns:
        DataFrame with place data or None on error
    """
    results_data = search_by_place_name(query)

    if results_data and 'places' in results_data and results_data['places']:
        try:
            df = pd.json_normalize(results_data['places'])
            df['search_query'] = query
            logger.info(f"Collected {len(df)} places for '{query}'")
            return df
        except Exception as e:
            logger.error(f"Error processing data for '{query}': {e}")
            return None
    else:
        logger.warning(f"No 'places' found for '{query}'")
        return None


def run_data_collection_loop() -> Optional[pd.DataFrame]:
    """
    Interactive loop to collect user queries and build a DataFrame.
    
    Returns:
        DataFrame with all collected place data or None if no data collected
    """
    all_dataframes_list: List[pd.DataFrame] = []

    print("\nWelcome to the Place Searcher. (Type 'exit' to quit)")

    while True:
        try:
            query = input("\nEnter the place name to search for: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting data collection...")
            break

        if query.lower() == 'exit':
            logger.info("User requested exit")
            break

        if query:
            df = collect_places_for_query(query)
            if df is not None:
                all_dataframes_list.append(df)
        else:
            print("No search query entered. Please try again.")

    if not all_dataframes_list:
        logger.warning("No data was collected")
        return None

    return pd.concat(all_dataframes_list, ignore_index=True)


def collect_places_from_list(place_names: List[str]) -> Optional[pd.DataFrame]:
    """
    Collects place data for a list of place names (non-interactive).
    
    Args:
        place_names: List of place names to search for
    
    Returns:
        DataFrame with all collected place data or None if no data collected
    """
    all_dataframes_list: List[pd.DataFrame] = []

    for query in place_names:
        query = query.strip()
        if query:
            df = collect_places_for_query(query)
            if df is not None:
                all_dataframes_list.append(df)

    if not all_dataframes_list:
        logger.warning("No data was collected")
        return None

    return pd.concat(all_dataframes_list, ignore_index=True)


# --- FUNCTIONS FOR PART 2: BigQuery Upload ---

def combine_opening_hours(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combines all openingHours columns into a single JSON string column.
    
    Finds columns like 'openingHours.Monday', 'openingHours.Tuesday', etc.
    and combines them into a single 'openingHours' column as a JSON string.
    Also cleans Unicode characters for better readability.
    
    Args:
        df: DataFrame with potentially separate openingHours columns
        
    Returns:
        DataFrame with combined openingHours column
    """
    df_copy = df.copy()
    
    # Find all columns that start with 'openingHours.'
    opening_hours_cols = [col for col in df_copy.columns if col.startswith('openingHours.')]
    
    if opening_hours_cols:
        logger.info(f"Combining {len(opening_hours_cols)} openingHours columns into one")
        
        def clean_hours_text(text):
            """Clean Unicode characters from opening hours text"""
            if not isinstance(text, str):
                return text
            
            # Replace Unicode characters with standard equivalents
            text = text.replace('\u202f', ' ')      # Narrow no-break space → regular space
            text = text.replace('\u2013', '-')      # En dash → hyphen
            text = text.replace('\u2014', '-')      # Em dash → hyphen
            text = text.replace('\xa0', ' ')        # Non-breaking space → regular space
            text = text.replace('\u2009', ' ')      # Thin space → regular space
            
            # Remove multiple spaces
            text = ' '.join(text.split())
            
            return text
        
        # Create a new column with dictionary of all opening hours
        def combine_hours_row(row):
            hours_dict = {}
            for col in opening_hours_cols:
                # Extract day name (e.g., 'Monday' from 'openingHours.Monday')
                day = col.replace('openingHours.', '')
                value = row[col]
                # Only add if not null/empty
                if pd.notna(value) and value != '':
                    # Clean the value
                    cleaned_value = clean_hours_text(value)
                    hours_dict[day] = cleaned_value
            # Return as JSON string for BigQuery compatibility
            return json.dumps(hours_dict, ensure_ascii=False) if hours_dict else None
        
        # Create the combined column
        df_copy['openingHours'] = df_copy.apply(combine_hours_row, axis=1)
        
        # Drop the individual columns
        df_copy = df_copy.drop(columns=opening_hours_cols)
        
        logger.info(f"✅ Combined openingHours columns into single JSON column")
    
    return df_copy


def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitizes DataFrame column names to be BigQuery-compatible.
    
    BigQuery column names must:
    - Contain only letters, numbers, and underscores
    - Start with a letter or underscore
    - Be at most 300 characters long
    
    Args:
        df: DataFrame with potentially invalid column names
        
    Returns:
        DataFrame with sanitized column names
    """
    new_columns = {}
    for col in df.columns:
        # Replace dots, spaces, and other special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', col)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'column_' + str(df.columns.get_loc(col))
        
        # Limit to 300 characters
        sanitized = sanitized[:300]
        
        # Handle duplicates by appending number
        if sanitized in new_columns.values():
            counter = 1
            while f"{sanitized}_{counter}" in new_columns.values():
                counter += 1
            sanitized = f"{sanitized}_{counter}"
        
        new_columns[col] = sanitized
    
    df_copy = df.copy()
    df_copy.columns = [new_columns[col] for col in df.columns]
    
    logger.info(f"Sanitized {len([c for c in df.columns if c != new_columns[c]])} column names for BigQuery compatibility")
    
    return df_copy


def check_table_exists(table_id: str = None) -> bool:
    """
    Checks if a BigQuery table exists.
    
    Args:
        table_id: Full table ID in format project.dataset.table
        
    Returns:
        True if table exists, False otherwise
    """
    client = get_bigquery_client()
    if not client:
        return False
    
    table_id = table_id or f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    try:
        client.get_table(table_id)
        logger.info(f"Table {table_id} exists")
        return True
    except Exception:
        logger.info(f"Table {table_id} does not exist")
        return False


def create_bigquery_table(table_id: str = None, schema: List[bigquery.SchemaField] = None) -> bool:
    """
    Creates a new BigQuery table.
    
    Args:
        table_id: Full table ID in format project.dataset.table
        schema: List of SchemaField objects (optional, will auto-detect if not provided)
        
    Returns:
        True if creation successful, False otherwise
    """
    client = get_bigquery_client()
    if not client:
        return False
    
    table_id = table_id or f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    try:
        # Check if table already exists
        if check_table_exists(table_id):
            logger.info(f"Table {table_id} already exists, skipping creation")
            return True
        
        # Create table object
        table = bigquery.Table(table_id, schema=schema)
        
        # Create the table
        table = client.create_table(table)
        logger.info(f"✅ Created table {table_id}")
        return True
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False


def get_bigquery_client(credentials_path: str = None) -> Optional[bigquery.Client]:
    """
    Creates and returns a BigQuery client with proper credentials.
    
    Args:
        credentials_path: Path to service account JSON file
        
    Returns:
        BigQuery client or None on error
    """
    credentials_path = credentials_path or BIGQUERY_CREDENTIALS_PATH
    
    if not credentials_path:
        logger.error("BIGQUERY_CREDENTIALS_PATH not set in environment")
        return None
    
    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found: {credentials_path}")
        return None
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        logger.info(f"Connected to BigQuery project: {PROJECT_ID}")
        return client
    except Exception as e:
        logger.error(f"Error creating BigQuery client: {e}")
        return None


def upload_to_bigquery(df: pd.DataFrame, table_id: str = None, create_if_needed: bool = True) -> bool:
    """
    Uploads a DataFrame to BigQuery.
    Creates the table on first run, then appends on subsequent runs.
    
    Args:
        df: DataFrame to upload
        table_id: Full table ID in format project.dataset.table
        create_if_needed: If True, creates table if it doesn't exist
        
    Returns:
        True if upload successful, False otherwise
    """
    if df is None or df.empty:
        logger.warning("Cannot upload empty DataFrame")
        return False
    
    client = get_bigquery_client()
    if not client:
        return False
    
    table_id = table_id or f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Combine openingHours columns into one
    df = combine_opening_hours(df)
    
    # Sanitize column names for BigQuery compatibility
    df = sanitize_column_names(df)
    
    # Check if table exists
    table_exists = check_table_exists(table_id)
    
    if not table_exists:
        if create_if_needed:
            logger.info(f"Table does not exist. Creating table {table_id}...")
            # First, create table with schema from first batch of data
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Create new table
                autodetect=True,  # Auto-detect schema
            )
        else:
            logger.error(f"Table {table_id} does not exist and create_if_needed=False")
            return False
    else:
        logger.info(f"Table exists. Appending data to {table_id}...")
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",  # Append to existing table
            autodetect=False,  # Use existing schema
        )
    
    try:
        logger.info(f"Uploading {len(df)} rows to {table_id}")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete
        
        if not table_exists and create_if_needed:
            logger.info(f"✅ Successfully created table and uploaded {len(df)} rows to {table_id}")
        else:
            logger.info(f"✅ Successfully appended {len(df)} rows to {table_id}")
        return True
    except Exception as e:
        logger.error(f"Error uploading to BigQuery: {e}")
        return False


def save_to_csv(df: pd.DataFrame, output_path: str) -> bool:
    """
    Saves DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to save CSV file
        
    Returns:
        True if save successful, False otherwise
    """
    if df is None or df.empty:
        logger.warning("Cannot save empty DataFrame")
        return False
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Data saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        return False


# --- MAIN EXECUTION ---

def main():
    """
    Main execution function with argument parsing.
    """
    parser = argparse.ArgumentParser(
        description='Collect location data from RapidAPI and upload to BigQuery'
    )
    parser.add_argument(
        '--mode',
        choices=['interactive', 'batch'],
        default='interactive',
        help='Run in interactive mode or batch mode'
    )
    parser.add_argument(
        '--places',
        nargs='+',
        help='List of place names to search (batch mode only)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to file with place names (one per line, batch mode only)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save results to CSV file instead of uploading to BigQuery'
    )
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Skip BigQuery upload (useful for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate required environment variables
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY environment variable not set")
        sys.exit(1)
    
    # Collect data based on mode
    collected_data_df = None
    
    if args.mode == 'interactive':
        logger.info("Starting interactive mode")
        collected_data_df = run_data_collection_loop()
    
    elif args.mode == 'batch':
        place_names = []
        
        if args.places:
            place_names = args.places
        elif args.file:
            if not os.path.exists(args.file):
                logger.error(f"File not found: {args.file}")
                sys.exit(1)
            with open(args.file, 'r') as f:
                place_names = [line.strip() for line in f if line.strip()]
        else:
            logger.error("Batch mode requires --places or --file argument")
            sys.exit(1)
        
        logger.info(f"Processing {len(place_names)} places in batch mode")
        collected_data_df = collect_places_from_list(place_names)
    
    # Process collected data
    if collected_data_df is not None and not collected_data_df.empty:
        logger.info(f"Data collection complete. Total places: {len(collected_data_df)}")
        print(f"\n✅ Collected {len(collected_data_df)} places")
        print("\nFirst 5 rows:")
        print(collected_data_df.head())
        
        # Save or upload data
        if args.output:
            save_to_csv(collected_data_df, args.output)
        
        if not args.no_upload and not args.output:
            upload_to_bigquery(collected_data_df)
        elif args.no_upload:
            logger.info("Skipping BigQuery upload (--no-upload flag set)")
    else:
        logger.warning("No data was collected")
        sys.exit(1)


if __name__ == "__main__":
    main()
