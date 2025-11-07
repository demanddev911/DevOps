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

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Reputation Agent",
    page_icon="🎯",
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
# CUSTOM CSS - MUHIMMA DESIGN (OPTIMIZED)
# ============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    /* ============================================================
       BASE STYLES
    ============================================================ */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .main {
        background: #f5f7fa;
        padding: 1.5rem;
        min-height: 100vh;
    }
    
    .block-container {
        max-width: 1500px;
        padding: 2.5rem 3rem;
        background: white;
        border-radius: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 0 auto;
    }
    
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Arabic text support */
    .arabic-text {
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    /* ============================================================
       TABS STYLING - MODERN TOP TABS
    ============================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8f9fa;
        padding: 10px 14px;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        background: white;
        border-radius: 12px;
        color: #666;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0 2rem;
        border: 2px solid #e0e0e0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #E3F2FD;
        border-color: #1976D2;
        color: #1976D2;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: #1976D2 !important;
        color: white !important;
        border-color: #1976D2 !important;
        box-shadow: 0 6px 20px rgba(25, 118, 210, 0.35) !important;
        font-weight: 700;
        transform: translateY(-1px);
    }
    
    /* ============================================================
       METRICS
    ============================================================ */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border-radius: 20px;
        padding: 2.25rem 2rem;
        border: 2px solid #f0f0f0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
        background: linear-gradient(90deg, #1976D2 0%, #1565C0 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
        border-color: #1976D2;
    }
    
    div[data-testid="metric-container"]:hover::before {
        opacity: 1;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.4rem;
        font-weight: 900;
        color: #1976D2;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #888;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* ============================================================
       SECTION HEADERS
    ============================================================ */
    .section-header {
        font-size: 1.4rem;
        font-weight: 800;
        color: #212121;
        margin: 3rem 0 1.75rem 0;
        padding-bottom: 1.25rem;
        border-bottom: 3px solid #1976D2;
        position: relative;
    }
    
    .section-header::before {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 80px;
        height: 3px;
        background: linear-gradient(90deg, #1976D2 0%, #1565C0 100%);
    }
    
    /* ============================================================
       BUTTONS - 3-COLOR SYSTEM (NO SHADOWS)
    ============================================================ */
    /* Default Buttons - Green */
    .stButton button {
        background: #00cc88;
        color: white;
        border: none !important;
        padding: 0.85rem 2rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: none !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.03em;
        cursor: pointer;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: none !important;
        background: #00b377;
        border: none !important;
    }
    
    .stButton button:active {
        transform: translateY(0px);
    }
    
    /* Primary Buttons - Blue */
    .stButton button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: #1976d2 !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    .stButton button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: #1565c0 !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    /* Secondary Buttons - Red */
    .stButton button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background: #ff6b6b !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    .stButton button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background: #e85555 !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    /* Button container spacing */
    .stButton {
        margin-bottom: 0.5rem;
        margin-top: 0;
    }
    
    /* ============================================================
       INFO BOXES
    ============================================================ */
    .info-box,
    .success-box,
    .warning-box,
    .error-box {
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin: 1.75rem 0;
        font-size: 0.95rem;
        line-height: 1.7;
        transition: all 0.3s ease;
    }
    
    .info-box {
        background: #e3f2fd;
        border-left: 5px solid #2196f3;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.15);
    }
    
    .info-box:hover {
        box-shadow: 0 6px 18px rgba(33, 150, 243, 0.25);
        transform: translateX(2px);
    }
    
    .success-box {
        background: #e8f5e9;
        border-left: 5px solid #4caf50;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
    }
    
    .success-box:hover {
        box-shadow: 0 6px 18px rgba(76, 175, 80, 0.25);
        transform: translateX(2px);
    }
    
    .warning-box {
        background: #fff3e0;
        border-left: 5px solid #ff9800;
        box-shadow: 0 4px 12px rgba(255, 152, 0, 0.15);
    }
    
    .warning-box:hover {
        box-shadow: 0 6px 18px rgba(255, 152, 0, 0.25);
        transform: translateX(2px);
    }
    
    .error-box {
        background: #ffebee;
        border-left: 5px solid #f44336;
        box-shadow: 0 4px 12px rgba(244, 67, 54, 0.15);
    }
    
    .error-box:hover {
        box-shadow: 0 6px 18px rgba(244, 67, 54, 0.25);
        transform: translateX(2px);
    }
    
    /* ============================================================
       ACCORDION REPORT SECTIONS - COLLAPSIBLE DESIGN
    ============================================================ */
    .accordion-card {
        background: white;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
        overflow: hidden;
        border: 1px solid #E5E7EB;
    }
    
    .accordion-card:hover {
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
        border-color: #D1D5DB;
    }
    
    .accordion-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        cursor: pointer;
        background: #F9FAFB;
        transition: all 0.2s ease;
        direction: rtl;
    }
    
    .accordion-header:hover {
        background: #F3F4F6;
    }
    
    .accordion-header-content {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex: 1;
    }
    
    .accordion-icon {
        width: 8px;
        height: 8px;
        background: #9CA3AF;
        border-radius: 50%;
        flex-shrink: 0;
    }
    
    .accordion-title-group {
        flex: 1;
    }
    
    .accordion-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1F2937;
        margin: 0;
        font-family: 'Cairo', sans-serif;
    }
    
    .accordion-subtitle {
        font-size: 0.8rem;
        color: #6B7280;
        margin: 0.25rem 0 0 0;
        font-style: normal;
        font-weight: 500;
    }
    
    .accordion-arrow {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease;
        font-size: 1.1rem;
        color: #6B7280;
    }
    
    .accordion-arrow.expanded {
        transform: rotate(180deg);
    }
    
    .accordion-body {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        direction: rtl;
        text-align: right;
    }
    
    .accordion-body.expanded {
        max-height: 5000px;
    }
    
    .accordion-content {
        padding: 1.75rem;
        direction: rtl;
        text-align: right;
        background: #FAFBFC;
    }
    
    .accordion-content p,
    .accordion-content div,
    .accordion-content ul,
    .accordion-content li {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }
    
    .selected-answer-box {
        background: #FAFBFC;
        border-radius: 8px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        border: 1px solid #E1E4E8;
        border-right: 3px solid #4CAF50;
        direction: rtl;
        text-align: right;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .selected-answer-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #6B7280;
        margin-bottom: 0.75rem;
        font-family: 'Cairo', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        direction: rtl;
        text-align: right;
    }
    
    .selected-answer-text {
        font-size: 1rem;
        font-weight: 500;
        color: #1F2937;
        font-family: 'Cairo', sans-serif;
        line-height: 1.8;
        direction: rtl;
        text-align: right;
    }
    
    .selected-answer-text p,
    .selected-answer-text div {
        direction: rtl;
        text-align: right;
        line-height: 1.8;
    }
    
    .reasoning-box {
        background: #FFFFFF;
        border-radius: 8px;
        padding: 1.75rem;
        border: 1px solid #E5E7EB;
        direction: rtl;
        text-align: right;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    
    .reasoning-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #6B7280;
        margin-bottom: 1.25rem;
        font-family: 'Cairo', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        direction: rtl;
        text-align: right;
        border-bottom: 1px solid #F3F4F6;
        padding-bottom: 0.75rem;
    }
    
    .reasoning-content {
        font-size: 0.95rem;
        line-height: 1.9;
        color: #374151;
        font-family: 'Cairo', 'Inter', sans-serif;
        text-align: right;
        direction: rtl;
    }
    
    .reasoning-content a {
        color: #1565C0;
        text-decoration: none;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 6px;
        background: #F8F9FA;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin: 3px 6px;
        border: 1px solid #DEE2E6;
        font-size: 0.875rem;
        direction: ltr;
        white-space: nowrap;
        vertical-align: middle;
    }
    
    .reasoning-content a:hover {
        color: #1565C0;
        background: #E8F4F8;
        border-color: #1565C0;
        text-decoration: none;
    }
    
    .reasoning-content a::before {
        content: '🔗';
        font-size: 0.9rem;
        opacity: 0.7;
    }
    
    /* Evidence Link Styling - Professional & Clean */
    .evidence-link {
        color: #1565C0 !important;
        text-decoration: none !important;
        font-weight: 600 !important;
        padding: 6px 14px !important;
        border-radius: 6px !important;
        background: #F8F9FA !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        margin: 3px 6px !important;
        border: 1px solid #DEE2E6 !important;
        font-size: 0.875rem !important;
        font-family: 'Inter', 'Cairo', sans-serif !important;
        direction: ltr !important;
        white-space: nowrap !important;
        vertical-align: middle !important;
    }
    
    .evidence-link::before {
        content: '🔗' !important;
        font-size: 0.9rem !important;
        opacity: 0.7 !important;
    }
    
    .evidence-link:hover {
        color: #1565C0 !important;
        background: #E8F4F8 !important;
        border-color: #1565C0 !important;
        text-decoration: none !important;
    }
    
    .evidence-link:active {
        background: #D1E7F0 !important;
    }
    
    /* Evidence links in lists */
    .reasoning-content ul li,
    .reasoning-content ol li {
        margin: 10px 0;
        line-height: 2;
        padding-right: 8px;
    }
    
    /* Ensure proper spacing around evidence links */
    .reasoning-content br + a.evidence-link,
    .reasoning-content p + a.evidence-link {
        display: inline-flex !important;
        margin-top: 4px !important;
    }
    
    /* Better paragraph spacing with Arabic text */
    .reasoning-content p {
        margin-bottom: 1rem;
        line-height: 1.9;
        direction: rtl;
        text-align: right;
    }
    
    /* Headlines and emphasis in Arabic */
    .reasoning-content strong,
    .reasoning-content b {
        color: #212121;
        font-weight: 700;
        direction: rtl;
    }
    
    .reasoning-content h1,
    .reasoning-content h2,
    .reasoning-content h3,
    .reasoning-content h4 {
        direction: rtl;
        text-align: right;
        margin: 1.5rem 0 0.8rem 0;
        color: #212121;
        font-family: 'Cairo', sans-serif;
        font-weight: 700;
    }
    
    /* Clean list styling */
    .reasoning-content ul {
        list-style-position: inside;
        padding-right: 0;
        direction: rtl;
    }
    
    .reasoning-content ol {
        list-style-position: inside;
        padding-right: 0;
        direction: rtl;
    }
    
    /* Hierarchical Typography */
    .reasoning-content h1 {
        font-size: 1.5rem;
        font-weight: 800;
        color: #111827;
        margin: 1.75rem 0 0.75rem 0;
        line-height: 1.3;
        font-family: 'Cairo', sans-serif;
    }
    
    .reasoning-content h2 {
        font-size: 1.15rem;
        font-weight: 700;
        color: #374151;
        margin: 1.25rem 0 0.5rem 0;
        line-height: 1.4;
        font-family: 'Cairo', sans-serif;
    }
    
    .reasoning-content h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #4B5563;
        margin: 1rem 0 0.4rem 0;
        font-family: 'Cairo', sans-serif;
    }
    
    /* ============================================================
       FILE UPLOADER
    ============================================================ */
    [data-testid="stFileUploader"] {
        background: #FAFAFA;
        border: 3px dashed #1976D2;
        border-radius: 20px;
        padding: 2.5rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        background: #E3F2FD;
        border-color: #1565C0;
    }
    
    /* ============================================================
       RADIO BUTTONS
    ============================================================ */
    .stRadio > div {
        background: white;
        padding: 1.25rem;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border: 2px solid #f0f0f0;
    }
    
    /* ============================================================
       PROGRESS BAR
    ============================================================ */
    .stProgress > div > div {
        background: linear-gradient(90deg, #1976D2 0%, #1565C0 100%);
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
    }
    
    /* ============================================================
       SCROLLBAR
    ============================================================ */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f3f5;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #1976D2 0%, #1565C0 100%);
        border-radius: 10px;
        border: 2px solid #f1f3f5;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #1565C0 0%, #1976D2 100%);
    }
    
    /* ============================================================
       RESPONSIVE DESIGN
    ============================================================ */
    @media (max-width: 768px) {
        .block-container {
            padding: 1.5rem 1.25rem;
        }
        
        .section-header {
            font-size: 1.2rem;
            margin: 2rem 0 1rem 0;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
        }
        
        .report-section {
            padding: 1.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0 1rem;
            font-size: 0.8rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# API CONFIGURATION
# ============================================================
# Twitter API Configuration
API_KEY = "ac0025f410mshd0c260cb60f3db6p18c4b0jsnc9b7413cd574"
API_HOST = "twitter241.p.rapidapi.com"
MAX_COMMENT_WORKERS = 15
CONNECTION_TIMEOUT = 15

# Google Gemini AI Configuration
GEMINI_API_KEY = "AIzaSyBIYTpbNSeo4mOHevMmXvpex4U7-IMP0TI"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 4000

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
# GEMINI AI ANALYZER
# ============================================================
class GeminiAnalyzer:
    """Google Gemini AI Analyzer with enhanced error handling and retry logic"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        self.session = self._create_session()
        self.request_count = 0
        self.success_count = 0
        
    def _create_session(self) -> requests.Session:
        """Create session with connection pooling and retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def analyze(self, prompt: str, max_tokens: int = GEMINI_MAX_TOKENS) -> Optional[str]:
        """Analyze prompt with Gemini AI with optimized error handling"""
        self.request_count += 1
        url = f"{GEMINI_API_URL}?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": GEMINI_TEMPERATURE,
                "maxOutputTokens": max_tokens
            }
        }
        
        for attempt in range(3):
            try:
                response = self.session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    self.success_count += 1
                    return text
                    
                elif response.status_code == 429:
                    # Rate limit - exponential backoff
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < 2:
                        time.sleep(2 * (attempt + 1))
                    continue
                    
                elif response.status_code == 400:
                    # Bad request - log and return None
                    return None
                    
                else:
                    # Other errors
                    return None
                    
            except requests.exceptions.Timeout:
                # Timeout - retry with longer wait
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                continue
                
            except requests.exceptions.RequestException as e:
                # Network errors - retry
                if attempt < 2:
                    time.sleep(2)
                continue
                
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                # JSON parsing errors - return None
                return None
                
            except Exception as e:
                # Unexpected errors - log and retry
                if attempt < 2:
                    time.sleep(2)
                continue
                    
        return None
    
    def get_stats(self) -> Dict:
        """Get analyzer statistics"""
        return {
            'total_requests': self.request_count,
            'successful_requests': self.success_count,
            'success_rate': (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        }

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
    """
    Create engagement timeline chart with optimized data processing
    
    Args:
        df: DataFrame with date and engagement columns
        
    Returns:
        Plotly figure or None if data is invalid
    """
    try:
        # Validate input data
        if df is None or df.empty:
            return None
        if 'date' not in df.columns or df['date'].isna().all():
            return None
        
        # Check required columns exist
        required_cols = ['likes', 'retweets', 'replies']
        if not all(col in df.columns for col in required_cols):
            return None

        # Optimized aggregation with error handling
        daily_stats = df.groupby('date', as_index=False).agg({
            'likes': 'sum',
            'retweets': 'sum',
            'replies': 'sum'
        })
        
        # Calculate total engagement
        daily_stats['total_engagement'] = daily_stats[required_cols].sum(axis=1)
        daily_stats = daily_stats.dropna()

        if daily_stats.empty or len(daily_stats) < 1:
            return None

        # Create figure with Muhimma purple theme
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['total_engagement'],
            name='Total Engagement',
            line=dict(color='#1976D2', width=3),
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(25, 118, 210, 0.1)',
            marker=dict(size=6, color='#1976D2')
        ))
        
        # Update layout with Muhimma styling
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
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        fig.update_xaxes(showgrid=False, showline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', showline=False)
        
        return fig
        
    except (KeyError, ValueError, TypeError) as e:
        return None
    except Exception as e:
        return None

def create_metric_comparison_chart(df, metric_name, metric_color='#1976D2'):
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
    # Brand Header with Logo
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 1rem; margin: 0 0 1.5rem 0; padding: 1.5rem; background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); border-radius: 16px;'>
        <div style='font-size: 2.5rem; line-height: 1;'>🎯</div>
        <div>
            <h2 style='margin: 0; padding: 0; font-size: 1.4rem; font-weight: 800; color: white;'>Reputation Agent</h2>
            <p style='margin: 0; padding: 0; font-size: 0.85rem; color: rgba(255,255,255,0.9); font-weight: 500;'>AI-Powered Social Media Analytics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
