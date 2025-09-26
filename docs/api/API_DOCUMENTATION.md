# 🎯 API Documentation - Learning-to-Content Python Backend

## 📋 API Overview

The Python backend provides a RESTful API that exactly replicates the n8n webhook functionality with additional endpoints for status monitoring and file downloads.

**Base URL**: `http://localhost:9000`

---

## 🎯 Core Endpoints

### **1. 🎬 Main Webhook Endpoint**

**Endpoint**: `POST /webhook/learning-to-content`  
**Description**: Main entry point that processes the complete workflow  
**Content-Type**: `application/json`

#### **Request Payload**
```json
{
  "raw_notes": "Your raw notes content here",
  "language": "Hinglish",
  "tone": "Friendly", 
  "voice_gender": "Female",
  "platforms": ["YouTube Shorts", "Instagram"],
  "track_name": "SkillBox 1",
  "posts_per_day": 1
}
```

#### **Payload Fields**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `raw_notes` | string | ✅ Yes | - | Raw content notes from user |
| `language` | string | ❌ No | "Hinglish" | Content language |
| `tone` | string | ❌ No | "Friendly" | Content tone |
| `voice_gender` | string | ❌ No | "Female" | TTS voice gender |
| `platforms` | array | ❌ No | ["YouTube Shorts"] | Target platforms |
| `track_name` | string | ❌ No | "Default Track" | Content track name |
| `posts_per_day` | integer | ❌ No | 1 | Posts per day setting |

#### **Success Response (200)**
```json
{
  "success": true,
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "Processing",
  "message": "Workflow started successfully",
  "result": {
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "steps_completed": ["topic_extraction", "script_generation"],
    "final_status": "Processing"
  }
}
```

#### **Error Response (400/500)**
```json
{
  "success": false,
  "error": "raw_notes field is required",
  "message": "Workflow processing failed"
}
```

#### **cURL Example**
```bash
curl -X POST http://localhost:9000/webhook/learning-to-content \
  -H "Content-Type: application/json" \
  -d '{
    "raw_notes": "Learn about Python programming basics",
    "language": "Hinglish",
    "tone": "Friendly",
    "voice_gender": "Female",
    "platforms": ["YouTube Shorts"],
    "track_name": "Python Basics"
  }'
```

---

### **2. 📊 Workflow Status Endpoint**

**Endpoint**: `GET /api/workflow/status/<workflow_id>`  
**Description**: Get real-time status of a specific workflow

#### **Request**
```
GET /api/workflow/status/550e8400-e29b-41d4-a716-446655440000
```

#### **Success Response (200)**
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "AudioGenerated",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:15Z",
  "found": true
}
```

#### **Not Found Response (404)**
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "found": false,
  "message": "Workflow not found"
}
```

---

### **3. 🎯 Features Endpoint**

**Endpoint**: `GET /api/features`  
**Description**: Get complete list of backend features and capabilities

#### **Response (200)**
```json
{
  "features": {
    "topic_extraction": {
      "provider": "Gemini API",
      "model": "gemini-1.5-flash-latest",
      "status": "active"
    },
    "script_generation": {
      "provider": "Gemini API", 
      "model": "gemini-1.5-flash-latest",
      "status": "active"
    },
    "audio_generation": {
      "provider": "Google Cloud TTS",
      "voices": {
        "Male": "en-US-Journey-D",
        "Female": "en-US-Journey-F"
      },
      "status": "active"
    },
    "image_generation": {
      "providers": [
        {
          "name": "Cloudflare Workers AI",
          "model": "stable-diffusion-xl-base-1.0",
          "priority": 1,
          "status": "active"
        },
        {
          "name": "Together AI",
          "model": "stabilityai/stable-diffusion-xl-base-1.0", 
          "priority": 2,
          "status": "active"
        },
        {
          "name": "HuggingFace",
          "model": "stabilityai/stable-diffusion-xl-base-1.0",
          "priority": 3,
          "status": "active"
        }
      ]
    },
    "video_assembly": {
      "tool": "FFmpeg",
      "format": "MP4",
      "resolution": "1080x1920",
      "duration": "40 seconds",
      "status": "active"
    },
    "storage": {
      "provider": "Google Drive",
      "folders": {
        "audio": "Audio Files",
        "images": "Generated Images", 
        "videos": "Final Videos"
      },
      "status": "active"
    },
    "database": {
      "provider": "Google Sheets",
      "worksheets": [
        "Topic Backlog",
        "Generated Content",
        "API_Usage", 
        "ErrorLog"
      ],
      "status": "active"
    }
  },
  "status_flow": [
    "Pending",
    "ScriptGenerated", 
    "AudioGenerated",
    "ImagesGenerated",
    "VideoGenerated",
    "Completed"
  ],
  "supported_languages": [
    "Hinglish",
    "English",
    "Hindi"
  ],
  "supported_tones": [
    "Friendly",
    "Professional",
    "Casual",
    "Educational"
  ],
  "supported_platforms": [
    "YouTube Shorts",
    "Instagram",
    "TikTok"
  ]
}
```

---

### **4. 💾 File Download Endpoint**

**Endpoint**: `GET /download/<filename>`  
**Description**: Download generated files (audio, images, videos)

#### **Request**
```
GET /download/550e8400-e29b-41d4-a716-446655440000_final_video.mp4
```

#### **Success Response (200)**
- **Content-Type**: Appropriate MIME type (video/mp4, audio/mpeg, image/png)
- **Content-Disposition**: attachment; filename="filename"
- **Body**: File binary data

