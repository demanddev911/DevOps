# Map Location Data Collector

A Python script to collect location data from RapidAPI's Google Maps service and upload it to Google BigQuery.

## Features

- 🔍 **Interactive Mode**: Search for places interactively with real-time feedback
- 📦 **Batch Mode**: Process multiple locations from command line or file
- 💾 **Flexible Output**: Save to CSV or upload directly to BigQuery
- 🚀 **Caching**: In-memory cache to avoid duplicate API calls
- 📝 **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Prerequisites

- Python 3.7+
- RapidAPI account with access to Google Search Master Mega API
- Google Cloud Platform account with BigQuery enabled (optional, for uploads)

## Installation

1. Clone this repository or download the script:
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Configuration

### Environment Variables

Create a `.env` file or export these environment variables:

- `RAPIDAPI_KEY` (required): Your RapidAPI key
- `BIGQUERY_CREDENTIALS_PATH` (optional): Path to Google Cloud service account JSON file
- `GCP_PROJECT_ID` (optional): Your GCP project ID (default: shopper-reviews-477306)
- `GCP_DATASET_ID` (optional): BigQuery dataset ID (default: place_data)
- `GCP_TABLE_ID` (optional): BigQuery table ID (default: Map_location)

### Setting Environment Variables

**Linux/Mac:**
```bash
export RAPIDAPI_KEY="your_key_here"
export BIGQUERY_CREDENTIALS_PATH="/path/to/credentials.json"
```

**Windows:**
```cmd
set RAPIDAPI_KEY=your_key_here
set BIGQUERY_CREDENTIALS_PATH=C:\path\to\credentials.json
```

## Usage

### Interactive Mode

Run the script in interactive mode to search for places one by one:

```bash
python Map_Location.py --mode interactive
```

You'll be prompted to enter place names. Type 'exit' when done.

### Batch Mode with Command Line Arguments

Search for multiple places in one command:

```bash
python Map_Location.py --mode batch --places "New York Pizza" "Tokyo Sushi" "Paris Cafe"
```

### Batch Mode with File Input

Create a file with place names (one per line) and process them:

```bash
python Map_Location.py --mode batch --file places.txt
```

Example `places.txt`:
```
New York Pizza
Tokyo Sushi
Paris Cafe
London Fish and Chips
```

### Save to CSV Instead of BigQuery

Use the `--output` flag to save results to a CSV file:

```bash
python Map_Location.py --mode batch --places "Coffee Shop NYC" --output results.csv
```

### Test Without Uploading

Use the `--no-upload` flag to test data collection without uploading to BigQuery:

```bash
python Map_Location.py --mode interactive --no-upload
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--mode` | Run mode: `interactive` or `batch` | `interactive` |
| `--places` | List of place names (batch mode only) | None |
| `--file` | Path to file with place names (batch mode only) | None |
| `--output` | Save to CSV file instead of BigQuery | None |
| `--no-upload` | Skip BigQuery upload | False |

## Google Cloud Setup

### Creating a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to IAM & Admin > Service Accounts
3. Click "Create Service Account"
4. Grant the following roles:
   - BigQuery Data Editor
   - BigQuery Job User
5. Create and download a JSON key
6. Set `BIGQUERY_CREDENTIALS_PATH` to the downloaded file path

### Creating BigQuery Dataset and Table

```bash
# Create dataset
bq mk --dataset your-project-id:place_data

# The table will be created automatically with auto-detect schema
```

## Data Structure

The script collects the following data for each place:
- Place name
- Address
- Rating
- Reviews
- Location coordinates
- Search query used
- And more (auto-detected from API response)

## Error Handling

The script includes comprehensive error handling:
- API connection errors
- Invalid credentials
- Missing environment variables
- File I/O errors
- BigQuery upload errors

All errors are logged with detailed messages for troubleshooting.

## Caching

API responses are cached in memory during script execution to avoid redundant API calls for the same query. The cache is cleared when the script exits.

## Logging

Logs are written to stdout with the following levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors

## Example Workflow

```bash
# 1. Set up environment
export RAPIDAPI_KEY="your_key_here"
export BIGQUERY_CREDENTIALS_PATH="./credentials.json"

# 2. Test with CSV output first
python Map_Location.py --mode batch --places "Pizza NYC" --output test.csv

# 3. Check the CSV file
cat test.csv

# 4. Run full workflow with BigQuery upload
python Map_Location.py --mode batch --file places.txt
```

## Troubleshooting

### "RAPIDAPI_KEY environment variable not set"
Make sure you've exported the `RAPIDAPI_KEY` environment variable.

### "BIGQUERY_CREDENTIALS_PATH not set in environment"
Export the path to your service account JSON file.

### "Credentials file not found"
Check that the path in `BIGQUERY_CREDENTIALS_PATH` is correct and the file exists.

### API Rate Limits
The RapidAPI service may have rate limits. Check your RapidAPI dashboard for quota information.

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