def generate_ai_section(gemini: GeminiAnalyzer, section_name: str, prompt: str, max_tokens: int = 2000) -> str:
    """
    Generate AI section with caching and error handling
    
    Args:
        gemini: GeminiAnalyzer instance
        section_name: Unique section identifier for caching
        prompt: AI prompt text
        max_tokens: Maximum tokens for response
        
    Returns:
        Generated text or error message
    """
    # Check cache first
    if section_name in st.session_state.ai_report_cache:
        return st.session_state.ai_report_cache[section_name]
    
    # Generate new content
    result = gemini.analyze(prompt, max_tokens)
    
    if result and result.strip():
        # Keep markdown formatting for proper hierarchy
        cleaned_result = result.strip()
        
        # Cache the result
        st.session_state.ai_report_cache[section_name] = cleaned_result
        return cleaned_result
    else:
        # Return error message
        error_msg = f"⚠️ تعذر إنشاء القسم {section_name}. يرجى المحاولة مرة أخرى."
        return error_msg

def display_report_section(title: str, content: str, section_id: str):
    """
    Display collapsible accordion report section with clickable hyperlinks using st.expander
    
    Args:
        title: Section title (Arabic)
        content: Section content with embedded URLs
        section_id: Unique identifier for the accordion section
    """
    import re
    
    # Convert markdown to HTML
    def convert_markdown_to_html(text):
        # Convert headers first
        text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        
        # Convert bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Process line by line for better control
        lines = text.split('\n')
        processed_lines = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append('')
            elif line.startswith('<h'):
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(line)
            elif stripped.startswith('- '):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                processed_lines.append(f'<li>{stripped[2:]}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                if not line.startswith('<'):
                    processed_lines.append(f'<p>{line}</p>')
                else:
                    processed_lines.append(line)
        
        if in_list:
            processed_lines.append('</ul>')
        
        return '\n'.join(processed_lines)
    
    # Convert evidence links to clickable hyperlinks with professional styling
    def make_link_clickable(match):
        url = match.group(1).strip()
        if not url.startswith('http'):
            return match.group(0)
        return f'<a href="{url}" target="_blank" class="evidence-link">المصدر</a>'
    
    def make_proof_link_clickable(match):
        url = match.group(1).strip()
        if not url.startswith('http'):
            return match.group(0)
        # Extract tweet ID if it's a Twitter link
        tweet_id = ''
        if 'twitter.com' in url or 'x.com' in url:
            parts = url.split('/')
            if 'status' in parts:
                idx = parts.index('status')
                if idx + 1 < len(parts):
                    tweet_id = parts[idx + 1].split('?')[0]
                    # Keep only last 6 digits for cleaner look
                    if len(tweet_id) > 6:
                        tweet_id = '...' + tweet_id[-6:]
        
        display_text = f'المصدر' if not tweet_id else f'تغريدة'
        return f'<a href="{url}" target="_blank" class="evidence-link">{display_text}</a>'
    
    # Convert markdown to HTML first
    content = convert_markdown_to_html(content)
    
    # Apply link patterns
    content = re.sub(r'\[الإثبات:\s*(https?://[^\]]+)\]', make_link_clickable, content)
    content = re.sub(r'[- ]*الدليل:\s*(https?://\S+)', make_proof_link_clickable, content)
    content = re.sub(r'[- ]*دليل:\s*(https?://\S+)', make_proof_link_clickable, content)
    content = re.sub(r'🔗\s*(https?://\S+)', make_proof_link_clickable, content)
    
    # Use Streamlit expander (native and working)
    with st.expander(f"🔵 {title}", expanded=False):
        # Detailed analysis box with full content
        st.markdown(f"""
        <div class="reasoning-box">
            <div class="reasoning-title">🧠 التحليل التفصيلي</div>
            <div class="reasoning-content">{content}</div>
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
    
    gemini = GeminiAnalyzer(GEMINI_API_KEY)
    sample_tweets = df_tweets['text'].dropna().head(50000).tolist()
    sample_comments_list = []
    if df_comments is not None and not df_comments.empty:
        sample_comments_list = df_comments['comment_text'].dropna().head(5000).tolist()
    
    # استخراج جميع التغريدات مع روابطها (بدون فلترة)
    tweet_evidence_links = extract_tweet_urls_for_evidence(df_tweets, sample_size=200)
    evidence_text = "\n\n".join([
        f"التغريدة رقم {i+1}:\nالنص: {ev['text']}\nالرابط: {ev['url']}\nالتفاعل: {ev['likes']} إعجاب، {ev['retweets']} إعادة نشر\nالتاريخ: {ev['date']}"
        for i, ev in enumerate(tweet_evidence_links[:100])
    ])
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    sections = [
        ("introduction", "🧭 الملخّص التنفيذي", 10),
        ("what_people_say", "💬 ماذا يقول الناس عن الحساب", 22),
        ("complaints_issues", "😟 نقاط الشكوى أو الانتقاد المتكررة", 34),
        ("why_they_say", "🧠 تحليل أسباب الرأي العام", 46),
        ("how_to_improve", "💡 ما الذي يمكن فعله لتحسين الصورة", 58),
        ("positive_opportunities", "🚀 الفرص الإيجابية القابلة للاستثمار", 70),
        ("evidence_examples", "🧩 أمثلة وتحليلات مدعومة بالأدلة", 82),
        ("monitoring_metrics", "📊 المؤشرات المقترحة للمتابعة والتقييم", 94),
    ]
    
    for idx, (section_key, section_title, progress_val) in enumerate(sections):
        status_text.info(f"عم ننشئ: {section_title}...")
        progress_bar.progress(progress_val)
        
        if section_key == "introduction":
            prompt = f"""أنت محلل سمعة رقمية. اكتب ملخص تنفيذي مختصر بالنقاط.

البيانات:
- الحساب: @{username}
- التغريدات: {len(df_tweets):,}
- عينة: {chr(10).join([f"- {t[:100]}" for t in sample_tweets[:50]])}

المطلوب - أجب بهذا التنسيق بالضبط:

**الانطباع العام:**
- [إيجابي / سلبي / مختلط]

**درجة التأثير:**
- [مرتفع / متوسط / منخفض]

**أبرز المواضيع:**
- [موضوع 1]
- [موضوع 2]
- [موضوع 3]

**نوع الجمهور:**
- [وصف مختصر]

**التقييم السريع:**
- [نقطة 1]
- [نقطة 2]
- [نقطة 3]

الرد بالعربية. نقاط مختصرة فقط."""
            content = generate_ai_section(gemini, section_key, prompt, 5000)
            
        elif section_key == "what_people_say":
            prompt = f"""أنت محلل محتوى. حلل ماذا يقول الناس.

التغريدات مع الروابط:
{evidence_text[:3000]}

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# الإيجابيات
## [عنوان فرعي مختصر يلخص الإيجابيات]
فقرة قصيرة (2-3 جمل) توضح الإيجابيات بشكل عام.

**نقطة #1:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

**نقطة #2:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

**نقطة #3:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

# السلبيات
## [عنوان فرعي مختصر يلخص السلبيات]
فقرة قصيرة (2-3 جمل) توضح السلبيات بشكل عام.

**نقطة #1:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

**نقطة #2:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

**نقطة #3:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

# الملاحظات المتكررة
## [عنوان فرعي مختصر]
فقرة قصيرة (2-3 جمل) عن الملاحظات.

**ملاحظة #1:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

**ملاحظة #2:** [وصف مختصر]
- الدليل: 🔗 [رابط كامل]

قواعد:
- كل رابط في سطر منفصل
- استخدم الروابط الفعلية من البيانات
- جمل قصيرة ومباشرة

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
            
        elif section_key == "complaints_issues":
            prompt = f"""أنت خبير تحليل شكاوى. حدد الشكاوى الرئيسية.

البيانات:
{evidence_text[:3000]}

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# الشكاوى الرئيسية
## [عنوان فرعي يلخص طبيعة الشكاوى]
فقرة قصيرة (2-3 جمل) توضح الشكاوى بشكل عام.

**الشكوى #1: [العنوان]**
- الوصف: [مختصر]
- التكرار: [عدد المرات]
- الدليل: 🔗 [رابط 1]
- الدليل: 🔗 [رابط 2]

**الشكوى #2: [العنوان]**
- الوصف: [مختصر]
- التكرار: [عدد المرات]
- الدليل: 🔗 [رابط 1]
- الدليل: 🔗 [رابط 2]

**الشكوى #3: [العنوان]**
- الوصف: [مختصر]
- التكرار: [عدد المرات]
- الدليل: 🔗 [رابط 1]
- الدليل: 🔗 [رابط 2]

# التقييم
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن التقييم.

- الأخطر: [أي شكوى ولماذا]
- الأسهل للحل: [أي شكوى]

قواعد:
- كل رابط في سطر منفصل
- استخدم الروابط الفعلية
- جمل قصيرة ومباشرة

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
            
        elif section_key == "why_they_say":
            prompt = f"""أنت محلل سلوكي. اشرح أسباب الآراء.

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# أسباب الرأي العام
## [عنوان فرعي يلخص الأسباب]
فقرة قصيرة (2-3 جمل) عن الأسباب بشكل عام.

**السبب #1: [عنوان السبب]**
- الشرح: [وصف مختصر]
- التأثير: [كيف يؤثر]

**السبب #2: [عنوان السبب]**
- الشرح: [وصف مختصر]
- التأثير: [كيف يؤثر]

**السبب #3: [عنوان السبب]**
- الشرح: [وصف مختصر]
- التأثير: [كيف يؤثر]

# الخلاصة
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) تلخص الأسباب.

- [نقطة رئيسية 1]
- [نقطة رئيسية 2]
- [نقطة رئيسية 3]

قواعد: جمل قصيرة ومباشرة.

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 7000)
            
        elif section_key == "how_to_improve":
            prompt = f"""أنت مستشار سمعة. قدم حلول مختصرة وواضحة.

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# حلول قصيرة المدى
## تنفذ خلال أيام
فقرة قصيرة (2-3 جمل) عن الحلول السريعة.

**الحل #1:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم يوم]

**الحل #2:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم يوم]

**الحل #3:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم يوم]

# حلول متوسطة المدى
## تنفذ خلال أسابيع
فقرة قصيرة (2-3 جمل) عن الحلول المتوسطة.

**الحل #1:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم أسبوع]

**الحل #2:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم أسبوع]

# حلول طويلة المدى
## تنفذ خلال أشهر
فقرة قصيرة (2-3 جمل) عن الحلول الاستراتيجية.

**الحل #1:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم شهر]

**الحل #2:** [عنوان الحل]
- الوصف: [كيف تنفذه]
- المدة: [كم شهر]

# الأولوية
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن الأولوية.

- ابدأ بـ: [الحل الأهم]
- السبب: [لماذا]

قواعد: جمل قصيرة ومباشرة.

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
            
        elif section_key == "positive_opportunities":
            prompt = f"""أنت خبير فرص. حدد الفرص الإيجابية.

