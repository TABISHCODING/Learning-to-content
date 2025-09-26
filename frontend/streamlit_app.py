import re
# app_ui/app.py
import streamlit as st
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials
import requests
import pandas as pd
import os
import time
import json
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
load_dotenv()

# ---------------- Professional CSS with Status Tracker Styling ----------------
def inject_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global App Styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #e2e8f0;
    }

    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }

    h1 {
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem !important;
    }

    /* Form Container */
    div[data-testid="stForm"] {
        background: linear-gradient(145deg, #1e293b, #334155) !important;
        border: 1px solid #475569 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Status Tracker Container */
    .status-tracker {
        background: linear-gradient(145deg, #1e293b, #334155) !important;
        border: 1px solid #475569 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25) !important;
    }

    /* Status Steps */
    .status-step {
        display: flex;
        align-items: center;
        margin: 0.75rem 0;
        padding: 0.75rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    .status-step.completed {
        background: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
    }

    .status-step.current {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        animation: pulse 2s infinite;
    }

    .status-step.pending {
        background: rgba(100, 116, 139, 0.1);
        border-left: 4px solid #64748b;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div,
    .stNumberInput > div > div > input {
        background: #334155 !important;
        border: 1px solid #64748b !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        font-weight: 400 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
    }

    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stMultiSelect label,
    .stNumberInput label,
    .stCheckbox label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }

    /* Checkbox text color fix */
    .stCheckbox > label > div {
        color: #cbd5e1 !important;
    }

    /* Primary Button */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        width: 100% !important;
        margin-top: 1rem !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #1e40af) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
    }

    /* Secondary Buttons */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #64748b, #475569) !important;
        border: 1px solid #64748b !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1e293b !important;
        border-radius: 10px !important;
        padding: 0.5rem !important;
        gap: 0.5rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #94a3b8 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
    }

    /* Data Tables */
    .stDataFrame,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"] {
        background: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    .stDataFrame table,
    div[data-testid="stDataFrame"] table {
        background: #1e293b !important;
        color: #e2e8f0 !important;
    }

    .stDataFrame thead th,
    div[data-testid="stDataFrame"] thead th {
        background: #334155 !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #475569 !important;
    }

    .stDataFrame tbody td,
    div[data-testid="stDataFrame"] tbody td {
        border-bottom: 1px solid #374151 !important;
        color: #d1d5db !important;
    }

    /* Success/Error Messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid #22c55e !important;
        border-radius: 8px !important;
        color: #86efac !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid #ef4444 !important;
        border-radius: 8px !important;
        color: #fca5a5 !important;
    }

    /* Columns */
    .stColumn {
        padding: 0 0.5rem !important;
    }

    /* Clickable Links */
    a.preview-link {
        color: #60a5fa !important;
        font-weight: 500 !important;
        text-decoration: none !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 4px !important;
        background: rgba(96, 165, 250, 0.1) !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        margin: 0 0.25rem !important;
        display: inline-block !important;
        transition: all 0.2s ease !important;
    }

    a.preview-link:hover {
        background: rgba(96, 165, 250, 0.2) !important;
        border-color: #60a5fa !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    # Orange/Black theme overrides
    st.markdown("""
    <style>
    /* Yellow Background with Black Accents Overrides */
    .stApp {
        background: linear-gradient(135deg, #fde047 0%, #facc15 50%, #eab308 100%) !important;
        color: #0b0b0b !important;
    }
    h1 {
        background: linear-gradient(135deg, #0b0b0b, #1a1a1a) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }
    /* Containers */
    div[data-testid="stForm"],
    .status-tracker,
    .stDataFrame,
    div[data-testid="stDataFrame"],
    div[data-testid="stDataEditor"],
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(145deg, rgba(0,0,0,0.85), rgba(20,20,20,0.9)) !important;
        border: 1px solid rgba(0,0,0,0.6) !important;
        color: #facc15 !important;
    }
    /* Status steps */
    .status-step.current {
        background: rgba(0, 0, 0, 0.10) !important;
        border-left: 4px solid #facc15 !important;
    }
    .status-step.completed {
        background: rgba(34, 197, 94, 0.10) !important;
        border-left: 4px solid #22c55e !important;
    }
    .status-step.pending {
        background: rgba(0, 0, 0, 0.08) !important;
        border-left: 4px solid #525252 !important;
    }
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div,
    .stNumberInput > div > div > input {
        background: rgba(0,0,0,0.85) !important;
        border: 1px solid rgba(0,0,0,0.45) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #facc15 !important;
        box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.25) !important;
    }
    /* Primary buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0b0b0b, #1a1a1a) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.35) !important;
        color: #facc15 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1a1a1a, #262626) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.45) !important;
    }
    /* Active tab */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0b0b0b, #1a1a1a) !important;
        color: #facc15 !important;
    }
    /* Links */
    a.preview-link {
        color: #0b0b0b !important;
        background: rgba(0, 0, 0, 0.10) !important;
        border: 1px solid rgba(0, 0, 0, 0.30) !important;
    }
    a.preview-link:hover {
        background: rgba(0, 0, 0, 0.20) !important;
        border-color: #0b0b0b !important;
    }
    /* Headings on orange background */
    h1, h2, h3, h4, h5, h6 { color: #0b0b0b !important; }
    /* Headings in dark containers */
    div[data-testid="stForm"] h1, div[data-testid="stForm"] h2, div[data-testid="stForm"] h3,
    div[data-testid="stForm"] h4, div[data-testid="stForm"] h5, div[data-testid="stForm"] h6,
    .status-tracker h1, .status-tracker h2, .status-tracker h3, .status-tracker h4, .status-tracker h5, .status-tracker h6,
    .stTabs [data-baseweb="tab-list"] h1, .stTabs [data-baseweb="tab-list"] h2, .stTabs [data-baseweb="tab-list"] h3,
    .stTabs [data-baseweb="tab-list"] h4, .stTabs [data-baseweb="tab-list"] h5, .stTabs [data-baseweb="tab-list"] h6 { color: #facc15 !important; }
    /* Labels inside inputs */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stCheckbox label { color: #facc15 !important; }
    /* Tabs default text (dark tab bar) */
    .stTabs [data-baseweb="tab"] { color: #facc15 !important; }
    /* Status tracker inline text override */
    .status-tracker .status-step div { color: #facc15 !important; }
    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(135deg, #0b0b0b, #1a1a1a) !important; color: #f59e0b !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 { color: #facc15 !important; }
    /* Links inside dark containers */
    .status-tracker a.preview-link, div[data-testid="stForm"] a.preview-link { color: #facc15 !important; background: rgba(0,0,0,0.15) !important; border-color: rgba(0,0,0,0.3) !important; }
    /* Radio group labels and options in dark forms */
    div[data-testid="stForm"] .stRadio, div[data-testid="stForm"] .stRadio * { color: #facc15 !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- Status Flow Definition ----------------
STATUS_FLOW = [
    {"key": "Topics Created", "label": "📝 Topics Created", "description": "Topics have been extracted from notes"},
    {"key": "Script Generated", "label": "📜 Script Generated", "description": "AI script and image prompts created"},
    {"key": "Audio Generated", "label": "🎵 Audio Generated", "description": "Text-to-speech audio created"},
    {"key": "Images Generated", "label": "🖼️ Images Generated", "description": "All 4 images generated successfully"},
    {"key": "Video Generated", "label": "🎬 Video Generated", "description": "Final video assembled with FFmpeg"},
    {"key": "Completed", "label": "✅ Completed", "description": "All assets saved and workflow finished"}
]

# ---------------- Paths & Auth ----------------
# Prefer explicit credentials path from env/secrets; fall back to container path
SECRETS_PATH = os.getenv(
    "GOOGLE_SHEETS_CREDENTIALS",
    st.secrets.get("GOOGLE_SHEETS_CREDENTIALS", "/app/config/secrets/google_sheets_service.json")
)
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def authorize_gspread():
    """Authorize gspread using either a credentials file path or inline JSON from secrets."""
    try:
        if os.path.exists(SECRETS_PATH):
            creds = Credentials.from_service_account_file(SECRETS_PATH, scopes=scope)
        elif "GOOGLE_SERVICE_ACCOUNT_JSON" in st.secrets:
            creds = Credentials.from_service_account_info(dict(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]), scopes=scope)
        else:
            raise FileNotFoundError("Google service account credentials not configured")
        return gspread.authorize(creds)
    except Exception as e:
        st.warning(f"Google Sheets auth not configured: {e}")
        return None

# Lazily resolve the Google Sheet by ID (preferred) or by name fallback
SHEET_ID = st.secrets.get("GOOGLE_SHEET_ID", os.getenv("GOOGLE_SHEET_ID"))
SHEET_NAME_FALLBACK = st.secrets.get("GOOGLE_SHEET_NAME", "LearningToContentDB")
client = authorize_gspread()
try:
    if client is not None:
        sheet = client.open_by_key(SHEET_ID) if SHEET_ID else client.open(SHEET_NAME_FALLBACK)
    else:
        sheet = None
except Exception as e:
    st.error(f"Failed to open Google Sheet: {e}")
    sheet = None

# ---------------- Helpers ----------------
@st.cache_data(ttl=5)  # Cache for 5 seconds for real-time updates
def load_worksheet_as_df(ws_name: str) -> pd.DataFrame:
    """Load a worksheet into DataFrame safely."""
    try:
        ws = sheet.worksheet(ws_name)
        all_values = ws.get_all_values()
        if not all_values:
            return pd.DataFrame()
        headers, data = all_values[0], all_values[1:]

        # Fix duplicate column names and empty headers
        seen = {}
        fixed_headers = []
        for i, header in enumerate(headers):
            # Handle empty headers
            if not header or header.strip() == "":
                header = f"Column_{i+1}"

            # Handle duplicates
            original_header = header
            counter = 0
            while header in seen:
                counter += 1
                header = f"{original_header}_{counter}"

            seen[header] = True
            fixed_headers.append(header)

        # Remove completely empty columns (all values are empty)
        df_temp = pd.DataFrame(data, columns=fixed_headers)
        non_empty_cols = []
        for col in df_temp.columns:
            if df_temp[col].astype(str).str.strip().ne('').any():
                non_empty_cols.append(col)

        if non_empty_cols:
            df_temp = df_temp[non_empty_cols]

        return df_temp

        return pd.DataFrame(data, columns=fixed_headers)
    except Exception as e:
        st.error(f"⚠️ Error loading {ws_name}: {e}")
        return pd.DataFrame()


# Robust parser for comma-separated or JSON lists of file links
def parse_links_field(val):
    links = []
    if val is None:
        return links
    try:
        # JSON array case
        if isinstance(val, list):
            candidates = val
        elif isinstance(val, str) and val.strip().startswith("["):
            candidates = json.loads(val)
        else:
            candidates = re.split(r"[\s,;]+", str(val))
    except Exception:
        candidates = str(val).split(',')

    for item in candidates:
        s = str(item).strip()
        if not s:
            continue
        # Filter out accidental non-URL tokens seen in sheets (e.g., 'hi-IN', 'Generated')
        if s in {"hi-IN", "en-US", "Male", "Female", "Generated"}:
            continue
        if s.startswith("http://") or s.startswith("https://") or s.lower().endswith((".png", ".jpg", ".jpeg")) or os.path.exists(s):
            links.append(s)
    return links

def get_topic_status(topic_id: str) -> dict:
    """Get current status for a specific TopicID from EssentialContent sheet."""
    try:
        df = load_worksheet_as_df("EssentialContent")
        if df.empty:
            return None

        # Find row with matching TopicID
        matching_rows = df[df["TopicID"].astype(str) == str(topic_id)]
        if matching_rows.empty:
            # No data found for this TopicID in EssentialContent
            return None


        row = matching_rows.iloc[0]
        return {
            "StatusProgress": row.get("StatusProgress", "Pending"),
            "FinalStatus": row.get("FinalStatus", "Pending"),
            "TopicID": topic_id,
            "Title": row.get("Title", ""),
            "Script": row.get("Script", ""),
            "Caption": row.get("Caption", ""),
            "Hashtag": row.get("Hashtag", ""),
            "AudioLink": row.get("AudioLink", ""),
            "Image1Link": row.get("Image1Link", ""),
            "Image2Link": row.get("Image2Link", ""),
            "Image3Link": row.get("Image3Link", ""),
            "Image4Link": row.get("Image4Link", ""),
            "Image1GeneratedBy": row.get("Image1GeneratedBy", ""),
            "Image2GeneratedBy": row.get("Image2GeneratedBy", ""),
            "Image3GeneratedBy": row.get("Image3GeneratedBy", ""),
            "Image4GeneratedBy": row.get("Image4GeneratedBy", ""),
            "VideoLink": row.get("VideoLink", ""),
            "LastUpdate": "Just now"
        }
    except Exception as e:
        st.error(f"Error fetching status: {e}")
        return None

def get_recent_topics(limit: int = 10) -> list:
    """Get recently created topics for quick selection."""
    try:
        df_essential = load_worksheet_as_df("EssentialContent")

        recent_topics = []

        # Get from EssentialContent table
        if not df_essential.empty and "TopicID" in df_essential.columns:
            for _, row in df_essential.tail(limit).iterrows():
                if row["TopicID"]:
                    recent_topics.append({
                        "TopicID": row["TopicID"],
                        "Title": row.get("Title", "No title"),
                        "FinalStatus": row.get("FinalStatus", "Pending"),
                        "StatusProgress": row.get("StatusProgress", "Topics Created")
                    })

        return recent_topics[-limit:]  # Return most recent
    except Exception as e:
        st.error(f"Error fetching recent topics: {e}")
        return []

def render_status_tracker(topic_data: dict):
    """Render the beautiful status tracker."""
    if not topic_data:
        st.warning("⚠️ No data found for this Topic ID")
        return

    # Use new schema fields: StatusProgress and FinalStatus
    current_status = topic_data.get("StatusProgress", topic_data.get("FinalStatus", "Pending"))
    current_index = next((i for i, step in enumerate(STATUS_FLOW) if step["key"] == current_status), 0)

    # Progress bar
    progress = (current_index + 1) / len(STATUS_FLOW)
    st.progress(progress)

    # Status steps
    st.markdown('<div class="status-tracker">', unsafe_allow_html=True)

    for i, step in enumerate(STATUS_FLOW):
        if i < current_index:
            status_class = "completed"
            icon = "✅"
        elif i == current_index:
            status_class = "current"
            icon = "🔄"
        else:
            status_class = "pending"
            icon = "⏳"

        st.markdown(f"""
            <div class="status-step {status_class}">
                <div style="margin-right: 12px; font-size: 1.2em;">{icon}</div>
                <div>
                    <div style="font-weight: 600; color: #f1f5f9;">{step['label']}</div>
                    <div style="font-size: 0.85em; color: #94a3b8; margin-top: 2px;">{step['description']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Show additional info if available
    if topic_data.get("Title"):
        st.info(f"**Topic:** {topic_data['Title']}")
    # Show caption and hashtags if available
    cap = topic_data.get("Caption")
    if cap:
        st.write(f"📝 Caption: {cap}")

    # Show image platform tracking
    platform_badges = []
    for i in range(1, 5):
        gen = topic_data.get(f"Image{i}GeneratedBy", "")
        link = topic_data.get(f"Image{i}Link", "")
        if link and gen:
            platform_badges.append(f"Image {i}: **{gen}**")
    if platform_badges:
        st.markdown("🖼️ **Image Generation Platforms:** " + " | ".join(platform_badges))

    # Handle hashtags from new schema (single Hashtag field)
    hashtag_data = topic_data.get("Hashtag")
    if hashtag_data:
        # Try to parse as JSON first, then as comma-separated string
        hashtags_list = []
        try:
            if hashtag_data.startswith('[') or hashtag_data.startswith('{'):
                hashtags_list = json.loads(hashtag_data) if isinstance(hashtag_data, str) else hashtag_data
            else:
                hashtags_list = [h.strip() for h in str(hashtag_data).split(",") if h.strip()]
        except Exception:
            hashtags_list = [h.strip() for h in str(hashtag_data).split(",") if h.strip()]

        if hashtags_list:
            if isinstance(hashtags_list, list):
                st.write("🏷️ Hashtags: " + " ".join(hashtags_list))
            else:
                st.write(f"🏷️ Hashtags: {hashtags_list}")

    # Show asset links using new schema field names
    col1, col2, col3 = st.columns(3)
    with col1:
        if topic_data.get("AudioLink"):
            st.markdown(f"🎵 [Audio File]({topic_data['AudioLink']})")
    with col2:
        # Handle individual image links from new schema with platform tracking
        image_links = []
        for i in range(1, 5):  # Image1Link to Image4Link
            img_link = topic_data.get(f"Image{i}Link")
            img_platform = topic_data.get(f"Image{i}GeneratedBy", "Unknown")
            if img_link:
                image_links.append((i, img_link, img_platform))

        if image_links:
            st.markdown("🖼️ Images:")
            for i, img_url, platform in image_links:
                st.markdown(f"[Image {i}]({img_url}) - *{platform}*")
    with col3:
        if topic_data.get("VideoLink"):
            st.markdown(f"🎬 [Final Video]({topic_data['VideoLink']})")

    # Show platform badges after image links
    platform_badges = []
    for i in range(1, 5):
        gen = topic_data.get(f"Image{i}GeneratedBy", "")
        link = topic_data.get(f"Image{i}Link", "")
        if link:
            platform_badges.append(f"Image {i}: **{gen or 'Unknown'}**")
    if platform_badges:
        st.markdown("🖼️ **Image platforms** • " + " | ".join(platform_badges))

def upsert_row(ws_name: str, key_cols: list, row_dict: dict):
    """Update a row if it exists, otherwise insert it."""
    ws = sheet.worksheet(ws_name)
    headers = ws.row_values(1)
    all_rows = ws.get_all_values()[1:]

    row_idx = None
    for i, row in enumerate(all_rows, start=2):
        match = True
        for key_col in key_cols:
            key_val = str(row_dict.get(key_col, ""))
            col_idx = headers.index(key_col)
            if len(row) <= col_idx or str(row[col_idx]) != key_val:
                match = False
                break
        if match:
            row_idx = i
            break

    output_row = []
    for header in headers:
        val = row_dict.get(header, "")
        if isinstance(val, list):
            val = ", ".join(map(str, val))
        output_row.append(str(val))

    if row_idx:
        end_a1 = rowcol_to_a1(row_idx, len(headers))
        ws.update(f"A{row_idx}:{end_a1}", [output_row])
    else:
        ws.append_row(output_row)

    st.cache_data.clear()

def sync_all_rows(ws_name: str, df: pd.DataFrame):
    """Overwrite entire worksheet with DataFrame (bulk sync)."""
    ws = sheet.worksheet(ws_name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
    st.cache_data.clear()

# ---------------- UI ----------------
st.set_page_config(
    page_title="Learning to Content - Clean UI v2.0",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clear any old session state that might be causing issues
if 'old_tabs_cleared' not in st.session_state:
    st.session_state.old_tabs_cleared = True
    st.cache_data.clear()
    st.cache_resource.clear()

# Inject CSS
inject_custom_css()

# Header with styled refresh button
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <h1 style="margin: 0;">🚀 Learning-to-Content Automation Dashboard</h1>
    <div style="display: flex; align-items: center; gap: 15px;">
        <span style="background: linear-gradient(45deg, #0b0b0b 0%, #1a1a1a 100%);
                     color: #facc15; padding: 8px 16px; border-radius: 20px;
                     font-size: 14px; font-weight: 600;">v2.0 - Clean UI</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Styled refresh button in sidebar
with st.sidebar:
    st.markdown("### 🔧 System Controls")
    if st.button("🔄 Force Refresh", help="Clear browser cache and reload", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

# -------- Real-Time Status Tracker --------
st.subheader("📊 Live Workflow Status Tracker")

# Auto-tracking current workflow if available
if 'current_workflow_id' in st.session_state:
    st.info(f"🔄 Auto-tracking active workflow: {st.session_state.current_workflow_id}")

    # Check current workflow status
    try:
        backend_url = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:9000"))
        status_response = requests.get(f"{backend_url}/api/workflow/status/{st.session_state.current_workflow_id}", timeout=10)

        if status_response.status_code == 200:
            status_data = status_response.json()
            current_status = status_data.get('status', 'Unknown')

            # Progress bar with detailed status
            col1, col2 = st.columns([3, 1])
            with col1:
                if current_status == 'Processing':
                    st.progress(0.05, "🚀 Workflow started - Initializing...")
                elif current_status == 'Extracting Topics':
                    st.progress(0.15, "🧠 Extracting topics from raw notes...")
                elif current_status == 'Topics Extracted':
                    st.progress(0.25, "✅ Topics extracted successfully")
                elif current_status == 'Script Generated':
                    st.progress(0.4, "📝 Scripts generated for topics")
                elif current_status == 'Audio Generated':
                    st.progress(0.6, "🎵 Audio files created with voice synthesis")
                elif current_status == 'Images Generated':
                    st.progress(0.8, "🖼️ Images generated for visual content")
                elif current_status == 'Video Generated':
                    st.progress(0.95, "🎬 Videos created with audio integration")
                elif current_status == 'Video Failed':
                    st.progress(0.85, "⚠️ Video generation failed (FFmpeg required)")
                    st.warning("⚠️ Video generation failed - FFmpeg not installed")
                elif current_status == 'Completed':
                    st.progress(1.0, "✅ Complete pipeline finished!")
                    st.success("🎉 All content generated successfully!")
                elif current_status == 'Failed':
                    st.progress(0.0, "❌ Pipeline failed")
                    st.error(f"❌ Workflow failed: {status_data.get('error', 'Unknown error')}")
                else:
                    st.progress(0.1, f"🔄 Status: {current_status}")

            with col2:
                if current_status in ['Completed', 'Failed', 'Video Failed']:
                    if st.button("🎯 Clear Tracking"):
                        del st.session_state.current_workflow_id
                        st.rerun()

            st.info(f"📊 Current Status: {current_status}")

            # Auto-refresh only if workflow is still active AND auto-refresh is enabled
            if (current_status not in ['Completed', 'Failed', 'Video Failed'] and
                st.session_state.get('auto_refresh_enabled', False)):
                st_autorefresh(interval=5000, key="active_workflow_refresh")  # 5 seconds for faster updates
            elif current_status in ['Completed', 'Failed', 'Video Failed']:
                # Disable auto-refresh when workflow completes
                st.session_state.auto_refresh_enabled = False

        else:
            st.warning("⚠️ Could not check active workflow status")

    except Exception as e:
        st.warning(f"⚠️ Active workflow status check error: {e}")

    st.markdown("---")

# Manual tracking section
st.markdown("**Manual Workflow Tracking:**")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    # Topic ID input with recent topics dropdown
    recent_topics = get_recent_topics()
    if recent_topics:
        topic_options = [""] + [f"{t['TopicID']} - {t['Title'][:50]}..." if len(t['Title']) > 50 else f"{t['TopicID']} - {t['Title']}" for t in recent_topics]
        selected_topic = st.selectbox("Recent Topics", topic_options, key="topic_selector")
        if selected_topic:
            selected_topic_id = selected_topic.split(" - ")[0]
        else:
            selected_topic_id = ""
    else:
        selected_topic_id = ""

    # Manual topic ID input
    manual_topic_id = st.text_input("Or enter Topic ID manually:", value=selected_topic_id, key="manual_topic")
    topic_id_to_track = manual_topic_id if manual_topic_id else selected_topic_id

with col2:
    # Auto-refresh checkbox that respects session state
    current_auto_refresh = st.session_state.get('auto_refresh_enabled', False)
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=current_auto_refresh)

    # Update session state when checkbox changes
    if auto_refresh != current_auto_refresh:
        st.session_state.auto_refresh_enabled = auto_refresh

with col3:
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

# Auto-refresh logic - only if enabled and no active workflow tracking
if (auto_refresh and
    'current_workflow_id' not in st.session_state):
    st_autorefresh(interval=5000, key="status_refresh")

# Clear any cached data that might reference old worksheets
if st.button("🧹 Clear Cache", key="clear_cache_btn"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ Cache cleared! Please refresh the page.")
    st.rerun()

# Display status tracker
if topic_id_to_track:
    topic_data = get_topic_status(topic_id_to_track)
    render_status_tracker(topic_data)
else:
    st.info("👆 Select or enter a Topic ID to track its workflow progress")

# -------- Content Request Form --------
st.subheader("📌 Create New Content Request")
with st.form("content_form"):
    input_type = st.radio(
        "Input Type",
        options=["Raw Notes", "Script/Story", "Custom Prompt"],
        index=0,
        help="Choose how you want to drive the workflow"
    )

    raw_notes = ""
    script_text = ""
    custom_prompt = ""
    # Optional duration and TTS controls (exposed for Raw Notes and Custom Prompt)
    target_duration_str = ""
    override_tts = False
    tts_rate = 1.0

    if input_type == "Raw Notes":
        raw_notes = st.text_area(
            "Raw Notes",
            "",
            help="Paste your notes here (minimum 50 characters)",
            height=120
        )
    elif input_type == "Script/Story":
        script_text = st.text_area(
            "Script / Story",
            "",
            help="Paste the full narration text. The system will skip script generation and use this directly.",
            height=160
        )
    else:
        custom_prompt = st.text_area(
            "Custom Prompt",
            "",
            help="Example: Create 5 topics about LLMs in order, then generate scripts for each.",
            height=140
        )
        raw_notes = st.text_area(
            "Optional Context Notes",
            "",
            help="Optional additional notes/context used with your custom prompt.",
            height=100
        )

    # Optional controls for duration and TTS in Raw Notes and Custom Prompt modes
    if input_type in ("Raw Notes", "Custom Prompt"):
        st.markdown("---")
        st.markdown("**⏱️ Duration & 🎙️ TTS Options (optional)**")
        target_duration_str = st.text_input(
            "Target Video Duration (seconds) [optional]",
            "",
            help="If provided, the model will aim to write a script sized for this speaking time."
        )
        override_tts = st.checkbox(
            "Override TTS speaking rate [optional]",
            value=False,
            help="If enabled, pick a custom speaking rate; 1.0 = normal speed"
        )
        if override_tts:
            tts_rate = st.slider(
                "TTS Speaking Rate (0.5–2.0)",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.05
            )
        st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Language", ["Hinglish", "English", "Hindi", "Urdu"])
        tone = st.selectbox("Tone", ["Friendly", "Professional", "Casual", "Enthusiastic"])
        voice_gender = st.selectbox("Voice Gender", ["Female", "Male"])
        posts_per_day = st.number_input("Posts Per Day", min_value=1, max_value=10, value=7)

    with col2:
        platforms = st.multiselect(
            "Platforms",
            ["YouTube Shorts", "Instagram", "LinkedIn", "Twitter"],
            default=["YouTube Shorts", "Instagram"]
        )
        track = st.text_input("Track Name", "SkillBox 1")
        auto_full_pipeline = st.checkbox(
            "Generate images + audio + video automatically",
            value=True
        )

    submitted = st.form_submit_button("🎯 Start Generation")

    if submitted:
        # Basic validations
        if input_type == "Raw Notes" and len(raw_notes.strip()) < 50:
            st.error("❌ Raw notes must be at least 50 characters.")
        elif input_type == "Script/Story" and len(script_text.strip()) < 20:
            st.error("❌ Script text is too short.")
        elif input_type == "Custom Prompt" and not (custom_prompt.strip() or raw_notes.strip()):
            st.error("❌ Provide a custom prompt or context notes.")
        elif not platforms:
            st.error("❌ Please select at least one platform.")
        else:
            payload = {
                "language": language,
                "tone": tone,
                "voice_gender": voice_gender,
                "posts_per_day": int(posts_per_day),
                "platforms": platforms,
                "track": track.strip(),
                "full_pipeline": auto_full_pipeline,
                # Image generation hints for 9:16 vertical assets
                "image_aspect_ratio": "9:16",
                "image_width": 1080,
                "image_height": 1920
            }

            # Map input type to backend fields
            if input_type == "Raw Notes":
                payload["input_type"] = "notes"
                payload["raw_notes"] = raw_notes.strip()
            elif input_type == "Script/Story":
                payload["input_type"] = "script"
                payload["script_text"] = script_text.strip()
                # Optional title override
                payload["title"] = st.session_state.get("title_override", "User Script")
            else:
                payload["input_type"] = "prompt"
                payload["custom_prompt"] = custom_prompt.strip()
                if raw_notes.strip():
                    payload["raw_notes"] = raw_notes.strip()

            # Forward optional duration and TTS controls for Raw Notes and Custom Prompt
            if input_type in ("Raw Notes", "Custom Prompt"):
                # Only include duration if user provided a valid positive integer
                try:
                    td_val = int(str(target_duration_str).strip()) if str(target_duration_str).strip() else 0
                    if td_val > 0:
                        payload["target_duration_seconds"] = td_val
                except Exception:
                    pass
                # Only include speaking rate if override explicitly enabled
                if override_tts:
                    try:
                        payload["audio_speaking_rate"] = float(tts_rate)
                    except Exception:
                        pass

            try:
                # Use backend URL from secrets or environment (fixed for local development)
                backend_url = st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:9000"))
                webhook_url = f"{backend_url}/webhook/learning-to-content"
                secret = st.secrets.get("WEBHOOK_SECRET", os.getenv("WEBHOOK_SECRET", "n8n_s3cR3t_p@s5phr@s3_f0R_p1p3l1n3"))

                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Secret": secret
                }

                st.info(f"🚀 Sending request to: {webhook_url}")
                res = requests.post(webhook_url, json=payload, headers=headers, timeout=60)

                if res.status_code in [200, 202]:
                    response_data = res.json()
                    st.success("✅ Workflow started successfully!")

                    # Show workflow details
                    if "workflow_id" in response_data:
                        workflow_id = response_data['workflow_id']
                        st.info(f"📋 Workflow ID: {workflow_id}")
                        st.info(f"⏱️ Estimated completion: {response_data.get('estimated_completion', '5-10 minutes')}")

                        # Live Progress Tracking
                        st.subheader("🔄 Live Workflow Progress")
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()

                        # Store workflow ID in session state for tracking
                        st.session_state.current_workflow_id = workflow_id
                        st.session_state.auto_refresh_enabled = True  # Enable auto-refresh when workflow starts

                        # Initial progress display
                        phase_text = "Processing raw notes..." if input_type == "Raw Notes" else ("Using provided script..." if input_type == "Script/Story" else "Executing custom prompt...")
                        progress_placeholder.progress(0.1, f"🚀 Workflow started - {phase_text}")
                        status_placeholder.info("📊 Current Status: Initializing pipeline")

                        st.cache_data.clear()
                        st.info("🔄 Auto-refresh enabled - Live status tracking activated!")
                        st.rerun()  # Immediately refresh to show tracking
                else:
                    st.error(f"❌ Backend returned {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"❌ Error sending request: {e}")

# -------- CONTENT MANAGEMENT --------
st.subheader("📊 Essential Content Management")

tab1, tab2, tab3 = st.tabs(["🎯 Essential Content", "📈 API Usage", "🚨 Error Log"])

# --- ESSENTIAL CONTENT (UNIFIED TABLE) ---
with tab1:
    df_ec = load_worksheet_as_df("EssentialContent")
    st.caption("🎯 **FRESH CLEAN SCHEMA** - All essential data in one place")

    if not df_ec.empty:
        # ESSENTIAL COLUMNS ONLY (24 columns with Image Generated By tracking)
        essential_cols = [
            "Time", "TopicID", "RunID", "Order", "Title", "Script", "Language",
            "Gender", "Tone", "Platform", "StatusProgress", "FinalStatus",
            "Caption", "Hashtag", "Image1Link", "Image2Link", "Image3Link",
            "Image4Link", "AudioLink", "VideoLink", "Image1GeneratedBy",
            "Image2GeneratedBy", "Image3GeneratedBy", "Image4GeneratedBy"
        ]

        # Ensure columns exist and map correctly
        available_cols = [col for col in essential_cols if col in df_ec.columns]
        if not available_cols:
            st.warning("⚠️ Column mapping issue detected. Available columns:")
            st.write(list(df_ec.columns))
            available_cols = list(df_ec.columns)[:20]  # Take first 20 columns

        df_ec_clean = df_ec[available_cols].copy()

        # Display with proper formatting
        st.markdown("### 📊 Essential Content Data")
        edited_ec = st.data_editor(
            df_ec_clean,
            num_rows="dynamic",
            width=None,
            key="ec_editor",
            height=500,
            column_config={
                "Time": st.column_config.TextColumn("Time", help="Creation timestamp"),
                "StatusProgress": st.column_config.SelectboxColumn(
                    "Status Progress",
                    options=["Topics Created", "Script Generated", "Audio Generated", "Images Generated", "Video Generated", "Completed"],
                    default="Topics Created"
                ),
                "FinalStatus": st.column_config.SelectboxColumn(
                    "Final Status",
                    options=["Pending", "In Progress", "Completed", "Failed"],
                    default="Pending"
                ),
                "Gender": st.column_config.SelectboxColumn(
                    "Voice Gender",
                    options=["Female", "Male"],
                    default="Female"
                ),
                # Clickable asset links
                "AudioLink": st.column_config.LinkColumn(
                    "Audio Link", help="Open audio file", display_text="Open audio"
                ),
                "VideoLink": st.column_config.LinkColumn(
                    "Video Link", help="Open final video", display_text="Open video"
                ),
                "Image1Link": st.column_config.LinkColumn(
                    "Image 1", help="Open image 1", display_text="Image 1"
                ),
                "Image2Link": st.column_config.LinkColumn(
                    "Image 2", help="Open image 2", display_text="Image 2"
                ),
                "Image3Link": st.column_config.LinkColumn(
                    "Image 3", help="Open image 3", display_text="Image 3"
                ),
                "Image4Link": st.column_config.LinkColumn(
                    "Image 4", help="Open image 4", display_text="Image 4"
                ),
                # Platform tracking for each image
                "Image1GeneratedBy": st.column_config.TextColumn("Image 1 Platform", help="Platform that generated Image 1"),
                "Image2GeneratedBy": st.column_config.TextColumn("Image 2 Platform", help="Platform that generated Image 2"),
                "Image3GeneratedBy": st.column_config.TextColumn("Image 3 Platform", help="Platform that generated Image 3"),
                "Image4GeneratedBy": st.column_config.TextColumn("Image 4 Platform", help="Platform that generated Image 4"),
                # Meta fields
                "Language": st.column_config.SelectboxColumn(
                    "Language",
                    options=["Hinglish", "English", "Hindi", "Urdu"],
                    default="English"
                ),
                "Tone": st.column_config.SelectboxColumn(
                    "Tone",
                    options=["Educational", "Casual", "Professional", "Entertaining"],
                    default="Educational"
                )
            }
        )

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Save Changes", key="save_ec"):
                try:
                    # Find changed rows
                    changes = []
                    for idx in range(len(edited_ec)):
                        if idx < len(df_ec_clean):
                            original_row = df_ec_clean.iloc[idx]
                            edited_row = edited_ec.iloc[idx]
                            if not original_row.equals(edited_row):
                                changes.append((idx + 2, edited_row))  # +2 for 1-indexed + header

                    if changes:
                        worksheet = sheet.worksheet("EssentialContent")
                        for row_idx, row_data in changes:
                            for col_idx, (col_name, value) in enumerate(row_data.items()):
                                if col_name in available_cols:
                                    worksheet.update_cell(row_idx, col_idx + 1, str(value))
                        st.success(f"✅ Updated {len(changes)} rows")
                    else:
                        st.info("No changes detected")
                except Exception as e:
                    st.error(f"❌ Error saving: {e}")

        with col2:
            if st.button("🔄 Sync All", key="sync_ec"):
                try:
                    worksheet = sheet.worksheet("EssentialContent")
                    # Clear existing data (keep headers)
                    worksheet.clear()
                    # Set headers
                    worksheet.append_row(available_cols)
                    # Add all data
                    for _, row in edited_ec.iterrows():
                        worksheet.append_row([str(row[col]) for col in available_cols])
                    st.success("✅ Essential Content synced successfully")
                except Exception as e:
                    st.error(f"❌ Error syncing: {e}")

        with col3:
            if st.button("🗑️ Reset Schema", key="reset_schema"):
                try:
                    response = requests.post("http://localhost:9000/admin/ensure-db?reset=true")
                    if response.status_code == 200:
                        st.success("✅ Schema reset successfully")
                        st.rerun()
                    else:
                        st.error(f"❌ Reset failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error resetting: {e}")
    else:
        st.info("No essential content data found")
        if st.button("🔧 Initialize Schema"):
            try:
                response = requests.post("http://localhost:9000/admin/ensure-db")
                if response.status_code == 200:
                    st.success("✅ Schema initialized successfully")
                    st.rerun()
                else:
                    st.error(f"❌ Initialization failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error initializing: {e}")

# --- API Usage ---
with tab2:
    df_api = load_worksheet_as_df("API_Usage")

    if not df_api.empty:
        # STREAMLINED: Essential API Usage columns only
        cols_api = [c for c in ["Timestamp", "RunID", "TopicID", "Provider", "StatusCode", "TokensUsed"] if c in df_api.columns]
        st.dataframe(df_api[cols_api] if cols_api else df_api, width=None, height=400)
    else:
        st.info("No API usage data found")

# --- Error Log ---
with tab3:
    df_err = load_worksheet_as_df("ErrorLog")
    if not df_err.empty:
        # STREAMLINED: Essential Error Log columns only
        error_cols = [c for c in ["Timestamp", "RunID", "TopicID", "ErrorMessage", "Status"] if c in df_err.columns]
        if error_cols:
            df_err_clean = df_err[error_cols]
            st.dataframe(df_err_clean, width=None, height=400)
        else:
            st.info("Error log data has formatting issues")
    else:
        st.info("No errors logged")




# System status section removed as requested

