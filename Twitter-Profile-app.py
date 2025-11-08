"""
X Analytics Suite - Professional Dashboard with AI Report
Version: 8.2 - Optimized Performance Update

Optimizations in this version:
- Refactored HTTP connections with connection pooling and automatic retries
- Eliminated duplicate pagination code with generic _paginate_tweets method
- Optimized DataFrame operations with better vectorization
- Improved error handling with specific exception types
- Added function-level caching for expensive operations
- Optimized parallel comment extraction with better batch processing
- Enhanced chart generation with optimized data processing
- Improved Mistral AI analyzer with better retry logic
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Dict, List, Optional
import io
import numpy as np
import plotly.graph_objects as go
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import sys
import os

# Add current directory to Python path for Streamlit Cloud compatibility
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import enhanced Gemini analyzer with rate limiting
try:
    from gemini_rate_limiter import EnhancedGeminiAnalyzer
    GEMINI_AVAILABLE = True
except ImportError as e:
    GEMINI_AVAILABLE = False
    print(f"Warning: Enhanced Gemini analyzer not available: {e}")
    # Will use legacy MistralAnalyzer as fallback

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="X Analytics Suite",
    page_icon="✕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# SESSION STATE
# ============================================================
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'show_raw_data' not in st.session_state:
    st.session_state.show_raw_data = False
if 'ai_report_cache' not in st.session_state:
    st.session_state.ai_report_cache = {}

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .arabic-text {
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .main {
        background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.5rem;
    }
    
    .block-container {
        max-width: 1400px;
        padding: 2rem;
        background: white;
        border-radius: 32px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .card {
        background: #fafafa;
        border-radius: 20px;
        padding: 1.75rem;
        border: none;
        box-shadow: none;
        margin-bottom: 1rem;
    }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
        border-radius: 24px;
        padding: 2rem 1.75rem;
        border: 1px solid #f0f0f0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a6f 50%, #667eea 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        border-color: #e8e8e8;
    }
    
    div[data-testid="metric-container"]:hover::before {
        opacity: 1;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #000 0%, #333 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #888;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    div[data-testid="stMetricDelta"] {
        background: linear-gradient(135deg, #e8fff8 0%, #d4f8ea 100%);
        color: #00aa6d;
        padding: 0.4rem 0.9rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #c0f0dc;
        box-shadow: 0 2px 6px rgba(0, 204, 136, 0.1);
        letter-spacing: 0.02em;
    }
    
    .hero-section {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #000;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: #ccc;
    }
    
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #000;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .report-section {
        background: #fafafa;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
        border-right: 4px solid #ff6b6b;
    }
    
    .report-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #000;
        margin-bottom: 1rem;
        font-family: 'Cairo', sans-serif;
    }
    
    .report-content {
        font-size: 1rem;
        line-height: 2;
        color: #000000;
        font-family: 'Cairo', sans-serif;
        text-align: justify;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #f25e6e 0%, #e04555 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 8px 20px rgba(242, 94, 110, 0.3);
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(242, 94, 110, 0.4);
    }
    
    .stButton button[kind="secondary"] {
        background: linear-gradient(135deg, #00cc88 0%, #00aa70 100%);
        box-shadow: 0 8px 20px rgba(0, 204, 136, 0.3);
    }
    
    .stButton button[kind="secondary"]:hover {
        box-shadow: 0 12px 30px rgba(0, 204, 136, 0.4);
    }
    
    button[key="main_extraction_btn"] {
        background: linear-gradient(135deg, #667eea 0%, #564ba2 100%) !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    button[key="main_extraction_btn"]:hover {
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem !important;
        background: transparent !important;
        margin-top: -1rem;
        margin-bottom: 0 !important;
        padding: 0 !important;
        border-bottom: none !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        border-bottom: none !important;
        background-clip: padding-box !important;
    }
    
    .stTabs {
        border-bottom: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .stTabs > div {
        border-bottom: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    
    .stTabs > div > div {
        background: transparent !important;
        padding: 0 !important;
    }
    
    [data-testid="stTabs"] {
        border-bottom: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    
    [data-testid="stTabs"] > div {
        background: transparent !important;
        padding: 0 !important;
    }
    
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    .stTabs [data-baseweb="tab"]::before,
    .stTabs [data-baseweb="tab"]::after {
        display: none !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f8f8 0%, #ececec 100%) !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 1rem 2.5rem !important;
        font-weight: 600 !important;
        color: #888 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        min-width: 160px !important;
        height: auto !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
        color: #555 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #564ba2 100%) !important;
        color: white !important;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.35) !important;
        transform: translateY(-1px) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }
    
    .stTabs [aria-selected="true"]:hover {
        background: linear-gradient(135deg, #7688eb 0%, #667eea 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4) !important;
    }
    
    button[data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f8f8 0%, #ececec 100%) !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 1rem 2.5rem !important;
        font-weight: 600 !important;
        color: #888 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #564ba2 100%) !important;
        color: white !important;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.35) !important;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a6f 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #999;
    }
    
    /* Detailed Report Page Enhancements - Unified Font */
    .main [direction="rtl"],
    .main [direction="rtl"] *,
    .main div[style*="direction: rtl"],
    .main div[style*="direction: rtl"] *,
    .report-section,
    .report-section *,
    .report-content,
    .report-content * {
        font-family: 'Cairo', sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }
    
    /* Simple table row hover */
    .main table tbody tr:hover {
        background: #f1f5f9 !important;
    }
    
    .main table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        direction: rtl;
        text-align: right;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        border-radius: 8px;
        overflow: hidden;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main table th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px;
        font-weight: 700;
        border: none;
        font-size: 1rem;
        letter-spacing: 0.02em;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main table td {
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
        line-height: 1.8;
        font-size: 0.9375rem;
        color: #000000;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main table tr:nth-child(even) {
        background-color: #f8fafc;
    }
    
    .main table tr:hover {
        background-color: #f1f5f9;
        transition: background-color 0.2s ease;
    }
    
    .main ul, .main ol {
        line-height: 2;
        margin: 15px 0;
        padding-right: 25px;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main li {
        margin-bottom: 12px;
        color: #000000;
        font-size: 1rem;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main strong {
        font-weight: 700;
        color: #000000;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main p {
        line-height: 2.1;
        margin-bottom: 18px;
        color: #000000;
        font-size: 1.125rem;
        font-weight: 400;
        font-family: 'Cairo', sans-serif !important;
    }
    
    /* Better text for divs with direction rtl */
    .main div[direction="rtl"] p,
    .main div[style*="direction: rtl"] p {
        font-size: 1.125rem;
        line-height: 2.1;
        color: #000000;
        margin-bottom: 18px;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main a {
        color: #2563eb;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.2s ease;
        border-bottom: 2px solid transparent;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .main a:hover {
        color: #1e40af;
        border-bottom-color: #93c5fd;
    }
    
    .main h1, .main h2, .main h3, .main h4 {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700;
        color: #000000;
        margin-top: 1.5em;
        margin-bottom: 0.75em;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# API CONFIGURATION "ac0025f410mshd0c260cb60f3db6p18c4b0jsnc9b7413cd574"
# ============================================================
API_KEY = "ac0025f410mshd0c260cb60f3db6p18c4b0jsnc9b7413cd574"

API_HOST = "twitter241.p.rapidapi.com"
MAX_COMMENT_WORKERS = 15
CONNECTION_TIMEOUT = 15

# Google Gemini API Keys for Rate Limit Resilience
# Option 1: Set environment variables (recommended for production)
# Option 2: Replace placeholder keys below with your actual keys
# Get your API keys from: https://makersuite.google.com/app/apikey

# Try to load from environment variables first
import os as _os
_gemini_keys_from_env = [
    _os.getenv('GEMINI_KEY_1'),
    _os.getenv('GEMINI_KEY_2'),
    _os.getenv('GEMINI_KEY_3'),
    _os.getenv('GEMINI_KEY_4'),
    _os.getenv('GEMINI_KEY_5'),
]
# Filter out None values
_gemini_keys_from_env = [k for k in _gemini_keys_from_env if k and k.strip()]

# If environment variables are not set, use these (replace with your keys)
GEMINI_KEYS: List[str] = _gemini_keys_from_env if _gemini_keys_from_env else [
    "AIzaSyDEMOKEY1-REPLACE_WITH_YOUR_ACTUAL_KEY",
    "AIzaSyDEMOKEY2-REPLACE_WITH_YOUR_ACTUAL_KEY",
    "AIzaSyDEMOKEY3-REPLACE_WITH_YOUR_ACTUAL_KEY",
]

# Validate that keys are not placeholders
_placeholder_detected = any('DEMOKEY' in key or 'REPLACE' in key for key in GEMINI_KEYS)
if _placeholder_detected:
    import warnings
    warnings.warn(
        "\n⚠️  GEMINI API KEYS NOT CONFIGURED!\n"
        "Please set environment variables (GEMINI_KEY_1, GEMINI_KEY_2, etc.)\n"
        "OR edit line 547 in Twitter-Profile-app.py with your actual keys.\n"
        "Get free keys at: https://makersuite.google.com/app/apikey\n"
        "The app will try to use Mistral AI as fallback.",
        UserWarning
    )
    # Clear placeholder keys to force fallback to Mistral
    GEMINI_KEYS = []

GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 4000

# Legacy Mistral API Keys (for fallback compatibility only)
MISTRAL_KEYS: List[str] = [
    "BhkR8enTgJufYmP9Z8ks5Ln6HXHp7MlQ",
    "FPph1ViTo77ONNDsaEz37p3FJQkY5jPY",
    "979RiVBzoIk0f9vovyXOPPAM4Rd88a2F",
    "FYNVQtcSIOPWjQi2ACIicwpWcDjLCXRD",
    "O17Iq9RmMsQmy0TnhdIjFjZ8DAcGYhRq",
    "z8cR4w32DRnE8meEd1WbteRi5EXjCPpb",
    "nbiq77t08ktW7n8nxl2UyiwO2gEHdHaA",
    "yb0pZZjCeBNeCRzALuwJj3RaHmIUqUNn",
    "6pdBLRZo08NW4h0EsZFFAts64ghqRb5u",
    "Egw4ZmA0cb6zCYp6iDs2NIZDyRpkdZN4",
    "O4wEppQCbjN4kWrGzXrHNoP4gsPnZQtp",
    "ca9CyWXY1U8xgQox6PxtvGdveaTeh42w",
    "BJ3rBW2EWTBnouiVilEwnDurUpw79HTc",
    "KourVlZelmO2HPND7m1zH6jcBdkCwVwP",
    "qBRwo8x0Hsp46I7RHPx9rT0gWD39gKAJ",
    "g4GJ1a6fy0FYRFI6F1DjLPnF2W0yYH8R",
    "ifvxjsJF6sadWo2T3ofIvYdqWMVz8F7J",
    "mkQoxuJqF64csdCVxDWO45cGPqhSmU3v",
    "FC5fAVYrag8d0OZx7TNG7dav94XbvB38",
    "SyaX5rgxtulaxgsUscz18o5Tp4dTWCR4",
    "Bt9bXLvrvuLcLPixxKYa4d33P8h8zAAI",
    "s18ja2B4x8nFiiaPL6tdtUGLzsJLnfYC",
    "KC0e1nzQOmDJq0SU7nS8NBy2ccWPyKcU",
    "GPKvOdqjWSFofhjQX6OoTGvciJXqrTbx",
    "PPmCIgn5DuyOU2ChKpzOR5KgY6iKZpEn",
    "iGAZ4cPmQfgFFdmwJoyW2qyn298ia3Zo",
    "uaOu9oHmqpMwp7HLAVcXVjH1D431ZyPd",
    "3WyjwFBlQLeoBJngJHdwjtlRC4nk5YEj",
    "x2iCU0Ru6n4XNAg9TdEh65RDnumbCosH",
    "G8bgrr14kwbojRgj9gRl5y3Y3UMq7wc9",
    "4IlbiW9YkrGmRpKL5iBY4vPjfF58P0Ot",
    "akABOZ5CJb1MmeMbVq2msDOx8AceHHfq",
    "DtcSNZAwk0oj1NzOdwLFVtVYWu5o3Bij",
    "5s9CiAuTnSGSULw94vrZaw8ymSsmYDmd",
    "NX8oYtaJjjFzXUsVTOZml4yc58s5bQ0Y",
    "4cLXjFMjU8QT4pcsoNeLPUOzjmlXjLlm",
    "K8wNVj71msOwgQ6vVQ1nfZeZEKVp3hHj",
    "dmgNRyqcqzAmCcKNKlirIukBIdlwhsJ3",
    "bNveWmpWZmoou7wsT5j3eAFZnKmksbUE",
]
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"
MISTRAL_TEMPERATURE = 0.3
MISTRAL_MAX_TOKENS = 4000

# ============================================================
# TWITTER API CLASSES
# ============================================================
class TwitterAPI:
    def __init__(self, api_key: str, api_host: str):
        self.api_key = api_key
        self.api_host = api_host
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host,
            'Connection': 'keep-alive'
        }
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a session with connection pooling and retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def call(self, endpoint: str) -> Dict:
        """Make API call with connection pooling and automatic retries"""
        try:
            url = f"https://{self.api_host}{endpoint}"
            response = self.session.get(url, headers=self.headers, timeout=CONNECTION_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": True, "message": str(e)}
        except json.JSONDecodeError as e:
            return {"error": True, "message": f"Invalid JSON response: {str(e)}"}

class TwitterExtractor:
    def __init__(self, api: TwitterAPI):
        self.api = api

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information including location and profile image"""
        data = self.api.call(f"/user?username={username}")

        if data.get('error'):
            return None

        user_result = data.get('result', {}).get('data', {}).get('user', {}).get('result', {})
        user_id = user_result.get('rest_id')
        legacy = user_result.get('legacy', {})

        if not user_id:
            return None
            

        # Get profile image URL - Enhanced path extraction
        # Try avatar path first (newer structure)
        avatar = user_result.get('avatar', {})
        image_url = avatar.get('image_url', '')
        
        # Fallback to legacy path if avatar is not available
        if not image_url:
            legacy = user_result.get('legacy', {})
            image_url = legacy.get('profile_image_url_https', '')
            if not image_url:
                image_url = legacy.get('profile_image_url', '')

        # High resolution image conversion
        image_url_high_res = image_url
        if image_url and '_normal' in image_url:
            image_url_high_res = image_url.replace('_normal', '_400x400')

        # Extract core user data
        core = user_result.get('core', {})
        legacy = user_result.get('legacy', {})
        
        # Extract verification status
        is_blue_verified = user_result.get('is_blue_verified', False)
        legacy_verified = legacy.get('verified', False)
        
        # Professional category
        professional = user_result.get('professional', {})
        category = ""
        if professional and 'category' in professional:
            category_obj = professional.get('category', [{}])[0] if professional.get('category') else {}
            category = category_obj.get('name', '')

        # Extract URL from entities if available
        url = legacy.get('url', '')
        url_entities = legacy.get('entities', {}).get('url', {}).get('urls', [])
        if url_entities:
            expanded_url = url_entities[0].get('expanded_url', '')
            if expanded_url:
                url = expanded_url

        user_data = {
            'user_id': user_id,
            'username': core.get('screen_name', username),
            'name': core.get('name', legacy.get('name', '')),
            'followers_count': legacy.get('followers_count', 0),
            'following_count': legacy.get('friends_count', 0),
            'bio': legacy.get('description', ''),
            'location': legacy.get('location', ''),
            'image_url': image_url,
            'image_url_high_res': image_url_high_res,
            'tweet_count': legacy.get('statuses_count', 0),
            'verified': is_blue_verified or legacy_verified,
            'category': category,
            'created_at': legacy.get('created_at', ''),
            'url': url
        }

        return user_data

    def _paginate_tweets(self, user_id: str, username: str, endpoint_path: str,
                         tweet_type: str, target_count: int = 2000, max_pages: int = 300,
                         progress_callback=None) -> List[Dict]:
        """Generic pagination method to avoid code duplication"""
        all_items = []
        cursor = None
        page = 0
        consecutive_empty_pages = 0
        seen_cursors = set()

        while len(all_items) < target_count and page < max_pages:
            page += 1
            endpoint = f"{endpoint_path}?user={user_id}&count=100" + (f"&cursor={cursor}" if cursor else "")
            data = self.api.call(endpoint)

            if data.get('error') or 'result' not in data:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 5:
                    break
                continue

            page_items = self._parse_tweets(data, username, tweet_type)

            if not page_items:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 5:
                    break
                next_cursor = self._extract_cursor(data)
                if next_cursor and next_cursor != cursor and next_cursor not in seen_cursors:
                    cursor = next_cursor
                    seen_cursors.add(cursor)
                    continue
                else:
                    break

            consecutive_empty_pages = 0
            all_items.extend(page_items)

            if progress_callback and page % 5 == 0:
                label = "Posts" if tweet_type == 'post' else "Replies"
                progress_callback(f"{label}: {len(all_items)} collected (page {page})")

            cursor = self._extract_cursor(data)
            if not cursor or cursor in seen_cursors:
                break
            seen_cursors.add(cursor)

        return all_items

    def get_user_posts_paginated(self, user_id: str, username: str, target_count: int = 2000, max_pages: int = 300, progress_callback=None) -> List[Dict]:
        """Fetch user posts with pagination"""
        return self._paginate_tweets(user_id, username, "/user-tweets", 'post', target_count, max_pages, progress_callback)

    def get_user_replies_paginated(self, user_id: str, username: str, target_count: int = 2000, max_pages: int = 300, progress_callback=None) -> List[Dict]:
        """Fetch user replies with pagination"""
        return self._paginate_tweets(user_id, username, "/user-replies", 'reply', target_count, max_pages, progress_callback)

    def _extract_cursor(self, data: Dict) -> Optional[str]:
        try:
            instructions = data.get('result', {}).get('timeline', {}).get('instructions', [])
            for instruction in instructions:
                if instruction.get('type') in ['TimelineAddEntries', 'TimelineAddToModule']:
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        entry_id = entry.get('entryId', '').lower()
                        if 'cursor-bottom' in entry_id:
                            cursor_value = entry.get('content', {}).get('value')
                            if cursor_value:
                                return cursor_value
                    for entry in reversed(entries):
                        entry_id = entry.get('entryId', '').lower()
                        if 'cursor' in entry_id:
                            cursor_value = entry.get('content', {}).get('value')
                            if cursor_value:
                                return cursor_value
            return None
        except (KeyError, TypeError, AttributeError):
            return None

    def _parse_tweets(self, data: Dict, username: str, tweet_type: str) -> List[Dict]:
        tweets = []
        instructions = data.get('result', {}).get('timeline', {}).get('instructions', [])
        for instruction in instructions:
            if instruction.get('type') not in ['TimelineAddEntries', 'TimelineAddToModule']:
                continue
            for entry in instruction.get('entries', []):
                entry_id = entry.get('entryId', '')
                if 'cursor' in entry_id.lower() or 'who-to-follow' in entry_id.lower():
                    continue
                tweet_result = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                legacy = tweet_result.get('legacy')
                if not legacy:
                    continue
                is_reply = legacy.get('in_reply_to_status_id_str') is not None
                is_retweet = 'retweeted_status_result' in legacy or legacy.get('full_text', '').startswith('RT @')
                if tweet_type == 'post':
                    if is_reply or is_retweet:
                        continue
                elif tweet_type == 'reply':
                    if is_retweet:
                        continue
                views = tweet_result.get('views', {}).get('count', 0)
                if isinstance(views, str):
                    views = int(views) if views.isdigit() else 0
                tweet_data = {
                    'tweet_id': legacy.get('id_str', ''),
                    'text': legacy.get('full_text', ''),
                    'created_at': legacy.get('created_at', ''),
                    'likes': legacy.get('favorite_count', 0),
                    'retweets': legacy.get('retweet_count', 0),
                    'replies': legacy.get('reply_count', 0),
                    'quotes': legacy.get('quote_count', 0),
                    'views': views,
                    'hashtags': ','.join([h['text'] for h in legacy.get('entities', {}).get('hashtags', [])]),
                    'mentions': ','.join([m['screen_name'] for m in legacy.get('entities', {}).get('user_mentions', [])]),
                    'has_media': len(legacy.get('entities', {}).get('media', [])) > 0,
                    'url': f"https://twitter.com/{username}/status/{legacy.get('id_str', '')}"
                }
                if is_reply:
                    tweet_data['replying_to_username'] = legacy.get('in_reply_to_screen_name', '')
                    tweet_data['replying_to_tweet_id'] = legacy.get('in_reply_to_status_id_str', '')
                tweets.append(tweet_data)
        return tweets

    def get_comments_on_post(self, tweet_id: str, count: int = 50) -> List[Dict]:
        endpoints = [
            f"/comments-v2?pid={tweet_id}&rankingMode=Recency&count={count}",
            f"/comments?pid={tweet_id}&count={count}",
        ]
        for endpoint in endpoints:
            data = self.api.call(endpoint)
            if not data.get('error') and 'result' in data:
                comments = self._parse_comments(data, tweet_id)
                if comments:
                    return comments
        return []

    def _parse_comments(self, data: Dict, tweet_id: str) -> List[Dict]:
        comments = []
        entries = []
        if 'result' in data:
            result = data['result']
            if 'instructions' in result:
                for instruction in result['instructions']:
                    if instruction.get('type') == 'TimelineAddEntries':
                        entries = instruction.get('entries', [])
                        break
        if not entries:
            instructions = data.get('data', {}).get('threaded_conversation_with_injections_v2', {}).get('instructions', [])
            if instructions and isinstance(instructions, list):
                for instruction in instructions:
                    if instruction.get('type') == 'TimelineAddEntries':
                        entries = instruction.get('entries', [])
                        break
        for entry in entries:
            entry_id = entry.get('entryId', '')
            if 'cursor' in entry_id.lower():
                continue
            content = entry.get('content', {})
            if content.get('entryType') == 'TimelineTimelineItem':
                item_content = content.get('itemContent', {})
                tweet_results = item_content.get('tweet_results', {})
                result = tweet_results.get('result', {})
                if result:
                    comment = self._extract_comment_from_result(result, tweet_id)
                    if comment:
                        comments.append(comment)
            elif content.get('entryType') == 'TimelineTimelineModule':
                items = content.get('items', [])
                for item in items:
                    item_content = item.get('item', {}).get('itemContent', {})
                    tweet_results = item_content.get('tweet_results', {})
                    result = tweet_results.get('result', {})
                    if result:
                        comment = self._extract_comment_from_result(result, tweet_id)
                        if comment:
                            comments.append(comment)
        return comments

    def _extract_comment_from_result(self, result: Dict, original_tweet_id: str) -> Optional[Dict]:
        try:
            if 'tweet' in result:
                tweet = result['tweet']
            else:
                tweet = result
            comment_id = tweet.get('rest_id') or tweet.get('id_str')
            if comment_id == original_tweet_id:
                return None
            legacy = tweet.get('legacy', {})
            if not legacy:
                return None
            comment_text = legacy.get('full_text', '')
            if not comment_text or comment_text == 'N/A':
                return None
            user_result = tweet.get('core', {}).get('user_results', {}).get('result', {})
            user_legacy = user_result.get('legacy', {})
            if not user_legacy:
                user_legacy = tweet.get('user', {}).get('legacy', {})
            commenter_username = 'unknown'
            if 'screen_name' in user_legacy:
                commenter_username = user_legacy['screen_name']
            elif 'core' in user_result and 'screen_name' in user_result['core']:
                commenter_username = user_result['core']['screen_name']
            if commenter_username == 'unknown':
                return None
            commenter_name = commenter_username
            if 'name' in user_legacy:
                commenter_name = user_legacy['name']
            elif 'core' in user_result and 'name' in user_result['core']:
                commenter_name = user_result['core']['name']
            
            # Extract profile image URL - Enhanced extraction
            commenter_image_url = ''
            
            # Try avatar path first (newer structure)
            avatar = user_result.get('avatar', {})
            commenter_image_url = avatar.get('image_url', '')
            
            # Fallback to legacy path if avatar is not available
            if not commenter_image_url:
                commenter_image_url = user_legacy.get('profile_image_url_https', '')
                if not commenter_image_url:
                    commenter_image_url = user_legacy.get('profile_image_url', '')
            
            # Convert to high resolution if possible
            commenter_image_url_high_res = commenter_image_url
            if commenter_image_url and '_normal' in commenter_image_url:
                commenter_image_url_high_res = commenter_image_url.replace('_normal', '_400x400')
            
            views = tweet.get('views', {}).get('count', 0)
            if isinstance(views, str):
                views = int(views) if views.isdigit() else 0
            is_verified = user_legacy.get('verified', False) or user_result.get('is_blue_verified', False)
            
            # Extract additional user data for network analysis
            commenter_followers = user_legacy.get('followers_count', 0)
            commenter_following = user_legacy.get('friends_count', 0)
            commenter_bio = user_legacy.get('description', '')
            commenter_location = user_legacy.get('location', '')
            commenter_tweet_count = user_legacy.get('statuses_count', 0)
            
            return {
                'original_tweet_id': original_tweet_id,
                'comment_id': comment_id,
                'comment_text': comment_text,
                'commenter_username': commenter_username,
                'commenter_name': commenter_name,
                'commenter_verified': is_verified,
                'commenter_image_url': commenter_image_url,
                'commenter_image_url_high_res': commenter_image_url_high_res,
                'commenter_followers': commenter_followers,
                'commenter_following': commenter_following,
                'commenter_bio': commenter_bio,
                'commenter_location': commenter_location,
                'commenter_tweet_count': commenter_tweet_count,
                'comment_date': legacy.get('created_at', ''),
                'comment_likes': legacy.get('favorite_count', 0),
                'comment_retweets': legacy.get('retweet_count', 0),
                'comment_replies': legacy.get('reply_count', 0),
                'comment_views': views,
                'comment_url': f"https://twitter.com/{commenter_username}/status/{comment_id}"
            }
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            return None

    def get_all_comments_parallel(self, tweets: List[Dict], username: str, max_tweets: int = 20,
                                  comments_per_tweet: int = 50, max_workers: int = 15, progress_callback=None) -> List[Dict]:
        """Fetch comments in parallel with optimized batch processing"""
        tweets_with_replies = [t for t in tweets if t.get('replies', 0) > 0]
        if not tweets_with_replies:
            return []

        tweets_to_check = tweets_with_replies[:max_tweets]
        all_comments = []
        completed = 0
        total = len(tweets_to_check)
        username_lower = username.lower()

        def fetch_comments(tweet: Dict) -> List[Dict]:
            """Fetch comments for a single tweet"""
            try:
                tweet_id = tweet['tweet_id']
                comments = self.get_comments_on_post(tweet_id, comments_per_tweet)
                return [c for c in comments if c.get('commenter_username', '').lower() != username_lower]
            except (KeyError, TypeError) as e:
                return []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_comments, tweet): tweet for tweet in tweets_to_check}
            for future in as_completed(futures):
                try:
                    comments = future.result(timeout=30)
                    all_comments.extend(comments)
                except Exception as e:
                    pass  # Skip failed requests
                finally:
                    completed += 1
                    if progress_callback:
                        progress_callback(f"Comments: {len(all_comments)} collected ({completed}/{total} tweets)")

        return all_comments