البيانات:
{evidence_text[:2000]}

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# الموضوعات الناجحة
## [عنوان فرعي يلخص المواضيع]
فقرة قصيرة (2-3 جمل) عن الموضوعات الناجحة.

**موضوع #1:** [اسم الموضوع]
- التفاعل: [رقم]
- السبب: [لماذا ينجح]

**موضوع #2:** [اسم الموضوع]
- التفاعل: [رقم]
- السبب: [لماذا ينجح]

**موضوع #3:** [اسم الموضوع]
- التفاعل: [رقم]
- السبب: [لماذا ينجح]

# المحتوى الذي يعزز الولاء
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن المحتوى.

**نوع محتوى #1:** [النوع]
- لماذا ينجح: [السبب]

**نوع محتوى #2:** [النوع]
- لماذا ينجح: [السبب]

# الجمهور الجديد المحتمل
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن الجمهور.

**شريحة #1:** [اسم الشريحة]
- كيفية الوصول: [الطريقة]

**شريحة #2:** [اسم الشريحة]
- كيفية الوصول: [الطريقة]

# خطة الاستفادة
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن الخطة.

- [خطوة 1]
- [خطوة 2]
- [خطوة 3]

قواعد: جمل قصيرة ومباشرة.

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
            
        elif section_key == "evidence_examples":
            prompt = f"""أنت محلل أدلة. قدم أمثلة حقيقية مع روابط منفصلة.

التغريدات:
{evidence_text[:3000]}

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# أمثلة التحليل المدعومة بالأدلة
## [عنوان فرعي يلخص الأمثلة]
فقرة قصيرة (2-3 جمل) عن الأمثلة والأدلة.

**مثال #1: [عنوان المثال]**
- الاقتباس: "[نص التغريدة - مختصر]"
- التحليل: [ماذا يعني هذا]
- الدليل: 🔗 [رابط التغريدة الكامل]

**مثال #2: [عنوان المثال]**
- الاقتباس: "[نص التغريدة - مختصر]"
- التحليل: [ماذا يعني هذا]
- الدليل: 🔗 [رابط التغريدة الكامل]

**مثال #3: [عنوان المثال]**
- الاقتباس: "[نص التغريدة - مختصر]"
- التحليل: [ماذا يعني هذا]
- الدليل: 🔗 [رابط التغريدة الكامل]

**مثال #4: [عنوان المثال]**
- الاقتباس: "[نص التغريدة - مختصر]"
- التحليل: [ماذا يعني هذا]
- الدليل: 🔗 [رابط التغريدة الكامل]

**مثال #5: [عنوان المثال]**
- الاقتباس: "[نص التغريدة - مختصر]"
- التحليل: [ماذا يعني هذا]
- الدليل: 🔗 [رابط التغريدة الكامل]

# الخلاصة
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) تلخص التحليلات.

- [نقطة رئيسية 1]
- [نقطة رئيسية 2]
- [نقطة رئيسية 3]

قواعد:
- كل رابط في سطر منفصل
- استخدم الروابط الفعلية من البيانات
- جمل قصيرة ومباشرة

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
            
        elif section_key == "monitoring_metrics":
            prompt = f"""أنت خبير مؤشرات. حدد مؤشرات المتابعة.

