# 🚀 Installation Guide

Complete step-by-step installation guide for X Analytics Suite

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB for application and dependencies
- **Internet**: Required for API calls

### Recommended Requirements
- **Python**: 3.10+
- **RAM**: 8GB+
- **CPU**: Multi-core processor for parallel processing
- **Internet**: High-speed connection for faster data extraction

---

## Pre-Installation

### 1. Check Python Version

```bash
python --version
# or
python3 --version
```

Should show Python 3.8 or higher. If not, install Python:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

### 2. Verify pip

```bash
pip --version
# or
pip3 --version
```

### 3. Install Git (if not installed)

```bash
git --version
```

If not found:
- **Windows**: Download from [git-scm.com](https://git-scm.com/)
- **macOS**: `brew install git`
- **Linux**: `sudo apt-get install git`

---

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd workspace

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLP data
python -m textblob.download_corpora

# Setup environment variables
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

### Method 2: Manual Install

1. **Download Files**
   - Download ZIP from GitHub
   - Extract to desired location

2. **Install Dependencies**
```bash
pip install streamlit>=1.32.0
pip install pandas>=2.2.0
pip install openpyxl>=3.1.2
pip install plotly>=5.18.0
pip install python-dotenv>=1.0.0
pip install requests>=2.31.0
pip install urllib3>=2.0.0
pip install textblob>=0.17.1
pip install numpy>=1.24.0
```

3. **Download NLP Data**
```bash
python -m textblob.download_corpora
```

4. **Configure Environment**
```bash
# Create .env file manually
touch .env
```

Add to `.env`:
```env
RAPIDAPI_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
```

---

## Getting API Keys

### RapidAPI Key (Twitter241 API)

1. Go to [RapidAPI](https://rapidapi.com/)
2. Sign up or log in
3. Search for "Twitter241"
4. Subscribe to a plan (Free tier available)
5. Copy your API key from the dashboard

### Mistral AI Key

1. Go to [Mistral AI](https://mistral.ai/)
2. Create an account
3. Navigate to API section
4. Generate a new API key
5. Copy the key

---

## Configuration

### 1. Environment Variables

Edit `.env` file:

```env
# Required
RAPIDAPI_KEY=your_rapidapi_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional (with defaults)
RAPIDAPI_HOST=twitter241.p.rapidapi.com
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_MODEL=mistral-large-latest
MAX_COMMENT_WORKERS=15
CONNECTION_TIMEOUT=15
MISTRAL_TEMPERATURE=0.3
MISTRAL_MAX_TOKENS=4000
DEBUG_MODE=false
```

### 2. Streamlit Configuration (Optional)

Edit `config.toml`:

```toml
[theme]
primaryColor = "#1DA1F2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## Running the Application

### Start Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run application
streamlit run Twitter-Profile-app.py
```

### Alternative Port

```bash
streamlit run Twitter-Profile-app.py --server.port 8502
```

### Headless Mode (Server)

```bash
streamlit run Twitter-Profile-app.py --server.headless true
```

---

## Verification

### 1. Check Application Startup

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 2. Verify Configuration

Look for log message:
```
✓ Configuration loaded successfully
```

### 3. Test Extraction

1. Click "Extract Data"
2. Enter a test username (e.g., "twitter")
3. Use minimal settings:
   - Target Posts: 100
   - Target Replies: 100
   - Max Pages: 10
4. Click "Start Extraction"

If successful, you'll see:
```
✅ Extraction complete in X.X seconds!
```

---

## Troubleshooting Installation

### Issue: Python not found

**Solution**:
```bash
# Use python3 explicitly
python3 --version
pip3 install -r requirements.txt
python3 -m streamlit run Twitter-Profile-app.py
```

### Issue: pip install fails

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Try with --user flag
pip install --user -r requirements.txt
```

### Issue: Virtual environment not working

**Solution**:
```bash
# Remove and recreate
rm -rf venv
python -m venv venv

# On Windows:
python -m venv venv
venv\Scripts\activate
```

### Issue: TextBlob corpora download fails

**Solution**:
```bash
# Manual download
python -c "import textblob; textblob.download_corpora()"

# Or use NLTK directly
python -c "import nltk; nltk.download('brown'); nltk.download('punkt')"
```

### Issue: Port already in use

**Solution**:
```bash
# Use different port
streamlit run Twitter-Profile-app.py --server.port 8502

# Or kill existing process
# Linux/macOS:
lsof -ti:8501 | xargs kill -9
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Issue: Permission denied

**Solution**:
```bash
# Linux/macOS:
chmod +x Twitter-Profile-app.py

# Windows: Run as Administrator
```

---

## Next Steps

After successful installation:

1. **Read the [README.md](README.md)** for usage instructions
2. **Check [CHANGELOG.md](CHANGELOG.md)** for latest features
3. **Review `config.toml`** for customization options
4. **Monitor `app.log`** for any issues
5. **Extract your first profile** to test the system

---

## Updating

### Update to Latest Version

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run application
streamlit run Twitter-Profile-app.py
```

### Check for Updates

```bash
git fetch origin
git status
```

---

## Uninstallation

### Remove Application

```bash
# Deactivate virtual environment
deactivate

# Remove files
cd ..
rm -rf workspace
```

### Remove Dependencies

```bash
# If using virtual environment, just delete it
rm -rf venv

# Or uninstall globally
pip uninstall -r requirements.txt -y
```

---

## Support

Need help?
- Check the [README.md](README.md) troubleshooting section
- Review logs in `app.log`
- Open an issue on GitHub
- Contact support team

---

## Security Notes

- **Never commit `.env` file** to version control
- **Keep API keys secret** and rotate regularly
- **Use HTTPS** in production environments
- **Monitor API usage** to avoid unexpected charges
- **Review logs** for suspicious activity

---

**Installation Complete!** 🎉

You're ready to start analyzing Twitter profiles!