# ============================================================
# MISTRAL AI ANALYZER (LEGACY - DEPRECATED)
# NOTE: This class is kept for backward compatibility only.
# New code should use EnhancedMistralAnalyzer from mistral_rate_limiter.py
# which includes advanced rate limiting, circuit breakers, and health tracking.
# ============================================================
class MistralAnalyzer:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.failed_keys = set()  # Track failed keys
        self.session = self._create_session()
        self.request_timeout = 60  # Reduced from 120 for faster failover
        
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        # Optimized retry strategy for faster failover
        retry_strategy = Retry(
            total=2,  # Reduced retries
            backoff_factor=0.5,  # Faster backoff
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Connection pooling
            pool_maxsize=20
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _get_current_key(self) -> str:
        """Get the current API key, skipping known failed keys"""
        attempts = 0
        while attempts < len(self.api_keys):
            key = self.api_keys[self.current_key_index]
            if key not in self.failed_keys:
                return key
            self._switch_to_next_key()
            attempts += 1
        # If all keys failed, clear failed set and retry
        self.failed_keys.clear()
        return self.api_keys[self.current_key_index]
    
    def _switch_to_next_key(self) -> bool:
        """Switch to next API key. Returns True if switched, False if no more keys"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return True
    
    def _reset_key_index(self):
        """Reset to first key for next request"""
        self.current_key_index = 0
    
    def _mark_key_failed(self, key: str):
        """Mark a key as temporarily failed"""
        self.failed_keys.add(key)

    def analyze(self, prompt: str, max_tokens: int = MISTRAL_MAX_TOKENS) -> Optional[str]:
        """Optimized analyze with faster failover and smart key management"""
        payload = {
            "model": MISTRAL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": MISTRAL_TEMPERATURE,
            "max_tokens": max_tokens
        }
        
        # Try up to 8 different keys before giving up (increased from 5)
        max_attempts = min(8, len(self.api_keys))
        
        for attempt in range(max_attempts):
            current_key = self._get_current_key()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {current_key}"
            }
            
            try:
                response = self.session.post(
                    MISTRAL_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()['choices'][0]['message']['content']
                    except (KeyError, ValueError, json.JSONDecodeError):
                        return None
                
                elif response.status_code == 429:
                    # Rate limit - mark key and switch immediately
                    self._mark_key_failed(current_key)
                    self._switch_to_next_key()
                    continue
                
                elif response.status_code >= 500:
                    # Server error - switch to next key
                    self._switch_to_next_key()
                    continue
                
                else:
                    # Other error - try next key
                    self._switch_to_next_key()
                    continue
            
            except requests.exceptions.Timeout:
                # Timeout - switch immediately, no retry
                self._mark_key_failed(current_key)
                self._switch_to_next_key()
                continue
            
            except requests.exceptions.RequestException:
                # Connection error - switch to next key
                self._switch_to_next_key()
                continue
            
            except Exception:
                # Unknown error - try next key
                self._switch_to_next_key()
                continue
        
        return None
    
    def analyze_batch(self, prompts: List[tuple], max_workers: int = 3) -> Dict[str, str]:
        """Parallel batch processing of multiple prompts"""
        results = {}
        
        def process_single(section_key: str, prompt: str, max_tokens: int):
            content = self.analyze(prompt, max_tokens)
            return section_key, content
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single, sk, p, mt): sk 
                for sk, p, mt in prompts
            }
            
            for future in as_completed(futures):
                try:
                    section_key, content = future.result(timeout=180)
                    if content:
                        results[section_key] = content
                except Exception:
                    pass
        
        return results

# ============================================================
# DATA PROCESSING
# ============================================================
@st.cache_data(ttl=3600)
def parse_twitter_date(date_str):
    """Parse Twitter date string with caching"""
    try:
        return pd.to_datetime(date_str, format='%a %b %d %H:%M:%S %z %Y')
    except (ValueError, TypeError):
        try:
            return pd.to_datetime(date_str)
        except (ValueError, TypeError):
            return None

def process_dataframe_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Process dataframe with optimized vectorized operations"""
    if df is None or df.empty:
        return df

    df = df.copy()

    # Vectorized date parsing
    if 'created_at' in df.columns:
        df['parsed_date'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
        if df['parsed_date'].notna().any():
            df['parsed_date'] = df['parsed_date'].dt.tz_localize(None)
            df['hour'] = df['parsed_date'].dt.hour
            df['day_of_week'] = df['parsed_date'].dt.day_name()
            df['date'] = df['parsed_date'].dt.date

    # Vectorized numeric conversion
    numeric_cols = ['likes', 'retweets', 'replies', 'views']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')

    # Vectorized engagement calculations
    if all(col in df.columns for col in ['likes', 'retweets', 'replies']):
        df['total_engagement'] = df[['likes', 'retweets', 'replies']].sum(axis=1)
        df['engagement_rate'] = np.where(
            df['views'] > 0,
            (df['total_engagement'] / df['views'] * 100),
            0
        )
        df['engagement_rate'] = df['engagement_rate'].replace([np.inf, -np.inf], 0).clip(upper=100)

    return df

def prepare_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df_excel = df.copy()
    for col in df_excel.columns:
        if pd.api.types.is_datetime64_any_dtype(df_excel[col]):
            if hasattr(df_excel[col].dtype, 'tz') and df_excel[col].dtype.tz is not None:
                df_excel[col] = df_excel[col].dt.tz_localize(None)
    return df_excel

# ============================================================
# CHARTS
# ============================================================
def create_line_chart(df):
    """Create engagement timeline chart with optimized data processing"""
    try:
        if df is None or df.empty or 'date' not in df.columns or df['date'].isna().all():
            return None

        # Optimized aggregation
        daily_stats = df.groupby('date', as_index=False).agg({
            'likes': 'sum',
            'retweets': 'sum',
            'replies': 'sum'
        })
        daily_stats['total_engagement'] = daily_stats[['likes', 'retweets', 'replies']].sum(axis=1)
        daily_stats = daily_stats.dropna()

        if daily_stats.empty:
            return None

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['total_engagement'],
            name='Total Engagement',
            line=dict(color='#ff6b6b', width=3),
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.1)'
        ))
        fig.update_layout(
            title="",
            xaxis_title="",
            yaxis_title="Total Engagement",
            height=350,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", color='#666'),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(showgrid=False, showline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', showline=False)
        return fig
    except (KeyError, ValueError, TypeError) as e:
        return None

def create_metric_comparison_chart(df, metric_name, metric_color='#667eea'):
    """Create metric comparison chart with posts count"""
    try:
        if df is None or df.empty or 'date' not in df.columns or df['date'].isna().all():
            return None
        metric_col = metric_name.lower()
        if metric_col not in df.columns:
            return None

        daily_stats = df.groupby('date', as_index=False).agg({
            'tweet_id': 'count',
            metric_col: 'sum'
        })
        daily_stats.columns = ['date', 'posts', metric_col]
        daily_stats = daily_stats.dropna()

        if daily_stats.empty:
            return None

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['posts'],
            name='Number of Posts',
            marker_color='#333333',
            opacity=0.6,
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats[metric_col],
            name=metric_name,
            line=dict(color=metric_color, width=3),
            mode='lines+markers',
            marker=dict(size=6),
            yaxis='y2'
        ))
        fig.update_layout(
            title="",
            xaxis_title="",
            height=320,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", color='#666'),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(
                title=dict(text="Posts", font=dict(color="#333333")),
                tickfont=dict(color="#333333"),
                showgrid=True,
                gridcolor='#f0f0f0'
            ),
            yaxis2=dict(
                title=dict(text=metric_name, font=dict(color=metric_color)),
                tickfont=dict(color=metric_color),
                overlaying="y",
                side="right",
                showgrid=False
            )
        )
        fig.update_xaxes(showgrid=False, showline=False)
        return fig
    except (KeyError, ValueError, TypeError):
        return None

