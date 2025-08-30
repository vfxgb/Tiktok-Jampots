# 🛡️ PrismGuard

**Multi-Modal Privacy Firewall for the AI Era**

PrismGuard is a comprehensive privacy-first conversational AI platform that protects Personally Identifiable Information (PII) before it ever reaches external AI services. Think of it as a **VPN for your prompts and images** - everything passes through PrismGuard's privacy layers first.

Youtube Link for the Project Submission: https://youtu.be/a9anWGeS6T8 

---

## 🏗️ Complete System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[Next.js Chat UI<br/>TypeScript + Tailwind<br/>Image Upload<br/>Markdown Chat]
    end
    
    subgraph "Backend Layer"  
        BE[PrismChat Backend :8000<br/>FastAPI + Docker<br/>LangChain/LangGraph<br/>LangSmith Tracing]
    end
    
    subgraph "Privacy Gateway Layer"
        GW[Gateway :8080<br/>Single Entry Point<br/>Audit Logging<br/>Auth & Storage]
    end
    
    subgraph "PrismGuard Services"
        VISION[Vision Service :8081<br/>YOLOv8 Detection<br/>Face & ID Blurring<br/>OCR Text Detection]
        
        LLM_GUARD[Text Guard :8082<br/>TinyBERT 4L-312D<br/>PII Detection<br/>Real-time Redaction]
    end
    
    subgraph "External Services"
        GEMINI[Google Gemini 2.0 Flash<br/>Fast Inference<br/>Multimodal AI]
        
        LANGSMITH[LangSmith<br/>Tracing & Analytics<br/>Observability]
    end
    
    subgraph "Data Layer"
        SB[(Supabase<br/>PostgreSQL<br/>File Storage<br/>RLS)]
        
        BUCKETS[(Storage Buckets<br/>prismchat raw<br/>prismguard-redacted<br/>Private + Signed URLs)]
    end
    
    %% User Flow
    FE -->|1. Chat Request| BE
    BE -->|2. Privacy Check| GW
    
    %% Privacy Processing  
    GW -->|3a. Image Anonymization| VISION
    GW -->|3b. Text Anonymization| LLM_GUARD
    
    VISION -->|4a. Blurred Images| GW
    LLM_GUARD -->|4b. Redacted Text| GW
    
    %% Storage & Processing
    GW -->|5. Store Redacted Assets| BUCKETS
    GW -->|6. Return Safe Content| BE
    
    %% AI Processing
    BE -->|7. Safe Prompt + Images| GEMINI
    GEMINI -->|8. AI Response| BE
    
    %% Persistence
    BE -->|9. Chat History| SB
    BE -->|10. Final Response| FE
    
    %% Observability
    BE -.->|Tracing| LANGSMITH
    GW -.->|Audit Logs| SB
    
    %% Styling
    classDef frontend fill:#4F46E5,stroke:#312E81,stroke-width:2px,color:#fff
    classDef backend fill:#059669,stroke:#064E3B,stroke-width:2px,color:#fff
    classDef privacy fill:#DC2626,stroke:#991B1B,stroke-width:2px,color:#fff
    classDef ai fill:#7C3AED,stroke:#5B21B6,stroke-width:2px,color:#fff
    classDef storage fill:#EA580C,stroke:#9A3412,stroke-width:2px,color:#fff
    
    class FE frontend
    class BE backend
    class GW,VISION,LLM_GUARD privacy
    class GEMINI,LANGSMITH ai
    class SB,BUCKETS storage
```

---

## 🔄 Detailed Data Flow

### 1️⃣ User Interaction
```
User types: "Hi, I'm John Doe, my SSN is 123-45-6789"
User uploads: [ID_photo.jpg]
```

### 2️⃣ Frontend Processing
- **Next.js Chat UI** captures user input
- Sends `POST /v1/chat` to PrismChat Backend
- Includes: `conversation_id`, `text`, `images[]`, `prismguard: true`

### 3️⃣ Backend Orchestration
- **FastAPI Backend** receives request
- Routes through **LangChain/LangGraph** pipeline
- Forwards to **Gateway** for privacy processing

### 4️⃣ Privacy Gateway Processing
```
POST /v1/gateway/text
{
  "text": "Hi, I'm John Doe, my SSN is 123-45-6789",
  "mode": "strict"
}

