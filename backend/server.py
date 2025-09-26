#!/usr/bin/env python3
"""
🎯 FIXED BACKEND SERVER
Flask server with proper payload handling
"""

from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string
import threading
import time
import os
import logging
import json
from dotenv import load_dotenv

# Load environment variables from config directory
# Get the project root directory (one level up from backend/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_dir = os.path.join(project_root, 'config')
env_path = os.path.join(config_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
    # Debug: Check if key variables are loaded
    print(f"🔍 AUDIO_FOLDER_ID: {os.getenv('AUDIO_FOLDER_ID')}")
    print(f"🔍 IMAGES_FOLDER_ID: {os.getenv('IMAGES_FOLDER_ID')}")
    print(f"🔍 VIDEOS_FOLDER_ID: {os.getenv('VIDEOS_FOLDER_ID')}")
    print(f"🔍 GOOGLE_SHEET_ID: {os.getenv('GOOGLE_SHEET_ID')}")
else:
    load_dotenv()  # Fallback to root .env
    print("⚠️ Using fallback .env loading")

# Import workflow engine
try:
    import sys
    import os
    # Add the current directory to Python path for local development
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Also add /app for Docker compatibility
    app_dir = '/app'
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from backend.workflow_engine import CompleteWorkflowEngine
    print("🎯 Initializing CompleteWorkflowEngine...")
    workflow_engine = CompleteWorkflowEngine()
    print("✅ CompleteWorkflowEngine initialized successfully")
except Exception as e:
    print(f"⚠️ Could not import workflow engine: {e}")
    print(f"⚠️ Exception type: {type(e)}")
    import traceback
    print(f"⚠️ Full traceback: {traceback.format_exc()}")
    print("Using mock responses")
    workflow_engine = None

# Setup Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active workflows
active_workflows = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Learning-to-Content Python Backend",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0.0",
        "workflow_engine": "active" if workflow_engine else "mock"
    }), 200

