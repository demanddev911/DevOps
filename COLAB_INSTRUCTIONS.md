# 🚀 How to Run in Google Colab

## 📋 Quick Start

### Option 1: Upload the Notebook File
1. Go to [Google Colab](https://colab.research.google.com/)
2. Click **File → Upload notebook**
3. Upload `Map_Location_Colab.ipynb`
4. Follow the instructions in the notebook

### Option 2: Copy & Paste Code (No File Upload Needed)

Just follow these steps in a new Colab notebook:

---

## 🔐 STEP 1: Set Up Colab Secrets

Before running any code, set up your API keys:

1. Click the **🔑 (Key icon)** in the left sidebar
2. Click **"Add new secret"**
3. Add these two secrets:

**Secret 1:**
- Name: `RAPIDAPI_KEY`
- Value: Your RapidAPI key (get it from [RapidAPI](https://rapidapi.com/))

**Secret 2:**
- Name: `BIGQUERY_KEY_JSON`  
- Value: Your entire BigQuery service account JSON (copy the whole JSON file content)

Example JSON format:
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  ...
}
```

---

## 💻 STEP 2: Copy This Code to Colab

Create a new notebook in Colab and paste each cell below:

### Cell 1: Install Libraries
```python
!pip install -q pandas-gbq google-auth google-cloud-bigquery db-dtypes
```

### Cell 2: Import Libraries
```python
import requests
import pandas as pd
import json
from typing import Optional, Dict, Any, List
from google.colab import userdata
from google.oauth2 import service_account
from google.cloud import bigquery
from IPython.display import display
import warnings
warnings.filterwarnings('ignore')

print("✅ All libraries imported successfully!")
```

### Cell 3: Configuration
```python
# Configuration - Update these with your values
PROJECT_ID = 'shopper-reviews-477306'
DATASET_ID = 'place_data'
TABLE_ID = 'Map_location'

# Colab Secret names
RAPIDAPI_KEY_SECRET = 'RAPIDAPI_KEY'
BIGQUERY_KEY_SECRET = 'BIGQUERY_KEY_JSON'

# In-memory cache
API_CACHE = {}

print("✅ Configuration loaded!")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET_ID}")
print(f"   Table: {TABLE_ID}")
```

### Cell 4: Data Collection Functions
```python
def search_by_place_name(place_name: str) -> Optional[Dict[str, Any]]:
    """Fetches data for a single place from RapidAPI."""
    if place_name in API_CACHE:
        print(f"📦 Loading '{place_name}' from cache")
        return API_CACHE[place_name]

    print(f"🔍 Searching for '{place_name}'...")

    try:
        API_KEY = userdata.get(RAPIDAPI_KEY_SECRET)
    except Exception as e:
        print(f"❌ Error: Could not get '{RAPIDAPI_KEY_SECRET}' from Colab Secrets")
        return None

    API_HOST = "google-search-master-mega.p.rapidapi.com"
    url = f"https://{API_HOST}/maps"
    
    querystring = {"q": place_name, "hl": "en", "page": "1"}
    headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code == 200:
            data = response.json()
            API_CACHE[place_name] = data
            print(f"✅ Found data for '{place_name}'")
            return data
        else:
            print(f"❌ API Error: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None


def collect_places_for_query(query: str) -> Optional[pd.DataFrame]:
    """Collects and normalizes place data for a single query."""
    results_data = search_by_place_name(query)
    if results_data and 'places' in results_data and results_data['places']:
        try:
            df = pd.json_normalize(results_data['places'])
            df['search_query'] = query
            print(f"✅ Collected {len(df)} places for '{query}'")
            return df
        except Exception as e:
            print(f"❌ Error processing data: {e}")
            return None
    else:
        print(f"⚠️ No places found for '{query}'")
        return None


def run_data_collection_loop() -> Optional[pd.DataFrame]:
    """Interactive loop to collect user queries."""
    all_dataframes_list = []
    print("\\n" + "="*60)
    print("🗺️  PLACE SEARCHER")
    print("="*60)
    print("Type place names to search. Type 'exit' when done.\\n")

    while True:
        try:
            query = input("\\n🔍 Enter place name: ").strip()
        except KeyboardInterrupt:
            print("\\n⏹️ Stopping data collection...")
            break

        if query.lower() == 'exit':
            print("⏹️ Exiting data collection...")
            break

        if query:
            df = collect_places_for_query(query)
            if df is not None:
                all_dataframes_list.append(df)
                print(f"📊 Total queries collected: {len(all_dataframes_list)}")

    if not all_dataframes_list:
        print("\\n⚠️ No data was collected")
        return None
    return pd.concat(all_dataframes_list, ignore_index=True)

print("✅ Data collection functions defined!")
```

### Cell 5: COLLECT DATA (Run This)
```python
# Collect data interactively
collected_data_df = run_data_collection_loop()

# Display results
if collected_data_df is not None and not collected_data_df.empty:
    print("\\n" + "="*60)
    print("✅ DATA COLLECTION COMPLETE")
    print("="*60)
    print(f"📊 Total places collected: {len(collected_data_df)}")
    print(f"📋 Total columns: {len(collected_data_df.columns)}")
    print("\\n🔍 Preview (first 5 rows):")
    display(collected_data_df.head())
else:
    print("\\n❌ No data to process")
```

### Cell 6: BigQuery Upload Functions
```python
def get_bigquery_client() -> Optional[bigquery.Client]:
    """Creates BigQuery client using Colab Secrets."""
    try:
        credentials_json = userdata.get(BIGQUERY_KEY_SECRET)
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
        return client
    except Exception as e:
        print(f"❌ Error creating BigQuery client: {e}")
        return None


def upload_to_bigquery(df: pd.DataFrame, table_id: str = None) -> bool:
    """Uploads DataFrame to BigQuery."""
    if df is None or df.empty:
        print("⚠️ Cannot upload empty DataFrame")
        return False

    client = get_bigquery_client()
    if not client:
        return False

    table_id = table_id or f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )

    try:
        print(f"\\n⏳ Uploading {len(df)} rows to BigQuery...")
        print(f"   Table: {table_id}")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"\\n✅ Successfully uploaded {len(df)} rows!")
        return True
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