POST /v1/gateway/image
multipart/form-data: file=ID_photo.jpg
```

### 5️⃣ Text Anonymization (TinyBERT 4L-312D)
```python
# Input Text Processing
original = "Hi, I'm John Doe, my SSN is 123-45-6789"

# Output
redacted = "Hi, I'm John Doe, my SSN is [REDACTED]"

```

### 6️⃣ Image Anonymization (YOLOv8 + OpenCV)
```python
# Vision Pipeline
1. YOLOv8 detects: faces, license plates, ID cards
2. OCR extracts: text regions, ID numbers, addresses  
3. OpenCV applies: Gaussian blur to detected regions
4. Result: Fully anonymized image

# Detected regions example
entities = [
  {"label": "face", "conf": 0.99, "bbox": [45, 23, 156, 134]},
  {"label": "id_text", "conf": 0.87, "bbox": [200, 300, 400, 350]}
]
```

### 7️⃣ Secure Storage
```
Original Image -> ❌ (Never stored)
Redacted Image -> ✅ Supabase Storage
Path: prismguard-redacted/{conversation_id}/image_uuid.png
Access: Private bucket with signed URLs (24h expiry)
```

### 8️⃣ AI Processing
```
# What Gemini receives:
text = "Hi, I'm [NAME], my SSN is [SSN]"
images = ["https://supabase.co/storage/sign/redacted_image.png?token=..."]

# What Gemini responds:
"Hello! I understand you've shared some personal information. 
I can help you with questions while keeping your privacy protected."
```

---

## 🛠️ Tech Stack Deep Dive

### Frontend Stack
```typescript
// Next.js 14 + TypeScript
- App Router for modern routing
- Tailwind CSS for styling  
- Marked + DOMPurify for safe Markdown
- Image optimization with next/image
- Real-time chat interface
```

### Backend Stack
```python
# FastAPI + Python Ecosystem
- LangChain: Prompt engineering & chains
- LangGraph: Stateful conversation flow
- LangSmith: Distributed tracing
- Supabase Python Client: Database & storage
- Google Gemini: Latest multimodal LLM
```

### Privacy Stack
```python
# PrismGuard Services
- TinyBERT 4L-312D: Fine-tuned on AI4Privacy dataset
- YOLOv8: Real-time object detection
- OpenCV: Image processing & blurring
- Tesseract OCR: Text extraction from images
- FastAPI: High-performance API services
```

---

## 🚀 Quick Start Guide

### Prerequisites
```bash
# Required
- Docker & Docker Compose
- Node.js 18+ 
- Supabase account
- Google AI API key
- LangSmith account (optional)
```

### 1️⃣ Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/prismguard
cd prismguard

# Copy environment template
cp .env.example .env

# Update .env with your keys
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key
GOOGLE_API_KEY=your-gemini-key
LANGCHAIN_API_KEY=your-langsmith-key
```

### 2️⃣ Backend Services
```bash
# Start all privacy services
docker-compose up -d --build

# Services will be available at:
# - Gateway: http://localhost:8080
# - Vision: http://localhost:8081  
# - Text Guard: http://localhost:8082
# - PrismChat Backend: http://localhost:8000
```

### 3️⃣ Frontend
```bash
# Install and start Next.js
cd prismchatfrontend2/prismchat
npm install
npm run dev

# Frontend available at: http://localhost:3000
```

---

### Architecture Decisions
- **Microservices**: Independent scaling of privacy components
- **FastAPI**: High-performance async Python APIs
- **Supabase**: Postgres + Storage + Auth in one platform  
- **Docker**: Consistent deployment across environments
- **LangChain**: Standardized LLM orchestration

---

## 🙏 Acknowledgements

- **AI4Privacy Dataset**: Training data for PII detection
- **Hugging Face**: Transformer models and training infrastructure
- **LangChain Ecosystem**: LLM orchestration and tracing
- **Supabase**: Backend-as-a-Service platform
- **Google AI**: Gemini multimodal capabilities
- **Varun Gupta**: YOLOv8 model and dashcam anonymizer implementation ([dashcam_anonymizer](https://github.com/varungupta31/dashcam_anonymizer)) - our vision component builds upon this excellent work

---
**🛡️ PrismGuard - Privacy-First AI for Everyone**
