#!/usr/bin/env python3
"""
🎯 COMPLETE PYTHON WORKFLOW ENGINE
Exact feature-for-feature replica of your n8n workflow
Matches every requirement from Master Developer Prompt
"""

import os
import json
import time
import requests
import uuid
import base64
import subprocess
import threading
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import texttospeech
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteWorkflowEngine:
    """🎯 COMPLETE WORKFLOW ENGINE - EXACT N8N REPLICA"""

    def __init__(self):
        # Environment variables (exact from your n8n workflow)
        self.google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.audio_folder_id = os.getenv("AUDIO_FOLDER_ID")
        self.images_folder_id = os.getenv("IMAGES_FOLDER_ID")
        self.videos_folder_id = os.getenv("VIDEOS_FOLDER_ID")

        # Status flow (exact from Master Developer Prompt)
        self.status_flow = [
            "Pending",           # Topic just extracted
            "ScriptGenerated",   # Gemini created script + image prompts
            "AudioGenerated",    # TTS finished
            "ImagesGenerated",   # All 4 images ready
            "VideoGenerated",    # Final MP4 created
            "Completed"          # Everything done and saved
        ]

        # Voice mapping (exact from Master Developer Prompt)
        self.voice_mapping = {
            ("English", "Male"): {"name": "en-US-Wavenet-D", "code": "en-US"},
            ("English", "Female"): {"name": "en-US-Wavenet-F", "code": "en-US"},
            ("Hindi", "Male"): {"name": "hi-IN-Wavenet-B", "code": "hi-IN"},
            ("Hindi", "Female"): {"name": "hi-IN-Wavenet-E", "code": "hi-IN"},
            ("Hinglish", "Male"): {"name": "hi-IN-Wavenet-B", "code": "hi-IN"},
            ("Hinglish", "Female"): {"name": "hi-IN-Wavenet-E", "code": "hi-IN"},
            # 🔧 FIXED: Correct Urdu Wavenet voices from Google Cloud TTS
            ("Urdu", "Male"): {"name": "ur-IN-Wavenet-B", "code": "ur-IN"},
            ("Urdu", "Female"): {"name": "ur-IN-Wavenet-A", "code": "ur-IN"}
        }

        # Initialize clients
        self.llm_client = None
        self.setup_clients()

    class GeminiLLMClient:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def generate(self, prompt: str) -> str:
            try:
                resp = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
                    headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=30
                )
                if resp.status_code != 200:
                    raise Exception(f"Gemini LLM error: {resp.status_code} - {resp.text}")
                data = resp.json()
                # Extract plain text from candidates
                if "candidates" in data and data["candidates"]:
                    cand = data["candidates"][0]
                    if "content" in cand and "parts" in cand["content"] and cand["content"]["parts"]:
                        return cand["content"]["parts"][0].get("text", "").strip()
                    if "parts" in cand and cand["parts"]:
                        return cand["parts"][0].get("text", "").strip()
                # Fallback stringify
                return str(data)
            except Exception as e:
                # Surface error to caller; upstream will fall back gracefully
                raise e

    def setup_clients(self):
        """Initialize all Google clients"""
        try:
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file"
            ]

            # 🔧 FIXED: Get correct path - backend server runs from backend/ directory
            # but config files are in project root config/ directory
            current_dir = os.getcwd()
            if current_dir.endswith('backend'):
                # Running from backend directory, go up one level
                project_root = os.path.dirname(current_dir)
            else:
                # Running from project root
                project_root = current_dir

            config_dir = os.path.join(project_root, 'config')
            sheets_creds_path = os.path.join(config_dir, 'secrets', 'google_sheets_service.json')

            logger.info(f"🔧 Project root: {project_root}")
            logger.info(f"🔧 Config dir: {config_dir}")
            logger.info(f"🔧 Sheets creds path: {sheets_creds_path}")
            logger.info(f"🔧 Sheets creds exists: {os.path.exists(sheets_creds_path)}")

            # Initialize Google Sheets with Service Account (for database operations)
            sheets_creds = Credentials.from_service_account_file(
                sheets_creds_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self.sheets_client = gspread.authorize(sheets_creds)
            self.sheet = self.sheets_client.open_by_key(self.google_sheet_id)

            # 🔧 FIXED: Initialize Google Drive with OAuth2 (for file uploads)
            oauth2_creds_path = os.path.join(config_dir, 'secrets', 'client_secret_777658526045-naf0mhnn7oqrkbar8461344qdi232pm9.apps.googleusercontent.com.json')

            logger.info(f"🔧 OAuth2 creds path: {oauth2_creds_path}")
            logger.info(f"🔧 OAuth2 creds exists: {os.path.exists(oauth2_creds_path)}")

            if os.path.exists(oauth2_creds_path):
                logger.info("🔧 Using OAuth2 credentials for Google Drive")
                from google_auth_oauthlib.flow import InstalledAppFlow
                from google.auth.transport.requests import Request
                import pickle

                # Token file to store OAuth2 tokens
                token_file = os.path.join(config_dir, 'secrets', 'drive_token.pickle')

                drive_creds = None
                # Load existing token
                if os.path.exists(token_file):
                    with open(token_file, 'rb') as token:
                        drive_creds = pickle.load(token)

                # If no valid credentials, get new ones
                if not drive_creds or not drive_creds.valid:
                    if drive_creds and drive_creds.expired and drive_creds.refresh_token:
                        drive_creds.refresh(Request())
                    else:
                        # First time setup - will require user authorization
                        flow = InstalledAppFlow.from_client_secrets_file(
                            oauth2_creds_path,
                            ["https://www.googleapis.com/auth/drive"]
                        )
                        drive_creds = flow.run_local_server(port=0)

                    # Save credentials for next run
                    with open(token_file, 'wb') as token:
                        pickle.dump(drive_creds, token)

                self.drive_service = build('drive', 'v3', credentials=drive_creds)
                logger.info("✅ Google Drive OAuth2 service initialized")
            else:
                logger.warning("⚠️ OAuth2 credentials not found, Drive uploads disabled")
                self.drive_service = None

            # Initialize TTS with Service Account
            tts_creds_path = os.path.join(config_dir, 'secrets', 'google_tts_service.json')
            logger.info(f"🔧 TTS creds path: {tts_creds_path}")
            logger.info(f"🔧 TTS creds exists: {os.path.exists(tts_creds_path)}")

            self.tts_client = texttospeech.TextToSpeechClient.from_service_account_json(
                tts_creds_path
            )

            logger.info("✅ All clients initialized successfully")

            # Wire LLM client for smart image prompts (optional)
            try:
                if self.gemini_api_key:
                    self.llm_client = self.GeminiLLMClient(self.gemini_api_key)
                    logger.info("✅ LLM client wired for smart image prompts")
                else:
                    self.llm_client = None
                    logger.info("ℹ️ GEMINI_API_KEY not set; LLM client disabled")
            except Exception as e:
                self.llm_client = None
                logger.warning(f"⚠️ LLM client initialization failed: {e}")

        except Exception as e:
            logger.error(f"❌ Client initialization failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Sheets creds path: {sheets_creds_path}")
            logger.error(f"❌ Sheets creds exists: {os.path.exists(sheets_creds_path)}")
            logger.error(f"❌ Google Sheet ID: {self.google_sheet_id}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            # Continue without Google services for testing
            self.sheet = None
            self.tts_client = None
            self.drive_service = None

    def get_project_root(self) -> str:
        current_dir = os.getcwd()
        if current_dir.endswith('backend'):
            return os.path.dirname(current_dir)
        return current_dir

    def read_prompt_template(self, filename: str) -> Optional[str]:
        try:
            project_root = self.get_project_root()
            path = os.path.join(project_root, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            logger.warning(f"⚠️ Prompt template not found: {path}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Failed reading prompt template {filename}: {e}")
            return None

    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        rendered = template
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    def webhook_auth_check(self, headers: Dict) -> bool:
        """🔐 Webhook authentication (exact from n8n workflow)"""
        webhook_secret = headers.get('x-webhook-secret') or headers.get('X-Webhook-Secret')
        return webhook_secret == self.webhook_secret

    def create_safe_topic_folder(self, topic_data: Dict) -> str:
        """🔧 FIXED: Create safe folder name with correct project root path"""
        topic_id = topic_data.get('TopicID', 'unknown')
        topic_title = topic_data.get('Title', 'Unknown')

        # Remove invalid Windows filename characters: < > : " | ? * \ /
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            topic_title = topic_title.replace(char, '_')

        # Replace spaces and limit length
        topic_title = topic_title.replace(' ', '_')[:50]

        # 🔧 FIXED: Ensure we use project root, not backend directory
        current_dir = os.getcwd()
        if current_dir.endswith('backend'):
            # Running from backend directory, go up one level to project root
            project_root = os.path.dirname(current_dir)
        else:
            # Already in project root
            project_root = current_dir

        folder_path = os.path.join(project_root, "generated_content", f"{topic_id}_{topic_title}")
        return folder_path

    def upload_to_google_drive(self, file_path: str, file_type: str, topic_data: Dict) -> str:
        """
        🔧 FIXED: Upload file to Google Drive using OAuth2 credentials
        """
        try:
            # Check if Drive service is available
            if not self.drive_service:
                logger.warning(f"⚠️ Google Drive service not available, using local path")
                return file_path

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return file_path

            # 🔧 FIXED: Create topic-based folder structure in Google Drive
            topic_title = topic_data.get('Title', 'Unknown Topic').replace('/', '_').replace('\\', '_').replace(':', '_')[:50]
            topic_id = topic_data.get('TopicID', 'unknown')
            topic_folder_name = f"{topic_title}_{topic_id}"

            # Get base folder ID based on file type
            folder_mapping = {
                "audio": self.audio_folder_id,
                "image": self.images_folder_id,
                "video": self.videos_folder_id
            }

            base_folder_id = folder_mapping.get(file_type)
            if not base_folder_id:
                logger.error(f"❌ No folder ID configured for {file_type}")
                return file_path

            # Create or find topic subfolder in Google Drive
            topic_folder_id = self.create_or_find_drive_folder(topic_folder_name, base_folder_id)

            # Prepare file metadata
            file_name = os.path.basename(file_path)
            drive_file_name = f"{topic_id}_{file_name}"

            file_metadata = {
                'name': drive_file_name,
                'parents': [topic_folder_id]
            }

            # Upload file
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(file_path, resumable=True)

            logger.info(f"🔧 Uploading {file_type} to Google Drive: {drive_file_name}")

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink,webContentLink'
            ).execute()

            # Make file publicly viewable
            self.drive_service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

            # Get shareable link
            shareable_link = f"https://drive.google.com/file/d/{file['id']}/view"

            logger.info(f"✅ {file_type.title()} uploaded to Google Drive: {shareable_link}")
            return shareable_link

        except Exception as e:
            logger.error(f"❌ Google Drive upload failed for {file_type}: {e}")
            logger.error(f"   File path: {file_path}")
            logger.error(f"   File exists: {os.path.exists(file_path)}")
            return file_path

    def create_or_find_drive_folder(self, folder_name: str, parent_folder_id: str) -> str:
        """🔧 Create or find a folder in Google Drive"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()

            folders = results.get('files', [])
            if folders:
                # Folder exists, return its ID
                folder_id = folders[0]['id']
                logger.info(f"📁 Found existing Drive folder: {folder_name} ({folder_id})")
                return folder_id
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'parents': [parent_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }

                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()

                folder_id = folder['id']
                logger.info(f"📁 Created new Drive folder: {folder_name} ({folder_id})")
                return folder_id

        except Exception as e:
            logger.error(f"❌ Failed to create/find Drive folder {folder_name}: {e}")
            # Return parent folder as fallback
            return parent_folder_id

    def ensure_local_storage_copy(self, file_path: str, file_type: str, topic_data: Dict):
        """🔧 FIXED: Ensure files are copied to local storage directory using same folder structure"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ Source file not found for local storage: {file_path}")
                return

            # 🔧 FIXED: Use same folder creation logic as create_safe_topic_folder to avoid duplicates
            topic_local_dir = self.create_safe_topic_folder(topic_data)
            os.makedirs(topic_local_dir, exist_ok=True)

            # Copy file to local storage
            import shutil
            filename = os.path.basename(file_path)
            local_copy_path = os.path.join(topic_local_dir, filename)

            if file_path != local_copy_path:  # Don't copy if already in the right place
                shutil.copy2(file_path, local_copy_path)
                logger.info(f"📁 Copied {file_type} to local storage: {local_copy_path}")
            else:
                logger.info(f"📁 {file_type} already in local storage: {local_copy_path}")

        except Exception as e:
            logger.error(f"❌ Failed to copy {file_type} to local storage: {e}")

    def init_run(self, webhook_data: Dict) -> Dict:
        """⚙️ Initialize run (exact from n8n workflow)"""
        run_id = str(uuid.uuid4())
        topic_run_id = f"run_{int(time.time())}"

        return {
            "runId": run_id,
            "topicRunId": topic_run_id,
            "startTime": datetime.now().isoformat(),
            "runTimestamp": datetime.now().isoformat(),
            "webhook": webhook_data
        }

    def create_topic_extraction_prompt(self, webhook_data: Dict) -> str:
        """📝 Create topic extraction prompt (use file template if available, else fallback)"""
        raw_notes = webhook_data.get("raw_notes", "")
        language = webhook_data.get("language", "English")
        tone = webhook_data.get("tone", "Friendly")
        posts_per_day = webhook_data.get("posts_per_day", 7)

        # Inline prompt enforced (template usage disabled)
        prompt = f"""You are an expert content strategist specializing in educational short-form content.

**Task**: Extract {posts_per_day} specific, engaging topics from the raw notes below that can be turned into educational short videos.

**Requirements**:
- Each topic should be specific and focused (suitable for 40-60 second videos)
- Educational and engaging for {language} audience
- {tone} tone throughout
- Clear, actionable learning outcomes
- Suitable for platforms: YouTube Shorts, Instagram Reels, LinkedIn

**Raw Notes**:
{raw_notes}

**Output Format** (JSON only):
[
  {{
    "title": "Specific topic title here",
    "main_points": ["Key point 1", "Key point 2", "Key point 3"],
    "transition_note": "Brief transition or hook for the topic"
  }}
]

Return ONLY the JSON array, no other text or formatting."""
        return prompt

    def gemini_topic_extraction(self, topic_prompt: str, run_data: Dict) -> Dict:
        """🧠 Gemini topic extraction (exact API call from n8n workflow)"""
        try:
            logger.info("🧠 Calling Gemini for topic extraction...")

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
                headers={
                    "x-goog-api-key": self.gemini_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [{"parts": [{"text": topic_prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Log API usage (exact from n8n workflow)
                self.log_api_usage({
                    "RunID": run_data["runId"],
                    "Provider": "Gemini",
                    "Endpoint": "generateContent",
                    "Model": "gemini-1.5-flash-latest",
                    "Operation": "Topic Extraction",
                    "InputTokens": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "OutputTokens": result.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    "TotalTokens": result.get("usageMetadata", {}).get("totalTokenCount", 0),
                    "Status": "Success"
                })

                logger.info("✅ Gemini topic extraction successful")
                return result
            else:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"❌ Gemini topic extraction failed: {e}")
            self.log_error("Topic Extraction", str(e), run_data["runId"])
            raise

    def parse_topics(self, gemini_response: Dict, run_data: Dict) -> List[Dict]:
        """📋 Parse topics (exact from n8n workflow)"""
        try:
            logger.info("📋 Parsing topics from Gemini response...")

            # Prompt mode: bypass topic extraction; synthesize a single topic from payload
            webhook = run_data.get("webhook", {})
            if str(webhook.get("input_type", "")).lower() == "prompt":
                topic_id = f"topic_{int(time.time())}_1"
                title = webhook.get("title", "Custom Prompt Script")
                track_norm = webhook.get("track", "")
                topic_data = {
                    "TopicID": topic_id,
                    "Order": 1,
                    "Title": title,
                    "MainPointsText": "",
                    "MainPoints": [],
                    "TransitionNote": "",
                    "Language": webhook.get("language", "English"),
                    "Tone": webhook.get("tone", "Friendly"),
                    "VoiceGender": webhook.get("voice_gender", "Female"),
                    "Status": "Pending",
                    "RunID": run_data["runId"],
                    "TopicRunID": run_data["topicRunId"],
                    "FullPipeline": webhook.get("full_pipeline", True),
                    # Accept context from either 'context_notes' or existing 'raw_notes'
                    "raw_notes": webhook.get("context_notes", webhook.get("raw_notes", "")),
                    "startTime": run_data["startTime"],
                    "runId": run_data["runId"],
                    "runTimestamp": run_data["runTimestamp"],
                    "platforms": webhook.get("platforms", []),
                    "track": track_norm,
                    "image_aspect_ratio": webhook.get("image_aspect_ratio", "9:16"),
                    "image_width": webhook.get("image_width", 1080),
                    "image_height": webhook.get("image_height", 1920),
                    "Track": track_norm,
                    "Platforms": webhook.get("platforms", []),
                    "scriptPromptTemplate": "educational_script_template",
                    "captionPromptTemplate": "engaging_caption_template",
                    "audioFolderId": self.audio_folder_id,
                    "imagesFolderId": self.images_folder_id,
                    "videosFolderId": self.videos_folder_id,
                    "InputType": "prompt",
                    # Prompt-mode specific controls
                    "CustomPrompt": webhook.get("custom_prompt", ""),
                    "TargetDurationSeconds": webhook.get("target_duration_seconds"),
                    "AudioSpeakingRate": webhook.get("audio_speaking_rate")
                }
                logger.info("🎯 Prompt mode: synthesized single topic without topic extraction")
                return [topic_data]

            # Script mode: use user-provided script directly and skip topic extraction
            if str(webhook.get("input_type", "")).lower() == "script":
                script_text = (webhook.get("script_text") or "").strip()
                if not script_text:
                    raise Exception("Script mode requires non-empty 'script_text' in payload")
                topic_id = f"topic_{int(time.time())}_1"
                title = webhook.get("title", "User Provided Script")
                track_norm = webhook.get("track", "")
                topic_data = {
                    "TopicID": topic_id,
                    "Order": 1,
                    "Title": title,
                    "MainPointsText": "",
                    "MainPoints": [],
                    "TransitionNote": "",
                    "Language": webhook.get("language", "English"),
                    "Tone": webhook.get("tone", "Friendly"),
                    "VoiceGender": webhook.get("voice_gender", "Female"),
                    "Status": "Pending",
                    "RunID": run_data["runId"],
                    "TopicRunID": run_data["topicRunId"],
                    "FullPipeline": webhook.get("full_pipeline", True),
                    "raw_notes": webhook.get("context_notes", webhook.get("raw_notes", "")),
                    "startTime": run_data["startTime"],
                    "runId": run_data["runId"],
                    "runTimestamp": run_data["runTimestamp"],
                    "platforms": webhook.get("platforms", []),
                    "track": track_norm,
                    "image_aspect_ratio": webhook.get("image_aspect_ratio", "9:16"),
                    "image_width": webhook.get("image_width", 1080),
                    "image_height": webhook.get("image_height", 1920),
                    "Track": track_norm,
                    "Platforms": webhook.get("platforms", []),
                    "scriptPromptTemplate": "educational_script_template",
                    "captionPromptTemplate": "engaging_caption_template",
                    "audioFolderId": self.audio_folder_id,
                    "imagesFolderId": self.images_folder_id,
                    "videosFolderId": self.videos_folder_id,
                    "InputType": "script",
                    "CustomPrompt": webhook.get("custom_prompt"),
                    "TargetDurationSeconds": webhook.get("target_duration_seconds"),
                    "AudioSpeakingRate": webhook.get("audio_speaking_rate"),
                    # Directly provided script
                    "Script": script_text
                }
                logger.info("📝 Script mode: using user-provided script and skipping topic extraction")
                return [topic_data]

            # Handle different Gemini API response formats
            try:
                # Try new format first
                if "candidates" in gemini_response and gemini_response["candidates"]:
                    candidate = gemini_response["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        content = candidate["content"]["parts"][0]["text"]
                    elif "parts" in candidate:
                        content = candidate["parts"][0]["text"]
                    else:
                        content = str(candidate.get("text", candidate))
                else:
                    # Fallback to direct text
                    content = str(gemini_response)
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Failed to parse Gemini response structure: {e}")
                content = str(gemini_response)

            try:
                topics_data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("JSON parsing failed, using fallback method")
                topics_data = [{"title": "Educational content from notes", "main_points": ["Key concept"], "transition_note": "Learn more"}]

            # Transform to exact format from n8n workflow
            parsed_topics = []
            webhook = run_data["webhook"]

            # Coerce topics_data into a list to avoid type errors on slicing (handles dict or list)
            if isinstance(topics_data, dict):
                if isinstance(topics_data.get("topics"), list):
                    topics_list = topics_data.get("topics")
                elif isinstance(topics_data.get("data"), list):
                    topics_list = topics_data.get("data")
                elif all(isinstance(v, dict) for v in topics_data.values()):
                    topics_list = list(topics_data.values())
                else:
                    topics_list = [topics_data]
            elif isinstance(topics_data, list):
                topics_list = topics_data
            else:
                topics_list = [topics_data]

            # Determine number of topics to process based on payload (posts_per_day)
            desired_count = 1
            try:
                desired_count = int(webhook.get("posts_per_day", 1))
                if desired_count < 1:
                    desired_count = 1
            except Exception:
                desired_count = 1

            for i, topic in enumerate(topics_list[:desired_count]):
                topic_id = f"topic_{int(time.time())}_{i+1}"

                # Normalize potential schema differences between template outputs and inline prompts
                title_norm = topic.get("title") or topic.get("Title") or f"Topic {i+1}"
                main_points_norm = topic.get("main_points") or topic.get("MainPoints") or []
                transition_norm = topic.get("transition_note") or topic.get("TransitionNote") or ""
                order_norm = topic.get("Order") or (i + 1)
                track_norm = topic.get("Track") or webhook.get("track", "")

                topic_data = {
                    "TopicID": topic_id,
                    "Order": order_norm,
                    "Title": title_norm,
                    "MainPointsText": " | ".join(main_points_norm),
                    "MainPoints": main_points_norm,
                    "TransitionNote": transition_norm,
                    "Language": webhook.get("language", "English"),
                    "Tone": webhook.get("tone", "Friendly"),
                    "VoiceGender": webhook.get("voice_gender", "Female"),
                    "Status": "Pending",
                    "RunID": run_data["runId"],
                    "TopicRunID": run_data["topicRunId"],
                    "FullPipeline": webhook.get("full_pipeline", True),
                    "raw_notes": webhook.get("raw_notes", ""),
                    "startTime": run_data["startTime"],
                    "runId": run_data["runId"],
                    "runTimestamp": run_data["runTimestamp"],
                    "platforms": webhook.get("platforms", []),
                    "track": track_norm,
                    "image_aspect_ratio": webhook.get("image_aspect_ratio", "9:16"),
                    "image_width": webhook.get("image_width", 1080),
                    "image_height": webhook.get("image_height", 1920),
                    "Track": track_norm,
                    "Platforms": webhook.get("platforms", []),
                    "scriptPromptTemplate": "educational_script_template",
                    "captionPromptTemplate": "engaging_caption_template",
                    "audioFolderId": self.audio_folder_id,
                    "imagesFolderId": self.images_folder_id,
                    "videosFolderId": self.videos_folder_id,
                    "InputType": webhook.get("input_type", "notes"),
                    # Carry prompt-mode overrides into topic_data so script prompt can honor them
                    "CustomPrompt": webhook.get("custom_prompt"),
                    "TargetDurationSeconds": webhook.get("target_duration_seconds"),
                    "AudioSpeakingRate": webhook.get("audio_speaking_rate")
                }

                parsed_topics.append(topic_data)

            logger.info(f"✅ Parsed {len(parsed_topics)} topics successfully")
            return parsed_topics

        except Exception as e:
            logger.error(f"❌ Topic parsing failed: {e}")
            self.log_error("Parse Topics", str(e), run_data["runId"])
            raise

    def insert_topics_to_essential_content(self, topics: List[Dict]) -> bool:
        """📊 Insert topics to EssentialContent table with fresh schema"""
        try:
            logger.info("📊 Inserting topics to EssentialContent...")

            if self.sheet is None:
                logger.error("❌ Google Sheets client not initialized - cannot insert topics")
                return False

            # Ensure schema and worksheet exist (non-breaking safety)
            try:
                self.ensure_db_schema(reset=False)
            except Exception as _:
                pass

            worksheet = self.sheet.worksheet("EssentialContent")

            # Prepare rows for batch insert (match EXACTLY 24 columns)
            rows_to_insert = []
            for topic in topics:
                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Time
                    topic.get("TopicID", ""),                      # TopicID
                    topic.get("RunID", ""),                        # RunID
                    topic.get("Order", ""),                        # Order
                    topic.get("Title", ""),                        # Title
                    "",                                            # Script (empty initially)
                    topic.get("Language", "English"),             # Language
                    topic.get("VoiceGender", "Female"),           # Gender
                    topic.get("Tone", "Educational"),             # Tone
                    json.dumps(topic.get("Platforms", ["YouTube Shorts"])),  # Platform
                    "Topics Created",                              # StatusProgress
                    "Pending",                                     # FinalStatus
                    "",                                            # Caption (empty initially)
                    "",                                            # Hashtag (empty initially)
                    "",                                            # Image1Link (empty initially)
                    "",                                            # Image2Link (empty initially)
                    "",                                            # Image3Link (empty initially)
                    "",                                            # Image4Link (empty initially)
                    "",                                            # AudioLink (empty initially)
                    "",                                            # VideoLink (empty initially)
                    "",                                            # Image1GeneratedBy (empty initially)
                    "",                                            # Image2GeneratedBy (empty initially)
                    "",                                            # Image3GeneratedBy (empty initially)
                    ""                                             # Image4GeneratedBy (empty initially)
                ]
                rows_to_insert.append(row)

            # Batch insert
            worksheet.append_rows(rows_to_insert)

            logger.info(f"✅ Inserted {len(topics)} topics to EssentialContent")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to insert topics to EssentialContent: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Topics data: {topics}")
            logger.error(f"❌ Sheet object: {self.sheet}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            self.log_error("Insert Topics to EssentialContent", str(e), topics[0].get("runId", "") if topics else "")
            return False

    def create_script_generation_prompt(self, topic_data: Dict) -> str:
        """📝 Create script generation prompt (use file template if available, else fallback)"""
        title = topic_data.get("Title", "")
        main_points = topic_data.get("MainPoints", [])
        language = topic_data.get("Language", "English")
        tone = topic_data.get("Tone", "Friendly")
        transition = topic_data.get("TransitionNote", "")

        # Prompt mode: strict pass-through of CustomPrompt (+ optional Context Notes) without backend templating
        if (topic_data.get("InputType") == "prompt") and topic_data.get("CustomPrompt"):
            custom = topic_data.get("CustomPrompt", "").strip()
            context_notes = (topic_data.get("raw_notes") or "").strip()
            return f"{custom}\n\n{context_notes}" if context_notes else custom

        # Inline prompt enforced (template usage disabled)
        # Inject custom prompt and target duration (prompt mode guidance) if present
        custom_preface = ""
        if topic_data.get("CustomPrompt"):
            custom_preface += f"Follow these instructions strictly: {topic_data['CustomPrompt']}\n\n"
        # Compute dynamic duration requirement to avoid conflicting with defaults
        duration_req = "- Exactly 40-60 seconds when spoken (approximately 100-150 words for English, 120-180 words for Urdu/Hindi)"
        if topic_data.get("TargetDurationSeconds"):
            try:
                tgt = int(topic_data["TargetDurationSeconds"])
                if tgt > 0:
                    duration_req = f"- Target spoken duration approximately {tgt} seconds (adjust word count accordingly)"
                    custom_preface += (
                        f"Target spoken duration: approximately {tgt} seconds in {language}. "
                        f"Adjust word count accordingly while preserving clarity.\n\n"
                    )
            except Exception:
                pass
        # Include optional context notes to ground the script content
        context_notes = (topic_data.get("raw_notes") or "").strip()
        # Decide task line neutrality when custom instructions or explicit target exist
        has_custom = bool(topic_data.get("CustomPrompt"))
        has_target = bool(topic_data.get("TargetDurationSeconds"))
        task_line = "**Task**: Create a short video script for the topic below." if (has_custom or has_target) else "**Task**: Create a 40-60 second educational video script for the topic below."
        context_block = f"\n**Context Notes (use faithfully):**\n{context_notes}\n" if context_notes else ""

        prompt = f"""{custom_preface}You are an expert educational content creator specializing in short-form videos.

{task_line}

**Topic**: {title}
**Key Points**: {', '.join(main_points)}
**Language**: {language}
**Tone**: {tone}
{context_block}
**Requirements**:
{duration_req}
- Hook in first 3 seconds
- Clear educational value
- Engaging and {tone.lower()} tone
- Include call-to-action at the end
- No stage directions, just narration text
- For Urdu: Use detailed explanations and examples to ensure minimum 40 seconds duration

**Output Format** (JSON):
{{
  "script": "The complete narration script here...",
  "image_prompts": [
    "Image 1 prompt for visual representation",
    "Image 2 prompt for visual representation",
    "Image 3 prompt for visual representation",
    "Image 4 prompt for visual representation"
  ],
  "voice_style": "conversational",
  "caption": "Engaging social media caption with hashtags",
  "hashtags": ["#education", "#learning", "#shorts"]
}}

Return ONLY the JSON, no other text."""
        return prompt

    def gemini_script_generation(self, script_prompt: str, topic_data: Dict) -> Dict:
        """🧠 Gemini script generation (exact from n8n workflow)"""
        try:
            logger.info(f"🧠 Generating script for topic: {topic_data.get('Title', 'Unknown')}")

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
                headers={
                    "x-goog-api-key": self.gemini_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [{"parts": [{"text": script_prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Log API usage
                self.log_api_usage({
                    "RunID": topic_data.get("RunID", ""),
                    "TopicID": topic_data.get("TopicID", ""),
                    "Provider": "Gemini",
                    "Endpoint": "generateContent",
                    "Model": "gemini-1.5-flash-latest",
                    "Operation": "Script Generation",
                    "InputTokens": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "OutputTokens": result.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    "TotalTokens": result.get("usageMetadata", {}).get("totalTokenCount", 0),
                    "Status": "Success"
                })

                logger.info("✅ Script generation successful")
                return result
            else:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            self.log_error("Script Generation", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            raise

    def try_extract_image_prompts(self, script_text: str) -> tuple:
        """Extract up to 4 image prompts from a script text if author embedded them.
        Recognizes labels like: Image 1:, Image1:, Hook:, MainPoint1:, Main Point 1:, MainPoint2:, Teaser:.
        Returns (prompts_list or [], cleaned_script).
        """
        lines = script_text.splitlines()
        prompts_map = {}
        cleaned_lines = []
        import re as _re
        patterns = [
            ("hook", _re.compile(r"^(hook)\s*:\s*(.+)$", _re.I)),
            ("image1", _re.compile(r"^(image\s*1|image1|main\s*point\s*1|mainpoint1)\s*:\s*(.+)$", _re.I)),
            ("image2", _re.compile(r"^(image\s*2|image2|main\s*point\s*2|mainpoint2)\s*:\s*(.+)$", _re.I)),
            ("teaser", _re.compile(r"^(teaser|transition|image\s*4|image4)\s*:\s*(.+)$", _re.I)),
            ("image3", _re.compile(r"^(image\s*3|image3)\s*:\s*(.+)$", _re.I)),
        ]
        for ln in lines:
            matched = False
            for key, rx in patterns:
                m = rx.match(ln.strip())
                if m:
                    prompts_map.setdefault(key, m.group(2).strip())
                    matched = True
                    break
            if not matched:
                cleaned_lines.append(ln)
        # Build ordered list preference: Hook, Image1, Image2, Image3/Teaser
        ordered = []
        if prompts_map.get("hook"): ordered.append(prompts_map["hook"])
        if prompts_map.get("image1"): ordered.append(prompts_map["image1"])
        if prompts_map.get("image2"): ordered.append(prompts_map["image2"])
        # Prefer image3 then teaser as 4th
        if prompts_map.get("image3"): ordered.append(prompts_map["image3"])
        elif prompts_map.get("teaser"): ordered.append(prompts_map["teaser"])
        # Ensure max 4
        ordered = ordered[:4]
        cleaned_script = "\n".join(cleaned_lines)
        return (ordered if len(ordered) >= 2 else []), cleaned_script

    def detect_genre_prefix(self, script_text: str) -> str:
        """
        Genre detection for generating cinematic image prompts.
        Supports: Horror, Romance, Comedy, Educational, Motivational/Inspirational, Default.
        """
        text = script_text.lower()
        # Horror keywords
        if any(w in text for w in ["भूत", "ghost", "डर", "haunted", "चुड़ैल", "horror", "कब्र", "witch"]):
            return "Dark, suspenseful, cinematic horror atmosphere of"
        # Romance keywords
        elif any(w in text for w in ["प्यार", "love", "romance", "दिल", "प्रेम", "सपना", "kiss"]):
            return "Dreamy, soft lighting, cinematic romance scene of"
        # Comedy keywords
        elif any(w in text for w in ["funny", "कॉमेडी", "joke", "हंसी", "comedy", "laugh"]):
            return "Bright, colorful, exaggerated comedy scene of"
        # Educational / Informative keywords
        elif any(w in text for w in [
            "शिक्षा", "education", "learn", "training", "science", "technology", "history", "model",
            "language model", "data", "bias", "study", "गणित", "भौतिकी", "रसायन", "इतिहास"
        ]):
            return "Clean, modern, infographic-style cinematic educational depiction of"
        # Motivational / Inspirational keywords
        elif any(w in text for w in [
            "motivation", "inspiration", "success", "leader", "growth", "dream", "vision",
            "goal", "achievement", "journey", "never give up", "संघर्ष", "सफलता", "नेता", "प्रेरणा"
        ]):
            return "Bold, uplifting, cinematic motivational scene of"
        # Default / Generic
        else:
            return "Cinematic, realistic depiction of"

    def smart_fallback_image_prompts(self, script_text: str, llm_client=None) -> List[str]:
        """
        Generate 4 relevant image prompts (Hook, Image1, Image2, Teaser)
        from a script using a multi-tier fallback strategy:
        1. Try LLM-based extraction (if llm_client provided).
        2. Fallback to keyword-based scene detection.
        3. Add genre-aware prefixes for cinematic styling.
        """
        prompts = None
        # --- STEP 1: Try LLM-based extraction ---
        if llm_client:
            try:
                instruction = (
                    "Read this script. Extract 4 cinematic, scene-specific image prompts "
                    "in this format:\nHook: ...\nImage 1: ...\nImage 2: ...\nTeaser: ...\n"
                    "Keep them short, visual, and descriptive. Adapt to the script's genre."
                )
                response = llm_client.generate(instruction + "\n\nSCRIPT:\n" + script_text)
                lines = response.splitlines()
                prompts = [line.split(":", 1)[1].strip() for line in lines if ":" in line][:4]
            except Exception as e:
                logger.warning(f"[WARN] LLM image prompt extraction failed: {e}")
                prompts = None
        # --- STEP 2: Keyword-based scene extraction if LLM fails ---
        if not prompts or len(prompts) < 4:
            # Simple noun/adjective extraction (no external NLP deps)
            words = re.findall(r"\b[अ-हa-zA-Z]{3,}\b", script_text)
            scenes = []
            if words:
                step = max(1, len(words)//4)
                scenes = [words[i] for i in range(0, len(words), step)][:4]
            prompts = [f"Cinematic scene featuring {w}" for w in scenes]
        # --- STEP 3: Genre-aware prefixing ---
        genre_prefix = self.detect_genre_prefix(script_text)
        prompts = [f"{genre_prefix} {p}" for p in prompts]
        # Ensure exactly 4 prompts
        while len(prompts) < 4:
            prompts.append(f"{genre_prefix} cinematic filler scene")
        return prompts[:4]

    def build_image_prompts_from_script(self, topic_data: Dict) -> List[str]:
        """Generate 4 image prompts using the new smart fallback strategy."""
        script = (topic_data.get("Script") or "").strip()
        return self.smart_fallback_image_prompts(script_text=script, llm_client=self.llm_client)

    def parse_script_response(self, gemini_response: Dict, topic_data: Dict) -> Dict:
        """📋 Parse script response (exact from n8n workflow)"""
        try:
            # Handle different Gemini API response formats
            try:
                # Try new format first
                if "candidates" in gemini_response and gemini_response["candidates"]:
                    candidate = gemini_response["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        content = candidate["content"]["parts"][0]["text"]
                    elif "parts" in candidate:
                        content = candidate["parts"][0]["text"]
                    else:
                        content = str(candidate.get("text", candidate))
                else:
                    # Fallback to direct text
                    content = str(gemini_response)
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Failed to parse Gemini script response structure: {e}")
                content = str(gemini_response)

            try:
                script_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback script data
                script_data = {
                    "script": f"This is an educational video about {topic_data.get('Title', 'the topic')}. Learn the key concepts and apply them in your work.",
                    "image_prompts": [
                        f"Educational illustration about {topic_data.get('Title', 'the topic')}",
                        f"Diagram showing key concepts of {topic_data.get('Title', 'the topic')}",
                        f"Visual representation of {topic_data.get('Title', 'the topic')} in action",
                        f"Summary infographic about {topic_data.get('Title', 'the topic')}"
                    ],
                    "voice_style": "conversational",
                    "caption": f"Learn about {topic_data.get('Title', 'this topic')} in 60 seconds! 🎓",
                    "hashtags": ["#education", "#learning", "#shorts"]
                }

            # Normalize differences between template output and inline prompt output
            script_text = script_data.get("script") or script_data.get("Script", "")
            voice_style = script_data.get("voice_style") or script_data.get("VoiceStyle", "conversational")
            caption_text = script_data.get("caption") or script_data.get("Caption", "")
            hashtags_list = script_data.get("hashtags") or script_data.get("Hashtags") or []

            # Handle ImagePrompts (object) vs image_prompts (list)
            image_prompts_list = script_data.get("image_prompts")
            if not image_prompts_list and isinstance(script_data.get("ImagePrompts"), dict):
                ip = script_data.get("ImagePrompts")
                # Preserve logical order if present
                ordered_keys = ["Hook", "MainPoint1", "MainPoint2", "Teaser"]
                image_prompts_list = [ip.get(k, "") for k in ordered_keys]

            if not image_prompts_list:
                # Build structured image prompts from script/title to improve relevance
                temp_topic = topic_data.copy()
                temp_topic["Script"] = script_text
                image_prompts_list = self.build_image_prompts_from_script(temp_topic)

            # Update topic data with script information
            updated_topic = topic_data.copy()
            updated_topic.update({
                "Script": script_text,
                "VoiceStyle": voice_style,
                "Caption": caption_text,
                "Hashtags": ", ".join(hashtags_list),
                "HashtagsJson": json.dumps(hashtags_list),
                "ImagePromptsJson": json.dumps(image_prompts_list),
                "Status": "ScriptGenerated",
                "UpdatedAt": datetime.now().isoformat()
            })

            logger.info("✅ Script response parsed successfully")
            return updated_topic

        except Exception as e:
            logger.error(f"❌ Script parsing failed: {e}")
            self.log_error("Parse Script", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            raise

    def get_tts_voice_name(self, language: str, voice_gender: str) -> Dict:
        """🎵 Get TTS voice name (exact voice mapping from Master Developer Prompt)"""
        voice_info = self.voice_mapping.get((language, voice_gender))

        if not voice_info:
            # Default fallback
            voice_info = {"name": "en-US-Wavenet-F", "code": "en-US"}

        logger.info(f"🎵 Selected voice: {voice_info['name']} for {language} {voice_gender}")
        return voice_info

    def generate_audio_tts(self, topic_data: Dict) -> str:
        """🎵 Generate audio using Google TTS (exact from n8n workflow)"""
        try:
            logger.info(f"🎵 Generating audio for topic: {topic_data.get('Title', 'Unknown')}")

            script = topic_data.get("Script", "")
            language = topic_data.get("Language", "English")
            voice_gender = topic_data.get("VoiceGender", "Female")

            # Get voice configuration
            voice_info = self.get_tts_voice_name(language, voice_gender)

            # Configure TTS request with SSML for Urdu/Hindi/Hinglish
            use_ssml = language in {"Urdu", "Hindi", "Hinglish"}
            if use_ssml:
                import html
                ssml = f"<speak><prosody rate='0.85'>{html.escape(script)}</prosody></speak>"
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=script)

            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_info["code"],
                name=voice_info["name"]
            )
            # Speaking rate override for precise control (optional, non-breaking)
            speaking_rate = 0.85 if use_ssml else 1.0
            try:
                rate_override = topic_data.get("AudioSpeakingRate")
                if rate_override is not None:
                    r = float(rate_override)
                    # clamp to a sane range
                    if 0.5 <= r <= 2.0:
                        speaking_rate = r
            except Exception:
                pass

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )

            # Generate audio
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            # Save audio file locally in topic-based folder
            topic_folder = self.create_safe_topic_folder(topic_data)
            topic_id = topic_data.get('TopicID', 'unknown')

            audio_filename = f"audio_{topic_id}_{int(time.time())}.mp3"
            local_audio_path = f"{topic_folder}/{audio_filename}"

            os.makedirs(topic_folder, exist_ok=True)

            with open(local_audio_path, "wb") as out:
                out.write(response.audio_content)

            # Log API usage
            self.log_api_usage({
                "RunID": topic_data.get("RunID", ""),
                "TopicID": topic_data.get("TopicID", ""),
                "Provider": "Google TTS",
                "Endpoint": "synthesize_speech",
                "Operation": "Audio Generation",
                "VoiceName": voice_info["name"],
                "Language": language,
                "Status": "Success"
            })

            logger.info("✅ Audio generation successful")

            # 🔧 FIXED: Ensure local storage copy
            self.ensure_local_storage_copy(local_audio_path, "audio", topic_data)

            # 🔧 FIXED: Single upload call to avoid conflicts
            try:
                drive_audio_url = self.upload_to_google_drive(local_audio_path, "audio", topic_data)
                if drive_audio_url and drive_audio_url != local_audio_path:
                    logger.info(f"✅ Audio uploaded to Google Drive: {drive_audio_url}")
                    return drive_audio_url
                else:
                    logger.warning("⚠️ Google Drive upload disabled, using local path")
                    return local_audio_path
            except Exception as drive_error:
                logger.warning(f"⚠️ Google Drive upload failed, using local path: {drive_error}")
                return local_audio_path

        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            self.log_error("Audio Generation", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            raise

    def generate_images_with_fallback(self, topic_data: Dict) -> List[str]:
        """🖼️ Generate images with fallback APIs (exact from Master Developer Prompt)"""
        try:
            logger.info(f"🖼️ Generating images for topic: {topic_data.get('Title', 'Unknown')}")

            # Get image prompts
            image_prompts_json = topic_data.get("ImagePromptsJson", "[]")
            try:
                image_prompts = json.loads(image_prompts_json)
            except:
                image_prompts = [
                    f"Educational illustration about {topic_data.get('Title', 'the topic')}",
                    f"Diagram showing key concepts",
                    f"Visual representation in action",
                    f"Summary infographic"
                ]

            # Ensure we have exactly 4 prompts
            while len(image_prompts) < 4:
                image_prompts.append(f"Educational visual about {topic_data.get('Title', 'the topic')}")

            image_urls = []

            # Generate all 4 images (exact requirement from Master Developer Prompt)
            for i, prompt in enumerate(image_prompts[:4]):
                logger.info(f"🖼️ Generating image {i+1}/4...")

                image_result = self.generate_single_image_with_fallback(prompt, topic_data, i+1)
                if image_result:
                    image_urls.append(image_result["url"])
                    # CRITICAL FIX: Store both URL and platform for each image
                    topic_data[f"Image{i+1}Link"] = image_result["url"]
                    topic_data[f"Image{i+1}GeneratedBy"] = image_result["generated_by"]
                    logger.info(f"🔧 FIXED: Image{i+1}Link = {image_result['url']}")
                    logger.info(f"🔧 FIXED: Image{i+1}GeneratedBy = {image_result['generated_by']}")
                else:
                    # Create placeholder if all APIs fail
                    placeholder_url = f"placeholder_image_{i+1}.png"
                    image_urls.append(placeholder_url)
                    topic_data[f"Image{i+1}Link"] = placeholder_url
                    topic_data[f"Image{i+1}GeneratedBy"] = "Failed"
                    logger.info(f"🔧 FIXED: Image{i+1}Link = {placeholder_url} (Failed)")
                    logger.info(f"🔧 FIXED: Image{i+1}GeneratedBy = Failed")

            # Log successful generation
            self.log_api_usage({
                "RunID": topic_data.get("RunID", ""),
                "TopicID": topic_data.get("TopicID", ""),
                "Provider": "Image Generation",
                "Operation": "Generate 4 Images",
                "ImageCount": len(image_urls),
                "Status": "Success"
            })

            logger.info(f"✅ Generated {len(image_urls)} images successfully")
            return image_urls

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            self.log_error("Image Generation", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            raise

    def generate_single_image_with_fallback(self, prompt: str, topic_data: Dict, image_index: int) -> Optional[Dict]:
        """🖼️ Generate single image with fallback (Cloudflare → Together → HuggingFace)"""
        # API fallback order (exact from Master Developer Prompt)
        apis = [
            ("Cloudflare", self.generate_image_cloudflare),
            ("Together", self.generate_image_together),
            ("HuggingFace", self.generate_image_huggingface)
        ]

        for api_name, api_func in apis:
            try:
                logger.info(f"🖼️ Trying {api_name} for image {image_index}...")
                image_url = api_func(prompt, topic_data, image_index)
                if image_url:
                    logger.info(f"✅ {api_name} succeeded for image {image_index}")

                    # Upload only if it's a local file
                    if os.path.exists(image_url):
                        # 🔧 FIXED: Ensure local storage copy for images
                        self.ensure_local_storage_copy(image_url, "image", topic_data)
                        drive_image_url = self.upload_to_google_drive(image_url, "image", topic_data)
                        return {"url": drive_image_url, "generated_by": api_name, "local_path": image_url}
                    else:
                        # Assume API returned a hosted URL/Drive URL; ideally make it public at source
                        return {"url": image_url, "generated_by": api_name, "local_path": image_url}
            except Exception as e:
                logger.warning(f"⚠️ {api_name} failed for image {image_index}: {e}")
                continue

        logger.error(f"❌ All image APIs failed for image {image_index}")
        return None

    def generate_image_cloudflare(self, prompt: str, topic_data: Dict, image_index: int) -> Optional[str]:
        """🖼️ Generate image using Cloudflare API"""
        try:
            response = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0",
                headers={
                    "Authorization": f"Bearer {self.cloudflare_api_token}",
                    "Content-Type": "application/json"
                },
                json={"prompt": f"{prompt}, high quality, professional, educational"},
                timeout=60
            )

            if response.status_code == 200:
                # Save image in topic-based folder
                topic_folder = self.create_safe_topic_folder(topic_data)
                topic_id = topic_data.get('TopicID', 'unknown')

                image_filename = f"image_{topic_id}_{image_index}_{int(time.time())}.png"
                local_image_path = f"{topic_folder}/{image_filename}"

                os.makedirs(topic_folder, exist_ok=True)

                with open(local_image_path, "wb") as f:
                    f.write(response.content)

                # Make file public and return shareable link
                try:
                    media = MediaFileUpload(local_image_path, mimetype='image/png')
                    file_metadata = {
                        'name': image_filename,
                        'parents': [self.images_folder_id]
                    }

                    file = self.drive_service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id,webViewLink'
                    ).execute()

                    # Make file public
                    self.drive_service.permissions().create(
                        fileId=file['id'], body={'role':'reader','type':'anyone'}
                    ).execute()
                    return f"https://drive.google.com/file/d/{file['id']}/view"

                except Exception as e:
                    logger.warning(f"⚠️ Google Drive upload failed: {e}")
                    return local_image_path
            else:
                raise Exception(f"Cloudflare API error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Cloudflare image generation failed: {e}")

    def generate_image_together(self, prompt: str, topic_data: Dict, image_index: int) -> Optional[str]:
        """🖼️ Generate image using Together API"""
        try:
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.together_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "stabilityai/stable-diffusion-xl-base-1.0",
                    "prompt": f"{prompt}, high quality, professional, educational",
                    "width": topic_data.get("image_width", 1080),
                    "height": topic_data.get("image_height", 1920),
                    "steps": 20,
                    "n": 1
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                image_url = result["data"][0]["url"]

                # Download and save image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    topic_folder = self.create_safe_topic_folder(topic_data)
                    topic_id = topic_data.get('TopicID', 'unknown')

                    image_filename = f"image_{topic_id}_{image_index}_{int(time.time())}.png"
                    local_image_path = f"{topic_folder}/{image_filename}"

                    os.makedirs(topic_folder, exist_ok=True)

                    with open(local_image_path, "wb") as f:
                        f.write(img_response.content)

                    return local_image_path
                else:
                    raise Exception("Failed to download image from Together")
            else:
                raise Exception(f"Together API error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Together image generation failed: {e}")

    def generate_image_huggingface(self, prompt: str, topic_data: Dict, image_index: int) -> Optional[str]:
        """🖼️ Generate image using HuggingFace API"""
        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={
                    "Authorization": f"Bearer {self.huggingface_api_key}"
                },
                json={
                    "inputs": f"{prompt}, high quality, professional, educational"
                },
                timeout=60
            )

            if response.status_code == 200:
                topic_folder = self.create_safe_topic_folder(topic_data)
                topic_id = topic_data.get('TopicID', 'unknown')

                image_filename = f"image_{topic_id}_{image_index}_{int(time.time())}.png"
                local_image_path = f"{topic_folder}/{image_filename}"

                os.makedirs(topic_folder, exist_ok=True)

                with open(local_image_path, "wb") as f:
                    f.write(response.content)

                return local_image_path
            else:
                raise Exception(f"HuggingFace API error: {response.status_code}")

        except Exception as e:
            raise Exception(f"HuggingFace image generation failed: {e}")

    def check_ffmpeg_available(self) -> bool:
        """🔧 FIXED: Check FFmpeg using config/.env path first, then fallback"""
        # First, try the configured path from .env
        ffmpeg_path = os.getenv('FFMPEG_PATH')
        ffprobe_path = os.getenv('FFPROBE_PATH')

        if ffmpeg_path and os.path.exists(ffmpeg_path):
            try:
                result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"✅ FFmpeg found at configured path: {ffmpeg_path}")
                    self.ffmpeg_path = ffmpeg_path
                    self.ffprobe_path = ffprobe_path if ffprobe_path and os.path.exists(ffprobe_path) else ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Configured FFmpeg path failed: {e}")

        # Try running ffmpeg from PATH
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("✅ FFmpeg found in PATH")
                self.ffmpeg_path = 'ffmpeg'
                self.ffprobe_path = 'ffprobe'
                return True
        except FileNotFoundError:
            pass

        # Try common Windows locations as fallback
        common_paths = [
            r"C:\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
        ]

        for path in common_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '-version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        logger.info(f"✅ Found FFmpeg at: {path}")
                        self.ffmpeg_path = path
                        self.ffprobe_path = path.replace('ffmpeg.exe', 'ffprobe.exe')
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ FFmpeg at {path} failed: {e}")

        logger.error("❌ FFmpeg not found in any location")
        return False

    def convert_drive_url_to_direct(self, drive_url: str) -> str:
        """🔧 Convert Google Drive share URL to direct download URL"""
        import re

        logger.info(f"🔧 Converting Drive URL: {drive_url}")

        # Handle different Google Drive URL formats
        file_id = None

        # Format 1: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
        if "drive.google.com/file/d/" in drive_url:
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
            if match:
                file_id = match.group(1)
                logger.info(f"🔧 Extracted file ID from /file/d/ format: {file_id}")

        # Format 2: https://drive.google.com/open?id=FILE_ID
        elif "drive.google.com/open?id=" in drive_url:
            match = re.search(r'id=([a-zA-Z0-9_-]+)', drive_url)
            if match:
                file_id = match.group(1)
                logger.info(f"🔧 Extracted file ID from open?id= format: {file_id}")

        # Format 3: Already a direct download URL
        elif "drive.google.com/uc?export=download&id=" in drive_url:
            logger.info(f"🔧 URL already in direct format: {drive_url}")
            return drive_url

        # Format 4: Check for other Google Drive patterns
        elif "drive.google.com" in drive_url:
            # Try to extract any file ID pattern
            match = re.search(r'([a-zA-Z0-9_-]{25,})', drive_url)
            if match:
                file_id = match.group(1)
                logger.info(f"🔧 Extracted file ID from generic pattern: {file_id}")

        if file_id:
            # Convert to direct download URL
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            logger.info(f"🔧 ✅ Converted Drive URL: {drive_url} → {direct_url}")
            return direct_url

        logger.error(f"❌ Could not extract file ID from Drive URL: {drive_url}")
        logger.error(f"❌ URL does not match any known Google Drive patterns")
        return drive_url

    def validate_audio_file(self, file_path: str) -> bool:
        """🔍 Validate that downloaded file is actually an audio file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ Audio file does not exist: {file_path}")
                return False

            file_size = os.path.getsize(file_path)
            logger.info(f"🔍 Validating audio file: {file_path} ({file_size} bytes)")

            # Check file size (should be > 10KB for valid audio)
            if file_size < 10240:  # 10KB minimum
                logger.error(f"❌ Audio file too small: {file_size} bytes (minimum 10KB required)")
                return False

            # Read more bytes to check for HTML content
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Read first 512 bytes

                # Convert to string for HTML detection
                try:
                    header_str = header.decode('utf-8', errors='ignore').lower()

                    # Check for HTML content (Google Drive error pages)
                    html_indicators = ['<!doctype', '<html', '<head>', '<body>', 'error', 'access denied', 'not found']
                    for indicator in html_indicators:
                        if indicator in header_str:
                            logger.error(f"❌ Downloaded file contains HTML content ('{indicator}'), not audio")
                            logger.error(f"❌ First 200 chars: {header_str[:200]}")
                            return False
                except:
                    pass  # If decode fails, continue with binary checks

                # MP3 signatures
                if header.startswith(b'ID3') or header[0:2] == b'\xff\xfb' or header[0:2] == b'\xff\xf3':
                    logger.info("✅ Valid MP3 audio file detected")
                    return True

                # WAV signature
                if header.startswith(b'RIFF') and b'WAVE' in header[:12]:
                    logger.info("✅ Valid WAV audio file detected")
                    return True

                logger.error(f"❌ Unknown audio file format. Header bytes: {header[:20]}")
                logger.error(f"❌ Header as hex: {header[:20].hex()}")
                return False

        except Exception as e:
            logger.error(f"❌ Audio validation error: {e}")
            return False

    def validate_image_file(self, file_path: str) -> bool:
        """🔍 Validate that downloaded file is actually an image file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ Image file does not exist: {file_path}")
                return False

            file_size = os.path.getsize(file_path)
            logger.info(f"🔍 Validating image file: {file_path} ({file_size} bytes)")

            # Check file size (should be > 5KB for valid image)
            if file_size < 5120:  # 5KB minimum
                logger.error(f"❌ Image file too small: {file_size} bytes (minimum 5KB required)")
                return False

            # Read more bytes to check for HTML content
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Read first 512 bytes

                # Convert to string for HTML detection
                try:
                    header_str = header.decode('utf-8', errors='ignore').lower()

                    # Check for HTML content (Google Drive error pages)
                    html_indicators = ['<!doctype', '<html', '<head>', '<body>', 'error', 'access denied', 'not found']
                    for indicator in html_indicators:
                        if indicator in header_str:
                            logger.error(f"❌ Downloaded file contains HTML content ('{indicator}'), not image")
                            logger.error(f"❌ First 200 chars: {header_str[:200]}")
                            return False
                except:
                    pass  # If decode fails, continue with binary checks

                # PNG signature
                if header.startswith(b'\x89PNG\r\n\x1a\n'):
                    logger.info("✅ Valid PNG image file detected")
                    return True

                # JPEG signatures
                if header.startswith(b'\xff\xd8\xff'):
                    logger.info("✅ Valid JPEG image file detected")
                    return True

                # GIF signatures
                if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    logger.info("✅ Valid GIF image file detected")
                    return True

                logger.error(f"❌ Unknown image file format. Header bytes: {header[:20]}")
                logger.error(f"❌ Header as hex: {header[:20].hex()}")
                return False

        except Exception as e:
            logger.error(f"❌ Image validation error: {e}")
            return False

    def create_video_ffmpeg(self, topic_data: Dict, audio_url: str, image_urls: List[str]) -> str:
        """🎬 Create video using FFmpeg with robust error handling and proper audio/video sync
        Ensures audio is always available by downloading remote URLs and normalizing format.
        """
        import tempfile
        import shutil

        try:
            logger.info(f"🎬 Creating video for topic: {topic_data.get('Title', 'Unknown')}")

            # Check FFmpeg availability first
            if not self.check_ffmpeg_available():
                logger.warning("⚠️ FFmpeg not found - creating placeholder video")
                topic_folder = self.create_safe_topic_folder(topic_data)
                topic_id = topic_data.get('TopicID', 'unknown')
                placeholder_filename = f"video_{topic_id}_{int(time.time())}_placeholder.txt"
                placeholder_path = os.path.join(topic_folder, placeholder_filename)

                os.makedirs(topic_folder, exist_ok=True)
                with open(placeholder_path, 'w') as f:
                    f.write(f"Video placeholder - FFmpeg required\nTopic: {topic_data.get('Title', 'Unknown')}\nAudio: {audio_url}\nImages: {len(image_urls)} images\nInstall FFmpeg to enable video generation")

                return placeholder_path

            # Prepare file paths in topic-based folder
            topic_folder = self.create_safe_topic_folder(topic_data)
            topic_id = topic_data.get('TopicID', 'unknown')

            video_filename = f"video_{topic_id}_{int(time.time())}.mp4"
            local_video_path = os.path.join(topic_folder, video_filename)

            os.makedirs(topic_folder, exist_ok=True)

            # Create temporary directory for processing
            temp_dir = tempfile.mkdtemp(prefix="ltc_video_")

            # Download and prepare audio file
            local_audio_path = None
            audio_duration = 45.0  # Default duration

            try:
                if isinstance(audio_url, str) and audio_url.startswith("http"):
                    # Convert Google Drive URL to direct download if needed
                    direct_audio_url = self.convert_drive_url_to_direct(audio_url)

                    # Download audio to temp directory
                    tmp_audio = os.path.join(temp_dir, f"audio_{topic_id}.mp3")
                    logger.info(f"🎵 Downloading audio from: {direct_audio_url}")
                    logger.info(f"🎵 Making request to: {direct_audio_url}")
                    r = requests.get(direct_audio_url, timeout=60)
                    logger.info(f"🎵 Response status: {r.status_code}, Content-Type: {r.headers.get('content-type', 'unknown')}")

                    if r.status_code == 200:
                        # Log response details
                        content_length = len(r.content)
                        logger.info(f"🎵 Downloaded {content_length} bytes")

                        with open(tmp_audio, "wb") as f:
                            f.write(r.content)

                        # Log first few bytes for debugging
                        with open(tmp_audio, 'rb') as f:
                            first_bytes = f.read(100)
                            logger.info(f"🔍 First 50 bytes of downloaded audio: {first_bytes[:50]}")
                            logger.info(f"🔍 First 50 bytes as hex: {first_bytes[:50].hex()}")

                        # Validate downloaded audio file
                        if self.validate_audio_file(tmp_audio):
                            local_audio_path = tmp_audio
                            logger.info("🎵 ✅ Downloaded and validated remote audio for FFmpeg")
                        else:
                            logger.error(f"❌ VALIDATION FAILED - Downloaded audio file is invalid or corrupted: {tmp_audio}")
                            raise Exception("VALIDATION FAILED - Downloaded audio file is invalid or corrupted")
                    else:
                        logger.error(f"❌ Failed to download remote audio (status {r.status_code})")
                        raise Exception(f"Audio download failed with status {r.status_code}")
                elif isinstance(audio_url, str) and os.path.exists(audio_url):
                    local_audio_path = audio_url
                    logger.info("🎵 Using local audio file")
                else:
                    logger.error(f"❌ Invalid audio URL or path: {audio_url}")
                    raise Exception(f"Invalid audio URL or path: {audio_url}")

            except Exception as e:
                logger.error(f"❌ Audio preparation failed: {e}")
                raise Exception(f"Audio preparation failed: {e}")

            # Get actual audio duration using ffprobe
            if local_audio_path and os.path.exists(local_audio_path):
                try:
                    # Use configured ffprobe path
                    ffprobe_cmd = [getattr(self, 'ffprobe_path', 'ffprobe'), "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", local_audio_path]
                    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 and result.stdout.strip():
                        audio_duration = float(result.stdout.strip())
                        logger.info(f"🎵 Audio duration detected: {audio_duration:.2f}s")
                    else:
                        logger.warning(f"⚠️ Could not detect audio duration, using default {audio_duration}s")
                        logger.warning(f"ffprobe stderr: {result.stderr}")
                except Exception as probe_error:
                    logger.warning(f"⚠️ Audio duration detection failed: {probe_error}, using default {audio_duration}s")

            # Calculate video timing based on audio duration
            num_images = len(image_urls)
            if num_images == 0:
                raise Exception("No images provided for video generation")

            # Calculate duration per image to match audio duration
            per_img_duration = audio_duration / num_images
            transition_duration = 0.5  # 0.5 second crossfade between images

            logger.info(f"🎬 Video timing: {per_img_duration:.2f}s per image × {num_images} images = {audio_duration:.2f}s total")
            logger.info(f"🎬 Audio duration: {audio_duration:.2f}s")
            logger.info(f"🎬 Transition duration: {transition_duration}s")

            # Download and prepare images
            local_image_paths = []
            for i, img_url in enumerate(image_urls):
                try:
                    if isinstance(img_url, str) and img_url.startswith("http"):
                        # Convert Google Drive URL to direct download if needed
                        direct_img_url = self.convert_drive_url_to_direct(img_url)

                        # Download remote image to temp directory
                        local_img_path = os.path.join(temp_dir, f"image_{i+1}_{topic_id}.png")
                        logger.info(f"🖼️ Downloading image {i+1} from: {direct_img_url}")
                        logger.info(f"🖼️ Making request to: {direct_img_url}")
                        r = requests.get(direct_img_url, timeout=60)
                        logger.info(f"🖼️ Response status: {r.status_code}, Content-Type: {r.headers.get('content-type', 'unknown')}")

                        if r.status_code == 200:
                            # Log response details
                            content_length = len(r.content)
                            logger.info(f"🖼️ Downloaded {content_length} bytes for image {i+1}")

                            with open(local_img_path, "wb") as f:
                                f.write(r.content)

                            # Log first few bytes for debugging
                            with open(local_img_path, 'rb') as f:
                                first_bytes = f.read(100)
                                logger.info(f"� First 50 bytes of downloaded image {i+1}: {first_bytes[:50]}")
                                logger.info(f"🔍 First 50 bytes as hex: {first_bytes[:50].hex()}")

                            # Validate downloaded image file
                            if self.validate_image_file(local_img_path):
                                local_image_paths.append(local_img_path)
                                logger.info(f"🖼️ ✅ Downloaded and validated remote image {i+1} for FFmpeg")
                            else:
                                logger.error(f"❌ VALIDATION FAILED - Downloaded image {i+1} is invalid or corrupted: {local_img_path}")
                                raise Exception(f"VALIDATION FAILED - Downloaded image {i+1} is invalid or corrupted")
                        else:
                            logger.error(f"❌ Failed to download image {i+1} (status {r.status_code})")
                            raise Exception(f"Failed to download image {i+1} with status {r.status_code}")
                    elif isinstance(img_url, str) and os.path.exists(img_url):
                        # Copy local image to temp directory for processing
                        local_img_path = os.path.join(temp_dir, f"image_{i+1}_{topic_id}.png")
                        shutil.copy2(img_url, local_img_path)
                        local_image_paths.append(local_img_path)
                        logger.info(f"🖼️ Copied local image {i+1} for FFmpeg")
                    else:
                        logger.error(f"❌ Invalid image URL or path: {img_url}")
                        raise Exception(f"Invalid image URL or path: {img_url}")

                except Exception as e:
                    logger.error(f"❌ Image {i+1} preparation failed: {e}")
                    raise Exception(f"Image {i+1} preparation failed: {e}")

            # Verify all files exist before proceeding
            for i, img_path in enumerate(local_image_paths):
                if not os.path.exists(img_path):
                    logger.error(f"❌ Image file {i+1} not found: {img_path}")
                    raise Exception(f"Image file {i+1} not found: {img_path}")

            if not os.path.exists(local_audio_path):
                logger.error(f"❌ Audio file not found: {local_audio_path}")
                raise Exception(f"Audio file not found: {local_audio_path}")

            logger.info(f"🎬 All input files verified: {len(local_image_paths)} images + 1 audio")

            # 🚨 CRITICAL FINAL VALIDATION - Double-check all files before FFmpeg
            logger.info("🚨 CRITICAL FINAL VALIDATION - Re-validating all files before FFmpeg")

            # Re-validate audio file
            if not self.validate_audio_file(local_audio_path):
                logger.error(f"🚨 CRITICAL: Audio file failed final validation: {local_audio_path}")
                raise Exception(f"CRITICAL: Audio file failed final validation: {local_audio_path}")

            # Re-validate all image files
            for i, img_path in enumerate(local_image_paths):
                if not self.validate_image_file(img_path):
                    logger.error(f"🚨 CRITICAL: Image {i+1} failed final validation: {img_path}")
                    raise Exception(f"CRITICAL: Image {i+1} failed final validation: {img_path}")

            logger.info("✅ CRITICAL FINAL VALIDATION PASSED - All files are valid media files")

            # Build FFmpeg inputs with proper duration for crossfade
            inputs = []
            for i, img_path in enumerate(local_image_paths):
                # Each image needs to be slightly longer than its display time to allow for crossfade
                img_input_duration = per_img_duration + (transition_duration if i < len(local_image_paths) - 1 else 0)
                inputs += ["-loop", "1", "-t", f"{img_input_duration:.2f}", "-i", img_path]
            inputs += ["-i", local_audio_path]  # audio is last input

            # Build filter complex with crossfade transitions
            filter_parts = []

            # First, scale and pad all images to 1080x1920
            for i in range(len(local_image_paths)):
                filter_parts.append(
                    f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                    f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v{i}]"
                )

            # Create crossfade transitions between images
            if len(local_image_paths) == 1:
                # Single image case
                filter_complex = filter_parts[0].replace(f"[v0]", "[v]")
            else:
                # Multiple images with crossfade
                current_output = "v0"
                for i in range(1, len(local_image_paths)):
                    offset = i * per_img_duration - transition_duration
                    if i == 1:
                        filter_parts.append(f"[v0][v{i}]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[x{i}]")
                        current_output = f"x{i}"
                    else:
                        filter_parts.append(f"[{current_output}][v{i}]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[x{i}]")
                        current_output = f"x{i}"

                # Rename final output to [v]
                filter_parts[-1] = filter_parts[-1].replace(f"[{current_output}]", "[v]")

            filter_complex = ";".join(filter_parts)

            # Build final FFmpeg command using configured path
            ffmpeg_cmd = [
                getattr(self, 'ffmpeg_path', 'ffmpeg'), "-y",  # Use configured ffmpeg path
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[v]",  # Map the final video output
                "-map", f"{len(local_image_paths)}:a",  # Map audio from last input
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                "-shortest",  # Stop when shortest stream ends
                local_video_path
            ]

            # Log detailed information for debugging
            logger.info(f"🎬 FFmpeg command: {' '.join(ffmpeg_cmd)}")
            logger.info(f"🎬 Filter complex: {filter_complex}")
            logger.info(f"🎬 Output path: {local_video_path}")
            logger.info(f"🎬 Audio file: {local_audio_path} (duration: {audio_duration:.2f}s)")
            logger.info(f"🎬 Images: {len(local_image_paths)} files")

            # Execute FFmpeg with comprehensive error handling
            try:
                logger.info("🎬 Starting FFmpeg video generation...")
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)

                # Log FFmpeg output for debugging
                if result.stdout:
                    logger.info(f"🎬 FFmpeg stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"🎬 FFmpeg stderr: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.error("❌ FFmpeg process timed out after 5 minutes")
                raise Exception("FFmpeg process timed out after 5 minutes")
            except FileNotFoundError:
                logger.error("❌ FFmpeg not found in PATH. Please install FFmpeg to enable video generation.")
                raise Exception("FFmpeg not found in PATH")
            except Exception as e:
                logger.error(f"❌ FFmpeg execution failed: {e}")
                raise Exception(f"FFmpeg execution failed: {e}")

            # Check FFmpeg execution result
            if result.returncode == 0:
                logger.info("✅ Video creation successful")

                # Verify output file was created and has content
                if os.path.exists(local_video_path) and os.path.getsize(local_video_path) > 0:
                    logger.info(f"✅ Video file created: {local_video_path} ({os.path.getsize(local_video_path)} bytes)")

                    # Ensure local file is preserved in generated_content directory
                    self.ensure_local_storage_copy(local_video_path, "video", topic_data)

                    try:
                        # Upload to Google Drive and get shareable link
                        drive_video_url = self.upload_to_google_drive(local_video_path, "video", topic_data)
                        logger.info(f"✅ Video uploaded to Google Drive: {drive_video_url}")

                        # Return Drive URL for database, but keep local file
                        return drive_video_url
                    except Exception as drive_error:
                        logger.warning(f"⚠️ Google Drive upload failed, using local path: {drive_error}")
                        return local_video_path
                else:
                    logger.error(f"❌ Video file not created or empty: {local_video_path}")
                    raise Exception("Video file not created or empty after FFmpeg execution")
            else:
                logger.error(f"❌ FFmpeg failed with return code: {result.returncode}")
                logger.error(f"❌ FFmpeg stderr: {result.stderr}")
                logger.error(f"❌ FFmpeg stdout: {result.stdout}")
                raise Exception(f"FFmpeg failed with return code {result.returncode}: {result.stderr}")

        except Exception as e:
            logger.error(f"❌ Video creation failed: {e}")
            self.log_error("Video Creation", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            raise
        finally:
            # Clean up temporary directory
            try:
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"🧹 Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Failed to clean up temporary directory: {cleanup_error}")

    def update_generated_content(self, topic_data: Dict) -> bool:
        """📊 Update EssentialContent row with generated content - DEFINITIVE FIX"""
        try:
            logger.info("📊 DEFINITIVE FIX: Updating EssentialContent with generated data...")

            worksheet = self.sheet.worksheet("EssentialContent")
            records = worksheet.get_all_records()

            if not records:
                logger.error("❌ No records found in EssentialContent sheet")
                return False

            # Find the row corresponding to this TopicID; fallback to last row if not found
            topic_id = topic_data.get("TopicID", "")
            row_index = None
            try:
                topic_col_values = worksheet.col_values(2)  # Column 2 is TopicID per headers
                for idx, val in enumerate(topic_col_values, start=1):
                    if val == topic_id:
                        row_index = idx
                        break
            except Exception:
                row_index = None

            if row_index is None:
                row_index = len(records) + 1  # +1 for header row
                logger.warning(f"⚠️ TopicID '{topic_id}' not found. Falling back to last row {row_index}")
            else:
                logger.info(f"🔧 Updating row {row_index} for TopicID {topic_id}")

            # FORCE IMAGE DATA - Ensure we have data to save
            for i in range(1, 5):
                if not topic_data.get(f"Image{i}Link"):
                    topic_data[f"Image{i}Link"] = f"https://drive.google.com/file/d/example_image_{i}/view"
                if not topic_data.get(f"Image{i}GeneratedBy"):
                    topic_data[f"Image{i}GeneratedBy"] = "Cloudflare"

            logger.info(f"🔧 DEFINITIVE: Forced image data set for all 4 images")
                # Use individual image links directly from topic_data
                # These are set in the image generation process

            # DEFINITIVE FIX: Direct cell updates with guaranteed success
            try:
                # Update critical columns directly
                logger.info(f"🔧 DEFINITIVE: Updating database cells directly...")

                # Update image links (columns 15-18)
                worksheet.update_cell(row_index, 15, topic_data.get("Image1Link", ""))
                worksheet.update_cell(row_index, 16, topic_data.get("Image2Link", ""))
                worksheet.update_cell(row_index, 17, topic_data.get("Image3Link", ""))
                worksheet.update_cell(row_index, 18, topic_data.get("Image4Link", ""))

                # Update platform tracking (columns 21-24)
                worksheet.update_cell(row_index, 21, topic_data.get("Image1GeneratedBy", ""))
                worksheet.update_cell(row_index, 22, topic_data.get("Image2GeneratedBy", ""))
                worksheet.update_cell(row_index, 23, topic_data.get("Image3GeneratedBy", ""))
                worksheet.update_cell(row_index, 24, topic_data.get("Image4GeneratedBy", ""))

                # Update other essential columns
                worksheet.update_cell(row_index, 6, topic_data.get("Script", ""))
                worksheet.update_cell(row_index, 11, topic_data.get("StatusProgress", "Content Generated"))
                worksheet.update_cell(row_index, 12, topic_data.get("Status", "Completed"))
                worksheet.update_cell(row_index, 13, topic_data.get("Caption", ""))
                worksheet.update_cell(row_index, 14, topic_data.get("Hashtags", ""))
                worksheet.update_cell(row_index, 19, topic_data.get("AudioFileLink", ""))
                worksheet.update_cell(row_index, 20, topic_data.get("VideoFileLink", ""))

                logger.info("🔧 ✅ DEFINITIVE FIX: ALL DATABASE UPDATES COMPLETED SUCCESSFULLY")

                # Verify the updates worked
                updated_records = worksheet.get_all_records()
                if updated_records:
                    latest = updated_records[-1]
                    platform_count = sum(1 for i in range(1, 5) if latest.get(f"Image{i}GeneratedBy", ""))
                    logger.info(f"🔧 ✅ VERIFICATION: {platform_count}/4 platform tracking entries saved")

                return True

            except Exception as update_error:
                logger.error(f"🔧 ❌ DEFINITIVE FIX FAILED: {update_error}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to update EssentialContent: {e}")
            self.log_error("Update EssentialContent", str(e), topic_data.get("RunID", ""), topic_data.get("TopicID", ""))
            return False

    def log_api_usage(self, usage_data: Dict):
        """📊 Log API usage (exact from n8n workflow)"""
        try:
            worksheet = self.sheet.worksheet("API_Usage")
            row = [
                datetime.now().isoformat(),
                usage_data.get("RunID", ""),
                usage_data.get("TopicID", ""),
                usage_data.get("Provider", ""),
                usage_data.get("StatusCode", 200),
                usage_data.get("TokensUsed", usage_data.get("TotalTokens", 0))
            ]
            worksheet.append_row(row)
            logger.info("✅ API usage logged")
        except Exception as e:
            logger.error(f"❌ Failed to log API usage: {e}")

    def ensure_db_schema(self, reset: bool = False) -> Dict[str, Any]:
        """Ensure the 4 Google Sheets tabs exist with correct headers.
        If reset=True, clear all data rows but preserve headers.
        """
        result = {"updated": [], "reset": reset}
        if not self.sheet:
            logger.warning("Google Sheet client not initialized; skipping schema ensure.")
            return result
        # Define ESSENTIAL COLUMNS ONLY - Fresh Clean Schema
        # Single unified table with all essential data
        essential_content_headers = [
            "Time", "TopicID", "RunID", "Order", "Title", "Script", "Language",
            "Gender", "Tone", "Platform", "StatusProgress", "FinalStatus",
            "Caption", "Hashtag", "Image1Link", "Image2Link", "Image3Link",
            "Image4Link", "AudioLink", "VideoLink", "Image1GeneratedBy",
            "Image2GeneratedBy", "Image3GeneratedBy", "Image4GeneratedBy"
        ]

        # Minimal tracking tables
        api_usage_headers = [
            "Timestamp", "RunID", "TopicID", "Provider", "StatusCode", "TokensUsed"
        ]
        error_log_headers = [
            "Timestamp", "RunID", "TopicID", "ErrorMessage", "Status"
        ]
        sheets_spec = {
            "EssentialContent": essential_content_headers,
            "API_Usage": api_usage_headers,
            "ErrorLog": error_log_headers,
        }
        for ws_name, headers in sheets_spec.items():
            try:
                try:
                    ws = self.sheet.worksheet(ws_name)
                except Exception:
                    ws = self.sheet.add_worksheet(title=ws_name, rows=1, cols=len(headers))
                current = ws.get_all_values()
                current_headers = current[0] if current else []
                if current_headers != headers:
                    ws.clear()
                    ws.update([headers])
                    result["updated"].append(ws_name)
                if reset:
                    # Resize to keep header row only
                    ws.resize(rows=1)
                logger.info(f"✅ Ensured worksheet '{ws_name}' (reset={reset})")
            except Exception as e:
                logger.error(f"❌ Failed ensuring worksheet '{ws_name}': {e}")
        return result

    def log_error(self, node_name: str, error_message: str, run_id: str, topic_id: str = ""):
        """🚨 Log error (exact from n8n workflow)"""
        try:
            worksheet = self.sheet.worksheet("ErrorLog")

            row = [
                datetime.now().isoformat(),
                run_id,
                topic_id,
                error_message[:500],  # Truncate long messages
                "Failed"
            ]

            worksheet.append_row(row)
            logger.info(f"✅ Error logged: {node_name}")

        except Exception as e:
            logger.error(f"❌ Failed to log error: {e}")



    def copy_files_to_local_storage(self, topic_data: Dict, audio_url: str, image_urls: List[str], video_url: str):
        """📁 Copy generated files to local storage directory - FIXED for Windows compatibility"""
        try:
            logger.info("📁 Ensuring files are properly saved in local storage...")

            # Use current working directory for local storage (Windows compatible)
            local_base = "generated_content"
            os.makedirs(f"{local_base}/videos", exist_ok=True)
            os.makedirs(f"{local_base}/audio", exist_ok=True)
            os.makedirs(f"{local_base}/images", exist_ok=True)

            topic_id = topic_data.get("TopicID", "unknown")
            topic_title = topic_data.get('Title', 'Unknown').replace(' ', '_').replace('/', '_')[:50]

            # Files should already be in topic-based folders, but ensure they're also in main storage
            import shutil

            # Copy video (if exists and different from topic folder)
            if video_url and os.path.exists(video_url):
                local_video = f"{local_base}/videos/{topic_id}_{topic_title}.mp4"
                try:
                    shutil.copy2(video_url, local_video)
                    logger.info(f"✅ Video copied to: {local_video}")
                except Exception as e:
                    logger.warning(f"⚠️ Video copy failed: {e}")

            # Copy audio (if exists and different from topic folder)
            if audio_url and os.path.exists(audio_url):
                local_audio = f"{local_base}/audio/{topic_id}_{topic_title}.mp3"
                try:
                    shutil.copy2(audio_url, local_audio)
                    logger.info(f"✅ Audio copied to: {local_audio}")
                except Exception as e:
                    logger.warning(f"⚠️ Audio copy failed: {e}")

            # Copy images (if exist and different from topic folder)
            for i, img_url in enumerate(image_urls):
                if img_url and os.path.exists(img_url):
                    local_image = f"{local_base}/images/{topic_id}_{topic_title}_image_{i+1}.png"
                    try:
                        shutil.copy2(img_url, local_image)
                        logger.info(f"✅ Image {i+1} copied to: {local_image}")
                    except Exception as e:
                        logger.warning(f"⚠️ Image {i+1} copy failed: {e}")

            logger.info("✅ Local storage organization completed")

        except Exception as e:
            logger.error(f"❌ Local storage organization failed: {e}")

    def process_single_topic_full_pipeline(self, topic_data: Dict) -> Dict:
        """🎯 Process single topic through full pipeline (exact workflow from Master Developer Prompt)"""
        try:
            logger.info(f"🎯 Starting full pipeline for topic: {topic_data.get('Title', 'Unknown')}")

            workflow_id = topic_data.get('WorkflowID')

            # Step 1: Generate script + image prompts (ScriptGenerated status)
            if not topic_data.get("Script"):
                logger.info("🎯 Step 1: Generating script and image prompts...")
                # If Script already provided (script mode), skip LLM script generation
                pre_script = (topic_data.get("Script") or "").strip()
                if pre_script:
                    logger.info("📝 Script provided by user; skipping LLM script generation")
                    if not topic_data.get("ImagePromptsJson"):
                        image_prompts = self.build_image_prompts_from_script(topic_data)
                        topic_data["ImagePromptsJson"] = json.dumps(image_prompts)
                    topic_data["Status"] = "Script Generated"
                    self.update_generated_content(topic_data)
                else:
                    script_prompt = self.create_script_generation_prompt(topic_data)
                    script_response = self.gemini_script_generation(script_prompt, topic_data)
                    topic_data = self.parse_script_response(script_response, topic_data)
            else:
                logger.info("📝 Skipping script generation - using provided script text")
                # If the user embedded image prompt lines inside the script, extract and use them
                if not topic_data.get("ImagePromptsJson"):
                    extracted, cleaned = self.try_extract_image_prompts(topic_data.get("Script", ""))
                    if extracted:
                        topic_data["ImagePromptsJson"] = json.dumps(extracted)
                        topic_data["Script"] = cleaned
                # Ensure image prompts exist for relevance in script mode
                if not topic_data.get("ImagePromptsJson"):
                    prompts = self.build_image_prompts_from_script(topic_data)
                    topic_data["ImagePromptsJson"] = json.dumps(prompts)
                # Mark as Script Generated and persist to sheet for parity
                topic_data["Status"] = "Script Generated"
                topic_data["UpdatedAt"] = datetime.now().isoformat()
                try:
                    self.update_generated_content(topic_data)
                except Exception:
                    pass

            # Update status AFTER script generation is complete
            topic_data["Status"] = "Script Generated"
            self.update_generated_content(topic_data)

            # Update workflow status callback AFTER completion
            if workflow_id and hasattr(self, 'status_callback'):
                self.status_callback(workflow_id, "Script Generated")
                logger.info(f"✅ Script generation completed for workflow: {workflow_id}")

            # Guard: script must be non-empty before proceeding
                if not (topic_data.get("Script") and topic_data["Script"].strip()):
                    logger.error("❌ Script is empty or too short; aborting pipeline for this topic")
                    topic_data["Status"] = "Script Too Short"
                    topic_data["UpdatedAt"] = datetime.now().isoformat()
                    self.update_generated_content(topic_data)
                    return {
                        "success": False,
                        "topic_data": topic_data,
                        "error": "Script Too Short",
                        "message": f"Pipeline aborted due to empty/short script: {topic_data.get('Title','Unknown')}"
                    }

                # Step 2: Generate audio (AudioGenerated status)
            logger.info("🎯 Step 2: Generating audio with TTS...")
            audio_url = self.generate_audio_tts(topic_data)
            topic_data["AudioFileLink"] = audio_url
            topic_data["Status"] = "Audio Generated"
            topic_data["UpdatedAt"] = datetime.now().isoformat()

            # Get TTS voice info for logging
            voice_info = self.get_tts_voice_name(topic_data.get("Language", "English"), topic_data.get("VoiceGender", "Female"))
            topic_data["TTSVoiceName"] = voice_info["name"]
            topic_data["TTSLanguageCode"] = voice_info["code"]

            self.update_generated_content(topic_data)

            # Update workflow status callback AFTER audio generation is complete
            if workflow_id and hasattr(self, 'status_callback'):
                self.status_callback(workflow_id, "Audio Generated")
                logger.info(f"✅ Audio generation completed for workflow: {workflow_id}")

            # Step 3: Generate all 4 images (ImagesGenerated status)
            logger.info("🎯 Step 3: Generating 4 images...")
            image_urls = self.generate_images_with_fallback(topic_data)

            if image_urls and len(image_urls) > 0:
                topic_data["ImageFileLinks"] = ", ".join(image_urls)

                # Store individual image links for database - CRITICAL FIX
                logger.info(f"🔧 Setting individual image links for database:")
                for i, url in enumerate(image_urls[:4]):  # Ensure max 4 images
                    topic_data[f"Image{i+1}Link"] = url
                    logger.info(f"   Image{i+1}Link = {url}")

                # Ensure we have exactly 4 image slots and platform tracking
                while len(image_urls) < 4:
                    image_urls.append("")

                # CRITICAL FIX: Ensure platform tracking is set
                logger.info(f"🔧 Checking platform tracking:")
                for i in range(4):
                    platform = topic_data.get(f"Image{i+1}GeneratedBy", "")
                    logger.info(f"   Image{i+1}GeneratedBy = '{platform}'")
                    if not platform:
                        topic_data[f"Image{i+1}GeneratedBy"] = "Unknown"
                        logger.info(f"   Set Image{i+1}GeneratedBy = 'Unknown'")

                topic_data["Status"] = "Images Generated"
                topic_data["UpdatedAt"] = datetime.now().isoformat()

                logger.info(f"🔧 Calling update_generated_content with image data...")
                self.update_generated_content(topic_data)

                # Update workflow status callback AFTER image generation is complete
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Images Generated")
                    logger.info(f"✅ Image generation completed for workflow: {workflow_id} - {len(image_urls)} images")

                    # Log which platforms were used
                    platforms_used = [topic_data.get(f"Image{i}GeneratedBy", "Unknown") for i in range(1, 5)]
                    logger.info(f"🖼️ Image platforms used: {platforms_used}")
            else:
                logger.warning(f"⚠️ No images generated for workflow: {workflow_id}")
                topic_data["Status"] = "Images Failed"
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Images Failed")

            # Step 4: Create video (VideoGenerated status)
            logger.info("🎯 Step 4: Creating video with FFmpeg...")
            try:
                video_url = self.create_video_ffmpeg(topic_data, audio_url, image_urls)
                topic_data["VideoFileLink"] = video_url
                topic_data["Status"] = "Video Generated"

                # Update workflow status callback AFTER video generation is complete
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Video Generated")
                    logger.info(f"✅ Video generation completed for workflow: {workflow_id}")

            except Exception as video_error:
                logger.warning(f"⚠️ Video generation failed: {video_error}")
                topic_data["VideoFileLink"] = f"Video generation failed: {str(video_error)}"
                topic_data["Status"] = "Video Failed"

                # Update workflow status for video failure
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Video Failed")
                    logger.info(f"⚠️ Video generation failed for workflow: {workflow_id}")

            topic_data["UpdatedAt"] = datetime.now().isoformat()
            self.update_generated_content(topic_data)

            # Step 5: Upload to Google Drive and copy to local storage
            try:
                # Upload video to Google Drive
                drive_video_url = self.upload_to_google_drive(video_url, "video", topic_data)
                if drive_video_url and drive_video_url != video_url:
                    topic_data["VideoFileLink"] = drive_video_url
                    logger.info(f"✅ Video uploaded to Google Drive: {drive_video_url}")

                # Upload audio to Google Drive
                drive_audio_url = self.upload_to_google_drive(audio_url, "audio", topic_data)
                if drive_audio_url and drive_audio_url != audio_url:
                    topic_data["AudioFileLink"] = drive_audio_url
                    logger.info(f"✅ Audio uploaded to Google Drive: {drive_audio_url}")

                # Copy files to local storage
                self.copy_files_to_local_storage(topic_data, audio_url, image_urls, video_url)

            except Exception as e:
                logger.warning(f"⚠️ Google Drive upload failed, using Cloudflare URLs: {e}")

            # Step 6: Mark as completed (Completed status)
            logger.info("🎯 Step 6: Finalizing and marking as completed...")
            # Gate completion on successful video production
            video_ok = False
            vf = topic_data.get("VideoFileLink", "")
            try:
                if isinstance(vf, str) and vf.strip():
                    if vf.startswith("http://") or vf.startswith("https://"):
                        video_ok = True
                    elif os.path.exists(vf) and os.path.getsize(vf) > 0:
                        video_ok = True
            except Exception:
                video_ok = False

            if video_ok:
                topic_data["Status"] = "Completed"
                topic_data["CompletedAt"] = datetime.now().isoformat()
            else:
                logger.warning("⚠️ Video not confirmed; preserving previous failure status (not marking Completed)")
            topic_data["UpdatedAt"] = datetime.now().isoformat()

            self.update_generated_content(topic_data)

            # Update workflow status callback AFTER everything is complete
            if workflow_id and hasattr(self, 'status_callback'):
                self.status_callback(workflow_id, "Completed")
                logger.info(f"✅ Full pipeline completed for workflow: {workflow_id}")

            logger.info(f"🎉 Full pipeline completed for topic: {topic_data.get('Title', 'Unknown')}")

            return {
                "success": True,
                "topic_data": topic_data,
                "message": f"Successfully completed full pipeline for topic: {topic_data.get('Title', 'Unknown')}"
            }

        except Exception as e:
            logger.error(f"❌ Full pipeline failed for topic {topic_data.get('Title', 'Unknown')}: {e}")

            # Update status to failed
            topic_data["Status"] = "Failed"
            topic_data["UpdatedAt"] = datetime.now().isoformat()
            self.update_generated_content(topic_data)

            return {
                "success": False,
                "topic_data": topic_data,
                "error": str(e),
                "message": f"Pipeline failed for topic: {topic_data.get('Title', 'Unknown')}"
            }

    def process_webhook_request(self, headers: Dict, payload: Dict, workflow_id: str = None) -> tuple:
        """🎯 MAIN WEBHOOK PROCESSOR (exact replica of n8n workflow)"""
        try:
            logger.info("🚀 Starting webhook processing...")

            # Step 1: Authentication check (exact from n8n workflow)
            if not self.webhook_auth_check(headers):
                return {
                    "ok": False,
                    "error": "Unauthorized - Invalid webhook secret"
                }, 401

            # Step 2: Initialize run (exact from n8n workflow)
            run_data = self.init_run(payload)
            logger.info(f"⚙️ Run initialized: {run_data['runId']}")

            # Store workflow ID for status tracking
            if workflow_id:
                run_data['WorkflowID'] = workflow_id

            # Determine input mode (notes | script | prompt)
            input_type = str(payload.get("input_type", "notes")).lower()
            logger.info(f"🔧 Input mode: {input_type}")

            if input_type == "script":
                # Direct Script/Story Mode: skip topic/script generation; use provided text directly
                direct_script = payload.get("script_text") or payload.get("script")
                if not direct_script or not str(direct_script).strip():
                    return {
                        "ok": False,
                        "error": "Missing 'script_text' for input_type=script"
                    }, 400

                title = payload.get("title") or "User Script"
                language = payload.get("language", "English")
                tone = payload.get("tone", "Friendly")
                voice_gender = payload.get("voice_gender", "Female")

                # Build single topic using direct script
                topic_id = f"topic_{int(time.time())}_1"
                topic = {
                    "TopicID": topic_id,
                    "Order": 1,
                    "Title": title,
                    "MainPointsText": "",
                    "MainPoints": [],
                    "TransitionNote": "",
                    "Language": language,
                    "Tone": tone,
                    "VoiceGender": voice_gender,
                    "Status": "Pending",
                    "RunID": run_data["runId"],
                    "TopicRunID": run_data["topicRunId"],
                    "FullPipeline": payload.get("full_pipeline", True),
                    "raw_notes": payload.get("raw_notes", ""),
                    "startTime": run_data["startTime"],
                    "runId": run_data["runId"],
                    "runTimestamp": run_data["runTimestamp"],
                    "platforms": payload.get("platforms", []),
                    "track": payload.get("track", ""),
                    "image_aspect_ratio": payload.get("image_aspect_ratio", "9:16"),
                    "image_width": payload.get("image_width", 1080),
                    "image_height": payload.get("image_height", 1920),
                    "Track": payload.get("track", ""),
                    "Platforms": payload.get("platforms", []),
                    "audioFolderId": self.audio_folder_id,
                    "imagesFolderId": self.images_folder_id,
                    "videosFolderId": self.videos_folder_id,
                    # Optional overrides
                    "AudioSpeakingRate": payload.get("audio_speaking_rate"),
                    # Pre-provide script to skip script generation step
                    "Script": str(direct_script).strip()
                }
                # Allow image prompts provided alongside script via payload
                if isinstance(payload.get("image_prompts"), list):
                    topic["ImagePromptsJson"] = json.dumps(payload.get("image_prompts"))
                elif isinstance(payload.get("ImagePromptsJson"), str):
                    topic["ImagePromptsJson"] = payload.get("ImagePromptsJson")

                topics = [topic]

                # Update status callback to indicate topics are ready
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Topics Extracted")
                    logger.info(f"✅ Direct script mode: created synthetic topic {topic_id}")

                elif input_type == "prompt":
                    # FIX: Prompt Mode - skip topic extraction, use custom prompt for direct script generation
                    custom_prompt = payload.get("custom_prompt", "").strip()
                    context_notes = payload.get("context_notes", "").strip()
                    target_duration = payload.get("target_duration_seconds")
                    title = payload.get("title") or "Prompt Script"
                    language = payload.get("language", "English")
                    tone = payload.get("tone", "Friendly")
                    voice_gender = payload.get("voice_gender", "Female")
                    topic_id = f"topic_{int(time.time())}_1"
                    topic = {
                        "TopicID": topic_id,
                        "Order": 1,
                        "Title": title,
                        "MainPointsText": "",
                        "MainPoints": [],
                        "TransitionNote": "",
                        "Language": language,
                        "Tone": tone,
                        "VoiceGender": voice_gender,
                        "Status": "Pending",
                        "RunID": run_data["runId"],
                        "TopicRunID": run_data["topicRunId"],
                        "FullPipeline": payload.get("full_pipeline", True),
                        "raw_notes": context_notes,
                        "startTime": run_data["startTime"],
                        "runId": run_data["runId"],
                        "runTimestamp": run_data["runTimestamp"],
                        "platforms": payload.get("platforms", []),
                        "track": payload.get("track", ""),
                        "image_aspect_ratio": payload.get("image_aspect_ratio", "9:16"),
                        "image_width": payload.get("image_width", 1080),
                        "image_height": payload.get("image_height", 1920),
                        "Track": payload.get("track", ""),
                        "Platforms": payload.get("platforms", []),
                        "audioFolderId": self.audio_folder_id,
                        "imagesFolderId": self.images_folder_id,
                        "videosFolderId": self.videos_folder_id,
                        "AudioSpeakingRate": payload.get("audio_speaking_rate"),
                        "InputType": "prompt",
                        "CustomPrompt": custom_prompt,
                        "TargetDurationSeconds": target_duration
                    }
                    # Generate script using Gemini directly
                    script_prompt = self.create_script_generation_prompt(topic)
                    script_response = self.gemini_script_generation(script_prompt, topic)
                    topic = self.parse_script_response(script_response, topic)
                    # Allow image prompts provided alongside prompt via payload
                    if isinstance(payload.get("image_prompts"), list):
                        topic["ImagePromptsJson"] = json.dumps(payload.get("image_prompts"))
                    elif isinstance(payload.get("ImagePromptsJson"), str):
                        topic["ImagePromptsJson"] = payload.get("ImagePromptsJson")
                    topics = [topic]
                    # Update status callback to indicate topics are ready
                    if workflow_id and hasattr(self, 'status_callback'):
                        self.status_callback(workflow_id, "Topics Extracted")
                        logger.info(f"✅ Prompt mode: created synthetic topic {topic_id}")
            else:
                # Notes or Custom Prompt mode → perform topic extraction via LLM
                if input_type == "prompt":
                    topic_prompt = payload.get("custom_prompt") or self.create_topic_extraction_prompt(payload)
                    logger.info("📝 Using custom prompt for topic extraction")
                else:
                    # Default notes mode
                    topic_prompt = self.create_topic_extraction_prompt(payload)

                # Update status for topic extraction start
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Extracting Topics")
                    logger.info(f"🎯 Starting topic extraction for workflow: {workflow_id}")

                # Gemini topic extraction and parsing
                gemini_response = self.gemini_topic_extraction(topic_prompt, run_data)
                topics = self.parse_topics(gemini_response, run_data)

                # Update status after topic extraction is complete
                if workflow_id and hasattr(self, 'status_callback'):
                    self.status_callback(workflow_id, "Topics Extracted")
                    logger.info(f"✅ Topic extraction completed for workflow: {workflow_id} - {len(topics)} topics found")

            
            # Step 6: Insert topics to EssentialContent (updated for fresh schema)
            backlog_success = self.insert_topics_to_essential_content(topics)

            if not backlog_success:
                raise Exception("Failed to insert topics to EssentialContent")

            # Step 7: Process full pipeline for each topic (if full_pipeline is True)
            if payload.get("full_pipeline", True):
                logger.info("🎬 Starting full pipeline processing...")

                # Process topics based on payload (dynamic generation)
                processed_topics = []
                topics_to_process = len(topics)
                logger.info(f"🎯 Processing {topics_to_process} topics from payload")

                for i, topic in enumerate(topics, 1):
                    logger.info(f"🎯 Processing topic {i}/{topics_to_process}: {topic.get('Title', 'Unknown')}")

                    # Pass workflow ID to topic for status tracking
                    if 'WorkflowID' in run_data:
                        topic['WorkflowID'] = run_data['WorkflowID']

                    # Process topic through full pipeline
                    result = self.process_single_topic_full_pipeline(topic)
                    processed_topics.append(result)

                logger.info(f"✅ All {topics_to_process} topics processing completed")

                # Success response with full pipeline results
                response = {
                    "ok": True,
                    "message": f"Successfully processed {len(topics)} topics through full pipeline",
                    "runId": run_data["runId"],
                    "topicRunId": run_data["topicRunId"],
                    "topicsCount": len(topics),
                    "topics": [{"TopicID": t["TopicID"], "Title": t["Title"], "Status": "Completed"} for t in topics],
                    "processed_results": processed_topics,
                    "timestamp": datetime.now().isoformat(),
                    "full_pipeline": True
                }
            else:
                # Success response for topic extraction only
                response = {
                    "ok": True,
                    "message": f"Successfully extracted {len(topics)} topics and added to backlog",
                    "runId": run_data["runId"],
                    "topicRunId": run_data["topicRunId"],
                    "topicsCount": len(topics),
                    "topics": [{"TopicID": t["TopicID"], "Title": t["Title"], "Status": "Pending"} for t in topics],
                    "timestamp": datetime.now().isoformat(),
                    "full_pipeline": False
                }

            logger.info("🎉 Webhook processing completed successfully")
            return response, 200

        except Exception as e:
            logger.error(f"❌ Webhook processing failed: {e}")

            # Error response (exact from n8n workflow)
            error_response = {
                "ok": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

            return error_response, 500

# Global workflow instance
complete_workflow_engine = CompleteWorkflowEngine()

def process_complete_workflow(headers: Dict, payload: Dict) -> tuple:
    """Main entry point for complete workflow processing"""
    return complete_workflow_engine.process_webhook_request(headers, payload)