❗️ مهم: التزم بالتسلسل الهرمي التالي:

المطلوب - أجب بهذا التنسيق بالضبط:

# مؤشرات المتابعة والتقييم
## [عنوان فرعي يلخص المؤشرات]
فقرة قصيرة (2-3 جمل) عن أهمية هذه المؤشرات.

**مؤشر #1: [اسم المؤشر]**
- كيفية القياس: [الطريقة]
- تردد القياس: [يومي/أسبوعي/شهري]
- الهدف المطلوب: [رقم أو نسبة]

**مؤشر #2: [اسم المؤشر]**
- كيفية القياس: [الطريقة]
- تردد القياس: [يومي/أسبوعي/شهري]
- الهدف المطلوب: [رقم أو نسبة]

**مؤشر #3: [اسم المؤشر]**
- كيفية القياس: [الطريقة]
- تردد القياس: [يومي/أسبوعي/شهري]
- الهدف المطلوب: [رقم أو نسبة]

**مؤشر #4: [اسم المؤشر]**
- كيفية القياس: [الطريقة]
- تردد القياس: [يومي/أسبوعي/شهري]
- الهدف المطلوب: [رقم أو نسبة]

**مؤشر #5: [اسم المؤشر]**
- كيفية القياس: [الطريقة]
- تردد القياس: [يومي/أسبوعي/شهري]
- الهدف المطلوب: [رقم أو نسبة]