def create_engagement_rate_chart(df):
    """Create engagement rate timeline chart"""
    try:
        if df is None or df.empty or 'date' not in df.columns or df['date'].isna().all() or 'engagement_rate' not in df.columns:
            return None

        daily_stats = df.groupby('date', as_index=False).agg({'engagement_rate': 'mean'})
        daily_stats = daily_stats.dropna()

        if daily_stats.empty:
            return None

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['engagement_rate'],
            name='Engagement Rate %',
            line=dict(color='#00cc88', width=3),
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(0, 204, 136, 0.1)'
        ))
        fig.update_layout(
            title="",
            xaxis_title="",
            yaxis_title="Engagement Rate %",
            height=320,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", color='#666'),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(showgrid=False, showline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', showline=False)
        return fig
    except (KeyError, ValueError, TypeError):
        return None

def create_bar_chart(df, column, title):
    """Create bar chart for hour or day of week analysis"""
    try:
        if df is None or df.empty or column not in df.columns or df[column].isna().all() or 'total_engagement' not in df.columns:
            return None

        if column == 'hour':
            data = df.groupby('hour', as_index=False)['total_engagement'].mean()
            data['hour'] = data['hour'].astype(str) + ':00'
            x_data = data['hour']
        else:
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            data = df.groupby('day_of_week', as_index=False)['total_engagement'].mean()
            data['day_of_week'] = pd.Categorical(data['day_of_week'], categories=day_order, ordered=True)
            data = data.sort_values('day_of_week')
            x_data = data['day_of_week']

        data = data.dropna()
        if data.empty:
            return None

        best_idx = data['total_engagement'].idxmax()
        colors = ['#ff6b6b' if i == best_idx else '#ffd4d4' for i in range(len(data))]

        fig = go.Figure(data=[go.Bar(
            x=x_data,
            y=data['total_engagement'],
            marker_color=colors,
            marker_line_width=0
        )])
        fig.update_layout(
            title="",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", color='#666')
        )
        fig.update_xaxes(showgrid=False, showline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', showline=False)
        return fig
    except (KeyError, ValueError, TypeError):
        return None

# ============================================================
# EXTRACTION MODAL
# ============================================================
@st.dialog("Extract X Data", width="large")
def show_extraction_modal():
    st.markdown("### Configure Your Extraction")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("X Username", value="thatdayin1992", help="Enter username without @")
        target_posts = st.number_input("Target Posts", min_value=100, max_value=30000, value=5000, step=100)
        target_replies = st.number_input("Target Replies", min_value=100, max_value=30000, value=5000, step=100)
    with col2:
        max_pages = st.slider("Maximum Pages", min_value=10, max_value=300, value=100, step=10)
        fetch_comments = st.checkbox("Fetch Comments on Posts", value=True)
        if fetch_comments:
            max_tweets_for_comments = st.number_input("Max Posts to Check", min_value=10, max_value=5000, value=500, step=10)
            comments_per_tweet = st.slider("Comments per Post", min_value=10, max_value=100, value=50, step=10)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Start Extraction", type="primary", use_container_width=True):
        if not username:
            st.error("Please enter a username to continue")
            return
        run_extraction(username, target_posts, target_replies, max_pages, fetch_comments, 
                      max_tweets_for_comments if fetch_comments else 0, 
                      comments_per_tweet if fetch_comments else 50)

def run_extraction(username, target_posts, target_replies, max_pages, fetch_comments, max_tweets_for_comments, comments_per_tweet):
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    start_time = time.time()
    try:
        api = TwitterAPI(API_KEY, API_HOST)
        extractor = TwitterExtractor(api)
        status_placeholder.info("Fetching user information...")
        user_info = extractor.get_user_info(username)
        if not user_info:
            st.error("User not found. Please check the username.")
            return
        col1, col2 = st.columns([1, 4])
        with col1:
            if user_info.get('image_url_high_res'):
                st.image(user_info['image_url_high_res'], width=80)
        with col2:
            st.markdown(f"**{user_info['name']}** (@{user_info['username']})")
            st.caption(f"{user_info['followers_count']:,} followers")
        st.divider()
        status_placeholder.info("Extracting posts...")
        progress_bar = progress_placeholder.progress(0)
        def update_progress(message):
            status_placeholder.info(message)
        posts = extractor.get_user_posts_paginated(user_info['user_id'], username, target_posts, max_pages, progress_callback=update_progress)
        progress_bar.progress(33)
        status_placeholder.info("Extracting replies...")
        replies = extractor.get_user_replies_paginated(user_info['user_id'], username, target_replies, max_pages, progress_callback=update_progress)
        progress_bar.progress(66)
        comments = []
        if fetch_comments and posts:
            status_placeholder.info("Extracting comments (this may take a while)...")
            comments = extractor.get_all_comments_parallel(posts, username, max_tweets=max_tweets_for_comments,
                                                           comments_per_tweet=comments_per_tweet, max_workers=MAX_COMMENT_WORKERS,
                                                           progress_callback=update_progress)
        progress_bar.progress(100)
        for post in posts:
            post['tweet_type'] = 'Original Post'
        for reply in replies:
            reply['tweet_type'] = 'Reply to Others'
        all_tweets = posts + replies
        if all_tweets:
            df_all = pd.DataFrame(all_tweets)
            df_all = df_all.drop_duplicates(subset=['tweet_id'], keep='first')
            cols = df_all.columns.tolist()
            if 'tweet_type' in cols:
                cols.remove('tweet_type')
                cols = ['tweet_type'] + cols
                df_all = df_all[cols]
            if 'created_at' in df_all.columns:
                df_all = df_all.sort_values('created_at', ascending=False)
            df_all = process_dataframe_for_analysis(df_all)
        else:
            df_all = pd.DataFrame()
        if comments:
            df_comments = pd.DataFrame(comments)
            df_comments = df_comments.drop_duplicates(subset=['comment_id'], keep='first')
        else:
            df_comments = pd.DataFrame()
        
        # Enhanced user profile data with more fields
        df_user_profile = pd.DataFrame([{
            'Username': user_info['username'],
            'User ID': user_info['user_id'],
            'Name': user_info['name'],
            'Followers Count': user_info['followers_count'],
            'Following Count': user_info['following_count'],
            'Bio': user_info['bio'],
            'Location': user_info['location'],
            'Image URL': user_info['image_url'],
            'Image URL (High Res)': user_info['image_url_high_res'],
            'Tweet Count': user_info.get('tweet_count', 0),
            'Verified': user_info.get('verified', False),
            'Category': user_info.get('category', ''),
            'Created At': user_info.get('created_at', ''),
            'URL': user_info.get('url', '')
        }])
        
        elapsed_time = time.time() - start_time
        st.session_state['extracted_data'] = {
            'profile': df_user_profile,
            'tweets': df_all,
            'comments': df_comments,
            'username': username,
            'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stats': {
                'posts': len(posts),
                'replies': len(replies),
                'comments': len(df_comments) if not df_comments.empty else 0,
                'elapsed': elapsed_time
            }
        }
        st.session_state.data_loaded = True
        st.session_state.ai_report_cache = {}
        progress_placeholder.empty()
        status_placeholder.success(f"✅ Extraction complete in {elapsed_time:.1f} seconds!")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Posts", len(posts))
        col2.metric("Replies", len(replies))
        col3.metric("Total", len(df_all) if not df_all.empty else 0)
        col4.metric("Comments", len(df_comments) if not df_comments.empty else 0)
        st.success("🎉 Data successfully loaded! Close this dialog to view your dashboard.")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)

# ============================================================
# AI REPORT GENERATION - مع روابط إثبات بعد كل جملة + Hyperlinks
# ============================================================
def generate_ai_section(ai_analyzer, section_name: str, prompt: str, max_tokens: int = 2000) -> str:
    """Generate AI section with enhanced error handling and diagnostics"""
    if section_name in st.session_state.ai_report_cache:
        return st.session_state.ai_report_cache[section_name]

    # Show processing indicator
    with st.spinner(f'جاري معالجة قسم: {section_name}...'):
        # First attempt with full prompt
        try:
            result = ai_analyzer.analyze(prompt, max_tokens)

            if result:
                cleaned_result = result.replace('**', '').replace('*', '').strip()
                st.session_state.ai_report_cache[section_name] = cleaned_result
                return cleaned_result
        except Exception as e:
            st.warning(f"تحذير: فشلت المحاولة الأولى ({str(e)[:100]})")
            # Continue to fallback
    
    # Fallback: Try with reduced prompt (shorter evidence)
    if "التغريدات مع روابطها:" in prompt or "التعليقات مع روابطها:" in prompt:
        # Reduce evidence text to 50% and retry
        lines = prompt.split('\n')
        reduced_lines = []
        evidence_section = False
        evidence_count = 0
        max_evidence = 30  # Reduced from original
        
        for line in lines:
            if 'التغريدات مع روابطها:' in line or 'التعليقات مع روابطها:' in line:
                evidence_section = True
                reduced_lines.append(line)
            elif evidence_section and ('المطلوب' in line or '**' in line):
                evidence_section = False
                reduced_lines.append(line)
            elif evidence_section:
                if evidence_count < max_evidence:
                    reduced_lines.append(line)
                    if line.strip().startswith('التغريدة رقم') or line.strip().startswith('التعليق رقم'):
                        evidence_count += 1
            else:
                reduced_lines.append(line)
        
        reduced_prompt = '\n'.join(reduced_lines)

        try:
            result = ai_analyzer.analyze(reduced_prompt, max_tokens)

            if result:
                cleaned_result = result.replace('**', '').replace('*', '').strip()
                st.session_state.ai_report_cache[section_name] = cleaned_result
                return cleaned_result
        except Exception as e:
            st.warning(f"تحذير: فشلت المحاولة الثانية ({str(e)[:100]})")

    # Show health report if using enhanced analyzer
    if GEMINI_AVAILABLE and hasattr(ai_analyzer, 'get_health_report'):
        try:
            health = ai_analyzer.get_health_report()
            available_keys = sum(1 for stats in health.values() if stats['is_available'])
            st.warning(f"⚠️ مفاتيح API المتاحة: {available_keys}/{len(health)}")
        except:
            pass

    # If still failed, return error with suggestion
    return f"⚠️ لم نتمكن من إنشاء القسم. جرب تقليل نطاق التاريخ أو أعد المحاولة."

def display_report_section(title: str, content: str):
    """عرض القسم مع تحويل الروابط لـ hyperlinks قابلة للضغط"""
    import re
    
    # تحويل الروابط لـ hyperlinks
    def make_link_clickable(match):
        url = match.group(1)
        return f'<a href="{url}" target="_blank" style="color: #1DA1F2; text-decoration: none; font-weight: bold; border-bottom: 1px solid #1DA1F2;">🔗 رابط الإثبات</a>'
    
    # Pattern للروابط داخل [الإثبات: ...]
    content = re.sub(r'\[الإثبات:\s*(https?://[^\]]+)\]', make_link_clickable, content)
    
    st.markdown(f"""
    <div class="report-section">
        <div class="report-title">{title}</div>
        <div class="report-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def extract_tweet_urls_for_evidence(df_tweets, sample_size=200):
    """استخراج جميع التغريدات مع روابطها (بدون فلترة)"""
    if df_tweets is None or df_tweets.empty:
        return []
    
    df_sorted = df_tweets.sort_values('total_engagement', ascending=False).head(sample_size)
    tweet_evidence = []
    
    for _, tweet in df_sorted.iterrows():
        evidence = {
            'url': tweet.get('url', ''),
            'text': tweet.get('text', '')[:300],
            'likes': tweet.get('likes', 0),
            'retweets': tweet.get('retweets', 0),
            'date': tweet.get('created_at', '')
        }
        tweet_evidence.append(evidence)
    
    return tweet_evidence

def ai_detailed_report_page():
    """صفحة التقرير التفصيلي مع روابط الإثبات كـ Hyperlinks"""
    if not st.session_state.data_loaded or 'extracted_data' not in st.session_state:
        st.info("📊 لازم تستخرج البيانات أول من قسم لوحة التحكم")
        if st.button("استخراج البيانات", type="primary"):
            show_extraction_modal()
        return
    
    data = st.session_state['extracted_data']
    df_tweets = data.get('tweets')
    df_comments = data.get('comments')
    username = data.get('username', 'User')
    
    if df_tweets is None or df_tweets.empty:
        st.warning("ما فيه بيانات متوفرة حق التحليل")
        return
    
    # Parse dates in dataframes if not already parsed
    if 'parsed_date' not in df_tweets.columns:
        df_tweets = process_dataframe_for_analysis(df_tweets.copy())
    if df_comments is not None and not df_comments.empty and 'parsed_date' not in df_comments.columns:
        df_comments_temp = df_comments.copy()
        if 'comment_date' in df_comments_temp.columns:
            df_comments_temp['created_at'] = df_comments_temp['comment_date']
            df_comments_temp = process_dataframe_for_analysis(df_comments_temp)
            df_comments = df_comments_temp
    
    # Get min and max dates from the data
    try:
        min_tweet_date = df_tweets['parsed_date'].min()
        max_tweet_date = df_tweets['parsed_date'].max()
        min_comment_date = df_comments['parsed_date'].min() if df_comments is not None and not df_comments.empty and 'parsed_date' in df_comments.columns else min_tweet_date
        max_comment_date = df_comments['parsed_date'].max() if df_comments is not None and not df_comments.empty and 'parsed_date' in df_comments.columns else max_tweet_date
        
        overall_min_date = min(min_tweet_date, min_comment_date)
        overall_max_date = max(max_tweet_date, max_comment_date)
        
        # Convert to date objects for the date picker
        default_start_date = overall_min_date.date() if pd.notna(overall_min_date) else datetime.now().date()
        default_end_date = overall_max_date.date() if pd.notna(overall_max_date) else datetime.now().date()
    except Exception as e:
        # Fallback to current date if parsing fails
        default_start_date = datetime.now().date()
        default_end_date = datetime.now().date()
    
    # Clean Professional Header
    current_time = datetime.now().strftime("%d %B %Y - %H:%M")
    st.markdown(f"""
    <div style="
        direction: rtl;
        background: white;
        padding: 40px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        font-family: 'Cairo', sans-serif;
        border-right: 5px solid #3b82f6;
    ">
        <h1 style="
            font-size: 2.25rem; 
            margin: 0 0 12px 0; 
            font-weight: 700;
            direction: rtl;
            color: #000000;
        ">📊 تقرير التحليل التفصيلي</h1>
        <h2 style="
            font-size: 1.25rem; 
            margin: 0 0 20px 0; 
            font-weight: 600;
            direction: rtl;
            color: #000000;
        ">حساب تويتر: @{username}</h2>
        <div style="
            display: flex;
            gap: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            direction: rtl;
        ">
            <div>
                <p style="
                    font-size: 0.875rem; 
                    margin: 0 0 5px 0;
                    color: #000000;
                    direction: rtl;
                ">📅 تاريخ التحليل</p>
                <p style="
                    font-size: 1rem; 
                    margin: 0;
                    font-weight: 600;
                    direction: rtl;
                    color: #000000;
                ">{current_time}</p>
            </div>
            <div>
                <p style="
                    font-size: 0.875rem; 
                    margin: 0 0 5px 0;
                    color: #000000;
                    direction: rtl;
                ">📈 حجم العينة</p>
                <p style="
                    font-size: 1rem; 
                    margin: 0;
                    font-weight: 600;
                    direction: rtl;
                    color: #000000;
                ">{len(df_tweets):,} تغريدة | {len(df_comments) if df_comments is not None and not df_comments.empty else 0:,} تعليق</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create date filter UI - Button on left side
    col1, col2, col3 = st.columns([0.6, 1, 1])
    
    with col1:
        st.markdown('<p style="margin-bottom: 10px; opacity: 0;">&nbsp;</p>', unsafe_allow_html=True)
        generate_button = st.button(
            "🔍 إنشاء التقرير",
            type="primary",
            use_container_width=True,
            key="generate_detailed_report_btn"
        )
    
    with col2:
        st.markdown("""
        <p style="
            direction: rtl; 
            margin-bottom: 12px; 
            color: #000000; 
            font-weight: 700;
            font-size: 1rem;
            font-family: 'Cairo', sans-serif;
            letter-spacing: -0.01em;
        ">📆 تاريخ النهاية (إلى)</p>
        """, unsafe_allow_html=True)
        end_date = st.date_input(
            "تاريخ النهاية",
            value=default_end_date,
            min_value=default_start_date,
            max_value=default_end_date,
            help="اختر تاريخ النهاية لنطاق التقرير",
            key="report_end_date",
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown("""
        <p style="
            direction: rtl; 
            margin-bottom: 12px; 
            color: #000000; 
            font-weight: 700;
            font-size: 1rem;
            font-family: 'Cairo', sans-serif;
            letter-spacing: -0.01em;
        ">📆 تاريخ البداية (من)</p>
        """, unsafe_allow_html=True)
        start_date = st.date_input(
            "تاريخ البداية",
            value=default_start_date,
            min_value=default_start_date,
            max_value=default_end_date,
            help="اختر تاريخ البداية لنطاق التقرير",
            key="report_start_date",
            label_visibility="collapsed"
        )
    
    # Validation
    date_validation_error = None
    if start_date and end_date:
        if start_date > end_date:
            date_validation_error = True
            st.markdown("""
            <div style="
                direction: rtl;
                background: #fef3c7;
                border-right: 4px solid #f59e0b;
                padding: 20px 25px;
                border-radius: 8px;
                margin-top: 20px;
                font-family: 'Cairo', sans-serif;
                text-align: right;
            ">
                <span style="
                    font-size: 1rem;
                    font-weight: 600;
                    color: #92400e;
                    direction: rtl;
                ">⚠️ تاريخ البداية يجب أن يكون أقل من أو يساوي تاريخ النهاية</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        date_validation_error = True
    
    # Display validation success
    if not date_validation_error and generate_button:
        st.markdown(f"""
        <div style="
            direction: rtl;
            background: #d1fae5;
            border-right: 4px solid #10b981;
            padding: 20px 25px;
            border-radius: 8px;
            margin-top: 20px;
            font-family: 'Cairo', sans-serif;
            text-align: right;
        ">
            <span style="
                font-size: 1rem;
                font-weight: 600;
                color: #065f46;
                direction: rtl;
            ">✅ سيتم إنشاء التقرير من {start_date.strftime('%Y-%m-%d')} ألى {end_date.strftime('%Y-%m-%d')}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if date_validation_error:
        st.stop()
    
    if not generate_button:
        st.markdown("""
        <div style="
            direction: rtl;
            text-align: right;
            padding: 16px 20px;
            background: #e3f2fd;
            border-radius: 8px;
            border-right: 4px solid #2196f3;
            font-family: 'Cairo', sans-serif;
            color: #000000;
            font-size: 1rem;
        ">
            👆 اضغط على زر إنشاء التقرير لبدء التحليل
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Filter data based on date range
    start_datetime = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    # Filter tweets
    df_tweets = df_tweets[
        (df_tweets['parsed_date'] >= start_datetime) & 
        (df_tweets['parsed_date'] <= end_datetime)
    ].copy()
    
    # Filter comments
    if df_comments is not None and not df_comments.empty:
        df_comments = df_comments[
            (df_comments['parsed_date'] >= start_datetime) & 
            (df_comments['parsed_date'] <= end_datetime)
        ].copy()
    
    # Check if filtered data is empty
    if df_tweets.empty:
        st.markdown(f"""
        <div style="
            direction: rtl;
            text-align: right;
            padding: 16px 20px;
            background: #fff3cd;
            border-radius: 8px;
            border-right: 4px solid #ffc107;
            font-family: 'Cairo', sans-serif;
            color: #000000;
            font-size: 1rem;
        ">
            ⚠️ لا توجد بيانات في الفترة المحددة من {start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}. الرجاء اختيار نطاق تاريخ مختلف.
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Clear the AI report cache when generating a new report with different dates
    if 'ai_report_cache' in st.session_state:
        st.session_state.ai_report_cache.clear()

    # Initialize analyzer with smart rate limiting (Gemini preferred, Mistral as fallback)
    if GEMINI_AVAILABLE and GEMINI_KEYS:
        try:
            ai_analyzer = EnhancedGeminiAnalyzer(
                api_keys=GEMINI_KEYS,
                model=GEMINI_MODEL,
                temperature=GEMINI_TEMPERATURE,
                max_tokens=GEMINI_MAX_TOKENS,
                rate_limit_per_key=15,  # Gemini has higher limits: 15 requests per minute per key
                timeout=60
            )
            st.success(f"✅ استخدام محلل Google Gemini 1.5 Flash المحسّن ({len(GEMINI_KEYS)} مفاتيح API)")
        except Exception as e:
            st.error(f"❌ فشل تهيئة Gemini: {str(e)[:200]}")
            st.info("🔄 التحويل إلى Mistral AI...")
            ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)
    elif not GEMINI_KEYS:
        st.warning("⚠️ مفاتيح Gemini API غير مكوّنة - استخدام Mistral AI كبديل")
        st.info("💡 للحصول على مفاتيح Gemini مجانية: https://makersuite.google.com/app/apikey")
        ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)

        # Show API health status in expander
        with st.expander("🔍 عرض حالة مفاتيح Gemini API", expanded=False):
            try:
                health = ai_analyzer.get_health_report()
                st.write(f"**إجمالي المفاتيح:** {len(health)}")
                available = sum(1 for s in health.values() if s['is_available'])
                st.write(f"**المفاتيح المتاحة:** {available}")

                for key_id, stats in health.items():
                    status_emoji = "✅" if stats['is_available'] else "❌"
                    st.write(f"{status_emoji} {key_id}: صحة {stats['health_score']:.0f}%, نجاح {stats['success_rate']:.0f}%")
            except Exception as e:
                st.write(f"تعذر جلب التقرير الصحي: {str(e)[:100]}")
    else:
        # Fallback to legacy Mistral analyzer
        ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)
        st.warning("⚠️ استخدام محلل Mistral القديم (Gemini غير متاح)")
        st.write(f"عدد مفاتيح Mistral API: {len(MISTRAL_KEYS)}")

    sample_tweets = df_tweets['text'].dropna().head(50000).tolist()
    sample_comments_list = []
    if df_comments is not None and not df_comments.empty:
        sample_comments_list = df_comments['comment_text'].dropna().head(5000).tolist()
    
    # استخراج جميع التغريدات مع روابطها (محسّن - أقل بيانات)
    tweet_evidence_links = extract_tweet_urls_for_evidence(df_tweets, sample_size=150)
    evidence_text = "\n\n".join([
        f"التغريدة رقم {i+1}:\nالنص: {ev['text'][:200]}\nالرابط: {ev['url']}"
        for i, ev in enumerate(tweet_evidence_links[:50])  # Reduced from 100 to 50
    ])
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    sections = [
        ("introduction", "المقدمة", 8),
        ("news_sources", "المصادر الإخبارية المعتمدة", 16),
        ("network", "الشبكة الاجتماعية والتفاعلات", 24),
        ("main_topics", "القضايا والموضوعات الرئيسية", 32),
        ("uae_content", "المحتوى المتعلق بدولة الإمارات", 40),
        ("influence", "التأثير على وسائل التواصل", 48),
        ("political", "التوجهات السياسية العامة", 56),
        ("mb_links", "الارتباطات بجماعة الإخوان", 64),
        ("electronic_army", "الجيوش الإلكترونية والحملات المنظمة", 72),
        ("comments_content", "تحليل التعليقات والنقاشات", 80),
        ("critical_questions", "التحليل العميق - الأسئلة الحرجة", 90),
    ]
    
    for idx, (section_key, section_title, progress_val) in enumerate(sections):
        status_text.markdown(f"""
        <div style="
            direction: rtl;
            text-align: right;
            padding: 12px 20px;
            background: #e3f2fd;
            border-radius: 8px;
            border-right: 4px solid #2196f3;
            font-family: 'Cairo', sans-serif;
            color: #000000;
        ">
            ⏳ عم ننشئ: {section_title}...
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(progress_val)
        
        if section_key == "introduction":
            prompt = f"""أنت محلل خبير. اكتب مقدمة احترافية حق تقرير تحليل حساب تويتر.

معلومات الحساب:
- اسم المستخدم: @{username}
- إجمالي التغريدات: {len(df_tweets):,}
- عينة من آخر التغريدات:
{chr(10).join([f"- {t[:150]}" for t in sample_tweets[:200]])}

المطلوب:
اكتب مقدمة تحليلية (200-300 كلمة) تشرح:
1. أهمية تحليل حسابات التواصل الاجتماعي
2. نظرة عامة عن الحساب @{username}
3. نطاق التقرير وشو يغطي
4. منهجية التحليل المتبعة

اكتب بأسلوب احترافي ومباشر من دون زخرفة. ما تستخدم أي رموز أو علامات نجمية.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 5000)
            
        elif section_key == "news_sources":
            prompt = f"""أنت محلل إعلامي خبير. حلل المصادر الإخبارية اللي يعتمد عليها الحساب @{username}.

التغريدات مع روابطها:
{evidence_text}

المطلوب - اكتب قسماً كاملاً (500-700 كلمة) يتضمن:

1. حدد المصادر الإخبارية المذكورة أو المشار لها
2. رتبها حسب الأكثر ذكراً
3. حلل شو يعني هالاختيار حق المصادر
4. استنتاجات عن مصداقية المحتوى

**مهم جداً - طريقة كتابة روابط الإثبات:**
بعد كل جملة تحليلية، حط رابط الإثبات بهالشكل بالضبط:

"الحساب يعتمد بشكل كبير على قناة الجزيرة [الإثبات: https://twitter.com/username/status/123456789]، وهالشي يدل على توجه معين [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل جملة تحليلية لازم يكون معاها رابط إثبات
- الرابط يكون بين قوسين مربعين: [الإثبات: رابط التغريدة الكامل]
- استخدم الروابط الفعلية من التغريدات اللي فوق
- ما تجمع الروابط في النهاية، لازم تكون inline

اكتب بأسلوب تحليلي احترافي. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 8000)
            
        elif section_key == "network":
            prompt = f"""أنت محلل شبكات اجتماعية خبير. حلل الشبكة الاجتماعية حق الحساب @{username}.

التغريدات مع روابطها:
{evidence_text}

المطلوب - اكتب قسماً كاملاً (500-700 كلمة) يتضمن:

1. استخرج كل الحسابات المذكورة (@username)
2. رتب الأكثر ذكراً
3. حدد طبيعة هالحسابات
4. شو تخبرنا هالشبكة عن توجهات الحساب
5. هل فيه أنماط مثيرة للاهتمام

**مهم جداً - طريقة كتابة روابط الإثبات:**
"الحساب يتفاعل مع @AlJazeera [الإثبات: https://twitter.com/username/status/123456789] و@AJArabic [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل جملة لازم يكون معاها رابط إثبات
- الرابط: [الإثبات: رابط التغريدة الكامل]
- استخدم الروابط الفعلية من التغريدات اللي فوق

اكتب بأسلوب تحليلي. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 8000)
            
        elif section_key == "main_topics":
            prompt = f"""أنت محلل محتوى خبير. حلل القضايا والموضوعات اللي يركز عليها الحساب @{username}.

التغريدات مع روابطها:
{evidence_text}

المطلوب - اكتب قسماً كاملاً (600-900 كلمة) يتضمن:

1. حدد أهم 10 قضايا/موضوعات يركز عليها الحساب
2. رتبها حسب الأهمية والتكرار
3. القضايا اللي يدعمها بقوة
4. القضايا اللي ينتقدها
5. القضايا الإقليمية والدولية
6. تحليل عميق للأجندة العامة

**مهم جداً - طريقة كتابة روابط الإثبات:**
"القضية الأولى: القضية الفلسطينية
الحساب يركز بشكل كبير على القضية الفلسطينية [الإثبات: https://twitter.com/username/status/123456789]، ويدعم المقاومة [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل قضية لازم يكون معاها 3-5 روابط إثبات موزعة
- الرابط: [الإثبات: رابط التغريدة الكامل]
- استخدم الروابط الفعلية

اكتب بأسلوب تحليلي شامل. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 10000)
            
        elif section_key == "uae_content":
            # Mistral هو اللي يحدد التغريدات الإماراتية
            prompt = f"""أنت محلل متخصص. حلل بدقة المحتوى المتعلق بدولة الإمارات في حساب @{username}.

جميع التغريدات مع روابطها (أنت حدد اللي متعلق بالإمارات):
{evidence_text}

عدد التغريدات الكلي: {len(df_tweets):,}

**مهمتك:**
1. **اقرأ جميع التغريدات** وحدد أنت اللي فيها كلام عن الإمارات (صريح أو ضمني)
   - ممكن تكون التغريدة تذكر: الإمارات، دبي، أبوظبي، محمد بن زايد، محمد بن راشد
   - أو تتكلم عن سياسات إماراتية بدون ذكر الاسم صراحة
   - أو تنتقد/تمدح قرارات إماراتية
2. **احسب كم تغريدة** من الـ {len(df_tweets):,} تتكلم عن الإمارات
3. **احسب النسبة المئوية**
4. **حلل المشاعر**: إيجابي/سلبي/محايد/معادي
5. **المواضيع الإماراتية المحددة** (السياسة الخارجية، التطبيع، القيادة، إلخ)
6. **هل فيه إشارات للقيادة الإماراتية**
7. **تحليل معمق لطبيعة الخطاب**
8. **التقييم النهائي**

**مهم جداً - طريقة كتابة روابط الإثبات:**
"الحساب ينتقد السياسة الخارجية الإماراتية [الإثبات: https://twitter.com/username/status/123456789]، ويهاجم التطبيع [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- **أنت حدد** التغريدات الإماراتية من خلال قراءة المحتوى (مش من keywords)
- كل جملة لازم يكون معاها رابط إثبات من التغريدات اللي قريتها
- عند تحليل المشاعر، حط 5-10 روابط على الأقل
- الرابط: [الإثبات: رابط التغريدة الكامل]
- استخدم الروابط الفعلية من التغريدات اللي فوق

كن دقيقاً وموضوعياً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية.

اكتب قسماً كاملاً (700-1000 كلمة)."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 12000)
            
        elif section_key == "influence":
            total_likes = int(df_tweets['likes'].sum())
            total_retweets = int(df_tweets['retweets'].sum())
            total_replies = int(df_tweets['replies'].sum())
            avg_engagement = int((total_likes + total_retweets + total_replies) / len(df_tweets))
            
            top_tweets = df_tweets.nlargest(10, 'total_engagement')
            top_tweets_evidence = "\n\n".join([
                f"التغريدة: {row['text'][:150]}\nالرابط: {row['url']}\nالتفاعل: {row['total_engagement']:,}"
                for _, row in top_tweets.iterrows()
            ])
            
            prompt = f"""أنت محلل تأثير رقمي خبير. حلل تأثير ووصول الحساب @{username}.

البيانات:
- إجمالي التغريدات: {len(df_tweets):,}
- إجمالي الإعجابات: {total_likes:,}
- إجمالي إعادة التغريد: {total_retweets:,}
- إجمالي التعليقات: {total_replies:,}
- متوسط التفاعل: {avg_engagement:,}

أكثر 10 تغريدات تفاعلاً:
{top_tweets_evidence}

المطلوب - اكتب قسماً كاملاً (500-700 كلمة) يتضمن:

1. تحليل أرقام التفاعل
2. تقدير الوصول الفعلي
3. تحليل جودة التفاعل
4. مستوى التأثير على الرأي العام
5. تقييم عام لقوة الحساب

**مهم جداً - طريقة كتابة روابط الإثبات:**
"الحساب حقق تفاعل كبير في تغريدة عن فلسطين بأكثر من 50 ألف إعجاب [الإثبات: https://twitter.com/username/status/123456789]."

**القواعد الإلزامية:**
- عند ذكر تغريدات ذات تفاعل عالي، حط روابطها
- الرابط: [الإثبات: رابط التغريدة الكامل]

اكتب بأسلوب تحليلي واضح. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 8000)
            
        elif section_key == "political":
            prompt = f"""أنت محلل سياسي خبير. حلل التوجهات السياسية حق الحساب @{username}.

التغريدات مع روابطها:
{evidence_text}

المطلوب - اكتب قسماً كاملاً (700-1000 كلمة) يتضمن:

1. التوجه السياسي العام
2. الموقف من القضايا الكبرى (فلسطين، سوريا، اليمن، ليبيا)
3. هل يتبنى خطاباً معيناً
4. الميول الأيديولوجية الواضحة
5. تحليل الخطاب السياسي العام

**مهم جداً - طريقة كتابة روابط الإثبات:**
"الحساب يتبنى خطاباً إسلامياً واضحاً [الإثبات: https://twitter.com/username/status/123456789]، ويدعم الثورات العربية [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل موقف سياسي لازم يكون معاه رابط إثبات
- عند الحديث عن قضايا محددة، حط 3-5 روابط
- الرابط: [الإثبات: رابط التغريدة الكامل]

كن دقيقاً وموضوعياً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 10000)
            
        elif section_key == "mb_links":
            prompt = f"""أنت محلل أمني متخصص في رصد التنظيمات. حلل بدقة عالية أي ارتباطات بجماعة الإخوان المسلمين.

التغريدات مع روابطها:
{evidence_text}

المطلوب - اكتب قسماً كاملاً (800-1200 كلمة) يتضمن:

1. البحث عن المؤشرات المباشرة
2. المؤشرات غير المباشرة
3. تحليل المؤسسات والمنصات
4. التقييم الكمي
5. تحليل الخطاب
6. التصنيف النهائي

**مهم جداً - طريقة كتابة روابط الإثبات:**
"المؤشرات المباشرة:
الحساب يدافع بشكل صريح عن جماعة الإخوان [الإثبات: https://twitter.com/username/status/123456789]، ويهاجم الحكومة المصرية [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل مؤشر لازم يكون معاه 2-3 روابط إثبات
- الرابط: [الإثبات: رابط التغريدة الكامل]

كن دقيقاً وموضوعياً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            content = generate_ai_section(ai_analyzer, section_key, prompt, 12000)
            
        elif section_key == "electronic_army":
            if df_comments is None or df_comments.empty:
                content = "ما فيه بيانات تعليقات كافية حق إجراء التحليل."
            else:
                total_comments = len(df_comments)
                unique_commenters = df_comments['commenter_username'].nunique()
                diversity_ratio = (unique_commenters/total_comments*100) if total_comments > 0 else 0
                
                top_commenters = df_comments['commenter_username'].value_counts().head(30)
                heavy_commenters = len(top_commenters[top_commenters > 10])
                top_commenters_text = '\n'.join([f"- @{user}: {count} تعليق" for user, count in top_commenters.items()])
                
                comments_evidence = df_comments.head(50)
                comments_evidence_text = "\n\n".join([
                    f"المعلق: @{row['commenter_username']}\nالتعليق: {row['comment_text'][:100]}\nالرابط: {row['comment_url']}"
                    for _, row in comments_evidence.iterrows()
                ])
                
                prompt = f"""أنت خبير أمن سيبراني متخصص في كشف الجيوش الإلكترونية. حلل بدقة أنماط التعليقات على حساب @{username}.