@app.route('/webhook/learning-to-content', methods=['POST'])
def learning_to_content_webhook():
    """
    🎯 MAIN WEBHOOK ENDPOINT - FIXED PAYLOAD HANDLING
    """
    try:
        logger.info("🚀 Webhook request received")

        # Get headers and payload (support JSON or HTML form)
        headers = dict(request.headers)
        payload = request.get_json(silent=True) or {}
        if not payload and request.form:
            # Build JSON-like payload from form fields
            payload = {k: v for k, v in request.form.items()}
            # Coerce types
            payload["full_pipeline"] = str(payload.get("full_pipeline", "false")).lower() in ("1","true","yes","on")
            # Default platforms
            if not payload.get("platforms"):
                payload["platforms"] = ["YouTube Shorts", "Instagram Reels"]

        # Allow secret via form field or query param when testing manually
        if 'X-Webhook-Secret' not in headers:
            form_secret = (payload.get('webhook_secret') if isinstance(payload, dict) else None) or request.args.get('webhook_secret')
            if form_secret:
                headers['X-Webhook-Secret'] = form_secret

        logger.info(f"📥 Raw payload received: {json.dumps(payload, indent=2)}")

        if not payload:
            return jsonify({
                "success": False,
                "error": "No payload provided",
                "expected_format": {
                    "raw_notes": "Your content notes here",
                    "language": "Hinglish",
                    "tone": "Friendly",
                    "voice_gender": "Female",
                    "platforms": ["YouTube Shorts"],
                    "track_name": "Track Name"
                }
            }), 400

        # Check if payload is the problematic format from UI
        if "Implemented" in payload and isinstance(payload.get("Implemented"), dict):
            logger.warning("⚠️ Received UI feature payload instead of content payload")
            return jsonify({
                "success": False,
                "error": "Invalid payload format - received UI feature data instead of content data",
                "received_keys": list(payload.keys()),
                "expected_format": {
                    "raw_notes": "Your actual content notes here (not feature data)",
                    "language": "Hinglish",
                    "tone": "Friendly",
                    "voice_gender": "Female",
                    "platforms": ["YouTube Shorts"],
                    "track_name": "Track Name"
                },
                "fix_instructions": [
                    "1. Check your Streamlit UI form submission",
                    "2. Ensure 'raw_notes' field contains actual text content",
                    "3. Verify payload construction in UI code",
                    "4. Use the expected format shown above"
                ]
            }), 400

        # Validate required fields based on input_type (notes | script | prompt)
        input_type = str(payload.get('input_type', 'notes')).lower()
        if input_type == 'script':
            script_text = str(payload.get('script_text', '')).strip() or str(payload.get('script', '')).strip()
            if not script_text:
                return jsonify({
                    "success": False,
                    "error": "Missing required field: script_text for input_type=script",
                    "received_payload": {k: (v if k != 'script_text' else '<omitted>') for k, v in payload.items()}
                }), 400
        elif input_type == 'prompt':
            custom_prompt = str(payload.get('custom_prompt', '')).strip()
            raw_notes = str(payload.get('raw_notes', '')).strip()
            if not custom_prompt and not raw_notes:
                return jsonify({
                    "success": False,
                    "error": "Provide custom_prompt (preferred) or raw_notes for input_type=prompt",
                    "received_payload": payload
                }), 400
        else:
            # Default notes mode
            raw_notes = str(payload.get('raw_notes', '')).strip()
            if not raw_notes:
                return jsonify({
                    "success": False,
                    "error": "raw_notes field cannot be empty for input_type=notes",
                    "received_raw_notes": payload.get('raw_notes', '')
                }), 400

        # Generate workflow ID
        workflow_id = f"workflow_{int(time.time())}"

        # Store workflow info
        active_workflows[workflow_id] = {
            "status": "Processing",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "payload": payload
        }

        logger.info(f"🔄 Initial workflow status set: {workflow_id} → Processing")

        logger.info(f"✅ Valid payload received for workflow: {workflow_id}")
        # Safe input preview depending on mode
        _it = str(payload.get('input_type', 'notes')).lower()
        if _it == 'script':
            _preview = (str(payload.get('script_text', '')) or str(payload.get('script', ''))).strip()[:100]
        elif _it == 'prompt':
            _preview = (str(payload.get('custom_prompt', '')) or str(payload.get('raw_notes', ''))).strip()[:100]
        else:
            _preview = str(payload.get('raw_notes', '')).strip()[:100]
        logger.info(f"📝 Input preview: {_preview}")

        # Status update callback function
        def update_workflow_status(wf_id, status):
            """Update workflow status in active_workflows"""
            if wf_id in active_workflows:
                active_workflows[wf_id]["status"] = status
                active_workflows[wf_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"🔄 Workflow status updated: {wf_id} → {status}")

        # Process workflow
        def process_workflow():
            try:
                if workflow_engine:
                    logger.info(f"🎯 Processing with workflow engine: {workflow_id}")

                    # Set up status callback for real-time updates
                    workflow_engine.status_callback = update_workflow_status

                    response_data, status_code = workflow_engine.process_webhook_request(headers, payload, workflow_id)
                else:
                    logger.info(f"🎯 Processing with mock engine: {workflow_id}")
                    # Mock response for testing with status updates
                    update_workflow_status(workflow_id, "Script Generated")
                    time.sleep(2)
                    update_workflow_status(workflow_id, "Audio Generated")
                    time.sleep(2)
                    update_workflow_status(workflow_id, "Images Generated")
                    time.sleep(2)
                    update_workflow_status(workflow_id, "Video Generated")
                    time.sleep(1)

                    response_data = {
                        "ok": True,
                        "message": "Mock processing completed",
                        "workflow_id": workflow_id,
                        "topics_extracted": 1,
                        "status": "Completed"
                    }
                    status_code = 200

                # Update workflow status
                active_workflows[workflow_id].update({
                    "status": "Completed" if status_code == 200 else "Failed",
                    "response": response_data,
                    "status_code": status_code,
                    # propagate error message for non-200 responses so UI can show it
                    "error": (response_data.get("error") if isinstance(response_data, dict) else None) if status_code != 200 else None,
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })

                logger.info(f"✅ Workflow completed: {workflow_id}")

            except Exception as e:
                logger.error(f"❌ Workflow failed: {workflow_id} - {e}")
                active_workflows[workflow_id].update({
                    "status": "Failed",
                    "error": str(e),
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })

        # Start background processing
        thread = threading.Thread(target=process_workflow)
        thread.daemon = True
        thread.start()

        # Return immediate response
        return jsonify({
            "success": True,
            "message": "Workflow started successfully",
            "workflow_id": workflow_id,
            # Backward-compatible preview plus generic input preview
            "raw_notes_preview": _preview,
            "input_preview": _preview,
            "language": payload.get("language", "Hinglish"),
            "tone": payload.get("tone", "Friendly"),
            "voice_gender": payload.get("voice_gender", "Female"),
            "platforms": payload.get("platforms", ["YouTube Shorts"]),
            "status_url": f"/api/workflow/status/{workflow_id}",
            "estimated_completion": "5-10 minutes",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 202  # Accepted for processing

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/api/workflow/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Get workflow status"""
    try:
        if workflow_id not in active_workflows:
            return jsonify({"error": "Workflow not found"}), 404

        workflow_info = active_workflows[workflow_id]

        return jsonify({
            "workflow_id": workflow_id,
            "status": workflow_info["status"],
            "started_at": workflow_info["started_at"],
            "completed_at": workflow_info.get("completed_at"),
            "response": workflow_info.get("response"),
            "error": workflow_info.get("error")
        }), 200

    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/ensure-db', methods=['POST'])
def ensure_db():
    """Ensure Google Sheets tabs exist with correct headers; optional reset."""
    try:
        reset = str(request.args.get('reset', 'false')).lower() in ('1','true','yes','on')
        print(f"🔍 ensure-db called with reset={reset}")
        print(f"🔍 workflow_engine is: {workflow_engine}")
        print(f"🔍 workflow_engine type: {type(workflow_engine)}")

        if not workflow_engine:
            print("⚠️ workflow_engine is None, trying to create temporary engine")
            # Try to create a temporary engine just for this operation
            try:
                from backend.workflow_engine import CompleteWorkflowEngine
                temp_engine = CompleteWorkflowEngine()
                print("✅ Temporary engine created successfully")
                result = temp_engine.ensure_db_schema(reset=reset)
                print(f"✅ ensure_db_schema result: {result}")
                return jsonify({"ok": True, **result}), 200
            except Exception as temp_e:
                print(f"❌ Temporary engine failed: {temp_e}")
                return jsonify({"ok": False, "error": f"engine not available: {str(temp_e)}"}), 500

        print("✅ Using existing workflow_engine")
        result = workflow_engine.ensure_db_schema(reset=reset)
        print(f"✅ ensure_db_schema result: {result}")
        return jsonify({"ok": True, **result}), 200
    except Exception as e:
        print(f"❌ ensure-db error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/admin/db-status', methods=['GET'])
def db_status():
    """Get database status and record counts."""
    try:
        # Get record counts from each sheet
        tables = {}

        if not workflow_engine:
            return jsonify({"error": "Workflow engine not available"}), 500

        # Try to get EssentialContent count
        try:
            ec_sheet = workflow_engine.gc.open_by_key(workflow_engine.sheet_id).worksheet("EssentialContent")
            ec_records = ec_sheet.get_all_records()
            tables['EssentialContent'] = len(ec_records)
        except Exception as e:
            logger.warning(f"Could not get EssentialContent count: {e}")
            tables['EssentialContent'] = 0

        # Try to get APIUsage count
        try:
            api_sheet = workflow_engine.gc.open_by_key(workflow_engine.sheet_id).worksheet("APIUsage")
            api_records = api_sheet.get_all_records()
            tables['APIUsage'] = len(api_records)
        except Exception as e:
            logger.warning(f"Could not get APIUsage count: {e}")
            tables['APIUsage'] = 0

        # Try to get ErrorLog count
        try:
            error_sheet = workflow_engine.gc.open_by_key(workflow_engine.sheet_id).worksheet("ErrorLog")
            error_records = error_sheet.get_all_records()
            tables['ErrorLog'] = len(error_records)
        except Exception as e:
            logger.warning(f"Could not get ErrorLog count: {e}")
            tables['ErrorLog'] = 0

        return jsonify({
            "success": True,
            "tables": tables,
            "total_records": sum(tables.values())
        })

    except Exception as e:
        logger.error(f"❌ Database status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/files/<path:filename>')
def serve_generated_file(filename):
    base_dir = "/app/generated_content"
    # Support subfolders: videos/, images/, audio/
    for sub in ["videos", "images", "audio"]:
        full_dir = os.path.join(base_dir, sub)
        candidate = os.path.join(full_dir, filename)
        if os.path.exists(candidate):
            return send_from_directory(full_dir, filename)
    return jsonify({"error": "file not found"}), 404

@app.route('/')
def manual_test_form():
    form_html = """
    <html><body style='font-family:system-ui;padding:20px'>
    <h2>Learning-to-Content Backend - Manual Test</h2>
    <form method='post' action='/webhook/learning-to-content'>
      <label>Raw Notes</label><br/>
      <textarea name='raw_notes' rows='8' cols='80'>Paste notes here…</textarea><br/>
      <label>Language</label>
      <select name='language'>
        <option>Hinglish</option>
        <option>English</option>
        <option>Hindi</option>
      </select>
      <label>Tone</label>
      <select name='tone'><option>Educational</option><option>Friendly</option></select>
      <label>Voice Gender</label>
      <select name='voice_gender'><option>Female</option><option>Male</option></select>
      <input type='hidden' name='full_pipeline' value='true' />
      <p>Use an HTTP client like curl or Postman to send header X-Webhook-Secret.</p>
      <button type='submit'>Send</button>
    </form>
    </body></html>
    """
    return render_template_string(form_html)


@app.route('/api/features', methods=['GET'])
def get_features():
    """Get feature list"""
    return jsonify({
        "backend_status": "active",
        "workflow_engine": "active" if workflow_engine else "mock",
        "features": {
            "topic_extraction": "✅ Implemented",
            "script_generation": "✅ Implemented",
            "audio_generation": "✅ Implemented",
            "image_generation": "✅ Implemented",
            "video_assembly": "✅ Implemented",
            "google_sheets": "✅ Implemented",
            "google_drive": "✅ Implemented",
            "status_flow": "✅ Implemented"
        },
        "payload_format": {
            "raw_notes": "Required - Your actual content notes",
            "language": "Optional - Default: Hinglish",
            "tone": "Optional - Default: Friendly",
            "voice_gender": "Optional - Default: Female",
            "platforms": "Optional - Default: [YouTube Shorts]",
            "track_name": "Optional - Default: Default Track"
        }
    }), 200

def main():
    """Start the backend server"""
    print("🎯 LEARNING-TO-CONTENT PYTHON BACKEND")
    print("=" * 60)
    print("🔧 Fixed payload processing issue")
    print("✅ Proper error handling and validation")
    print("🎬 100% feature parity with n8n workflow")
    print("=" * 60)

    # Check environment
    required_env_vars = ["GOOGLE_SHEET_ID", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print("⚠️ Missing environment variables (will use mock mode):")
        for var in missing_vars:
            print(f"   - {var}")
    else:
        print("✅ Environment variables configured")
    print("\nENDPOINTS:")
    print("Main Webhook: http://localhost:9000/webhook/learning-to-content")
    print("Health Check: http://localhost:9000/health")
    print("Features: http://localhost:9000/api/features")
    print("Status: http://localhost:9000/api/workflow/status/<id>")
    print("\nStarting server on port 9000...")
    # Start Flask server
    app.run(host='0.0.0.0', port=9000, debug=False, threaded=True)

if __name__ == "__main__":
    main()