# معايير النجاح
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن معايير النجاح.

- [معيار 1]
- [معيار 2]
- [معيار 3]

# تنبيهات وإشارات الخطر
## [عنوان فرعي]
فقرة قصيرة (2-3 جمل) عن التنبيهات.

- [تنبيه 1]
- [تنبيه 2]
- [تنبيه 3]

قواعد: جمل قصيرة ومباشرة.

الرد بالعربية."""
            content = generate_ai_section(gemini, section_key, prompt, 8000)
        # عرض القسم مع تحويل الروابط لـ hyperlinks (Accordion style)
        display_report_section(section_title, content, section_key)
        time.sleep(1)
    
    progress_bar.progress(100)
    status_text.success("✅ تم إنشاء التقرير التفصيلي بنجاح!")

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
                    <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem; font-weight: bold; margin: 0 auto; border: 3px solid #f0f0f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
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
                <div style="font-size: 1.8rem; font-weight: 700; color: #1976D2;">{profile['Following Count']:,}</div>
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
            marker=dict(colors=['#ff6b6b', '#1976D2', '#4CAF50']),
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
        fig_replies = create_metric_comparison_chart(df_tweets, 'Replies', '#1976D2')
        if fig_replies:
            st.plotly_chart(fig_replies, use_container_width=True)
            total_replies = df_tweets['replies'].sum()
            avg_replies = df_tweets['replies'].mean()
            best_post_replies = df_tweets['replies'].max()
            st.markdown(f"""
            <div style="background: #E3F2FD; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid #1976D2; margin-top: 0.5rem;">
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
            background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%) !important;
            box-shadow: 0 8px 20px rgba(25, 118, 210, 0.3) !important;
        }
        [data-testid="column"]:nth-child(2) button:hover {
            box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header Section with Logo and Text
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown("""
            <div style='display: flex; align-items: center; gap: 1rem; margin: 0 0 1rem 0; padding: 0;'>
                <div style='font-size: 2.5rem; line-height: 1;'>🎯</div>
                <div>
                    <h3 style='margin: 0; padding: 0; font-size: 1.5rem; font-weight: 800; color: #212121;'>Reputation Agent</h3>
                    <p style='margin: 0; padding: 0; font-size: 0.85rem; color: #888; font-weight: 500;'>AI-Powered Social Media Analytics</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("Start Extraction", type="primary", use_container_width=True, key="main_extraction_btn"):
                show_extraction_modal()
        with col3:
            if st.button("Reset App", type="secondary", use_container_width=True, key="reset_app_btn"):
                st.session_state.clear()
                st.rerun()
        
        # Main Tabs - 2 tabs
        tab1, tab2 = st.tabs(["📊 Dashboard", "📄 Detailed Report"])
        
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
                
                # Header for Detailed Report
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); padding: 2.5rem; border-radius: 24px; margin-bottom: 2.5rem; box-shadow: 0 10px 40px rgba(25, 118, 210, 0.3);">
                    <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">🎯 تقرير إدارة السمعة الشامل</h1>
                    <h2 style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1.3rem; font-weight: 600; margin-bottom: 1rem;">Reputation Management Report</h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1rem; line-height: 1.8;">
                        تحليل شامل لسمعة الحساب @{username} على تويتر/إكس<br>
                        يتضمن ما يقوله الناس، الشكاوى، الأسباب، والحلول العملية لتحسين الصورة العامة
                    </p>
                    <div style="background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 12px; margin-top: 1.5rem;">
                        <p style="color: white; margin: 0; font-size: 0.9rem;">
                            <strong>🎯 الهدف:</strong> تحويل البيانات إلى خطة عمل واضحة لتحسين السمعة وبناء علاقة أقوى مع الجمهور
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate Detailed Report
                ai_detailed_report_page()
                
                # Download Button for Detailed Report
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    # Check if report has been generated
                    sections_list = [
                        ("introduction", "🧭 Executive Summary"),
                        ("what_people_say", "💬 What People Say About Account"),
                        ("complaints_issues", "😟 Complaints & Criticism Points"),
                        ("why_they_say", "🧠 Analysis of Public Opinion Reasons"),
                        ("how_to_improve", "💡 How to Improve Image & Impression"),
                        ("positive_opportunities", "🚀 Positive Opportunities to Invest"),
                        ("evidence_examples", "🧩 Examples & Evidence-Based Analysis"),
                        ("monitoring_metrics", "📊 Monitoring & Evaluation Metrics"),
                    ]
                    
                    # Check if at least one section exists
                    has_report = any(section_key in st.session_state.ai_report_cache for section_key, _ in sections_list)
                    
                    if has_report:
                        detailed_report = f"""
Detailed Analysis Report with Evidence Links - Twitter Account
Account: @{username}
Analysis Date: {datetime.now().strftime('%d %B %Y - %H:%M')}
Sample Size: {len(data.get('tweets')):,} tweets | {len(data.get('comments')) if data.get('comments') is not None else 0:,} comments

"""
                        for section_key, section_title in sections_list:
                            if section_key in st.session_state.ai_report_cache:
                                detailed_report += f"\n\n{'='*60}\n{section_title}\n{'='*60}\n\n{st.session_state.ai_report_cache[section_key]}"
                        
                        detailed_report += f"""

{'='*60}
Report ID: DETAILED-ANALYSIS-{datetime.now().strftime('%Y%m%d-%H%M%S')}
Issue Date: {datetime.now().strftime('%d %B %Y - %H:%M:%S')}
Report Type: Detailed Report with Evidence Links
{'='*60}
"""
                        
                        filename = f"Detailed_Report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        st.download_button(
                            label="💾 Download Detailed Report",
                            data=detailed_report.encode('utf-8'),
                            file_name=filename,
                            mime="text/plain",
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.info("ℹ️ Generate the report above first, then you can download it here.")
            
    except Exception as e:
        st.error("An error occurred")
        st.exception(e)
        if st.button("Restart Application"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