print("✅ BigQuery functions defined!")
```

### Cell 7: Upload to BigQuery
```python
if collected_data_df is not None and not collected_data_df.empty:
    print("="*60)
    print("☁️  UPLOADING TO BIGQUERY")
    print("="*60)
    success = upload_to_bigquery(collected_data_df)
    if success:
        print("\\n🎉 Upload complete! Your data is now in BigQuery.")
    else:
        print("\\n⚠️ Upload failed. Check the error messages above.")
else:
    print("❌ No data to upload. Run Cell 5 first.")
```

### Cell 8 (Optional): Save to CSV
```python
# Save to CSV and download
if collected_data_df is not None and not collected_data_df.empty:
    filename = "map_locations_data.csv"
    collected_data_df.to_csv(filename, index=False)
    print(f"✅ Data saved to: {filename}")
    
    from google.colab import files
    files.download(filename)
    print(f"⬇️ Download started for {filename}")
else:
    print("❌ No data to save")
```

---

## 🎯 How to Use

1. **Setup Secrets** (Step 1 above) - Do this first!
2. **Run Cells in Order** - Start from Cell 1, go to Cell 8
3. **Interactive Mode**: When Cell 5 runs, it will prompt you to enter place names
   - Type a place name (e.g., "Pizza New York")
   - Press Enter
   - Repeat for more places
   - Type "exit" when done
4. **Upload**: Cell 7 will upload everything to BigQuery
5. **Optional**: Cell 8 downloads a CSV copy

---

## 🔥 Quick Batch Mode Alternative

If you don't want interactive input, replace **Cell 5** with this:

```python
# Batch mode - process multiple places at once
places_to_search = [
    "Pizza New York",
    "Sushi Tokyo",
    "Coffee Shop Paris",
    "Burger London",
]

all_dataframes_list = []
for place in places_to_search:
    df = collect_places_for_query(place)
    if df is not None:
        all_dataframes_list.append(df)

if all_dataframes_list:
    collected_data_df = pd.concat(all_dataframes_list, ignore_index=True)
    print(f"\\n✅ Collected {len(collected_data_df)} total places")
    display(collected_data_df.head())
else:
    collected_data_df = None
    print("❌ No data collected")
```

---

## 🆘 Troubleshooting

### "Could not get RAPIDAPI_KEY from Colab Secrets"
- Make sure you added the secret with the exact name `RAPIDAPI_KEY`
- Toggle notebook access for the secret (click the toggle switch)

### "Could not get BIGQUERY_KEY_JSON from Colab Secrets"
- Make sure you pasted the ENTIRE JSON file content
- The JSON must be valid (test with `json.loads()` if needed)

### "API Error: Status code 403"
- Your RapidAPI key might be invalid
- Check your RapidAPI quota/subscription

### "No places found"
- Try a different search query
- Make the query more specific (e.g., "Pizza NYC Manhattan")

---

## ✅ You're All Set!

This is the complete code to run in Google Colab without pushing anything to GitHub. Just copy the cells above into a new Colab notebook and you're good to go! 🚀
