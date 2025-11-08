# 🎯 X Analytics Suite - Reputation Agent

![Version](https://img.shields.io/badge/version-9.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-production-brightgreen)

A professional, enterprise-grade Twitter/X analytics dashboard with AI-powered reputation analysis, sentiment analysis, and comprehensive data visualization.

## ✨ Features

### 🔍 Data Extraction
- **Profile Analysis**: Extract complete user profile information
- **Posts & Replies**: Fetch up to 30,000 posts and replies
- **Comment Analysis**: Parallel extraction of comments with configurable depth
- **Smart Pagination**: Intelligent cursor-based pagination with automatic retry logic

### 📊 Advanced Analytics
- **Engagement Metrics**: Likes, retweets, replies, views, and engagement rates
- **Time-based Analysis**: Hourly and daily posting patterns
- **Sentiment Analysis**: AI-powered sentiment classification for tweets and comments
- **Trend Detection**: Moving averages and pattern recognition

### 🤖 AI-Powered Insights
- **Google Gemini 1.5 Flash**: Fast, powerful AI for intelligent analysis
  - 3x higher rate limits than Mistral
  - Excellent multilingual support (Arabic & English)
  - Cost-effective with free tier available
- **Reputation Analysis**: Comprehensive reputation assessment based on public feedback
- **Evidence-based Reports**: All insights backed by actual tweet/comment links
- **Automatic Fallback**: Uses Mistral AI if Gemini unavailable

### 📈 Visualizations
- **Interactive Charts**: 12+ different chart types using Plotly
- **Sentiment Dashboards**: Distribution and timeline visualizations
- **Engagement Trends**: Time-series analysis with moving averages
- **Custom Themes**: Modern, professional UI with gradient designs

### 🔒 Security & Performance
- **Environment Variables**: Secure API key management with .env files
- **Input Validation**: Comprehensive sanitization and validation
- **Connection Pooling**: Optimized HTTP connections with retry strategies
- **Caching System**: Multi-level caching for improved performance
- **Advanced Rate Limiting**: NEW! Token bucket rate limiter with circuit breaker pattern
  - Intelligent key health tracking and automatic rotation
  - Exponential backoff with jitter
  - Per-key rate limiting and cooldown management
  - Self-healing circuit breakers
- **Logging**: Comprehensive error tracking and debugging

### 📤 Export Options
- **Excel Reports**: Multi-sheet workbooks with all data
- **Text Reports**: AI analysis reports in plain text
- **Downloadable**: One-click downloads with timestamps

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- RapidAPI account with Twitter241 API access
- Google Gemini API key(s) - [Get free keys here](https://makersuite.google.com/app/apikey)
  - Free tier: 15 requests/min per key
  - Recommend 3-5 keys for best performance

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd workspace
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Download NLTK data for sentiment analysis**
```bash
python -m textblob.download_corpora
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
RAPIDAPI_KEY=your_rapidapi_key_here
GEMINI_KEY_1=your_first_gemini_key_here
GEMINI_KEY_2=your_second_gemini_key_here
GEMINI_KEY_3=your_third_gemini_key_here
```

Or edit `Twitter-Profile-app.py` directly (line 534) to add your Gemini keys.

📖 **See [GEMINI_SETUP_GUIDE.md](GEMINI_SETUP_GUIDE.md) for detailed setup instructions**

5. **Run the application**
```bash
streamlit run Twitter-Profile-app.py
```

The application will open in your default web browser at `http://localhost:8501`

---

## 📖 Usage Guide

### 1. Extract Data

1. Click the **"Extract Data"** button on the main page
2. Configure extraction parameters:
   - **Username**: Twitter/X username (without @)
   - **Target Posts**: Number of posts to extract (100-30,000)
   - **Target Replies**: Number of replies to extract (100-30,000)
   - **Maximum Pages**: API pagination limit (10-300)
   - **Fetch Comments**: Enable comment extraction
   - **Enable Sentiment Analysis**: Analyze sentiment automatically

3. Click **"🚀 Start Extraction"**
4. Wait for the extraction process (progress shown in real-time)

### 2. View Dashboard

The dashboard displays:
- **Profile Overview**: User information and key metrics
- **Engagement Statistics**: Total engagement, average engagement, views
- **Visual Analytics**: 12 different charts and graphs
- **Top Content**: Best performing posts and replies
- **Comment Analysis**: Most engaged comments

### 3. Generate AI Reports

Navigate to the **"🎯 AI Detailed Report"** tab:
- **Executive Summary**: Overview of account reputation
- **Pros & Cons**: Strengths and weaknesses analysis
- **Complaints Classification**: Categorized feedback
- **Public Opinion Insights**: Sentiment trends and patterns

### 4. Download Reports

- **Excel Export**: Complete data in structured format
- **AI Reports**: Text-based analysis reports
- **Summary Reports**: Executive summaries

---

## 🏗️ Architecture

### Project Structure
```
workspace/
├── Twitter-Profile-app.py      # Main application
├── gemini_rate_limiter.py      # Gemini API rate limiter module
├── mistral_rate_limiter.py     # Legacy Mistral rate limiter (fallback)
├── requirements.txt            # Python dependencies
├── config.toml                 # Streamlit configuration
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── GEMINI_SETUP_GUIDE.md      # Gemini API setup guide
├── RATE_LIMITER_GUIDE.md      # Rate limiter documentation
└── app.log                     # Application logs
```

### Key Components

#### **1. Configuration Layer**
- Environment variable management
- API configuration
- Logging setup

#### **2. API Layer**
- `TwitterAPI`: HTTP connection management
- `TwitterExtractor`: Data extraction logic
- `MistralAnalyzer`: AI analysis engine

#### **3. Data Processing Layer**
- Input validation and sanitization
- DataFrame processing
- Sentiment analysis
- Caching utilities

#### **4. Visualization Layer**
- Chart generation functions
- Dashboard components
- Report generators

#### **5. User Interface**
- Streamlit-based web interface
- Custom CSS styling
- Interactive widgets

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RAPIDAPI_KEY` | RapidAPI key for Twitter241 API | - | Yes |
| `RAPIDAPI_HOST` | RapidAPI host | twitter241.p.rapidapi.com | No |
| `GEMINI_KEY_1` | First Google Gemini API key | - | Yes |
| `GEMINI_KEY_2` | Second Gemini API key (recommended) | - | No |
| `GEMINI_KEY_3` | Third Gemini API key (recommended) | - | No |
| `GEMINI_MODEL` | Gemini model to use | gemini-1.5-flash | No |
| `MAX_COMMENT_WORKERS` | Parallel workers for comments | 15 | No |
| `CONNECTION_TIMEOUT` | API timeout in seconds | 15 | No |
| `GEMINI_TEMPERATURE` | AI temperature setting | 0.3 | No |
| `GEMINI_MAX_TOKENS` | Max tokens per AI request | 4000 | No |

### Rate Limiting Configuration

The Enhanced Rate Limiter provides intelligent API request management:

```python
# Configure in Twitter-Profile-app.py
rate_limit_per_key=15   # Requests per minute per key (Gemini)
timeout=60              # Request timeout in seconds
```

**Gemini Rate Limits (Free Tier):**
- 15 requests per minute per key
- 1,500 requests per day per key
- With 3 keys: 45 requests/min = 2,700/hour

For detailed configuration, see:
- [GEMINI_SETUP_GUIDE.md](GEMINI_SETUP_GUIDE.md) - Setup instructions
- [RATE_LIMITER_GUIDE.md](RATE_LIMITER_GUIDE.md) - Technical details

### Streamlit Configuration

Edit `config.toml` to customize:
- Theme colors
- Server settings
- Browser behavior

---

## 📊 Data Schema

### Tweets DataFrame
```python
{
    'tweet_id': str,
    'text': str,
    'created_at': datetime,
    'likes': int,
    'retweets': int,
    'replies': int,
    'views': int,
    'total_engagement': int,
    'engagement_rate': float,
    'sentiment': str,              # New in v9.0
    'sentiment_polarity': float,   # New in v9.0
    'sentiment_subjectivity': float, # New in v9.0
    'hashtags': str,
    'mentions': str,
    'has_media': bool,
    'url': str
}
```

### Comments DataFrame
```python
{
    'comment_id': str,
    'comment_text': str,
    'commenter_username': str,
    'commenter_name': str,
    'commenter_verified': bool,
    'comment_date': datetime,
    'comment_likes': int,
    'comment_retweets': int,
    'comment_replies': int,
    'sentiment': str,              # New in v9.0
    'sentiment_polarity': float,   # New in v9.0
    'original_tweet_id': str,
    'comment_url': str
}
```

---

## 🎨 Customization

### Modify Extraction Limits
Edit these constants in `Twitter-Profile-app.py`:
```python
MAX_COMMENT_WORKERS = 15    # Increase for faster comment extraction
CONNECTION_TIMEOUT = 15     # Increase for slower networks
```

### Customize AI Analysis
Modify Mistral AI parameters:
```python
MISTRAL_TEMPERATURE = 0.3   # 0 = focused, 1 = creative
MISTRAL_MAX_TOKENS = 4000   # Longer responses
```

### Add Custom Charts
Use the chart template:
```python
def create_custom_chart(df):
    """Your custom visualization"""
    fig = go.Figure(...)
    return fig
```

---

## 🐛 Troubleshooting

### Common Issues

**1. API Keys Not Found**
```
Error: ❌ Missing RAPIDAPI_KEY
Solution: Ensure .env file exists with valid keys
```

**2. User Not Found**
```
Error: User not found. Please check the username.
Solution: Verify username spelling (without @)
```

**3. Rate Limit Errors**
```
Error: 429 Too Many Requests
Solution: Wait a few minutes, reduce extraction targets
```

**4. Sentiment Analysis Fails**
```
Error: Sentiment analysis error
Solution: Run: python -m textblob.download_corpora
```

**5. Connection Timeout**
```
Error: requests.exceptions.Timeout
Solution: Increase CONNECTION_TIMEOUT in .env
```

### Debug Mode

Enable detailed logging:
```bash
export DEBUG_MODE=true
streamlit run Twitter-Profile-app.py
```

View logs:
```bash
tail -f app.log
```

---

## 🔄 Updates & Changelog

### Version 11.0 (Current) - Gemini Migration
- ✅ **MAJOR**: Migrated from Mistral AI to Google Gemini 1.5 Flash
  - 3x higher rate limits (15 vs 5 requests/min per key)
  - Better multilingual support (especially Arabic)
  - Cost-effective with free tier available
  - Faster response times
  - Improved reliability
- ✅ **NEW**: Gemini-specific rate limiter with enhanced features
- ✅ Automatic fallback to Mistral AI if Gemini unavailable
- ✅ Comprehensive setup guide ([GEMINI_SETUP_GUIDE.md](GEMINI_SETUP_GUIDE.md))
- ✅ Updated documentation and configuration
- ✅ Backward compatible with existing reports

### Version 10.0 (Previous)
- ✅ Advanced Rate Limiting System
  - Token bucket rate limiter with circuit breaker pattern
  - Intelligent key health tracking and automatic rotation
  - Exponential backoff with jitter
  - Per-key cooldown management
  - Comprehensive monitoring and diagnostics
- ✅ Enhanced error handling and recovery
- ✅ Improved timeout management

### Version 9.0 (Previous)
- ✅ Environment-based configuration
- ✅ Sentiment analysis for tweets and comments
- ✅ Enhanced error handling and logging
- ✅ Input validation and sanitization
- ✅ Performance optimizations
- ✅ Improved UI with loading animations
- ✅ Better rate limit handling

### Version 8.2 (Previous)
- Refactored HTTP connections
- Optimized DataFrame operations
- Enhanced chart generation
- Improved Mistral AI analyzer

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📧 Support

For issues and questions:
- Check the Troubleshooting section
- Review `app.log` for error details
- Open an issue on GitHub

---

## 🙏 Acknowledgments

- **Streamlit**: Web framework
- **Plotly**: Interactive visualizations
- **Mistral AI**: AI analysis engine
- **RapidAPI**: Twitter API access
- **TextBlob**: Sentiment analysis

---

## ⚠️ Disclaimer

This tool is for analytics and research purposes. Please:
- Respect Twitter's Terms of Service
- Follow rate limits and usage guidelines
- Handle user data responsibly
- Comply with data privacy regulations (GDPR, CCPA, etc.)

---

Made with ❤️ by the X Analytics Suite Team