البيانات الإحصائية:
- إجمالي التعليقات: {total_comments:,}
- عدد المعلقين الفريدين: {unique_commenters:,}
- نسبة التنوع: {diversity_ratio:.2f}%
- المعلقين الكثيفين (>10 تعليقات): {heavy_commenters}

أكثر 30 معلقاً نشاطاً:
{top_commenters_text}

عينة من التعليقات مع روابطها:
{comments_evidence_text}

المطلوب - اكتب قسماً كاملاً (800-1200 كلمة) يتضمن التحليل الكامل مع الأدلة.

**مهم جداً - طريقة كتابة روابط الإثبات:**
"الحساب @user123 علق 45 مرة في أسبوع واحد [الإثبات: https://twitter.com/username/status/123456789]، والتعليقات كلها تدعم نفس الموقف [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل مؤشر لازم يكون معاه 3-5 روابط تعليقات
- الرابط: [الإثبات: رابط التعليق الكامل]

كن دقيقاً ومفصلاً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
                content = generate_ai_section(ai_analyzer, section_key, prompt, 12000)
                
        elif section_key == "comments_content":
            if df_comments is None or df_comments.empty:
                content = "ما فيه بيانات تعليقات."
            else:
                # استخراج جميع التعليقات - Mistral يحدد الإماراتية منها
                all_comments_with_urls = []
                for idx, row in df_comments.head(100).iterrows():
                    all_comments_with_urls.append({
                        'commenter': row['commenter_username'],
                        'text': row['comment_text'][:200],
                        'url': row['comment_url']
                    })
                
                comments_evidence_text = "\n\n".join([
                    f"التعليق رقم {i+1}:\nالمعلق: @{c['commenter']}\nالنص: {c['text']}\nالرابط: {c['url']}"
                    for i, c in enumerate(all_comments_with_urls)
                ])
                
                prompt = f"""أنت محلل محتوى. حلل التعليقات على تغريدات @{username} وركز على الإمارات.

جميع التعليقات مع روابطها (أنت حدد اللي متعلق بالإمارات):
{comments_evidence_text}

إجمالي التعليقات: {len(df_comments):,}

**مهمتك:**
1. **اقرأ جميع التعليقات** وحدد أنت اللي فيها كلام عن الإمارات
2. **احسب كم تعليق** من الـ {len(df_comments):,} يتكلم عن الإمارات
3. **احسب النسبة المئوية**
4. **حلل المشاعر**: إيجابي/سلبي/محايد/معادي
5. **المواضيع الإماراتية في التعليقات**
6. **النبرة العامة**
7. **هل فيه خطاب تحريضي**
8. **التقييم الأمني**

**مهم جداً - طريقة كتابة روابط الإثبات:**
"أغلب التعليقات المتعلقة بالإمارات تحمل نبرة سلبية. أحد المعلقين يتهم الإمارات بدعم الانقلابات [الإثبات: https://twitter.com/username/status/123456789]."

**القواعد الإلزامية:**
- **أنت حدد** التعليقات الإماراتية من خلال قراءة المحتوى
- كل تحليل لازم يكون معاه 5-10 روابط تعليقات داعمة
- الرابط: [الإثبات: رابط التعليق الكامل]

كن موضوعياً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية.

اكتب قسماً كاملاً (700-1000 كلمة)."""
                content = generate_ai_section(ai_analyzer, section_key, prompt, 12000)
        
        elif section_key == "critical_questions":
            all_previous_analysis = ""
            for prev_key, prev_title, _ in sections[:-1]:
                if prev_key in st.session_state.ai_report_cache:
                    all_previous_analysis += f"\n\n=== {prev_title} ===\n{st.session_state.ai_report_cache[prev_key][:1500]}"
            
            prompt = f"""أنت محلل استخباراتي كبير متخصص في التحليل العميق للشخصيات المؤثرة. بناءً على جميع التحليلات السابقة للحساب @{username}، أجب على الأسئلة الحرجة التالية بعمق ودقة.

جميع التحليلات السابقة:
{all_previous_analysis}

التغريدات مع روابطها:
{evidence_text[:5000]}

المطلوب - اكتب تحليلاً عميقاً (1500-2000 كلمة) يجيب على الأسئلة التالية مع أدلة كاملة:

**السؤال الأول: شو هي الارتباطات غير المعلنة حق الحساب؟**
**السؤال الثاني: شو هي الأجندات السياسية غير المعلنة؟**
**السؤال الثالث: هل كان فيه نقطة محورية في تغيير التوجه؟**
**السؤال الرابع: هل الشخصية ممولة؟**
**السؤال الخامس: هل الشخصية تابعة لمنظومة؟ وشو دورها؟**
**السؤال السادس: شو علاقة كل هالنقاط ببعضها؟**
**السؤال السابع: شو سبب التغيير في التوجه؟ ومن يوقف وراءه؟**

**مهم جداً - طريقة كتابة روابط الإثبات:**
"السؤال الأول: الارتباطات غير المعلنة

ارتباطات بجماعة الإخوان المسلمين:
الحساب يدافع بشكل صريح عن الجماعة [الإثبات: https://twitter.com/username/status/123456789]، ويهاجم الدول المحاربة لها [الإثبات: https://twitter.com/username/status/987654321]."

**القواعد الإلزامية:**
- كل إجابة لازم تكون معاها 10-15 رابط إثبات على الأقل
- كل ادعاء لازم يكون معاه دليل
- الرابط: [الإثبات: رابط التغريدة الكامل]
- استخدم الروابط الفعلية من التغريدات

اعتمد على الأدلة الفعلية. كن دقيقاً وموضوعياً ومهنياً. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
            
            content = generate_ai_section(ai_analyzer, section_key, prompt, 15000)
        
        # عرض القسم مع تحويل الروابط لـ hyperlinks
        display_report_section(section_title, content)
        time.sleep(1)
    
    progress_bar.progress(100)
    status_text.empty()

def generate_pdf_report(username: str, sections_list: list, report_data: dict) -> bytes:
    """Generate PDF report with Arabic support"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from arabic_reshaper import reshape
        from bidi.algorithm import get_display
        import io
    except ImportError as e:
        raise ImportError(f"PDF libraries not available. Please install: pip install reportlab arabic-reshaper python-bidi")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Create custom styles for RTL Arabic text
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        alignment=TA_RIGHT,
        leading=20,
        rightIndent=0,
        leftIndent=0,
        spaceAfter=12,
        wordWrap='RTL'
    )
    
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        leading=24,
        spaceAfter=20,
        textColor='#1f2937'
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=TA_RIGHT,
        leading=20,
        spaceAfter=15,
        spaceBefore=15,
        textColor='#374151'
    )
    
    def process_arabic(text):
        """Process Arabic text for proper display in PDF"""
        if not text:
            return ""
        # Reshape Arabic text
        reshaped_text = reshape(text)
        # Apply bidirectional algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    # Title
    title_text = process_arabic(f"تقرير التحليل التفصيلي - حساب @{username}")
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Report Info
    date_str = datetime.now().strftime('%d %B %Y - %H:%M')
    tweets_count = len(report_data.get('tweets', [])) if report_data.get('tweets') is not None else 0
    comments_count = len(report_data.get('comments', [])) if report_data.get('comments') is not None and not report_data.get('comments').empty else 0
    
    info_text = process_arabic(f"تاريخ التحليل: {date_str}")
    story.append(Paragraph(info_text, arabic_style))
    
    sample_text = process_arabic(f"حجم العينة: {tweets_count:,} تغريدة | {comments_count:,} تعليق")
    story.append(Paragraph(sample_text, arabic_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Add sections
    for section_key, section_title in sections_list:
        if section_key in st.session_state.ai_report_cache:
            # Section title
            section_title_ar = process_arabic(section_title)
            story.append(Paragraph(section_title_ar, section_style))
            
            # Section content
            content = st.session_state.ai_report_cache[section_key]
            
            # Split content into paragraphs and process each
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Remove markdown links and clean text
                    clean_para = para.replace('[الإثبات:', '').replace(']', '')
                    processed_para = process_arabic(clean_para)
                    try:
                        story.append(Paragraph(processed_para, arabic_style))
                    except:
                        # Fallback for problematic text
                        story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = process_arabic(f"معرف التقرير: DETAILED-ANALYSIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    story.append(Paragraph(footer_text, arabic_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

def ai_summary_report_page():
    """صفحة ملخص التقرير الذكي"""
    if not st.session_state.data_loaded or 'extracted_data' not in st.session_state:
        st.info("📊 لازم تنشئ التقرير التفصيلي أول")
        return
    
    required_sections = ["news_sources", "network", "main_topics", "uae_content", "influence", 
                        "political", "mb_links", "electronic_army", "comments_content", "critical_questions"]
    
    missing_sections = [s for s in required_sections if s not in st.session_state.ai_report_cache]
    
    if missing_sections:
        st.warning("⚠️ لازم تنشئ التقرير التفصيلي أول قبل ما تشوف الملخص")
        st.info("روح لتبويب 'التقرير التفصيلي' وانشئ التقرير أول")
        return
    
    data = st.session_state['extracted_data']
    df_tweets = data.get('tweets')
    df_comments = data.get('comments')
    username = data.get('username', 'User')

    # Initialize analyzer with smart rate limiting (Gemini preferred, Mistral as fallback)
    if GEMINI_AVAILABLE and GEMINI_KEYS:
        try:
            ai_analyzer = EnhancedGeminiAnalyzer(
                api_keys=GEMINI_KEYS,
                model=GEMINI_MODEL,
                temperature=GEMINI_TEMPERATURE,
                max_tokens=GEMINI_MAX_TOKENS,
                rate_limit_per_key=15,  # Gemini has higher limits: 15 requests per minute per key
                timeout=60
            )
            st.success(f"✅ استخدام محلل Google Gemini 1.5 Flash المحسّن ({len(GEMINI_KEYS)} مفاتيح API)")
        except Exception as e:
            st.error(f"❌ فشل تهيئة Gemini: {str(e)[:200]}")
            st.info("🔄 التحويل إلى Mistral AI...")
            ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)
    elif not GEMINI_KEYS:
        st.warning("⚠️ مفاتيح Gemini API غير مكوّنة - استخدام Mistral AI كبديل")
        st.info("💡 للحصول على مفاتيح Gemini مجانية: https://makersuite.google.com/app/apikey")
        ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)

        # Show API health status in expander
        with st.expander("🔍 عرض حالة مفاتيح Gemini API", expanded=False):
            try:
                health = ai_analyzer.get_health_report()
                st.write(f"**إجمالي المفاتيح:** {len(health)}")
                available = sum(1 for s in health.values() if s['is_available'])
                st.write(f"**المفاتيح المتاحة:** {available}")

                for key_id, stats in health.items():
                    status_emoji = "✅" if stats['is_available'] else "❌"
                    st.write(f"{status_emoji} {key_id}: صحة {stats['health_score']:.0f}%, نجاح {stats['success_rate']:.0f}%")
            except Exception as e:
                st.write(f"تعذر جلب التقرير الصحي: {str(e)[:100]}")
    else:
        # Fallback to legacy Mistral analyzer
        ai_analyzer = MistralAnalyzer(MISTRAL_KEYS)
        st.warning("⚠️ استخدام محلل Mistral القديم (Gemini غير متاح)")
        st.write(f"عدد مفاتيح Mistral API: {len(MISTRAL_KEYS)}")

    previous_sections = {}
    sections_list = [
        ("news_sources", "المصادر الإخبارية المعتمدة"),
        ("network", "الشبكة الاجتماعية والتفاعلات"),
        ("main_topics", "القضايا والموضوعات الرئيسية"),
        ("uae_content", "المحتوى المتعلق بدولة الإمارات"),
        ("influence", "التأثير على وسائل التواصل"),
        ("political", "التوجهات السياسية العامة"),
        ("mb_links", "الارتباطات بجماعة الإخوان"),
        ("electronic_army", "الجيوش الإلكترونية والحملات المنظمة"),
        ("comments_content", "تحليل التعليقات والنقاشات"),
        ("critical_questions", "التحليل العميق - الأسئلة الحرجة"),
    ]
    
    for section_key, section_title in sections_list:
        if section_key in st.session_state.ai_report_cache:
            previous_sections[section_title] = st.session_state.ai_report_cache[section_key]
    
    sections_summary = "\n\n".join([
        f"=== {title} ===\n{content[:1200]}..."
        for title, content in previous_sections.items()
    ])
    
    total_likes = int(df_tweets['likes'].sum())
    total_retweets = int(df_tweets['retweets'].sum())
    total_replies = int(df_tweets['replies'].sum())
    total_engagement = total_likes + total_retweets + total_replies
    avg_engagement = int(total_engagement / len(df_tweets)) if len(df_tweets) > 0 else 0
    
    with st.spinner("عم ننشئ الملخص الذكي..."):
        prompt = f"""أنت محلل استراتيجي كبير. اكتب ملخصاً تنفيذياً شاملاً ومركزاً لحساب @{username} بناءً على التقرير التفصيلي.

حجم العينة المحللة:
- إجمالي التغريدات: {len(df_tweets):,}
- إجمالي التعليقات: {len(df_comments) if df_comments is not None else 0:,}
- إجمالي الإعجابات: {total_likes:,}
- إجمالي إعادة التغريد: {total_retweets:,}
- إجمالي الردود: {total_replies:,}
- متوسط التفاعل لكل تغريدة: {avg_engagement:,}

نتائج التحليل من جميع الأقسام السابقة:
{sections_summary}

المطلوب - اكتب ملخصاً تنفيذياً شاملاً (1500-2000 كلمة) يتضمن:

**القسم الأول: الملخص التنفيذي**
**القسم الثاني: المصادر الإخبارية**
**القسم الثالث: الشبكة الاجتماعية**
**القسم الرابع: القضايا الرئيسية**
**القسم الخامس: المحتوى المتعلق بالإمارات**
**القسم السادس: التأثير والوصول**
**القسم السابع: التوجهات السياسية**
**القسم الثامن: الارتباطات بالإخوان**
**القسم التاسع: الجيوش الإلكترونية**
**القسم العاشر: التعليقات**
**القسم الحادي عشر: الأسئلة الحرجة**
**القسم الثاني عشر: التقييم النهائي والتوصيات**

كن دقيقاً وموضوعياً. استخدم الأرقام. ما تستخدم رموز.
الرد لازم يكون بالعربية الفصحى مع لمسة إماراتية."""
        
        summary_content = generate_ai_section(ai_analyzer, "summary_conclusion", prompt, 12000)
        
        display_report_section("📋 الملخص التنفيذي الشامل", summary_content)
        
        st.success("✅ تم إنشاء الملخص الذكي بنجاح!")
# ============================================================
# DASHBOARD PAGE - COMPLETE WITH ALL CHARTS
# ============================================================
def dashboard_page():
    """Dashboard Tab with ALL Charts"""
    
    if not st.session_state.data_loaded or 'extracted_data' not in st.session_state:
        st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">Hey, Need help? 👋</h1>
            <p class="hero-subtitle">Just ask me anything!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="background: #fafafa; padding: 2rem; border-radius: 20px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="font-weight: 700; margin-bottom: 0.5rem;">Advanced Analytics</h3>
                <p style="color: #999;">Interactive charts and real-time insights</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background: #fafafa; padding: 2rem; border-radius: 20px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <h3 style="font-weight: 700; margin-bottom: 0.5rem;">Smart Insights</h3>
                <p style="color: #999;">AI-powered recommendations</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="background: #fafafa; padding: 2rem; border-radius: 20px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💾</div>
                <h3 style="font-weight: 700; margin-bottom: 0.5rem;">Export Reports</h3>
                <p style="color: #999;">Download comprehensive Excel reports</p>
            </div>
            """, unsafe_allow_html=True)
        return
    
    data = st.session_state['extracted_data']
    df_tweets = data.get('tweets')
    df_profile = data.get('profile')
    df_comments = data.get('comments')
    username = data.get('username', 'User')
    
    if df_tweets is None or df_tweets.empty:
        st.warning("No data available")
        return
    
    # Profile Section
    st.markdown('<div class="section-header">📊 Extracted Profile</div>', unsafe_allow_html=True)
    
    if 'extraction_time' in data:
        st.markdown(f"""
        <div style="background: #e8f5e9; padding: 0.75rem 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; border-left: 3px solid #4caf50;">
            <span style="color: #2e7d32; font-weight: 600;">✓ Data extracted on: {data['extraction_time']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if df_profile is not None and not df_profile.empty:
        profile = df_profile.iloc[0]
        total_engagement = df_tweets['total_engagement'].sum() if 'total_engagement' in df_tweets.columns else 0
        
        image_col, name_col, stats_col1, stats_col2, stats_col3, stats_col4 = st.columns([0.8, 2, 1.5, 1.5, 1.5, 2])
        
        with image_col:
            if profile.get('Image URL (High Res)') and str(profile['Image URL (High Res)']) != '' and str(profile['Image URL (High Res)']) != 'nan':
                st.markdown(f"""
                <div style="text-align: center;">
                    <img src="{profile['Image URL (High Res)']}" 
                         style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #f0f0f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
                         alt="{profile['Name']} profile picture">
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center;">
                    <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem; font-weight: bold; margin: 0 auto; border: 3px solid #f0f0f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        👤
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with name_col:
            st.markdown(f"""
            <div style="padding-left: 0.5rem;">
                <h2 style="margin: 0; padding: 0; font-weight: 700; color: #000; font-size: 1.6rem;">{profile['Name']}</h2>
                <p style="margin: 0; color: #888; font-size: 0.95rem;">@{profile['Username']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with stats_col1:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #ff6b6b;">{profile['Followers Count']:,}</div>
                <div style="color: #888; font-size: 0.85rem;">Followers</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stats_col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{profile['Following Count']:,}</div>
                <div style="color: #888; font-size: 0.85rem;">Following</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stats_col3:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #00cc88;">{len(df_tweets):,}</div>
                <div style="color: #888; font-size: 0.85rem;">Posts</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stats_col4:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #ff9800;">{total_engagement:,.0f}</div>
                <div style="color: #888; font-size: 0.85rem;">Engagements</div>
            </div>
            """, unsafe_allow_html=True)
        
        if profile.get('Bio') and str(profile['Bio']) != '' and str(profile['Bio']) != 'nan':
            st.markdown(f"""
            <div style="margin-top: 1.5rem; padding: 1.25rem 1.5rem; background: #fef5f5; border-radius: 12px; border-left: 4px solid #ff6b6b;">
                <p style="margin: 0; color: #555; font-size: 0.95rem; line-height: 1.7; font-style: italic;">
                    "{profile['Bio']}"
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display verification status if available
        if 'Verified' in profile and profile['Verified']:
            st.markdown("""
            <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: #e3f2fd; border-radius: 8px; border-left: 3px solid #2196f3;">
                <p style="margin: 0; color: #1565c0; font-size: 0.85rem;">
                    ✅ <strong>Verified Account</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Overview Statistics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        avg_likes = df_tweets['likes'].mean()
        st.metric("Total Likes", f"{df_tweets['likes'].sum():,.0f}", delta=f"Avg: {avg_likes:.0f}")
    with col2:
        avg_retweets = df_tweets['retweets'].mean()
        st.metric("Total Retweets", f"{df_tweets['retweets'].sum():,.0f}", delta=f"Avg: {avg_retweets:.0f}")
    with col3:
        avg_replies = df_tweets['replies'].mean()
        st.metric("Total Replies", f"{df_tweets['replies'].sum():,.0f}", delta=f"Avg: {avg_replies:.0f}")
    with col4:
        if 'views' in df_tweets.columns:
            avg_views = df_tweets['views'].mean()
            st.metric("Total Views", f"{df_tweets['views'].sum():,.0f}", delta=f"Avg: {avg_views:.0f}")
        else:
            st.metric("Total Views", "N/A")
    with col5:
        avg_eng = df_tweets['engagement_rate'].mean() if 'engagement_rate' in df_tweets.columns else 0
        st.metric("Engagement Rate", f"{avg_eng:.2f}%", delta="Excellent!" if avg_eng > 2 else "Good")
    
    st.markdown('<div class="section-header">Content Insights</div>', unsafe_allow_html=True)
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.markdown("**📊 Content Type Distribution**")
        posts_count = len(df_tweets[df_tweets['tweet_type'] == 'Original Post']) if 'tweet_type' in df_tweets.columns else len(df_tweets)
        replies_count = len(df_tweets[df_tweets['tweet_type'] == 'Reply to Others']) if 'tweet_type' in df_tweets.columns else 0
        comments_count = len(df_comments) if df_comments is not None and not df_comments.empty else 0
        
        fig_content = go.Figure(data=[go.Pie(
            labels=['Original Posts', 'Replies', 'Comments Received'],
            values=[posts_count, replies_count, comments_count],
            hole=0.4,
            marker=dict(colors=['#ff6b6b', '#667eea', '#00cc88']),
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        fig_content.update_layout(
            height=300,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=11)
        )
        st.plotly_chart(fig_content, use_container_width=True)
    
    with insight_col2:
        st.markdown("**🎬 Media Usage**")
        if 'has_media' in df_tweets.columns:
            media_count = df_tweets['has_media'].sum()
            no_media_count = len(df_tweets) - media_count
            
            fig_media = go.Figure(data=[go.Pie(
                labels=['With Media', 'Without Media'],
                values=[media_count, no_media_count],
                hole=0.4,
                marker=dict(colors=['#ff9800', '#e0e0e0']),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            fig_media.update_layout(
                height=300,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter", size=11)
            )
            st.plotly_chart(fig_media, use_container_width=True)
            
            if media_count > 0 and no_media_count > 0:
                media_eng = df_tweets[df_tweets['has_media'] == True]['total_engagement'].mean()
                no_media_eng = df_tweets[df_tweets['has_media'] == False]['total_engagement'].mean()
                if media_eng > no_media_eng:
                    improvement = ((media_eng/no_media_eng - 1) * 100)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ff9800; margin-top: 0.5rem;">
                        <p style="margin: 0; color: #e65100; font-size: 0.85rem;">
                            💡 Posts with media get <strong>{improvement:.0f}% more engagement!</strong><br>
                            📸 Keep using images and videos to boost your reach.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    improvement = ((no_media_eng/media_eng - 1) * 100)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #2196f3; margin-top: 0.5rem;">
                        <p style="margin: 0; color: #1565c0; font-size: 0.85rem;">
                            💡 Text-only posts perform <strong>{improvement:.0f}% better</strong>!<br>
                            ✍️ Your audience loves your written content.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Engagement Timeline</div>', unsafe_allow_html=True)
    
    fig = create_line_chart(df_tweets)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        total_eng = df_tweets['total_engagement'].sum() if 'total_engagement' in df_tweets.columns else 0
        avg_daily_eng = df_tweets.groupby('date')['total_engagement'].sum().mean() if 'date' in df_tweets.columns else 0
        best_day_eng = df_tweets.groupby('date')['total_engagement'].sum().max() if 'date' in df_tweets.columns else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #e1f5fe 100%); padding: 1rem 1.5rem; border-radius: 12px; border-left: 4px solid #2196f3; margin-top: 1rem;">
            <p style="margin: 0; color: #1565c0; font-size: 0.95rem; line-height: 1.7;">
                💫 <strong>Total Engagement: {total_eng:,.0f}</strong><br>
                📊 Your posts generate an average of <strong>{avg_daily_eng:.0f} engagements per day</strong>. 
                Your best performing day achieved <strong>{best_day_eng:,.0f} engagements</strong>!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📊 Timeline chart requires date information to display")
    
    st.markdown('<div class="section-header">Engagement Rate Trend</div>', unsafe_allow_html=True)
    
    fig_rate = create_engagement_rate_chart(df_tweets)
    if fig_rate:
        st.plotly_chart(fig_rate, use_container_width=True)
        avg_rate = df_tweets['engagement_rate'].mean() if 'engagement_rate' in df_tweets.columns else 0
        best_rate = df_tweets['engagement_rate'].max() if 'engagement_rate' in df_tweets.columns else 0
        
        if avg_rate > 3:
            performance = "🔥 Excellent"
            color = "#4caf50"
        elif avg_rate > 1.5:
            performance = "✨ Great"
            color = "#2196f3"
        elif avg_rate > 0.5:
            performance = "👍 Good"
            color = "#ff9800"
        else:
            performance = "📈 Room for Growth"
            color = "#f44336"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); padding: 1rem 1.5rem; border-radius: 12px; border-left: 4px solid {color}; margin-top: 1rem;">
            <p style="margin: 0; color: #2e7d32; font-size: 0.95rem; line-height: 1.7;">
                {performance} - Your average engagement rate is <strong>{avg_rate:.2f}%</strong> with a peak of <strong>{best_rate:.2f}%</strong>. 
                Industry average is around 1-3%, so {"you're doing fantastic! 🎉" if avg_rate > 1.5 else "keep optimizing your content! 💪"}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📊 Engagement rate chart requires date information to display")
    
    st.markdown('<div class="section-header">Posts vs Metrics Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📊 Posts vs Likes**")
        fig_likes = create_metric_comparison_chart(df_tweets, 'Likes', '#ff6b6b')
        if fig_likes:
            st.plotly_chart(fig_likes, use_container_width=True)
            total_likes = df_tweets['likes'].sum()
            avg_likes = df_tweets['likes'].mean()
            best_post_likes = df_tweets['likes'].max()
            st.markdown(f"""
            <div style="background: #fff5f5; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ff6b6b; margin-top: 0.5rem;">
                <p style="margin: 0; color: #c62828; font-size: 0.85rem;">
                    ❤️ <strong>{total_likes:,} total likes</strong> | Avg: {avg_likes:.0f} per post | Best: {best_post_likes:,}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 Chart requires date information to display")
    
    with col2:
        st.markdown("**🔄 Posts vs Retweets**")
        fig_retweets = create_metric_comparison_chart(df_tweets, 'Retweets', '#00cc88')
        if fig_retweets:
            st.plotly_chart(fig_retweets, use_container_width=True)
            total_retweets = df_tweets['retweets'].sum()
            avg_retweets = df_tweets['retweets'].mean()
            best_post_retweets = df_tweets['retweets'].max()
            st.markdown(f"""
            <div style="background: #e8f5e9; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #00cc88; margin-top: 0.5rem;">
                <p style="margin: 0; color: #2e7d32; font-size: 0.85rem;">
                    🔄 <strong>{total_retweets:,} total retweets</strong> | Avg: {avg_retweets:.0f} per post | Best: {best_post_retweets:,}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 Chart requires date information to display")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💬 Posts vs Replies**")
        fig_replies = create_metric_comparison_chart(df_tweets, 'Replies', '#667eea')
        if fig_replies:
            st.plotly_chart(fig_replies, use_container_width=True)
            total_replies = df_tweets['replies'].sum()
            avg_replies = df_tweets['replies'].mean()
            best_post_replies = df_tweets['replies'].max()
            st.markdown(f"""
            <div style="background: #f3e5f5; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #667eea; margin-top: 0.5rem;">
                <p style="margin: 0; color: #4a148c; font-size: 0.85rem;">
                    💬 <strong>{total_replies:,} total replies</strong> | Avg: {avg_replies:.0f} per post | Best: {best_post_replies:,}<br>
                    {"🎯 Great conversation starter!" if avg_replies > 5 else "💡 Try asking questions to boost replies!"}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 Chart requires date information to display")
    
    with col2:
        st.markdown("**👁️ Posts vs Views**")
        if 'views' in df_tweets.columns:
            fig_views = create_metric_comparison_chart(df_tweets, 'Views', '#ff9800')
            if fig_views:
                st.plotly_chart(fig_views, use_container_width=True)
                total_views = df_tweets['views'].sum()
                avg_views = df_tweets['views'].mean()
                best_post_views = df_tweets['views'].max()
                st.markdown(f"""
                <div style="background: #fff3e0; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ff9800; margin-top: 0.5rem;">
                    <p style="margin: 0; color: #e65100; font-size: 0.85rem;">
                        👁️ <strong>{total_views:,} total views</strong> | Avg: {avg_views:.0f} per post | Best: {best_post_views:,}<br>
                        Your content reaches {"a massive audience! 🚀" if avg_views > 10000 else "an engaged audience! 📈"}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("📊 Chart requires date information to display")
        else:
            st.info("📊 Views data not available in dataset")
    
    if df_comments is not None and not df_comments.empty:
        st.markdown("**💭 Posts vs Comments Received**")
        
        df_comments_analysis = df_comments.copy()
        df_tweets_with_date = df_tweets[['tweet_id', 'date']].copy()
        df_comments_analysis = df_comments_analysis.merge(
            df_tweets_with_date, 
            left_on='original_tweet_id', 
            right_on='tweet_id',
            how='left'
        )
        
        if 'date' in df_comments_analysis.columns and not df_comments_analysis['date'].isna().all():
            daily_comments = df_comments_analysis.groupby('date').size().reset_index(name='comments')
            daily_posts = df_tweets.groupby('date').size().reset_index(name='posts')
            
            merged = daily_posts.merge(daily_comments, on='date', how='left').fillna(0)
            
            fig_comments = go.Figure()
            fig_comments.add_trace(go.Scatter(
                x=merged['date'], 
                y=merged['posts'],
                name='Number of Posts',
                line=dict(color='#333333', width=2.5),
                mode='lines+markers',
                yaxis='y'
            ))
            fig_comments.add_trace(go.Scatter(
                x=merged['date'], 
                y=merged['comments'],
                name='Comments',
                line=dict(color='#9c27b0', width=2.5),
                mode='lines+markers',
                yaxis='y2'
            ))
            
            fig_comments.update_layout(
                title="",
                xaxis_title="",
                height=320,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter", color='#666'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(
                    title=dict(text="Posts", font=dict(color="#333333")),
                    tickfont=dict(color="#333333"),
                    showgrid=True,
                    gridcolor='#f0f0f0'
                ),
                yaxis2=dict(
                    title=dict(text="Comments", font=dict(color="#9c27b0")),
                    tickfont=dict(color="#9c27b0"),
                    overlaying="y",
                    side="right",
                    showgrid=False
                )
            )
            fig_comments.update_xaxes(showgrid=False, showline=False)
            st.plotly_chart(fig_comments, use_container_width=True)
            
            total_comments = len(df_comments)
            posts_with_comments = df_comments['original_tweet_id'].nunique()
            avg_comments_per_post = total_comments / posts_with_comments if posts_with_comments > 0 else 0
            st.markdown(f"""
            <div style="background: #f3e5f5; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #9c27b0; margin-top: 0.5rem;">
                <p style="margin: 0; color: #6a1b9a; font-size: 0.85rem;">
                    💭 <strong>{total_comments:,} comments received</strong> across {posts_with_comments} posts<br>
                    Average: {avg_comments_per_post:.1f} comments per engaged post. {"🔥 Your content sparks great discussions!" if avg_comments_per_post > 3 else "💡 Engage with your audience to boost comments!"}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 Chart requires date information to display")
    
    st.markdown('<div class="section-header">Optimal Posting Times</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Best Hours to Post**")
        fig = create_bar_chart(df_tweets, 'hour', 'Best Hours')
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            if 'hour' in df_tweets.columns and df_tweets['hour'].notna().any():
                hourly_engagement = df_tweets.groupby('hour')['total_engagement'].mean()
                best_hour = hourly_engagement.idxmax()
                worst_hour = hourly_engagement.idxmin()
                best_engagement = hourly_engagement.max()
                worst_engagement = hourly_engagement.min()
                improvement = ((best_engagement - worst_engagement) / worst_engagement * 100) if worst_engagement > 0 else 0
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #ff9800; margin-top: 0.5rem;">
                    <p style="margin: 0; color: #e65100; font-size: 0.85rem; line-height: 1.6;">
                        🎯 <strong>Peak hour: {best_hour}:00</strong> (Avg: {best_engagement:.0f} engagements)<br>
                        📉 Lowest: {worst_hour}:00 (Avg: {worst_engagement:.0f} engagements)<br>
                        💡 Posting at {best_hour}:00 gets {improvement:.0f}% more engagement!
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📊 Hours chart requires time information to display")
    
    with col2:
        st.markdown("**Best Days to Post**")
        fig = create_bar_chart(df_tweets, 'day_of_week', 'Best Days')
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            if 'day_of_week' in df_tweets.columns and df_tweets['day_of_week'].notna().any():
                daily_engagement = df_tweets.groupby('day_of_week')['total_engagement'].mean()
                best_day = daily_engagement.idxmax()
                worst_day = daily_engagement.idxmin()
                best_engagement = daily_engagement.max()
                worst_engagement = daily_engagement.min()
                improvement = ((best_engagement - worst_engagement) / worst_engagement * 100) if worst_engagement > 0 else 0
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #4caf50; margin-top: 0.5rem;">
                    <p style="margin: 0; color: #2e7d32; font-size: 0.85rem; line-height: 1.6;">
                        🎯 <strong>Peak day: {best_day}</strong> (Avg: {best_engagement:.0f} engagements)<br>
                        📉 Lowest: {worst_day} (Avg: {worst_engagement:.0f} engagements)<br>
                        💡 {best_day} performs {improvement:.0f}% better than {worst_day}!
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📊 Days chart requires date information to display")
    
    # Export Section
    st.markdown('<div class="section-header">Export Data</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Download Excel Report", type="primary", use_container_width=True):
            df_profile_data = data.get('profile')
            df_tweets_data = data.get('tweets')
            df_comments_data = data.get('comments')
            
            if not df_tweets_data.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_profile_data.to_excel(writer, sheet_name='Profile', index=False)
                    prepare_dataframe_for_excel(df_tweets_data).to_excel(writer, sheet_name='Posts', index=False)
                    if df_comments_data is not None and not df_comments_data.empty:
                        prepare_dataframe_for_excel(df_comments_data).to_excel(writer, sheet_name='Comments', index=False)
                
                excel_data = output.getvalue()
                filename = f"X_Analytics_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                st.download_button(
                    label="💾 Download Now",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col2:
        if st.button("🔗 Download Network File", type="secondary", use_container_width=True):
            df_tweets_data = data.get('tweets')
            df_comments_data = data.get('comments')
            
            if not df_tweets_data.empty:
                with st.spinner("Generating network data..."):
                    # Generate network data
                    network_connections = []
                    network_elements = []
                    
                    # Add main user to elements
                    network_elements.append({
                        'Label': username,
                        'Screen_name': df_profile.iloc[0]['Name'] if df_profile is not None and not df_profile.empty else username,
                        'Description': df_profile.iloc[0]['Bio'][:200] + "..." if df_profile is not None and not df_profile.empty and df_profile.iloc[0]['Bio'] else 'Main user',
                        'followers': df_profile.iloc[0]['Followers Count'] if df_profile is not None and not df_profile.empty else 0,
                        'following': df_profile.iloc[0]['Following Count'] if df_profile is not None and not df_profile.empty else 0,
                        'tweets': len(df_tweets_data),
                        'Location': df_profile.iloc[0]['Location'] if df_profile is not None and not df_profile.empty else '',
                        'Image': df_profile.iloc[0]['Image URL (High Res)'] if df_profile is not None and not df_profile.empty else '',
                        'verified': df_profile.iloc[0]['Verified'] if df_profile is not None and not df_profile.empty else False,
                        'type': 'primary_user'
                    })
                    
                    # Keep track of unique users to avoid duplicates
                    unique_users = {}
                    
                    # Extract mentions from tweets
                    for _, tweet in df_tweets_data.iterrows():
                        if 'mentions' in tweet and tweet['mentions']:
                            mentions = [m.strip() for m in str(tweet['mentions']).split(',') if m.strip()]
                            for mention in mentions:
                                if mention.lower() != username.lower():
                                    # Add connection
                                    network_connections.append({
                                        'From': username,
                                        'To': mention,
                                        'Type': 'mention',
                                        'Description': tweet['text'][:100] + "..." if len(tweet['text']) > 100 else tweet['text'],
                                        'tweet_id': tweet['tweet_id'],
                                        'timestamp': tweet['created_at'],
                                        'weight': 1
                                    })
                                    
                                    # Track unique user
                                    if mention.lower() not in unique_users:
                                        unique_users[mention.lower()] = {
                                            'username': mention,
                                            'type': 'mentioned_user',
                                            'description': 'Mentioned user - limited data'
                                        }
                        
                        # Add reply connections
                        if 'replying_to_username' in tweet and tweet['replying_to_username']:
                            replied_user = tweet['replying_to_username']
                            network_connections.append({
                                'From': username,
                                'To': replied_user,
                                'Type': 'reply',
                                'Description': tweet['text'][:100] + "..." if len(tweet['text']) > 100 else tweet['text'],
                                'tweet_id': tweet['tweet_id'],
                                'timestamp': tweet['created_at'],
                                'weight': 1
                            })
                            
                            # Track unique user
                            if replied_user.lower() not in unique_users:
                                unique_users[replied_user.lower()] = {
                                    'username': replied_user,
                                    'type': 'replied_user',
                                    'description': 'Replied to user - limited data'
                                }
                    
                    # Add comment connections and commenters
                    if df_comments_data is not None and not df_comments_data.empty:
                        for _, comment in df_comments_data.iterrows():
                            commenter = comment['commenter_username']
                            if commenter.lower() != username.lower():
                                # Add connection from commenter to main user
                                network_connections.append({
                                    'From': commenter,
                                    'To': username,
                                    'Type': 'comment',
                                    'Description': comment['comment_text'][:100] + "..." if len(comment['comment_text']) > 100 else comment['comment_text'],
                                    'tweet_id': comment['comment_id'],
                                    'timestamp': comment['comment_date'],
                                    'weight': 1
                                })
                                
                                # Track unique user (commenters have more data available)
                                if commenter.lower() not in unique_users:
                                    unique_users[commenter.lower()] = {
                                        'username': commenter,
                                        'name': comment['commenter_name'],
                                        'type': 'commenter',
                                        'description': f"Commenter - {comment['comment_text'][:100]}..." if len(comment['comment_text']) > 100 else f"Commenter - {comment['comment_text']}",
                                        'verified': comment.get('commenter_verified', False),
                                        'image_url': comment.get('commenter_image_url_high_res', ''),
                                        'followers': comment.get('commenter_followers', 0),
                                        'following': comment.get('commenter_following', 0),
                                        'bio': comment.get('commenter_bio', ''),
                                        'location': comment.get('commenter_location', ''),
                                        'tweet_count': comment.get('commenter_tweet_count', 0)
                                    }
                    
                    # Create network elements from unique users
                    for user_key, user_data in unique_users.items():
                        network_elements.append({
                            'Label': user_data['username'],
                            'Screen_name': user_data.get('name', user_data['username']),
                            'Description': user_data.get('bio', user_data.get('description', ''))[:200] + "..." if user_data.get('bio', user_data.get('description', '')) else user_data.get('description', 'Limited data'),
                            'followers': user_data.get('followers', 0),
                            'following': user_data.get('following', 0),
                            'tweets': user_data.get('tweet_count', 0),
                            'Location': user_data.get('location', ''),
                            'Image': user_data.get('image_url', ''),
                            'verified': user_data.get('verified', False),
                            'type': user_data['type']
                        })
                    
                    # Create network DataFrames
                    df_connections = pd.DataFrame(network_connections)
                    df_elements = pd.DataFrame(network_elements)
                    
                    # Create Excel file for network data
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_connections.to_excel(writer, sheet_name='Connections', index=False)
                        df_elements.to_excel(writer, sheet_name='Elements', index=False)
                    
                    network_data = output.getvalue()
                    network_filename = f"X_Network_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    
                    st.download_button(
                        label="🔗 Download Now",
                        data=network_data,
                        file_name=network_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Show network statistics
                    st.success(f"📊 Network contains {len(df_connections)} connections and {len(df_elements)} users • Ready for Gephi, Kumu, or other network analysis tools")

# ============================================================
# MAIN - COMPLETE
# ============================================================
def main():
    try:
        # Custom CSS for Start Extraction button
        st.markdown("""
        <style>
        [data-testid="column"]:nth-child(2) button {
            background: linear-gradient(135deg, #667eea 0%, #564ba2 100%) !important;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
        }
        [data-testid="column"]:nth-child(2) button:hover {
            box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header Section
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            logo_col, title_col = st.columns([0.3, 2.7])
            with logo_col:
                st.image("https://t4.ftcdn.net/jpg/06/96/89/13/360_F_696891328_utj80ZwXsdy8SloC9IBaFGDIcGNBrEze.jpg", width=100)
            with title_col:
                st.markdown("<h3 style='margin: 0 0 1rem 0; padding: 0;'>X Analytics Suite</h3>", unsafe_allow_html=True)
        with col2:
            if st.button("Start Extraction", type="primary", use_container_width=True, key="main_extraction_btn"):
                show_extraction_modal()
        with col3:
            if st.button("Reset App", type="secondary", use_container_width=True, key="reset_app_btn"):
                st.session_state.clear()
                st.rerun()

        # Configuration Status Banner
        if not GEMINI_KEYS:
            st.warning("""
            ⚠️ **إعداد Gemini API مطلوب / Gemini API Setup Required**

            للحصول على أفضل أداء مع معدلات مجانية أعلى:
            1. احصل على مفاتيح API مجانية من: https://makersuite.google.com/app/apikey
            2. أضف المفاتيح في ملف `.env` أو مباشرة في `Twitter-Profile-app.py` (السطر 550)
            3. راجع دليل الإعداد: `GEMINI_SETUP_GUIDE.md`

            حالياً: استخدام Mistral AI كبديل
            """)
        elif GEMINI_AVAILABLE and len(GEMINI_KEYS) > 0:
            with st.expander("✅ تم تكوين Gemini API - انقر لعرض التفاصيل", expanded=False):
                st.success(f"""
                **محلل AI النشط:** Google Gemini 1.5 Flash
                **عدد المفاتيح:** {len(GEMINI_KEYS)}
                **معدل الطلبات:** {len(GEMINI_KEYS) * 15} طلب/دقيقة ({len(GEMINI_KEYS) * 1500} طلب/يوم)
                **النموذج:** {GEMINI_MODEL}
                """)

        # Main Tabs - 3 tabs on the same level
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 Detailed Report", "📋 AI Summary"])
        
        # ============================================================
        # TAB 1: DASHBOARD
        # ============================================================
        with tab1:
            dashboard_page()
        
        # ============================================================
        # TAB 2: DETAILED REPORT
        # ============================================================
        with tab2:
            if not st.session_state.data_loaded or 'extracted_data' not in st.session_state:
                st.info("📊 Please extract data first from the Dashboard section")
                if st.button("Extract Data", type="primary", key="extract_detailed"):
                    show_extraction_modal()
            else:
                data = st.session_state['extracted_data']
                username = data.get('username', 'User')
                
                # Generate Detailed Report
                ai_detailed_report_page()
                
                # Download Buttons for Detailed Report
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Check if report has been generated
                sections_list = [
                    ("introduction", "المقدمة"),
                    ("news_sources", "المصادر الإخبارية المعتمدة"),
                    ("network", "الشبكة الاجتماعية والتفاعلات"),
                    ("main_topics", "القضايا والموضوعات الرئيسية"),
                    ("uae_content", "المحتوى المتعلق بدولة الإمارات"),
                    ("influence", "التأثير على وسائل التواصل"),
                    ("political", "التوجهات السياسية العامة"),
                    ("mb_links", "الارتباطات بجماعة الإخوان"),
                    ("electronic_army", "الجيوش الإلكترونية والحملات المنظمة"),
                    ("comments_content", "تحليل التعليقات والنقاشات"),
                ]
                
                # Check if at least one section exists
                has_report = any(section_key in st.session_state.ai_report_cache for section_key, _ in sections_list)
                
                if has_report:
                    # Check if PDF libraries are available
                    pdf_available = True
                    try:
                        import reportlab
                        import arabic_reshaper
                        import bidi
                    except ImportError:
                        pdf_available = False
                    
                    if pdf_available:
                        col1, col2, col3 = st.columns([1, 1, 1])
                    else:
                        col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Text download
                        detailed_report = f"""
تقرير التحليل التفصيلي مع روابط الإثبات - حساب تويتر
الحساب: @{username}
تاريخ التحليل: {datetime.now().strftime('%d %B %Y - %H:%M')}
حجم العينة: {len(data.get('tweets')):,} تغريدة | {len(data.get('comments')) if data.get('comments') is not None else 0:,} تعليق

"""
                        for section_key, section_title in sections_list:
                            if section_key in st.session_state.ai_report_cache:
                                detailed_report += f"\n\n{'='*60}\n{section_title}\n{'='*60}\n\n{st.session_state.ai_report_cache[section_key]}"
                        
                        detailed_report += f"""

{'='*60}
معرف التقرير: DETAILED-ANALYSIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}
تاريخ الإصدار: {datetime.now().strftime('%d %B %Y - %H:%M:%S')}
نوع التقرير: تقرير تحليل تفصيلي مع روابط الإثبات
{'='*60}
"""
                        
                        filename_txt = f"Detailed_Report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        st.download_button(
                            label="📄 Download TXT",
                            data=detailed_report.encode('utf-8'),
                            file_name=filename_txt,
                            mime="text/plain",
                            use_container_width=True,
                            type="secondary"
                        )
                    
                    if pdf_available:
                        with col2:
                            # PDF download with better error handling
                            if st.button("📑 Generate PDF", use_container_width=True, type="primary"):
                                with st.spinner("Generating PDF..."):
                                    try:
                                        pdf_data = generate_pdf_report(username, sections_list, data)
                                        filename_pdf = f"Detailed_Report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                        st.download_button(
                                            label="⬇️ Download PDF",
                                            data=pdf_data,
                                            file_name=filename_pdf,
                                            mime="application/pdf",
                                            use_container_width=True,
                                            key="pdf_download_btn"
                                        )
                                    except Exception as e:
                                        st.error(f"⚠️ Error generating PDF: {str(e)[:100]}")
                                        st.info("💡 Please use TXT download instead.")
                        
                        with col3:
                            st.markdown("""
                            <div style="
                                padding: 12px;
                                background: #f0f9ff;
                                border-radius: 8px;
                                text-align: center;
                                font-size: 0.9rem;
                                color: #0369a1;
                            ">
                                ✨ Report Ready
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        with col2:
                            st.info("📄 TXT format available. PDF export requires additional libraries.")
                else:
                    st.info("ℹ️ Generate the report above first, then you can download it here.")
        
        # ============================================================
        # TAB 3: AI SUMMARY
        # ============================================================
        with tab3:
            if not st.session_state.data_loaded or 'extracted_data' not in st.session_state:
                st.info("📊 Please extract data first from the Dashboard section")
                if st.button("Extract Data", type="primary", key="extract_summary"):
                    show_extraction_modal()
            else:
                data = st.session_state['extracted_data']
                username = data.get('username', 'User')
                
                # Header for AI Summary
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #00cc88 0%, #00aa70 100%); padding: 1.5rem; border-radius: 16px; margin-bottom: 2rem;">
                    <h2 style="color: white; margin: 0; font-size: 1.5rem;">📋 AI Report Summary</h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                        Comprehensive executive summary of all detailed analysis results for @{username}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate Summary Report
                ai_summary_report_page()
                
                # Download Button for Summary
                if "summary_conclusion" in st.session_state.ai_report_cache:
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        summary_report = f"""
AI Report Summary - Twitter Account
Account: @{username}
Analysis Date: {datetime.now().strftime('%d %B %Y - %H:%M')}
Sample Size: {len(data.get('tweets')):,} tweets | {len(data.get('comments')) if data.get('comments') is not None else 0:,} comments

{'='*60}
Executive Summary
{'='*60}

{st.session_state.ai_report_cache.get('summary_conclusion', '')}

{'='*60}
Report ID: SUMMARY-ANALYSIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}
Issue Date: {datetime.now().strftime('%d %B %Y - %H:%M:%S')}
Report Type: AI Executive Summary
{'='*60}
"""
                        
                        filename = f"Summary_Report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        st.download_button(
                            label="💾 Download AI Summary",
                            data=summary_report.encode('utf-8'),
                            file_name=filename,
                            mime="text/plain",
                            use_container_width=True,
                            type="primary"
                        )
                else:
                    st.info("ℹ️ Generate the summary above first, then you can download it here.")
            
    except Exception as e:
        st.error("An error occurred")
        st.exception(e)
        if st.button("Restart Application"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
