# Google Gemini API Setup Guide

## Overview

The X Analytics Suite now uses **Google Gemini 1.5 Flash** for AI-powered analysis instead of Mistral AI. Gemini offers:
- Higher rate limits (15 requests/min per key vs 5 for Mistral)
- Better multilingual support (especially Arabic)
- Faster response times
- More cost-effective pricing
- Free tier available

## Getting Your Gemini API Keys

### Step 1: Access Google AI Studio

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Accept the terms of service if prompted

### Step 2: Create API Keys

1. Click "Create API Key" button
2. Choose "Create API key in new project" (recommended) or select an existing project
3. Copy the generated API key (starts with `AIzaSy...`)
4. **Important:** Store this key securely - you won't be able to see it again

### Step 3: Create Multiple Keys (Recommended)

For better reliability and higher throughput, create 3-5 API keys:

1. Repeat Step 2 for each additional key
2. You can create keys in the same project or different projects
3. Each key has its own rate limit

## Adding Keys to the Application

### Method 1: Direct Configuration (Quick Start)

1. Open `Twitter-Profile-app.py`
2. Find the `GEMINI_KEYS` section (around line 534)
3. Replace the placeholder keys with your actual keys:

```python
GEMINI_KEYS: List[str] = [
    "AIzaSyYOUR_FIRST_KEY_HERE",
    "AIzaSyYOUR_SECOND_KEY_HERE",
    "AIzaSyYOUR_THIRD_KEY_HERE",
]
```

### Method 2: Environment Variables (Recommended for Production)

1. Create or edit `.env` file:
```bash
GEMINI_KEY_1=AIzaSyYOUR_FIRST_KEY_HERE
GEMINI_KEY_2=AIzaSyYOUR_SECOND_KEY_HERE
GEMINI_KEY_3=AIzaSyYOUR_THIRD_KEY_HERE
```

2. Update `Twitter-Profile-app.py` to load from environment:
```python
import os
GEMINI_KEYS: List[str] = [
    os.getenv('GEMINI_KEY_1'),
    os.getenv('GEMINI_KEY_2'),
    os.getenv('GEMINI_KEY_3'),
]
# Filter out None values
GEMINI_KEYS = [key for key in GEMINI_KEYS if key]
```

## API Rate Limits

### Free Tier
- **15 requests per minute** per API key
- **1,500 requests per day** per API key
- **1 million tokens per minute**

### With Multiple Keys
- 3 keys = 45 requests/min = ~2,700 requests/hour
- 5 keys = 75 requests/min = ~4,500 requests/hour

This is usually more than enough for most analytics tasks!

## Testing Your Setup

### Quick Test

Run this Python script to test your keys:

```python
import google.generativeai as genai

# Test each key
keys = [
    "AIzaSyYOUR_FIRST_KEY_HERE",
    "AIzaSyYOUR_SECOND_KEY_HERE",
]

for i, key in enumerate(keys, 1):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello in Arabic")
        print(f"✅ Key {i}: Working! Response: {response.text[:50]}")
    except Exception as e:
        print(f"❌ Key {i}: Failed - {str(e)[:100]}")
```

### In the Application

1. Run the Streamlit app:
```bash
streamlit run Twitter-Profile-app.py
```

2. Navigate to the AI Report section
3. Look for: "✅ استخدام محلل Google Gemini 1.5 Flash المحسّن"
4. Expand "🔍 عرض حالة مفاتيح Gemini API" to see health status

## Troubleshooting

### Error: "google-generativeai not installed"

**Solution:**
```bash
pip install google-generativeai>=0.3.0
```

### Error: "Invalid API key"

**Possible causes:**
1. Key is incorrect - double-check you copied it fully
2. Key was deleted in Google AI Studio
3. API not enabled for your Google Cloud project