#### **Not Found Response (404)**
```json
{
  "error": "File not found",
  "filename": "550e8400-e29b-41d4-a716-446655440000_final_video.mp4"
}
```

---

### **5. 🏥 Health Check Endpoint**

**Endpoint**: `GET /health`  
**Description**: Check backend service health and all integrations

#### **Response (200)**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "gemini_api": {
      "status": "connected",
      "response_time_ms": 150
    },
    "google_tts": {
      "status": "connected", 
      "response_time_ms": 200
    },
    "cloudflare_api": {
      "status": "connected",
      "response_time_ms": 300
    },
    "together_api": {
      "status": "connected",
      "response_time_ms": 250
    },
    "huggingface_api": {
      "status": "connected",
      "response_time_ms": 400
    },
    "google_drive": {
      "status": "connected",
      "response_time_ms": 180
    },
    "google_sheets": {
      "status": "connected",
      "response_time_ms": 220
    },
    "ffmpeg": {
      "status": "available",
      "version": "4.4.2"
    }
  },
  "database_connection": "active",
  "storage_connection": "active"
}
```

---

## 🔧 Error Handling

### **Standard Error Response Format**
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_CODE",
  "message": "User-friendly error message",
  "timestamp": "2024-01-15T10:30:00Z",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000" // if applicable
}
```

### **Common Error Codes**
| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field missing from payload | 400 |
| `INVALID_PAYLOAD` | Malformed JSON payload | 400 |
| `WORKFLOW_NOT_FOUND` | Workflow ID not found | 404 |
| `API_SERVICE_ERROR` | External API service error | 502 |
| `STORAGE_ERROR` | File storage operation failed | 500 |
| `DATABASE_ERROR` | Database operation failed | 500 |
| `PROCESSING_ERROR` | General workflow processing error | 500 |

---

## 🎯 Status Flow

### **Workflow Status Values**
| Status | Description | Next Status |
|--------|-------------|-------------|
| `Pending` | Workflow started, processing topic extraction | `ScriptGenerated` |
| `ScriptGenerated` | Topic extracted and script generated | `AudioGenerated` |
| `AudioGenerated` | Audio file created from script | `ImagesGenerated` |
| `ImagesGenerated` | All 4 images generated successfully | `VideoGenerated` |
| `VideoGenerated` | Video assembled from audio and images | `Completed` |
| `Completed` | All files uploaded and database updated | - |
| `Error` | Workflow failed at some step | - |

---

## 🔐 Authentication

### **API Key Authentication (Optional)**
If webhook secret is configured:

```bash
curl -X POST http://localhost:9000/webhook/learning-to-content \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_webhook_secret_here" \
  -d '{"raw_notes": "content"}'
```

---

## 📊 Rate Limiting

### **Default Limits**
- **Webhook Endpoint**: 10 requests per minute per IP
- **Status Endpoint**: 60 requests per minute per IP  
- **Features Endpoint**: 30 requests per minute per IP
- **Download Endpoint**: 20 requests per minute per IP

### **Rate Limit Headers**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1642248600
```

---

## 🎯 Integration Examples

### **JavaScript/Frontend Integration**
```javascript
// Send workflow request
async function startWorkflow(payload) {
  const response = await fetch('http://localhost:9000/webhook/learning-to-content', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Start polling for status updates
    pollWorkflowStatus(result.workflow_id);
  }
  
  return result;
}

// Poll workflow status
async function pollWorkflowStatus(workflowId) {
  const response = await fetch(`http://localhost:9000/api/workflow/status/${workflowId}`);
  const status = await response.json();
  
  console.log(`Workflow ${workflowId} status: ${status.status}`);
  
  if (status.status !== 'Completed' && status.status !== 'Error') {
    // Continue polling every 5 seconds
    setTimeout(() => pollWorkflowStatus(workflowId), 5000);
  }
}
```

### **Python Client Integration**
```python
import requests
import time

def start_workflow(payload):
    """Start workflow and return workflow_id"""
    response = requests.post(
        'http://localhost:9000/webhook/learning-to-content',
        json=payload
    )
    
    result = response.json()
    
    if result['success']:
        return result['workflow_id']
    else:
        raise Exception(f"Workflow failed: {result['error']}")

def wait_for_completion(workflow_id, timeout=300):
    """Wait for workflow completion with timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f'http://localhost:9000/api/workflow/status/{workflow_id}')
        status = response.json()
        
        if status['status'] == 'Completed':
            return True
        elif status['status'] == 'Error':
            return False
        
        time.sleep(5)  # Poll every 5 seconds
    
    return False  # Timeout

# Usage example
payload = {
    "raw_notes": "Learn Python programming basics",
    "language": "Hinglish",
    "tone": "Friendly",
    "voice_gender": "Female"
}

workflow_id = start_workflow(payload)
success = wait_for_completion(workflow_id)

if success:
    print(f"Workflow {workflow_id} completed successfully!")
else:
    print(f"Workflow {workflow_id} failed or timed out")
```

---

## 🎯 Complete API Feature Parity

This API provides **100% feature parity** with the original n8n webhook while adding:

✅ **Real-time status monitoring**  
✅ **Comprehensive error handling**  
✅ **File download capabilities**  
✅ **Health monitoring**  
✅ **Feature discovery**  
✅ **Rate limiting**  
✅ **Better documentation**  
✅ **Client integration examples**  

The API is a **complete replacement** for n8n webhook functionality with enhanced capabilities.