**Solution:**
- Verify the key in [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create a new key if needed

### Error: "Quota exceeded" or "429 Rate Limit"

**Solution:**
1. Add more API keys to spread the load
2. The rate limiter will automatically switch to another key
3. Check the health status to see which keys are available

### Warning: "استخدام محلل Mistral القديم"

This means Gemini couldn't be loaded, so it fell back to Mistral.

**Solution:**
1. Install google-generativeai: `pip install google-generativeai`
2. Verify your API keys are correct
3. Check the error message in terminal/logs

## Configuration Options

### Adjust Rate Limits

In `Twitter-Profile-app.py`, modify the rate limit settings:

```python
ai_analyzer = EnhancedGeminiAnalyzer(
    api_keys=GEMINI_KEYS,
    rate_limit_per_key=15,  # Requests per minute
    timeout=60,  # Request timeout in seconds
)
```

**Recommended values:**
- Free tier: `rate_limit_per_key=15`
- If experiencing rate limits: `rate_limit_per_key=10`
- For testing: `rate_limit_per_key=5`

### Model Selection

Gemini offers different models:

```python
GEMINI_MODEL = "gemini-1.5-flash"  # Fast, cost-effective (recommended)
# GEMINI_MODEL = "gemini-1.5-pro"  # More capable, slower, more expensive
```

### Temperature Setting

Controls response creativity:

```python
GEMINI_TEMPERATURE = 0.3  # Focused, consistent (recommended for analytics)
# GEMINI_TEMPERATURE = 0.7  # More creative
# GEMINI_TEMPERATURE = 0.0  # Most deterministic
```

## Cost Estimation

### Gemini 1.5 Flash Pricing (as of 2024)

**Free Tier:**
- First 1,500 requests/day: **FREE**
- Perfect for personal use and testing

**Paid Tier** (after free quota):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

**Typical Usage:**
- Analyzing one Twitter profile: ~500-1,000 tokens
- Daily cost for 100 profiles: ~$0.01-0.05
- Monthly cost for heavy use: $5-20

**Much cheaper than Mistral!**

## Comparison: Gemini vs Mistral

| Feature | Gemini 1.5 Flash | Mistral Large |
|---------|------------------|---------------|
| Rate Limit (free) | 15 req/min | 5 req/min |
| Speed | Faster | Slower |
| Arabic Support | Excellent | Good |
| Cost | Lower | Higher |
| Free Tier | Yes (1.5K/day) | No |
| Context Window | 1M tokens | 128K tokens |

## Security Best Practices

1. **Never commit API keys** to Git
   - Use `.env` files (add to `.gitignore`)
   - Or use environment variables

2. **Restrict API keys** in Google Cloud Console
   - Limit to specific IPs if possible
   - Set daily quotas
   - Enable only required APIs

3. **Rotate keys regularly**
   - Create new keys every 90 days
   - Delete old keys

4. **Monitor usage**
   - Check [Google Cloud Console](https://console.cloud.google.com/)
   - Set up billing alerts
   - Monitor the health dashboard in the app

## Support & Resources

### Official Documentation
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Python SDK Guide](https://ai.google.dev/tutorials/python_quickstart)
- [Rate Limits](https://ai.google.dev/docs/rate_limits)

### Getting Help
- Check application logs: `app.log`
- View health status in the app
- Review error messages in Streamlit

### Common Questions

**Q: Can I use free tier keys only?**
A: Yes! With 3 free keys, you get 45 requests/min - enough for most uses.

**Q: How many keys should I create?**
A: 3-5 keys is optimal for most use cases.

**Q: Will my old Mistral reports still work?**
A: Yes! The system automatically falls back to Mistral if Gemini is unavailable.

**Q: Can I switch back to Mistral?**
A: Yes, simply don't add Gemini keys and the app will use Mistral automatically.

## Migration from Mistral

If you're upgrading from Mistral-based version:

1. **Keep your Mistral keys** - they're still used as fallback
2. **Add Gemini keys** using the guide above
3. **Install new dependency**: `pip install google-generativeai`
4. **Restart the application**
5. **Verify** you see "استخدام محلل Google Gemini"

Your old reports and data are fully compatible!

---

**Need Help?** Check the main README.md or open an issue on GitHub.
