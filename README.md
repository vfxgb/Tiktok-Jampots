# Tiktok-Jampots

We are the Tiktok-Jampot and we have decided to tackle issues pertaining to Personally Identifiable Information pertaining to LLM-powered Applications. In this case, we decided to look at chatbots that send text or image prompts to external LLM APIs. Our solution is called PrismGuard.

# 🛡 PrismGuard
**Multi-Modal Privacy Firewall for the AI Era**

PrismGuard is a two-layer system that protects Personally Identifiable Information (PII) before it ever reaches an external AI service. 
Think of it as a **VPN for your prompts and images**: everything you send to an LLM or AI API first passes through PrismGuard, where sensitive details are detected, anonymized, and logged transparently.

⸻

PrismChat + PrismGuard 🔒🤖

A privacy-first conversational AI platform combining chat experiences with automatic PII detection and redaction for both text and images.

⸻

🚀 Overview

PrismChat has a Next.js frontend and a Dockerized FastAPI backend. It integrates LangChain and LangGraph for conversation orchestration, Supabase for storage, and LangSmith for observability.

When PrismGuard mode is activated:
	•	Text is filtered through a TinyBERT-based PII detector, fine-tuned on the AI4Privacy dataset. It tags and redacts sensitive tokens.
	•	Images are processed with a vision redaction pipeline (OCR + OpenCV) that blurs sensitive regions (faces, IDs, names, numbers).
	•	This ensures no raw PII leaves the system unprotected.

⸻

🏗️ Architecture

flowchart TD
    User[Next.js Chat UI] -->|API Calls| Backend[FastAPI Backend (Docker)]
    Backend -->|LangChain Runnable| Gemini[Google Gemini LLM]
    Backend -->|LangGraph| Langsmith[LangSmith Tracing]
    Backend --> Supabase[(Supabase Postgres + Storage)]
    Backend --> PrismGuard[PrismGuard Privacy Layer]
    PrismGuard --> TextModel[TinyBERT PII Detector]
    PrismGuard --> VisionModel[Vision OCR + Blur]
    Supabase -->|Signed URLs| Frontend


⸻

✨ Features
	•	Conversational Chatbot
	•	Powered by Google Gemini 2.0 Flash (via LangChain).
	•	Supports multimodal inputs (text + images).
	•	History-aware using LangGraph.
	•	PrismGuard (Privacy Layer)
	•	Text Privacy:
	•	Fine-tuned TinyBERT (General 4L-312D).
	•	Trained on AI4Privacy PII-Masking dataset (~300k samples).
	•	Labels: O, B-PII, I-PII (IOB tagging).
	•	Detects names, usernames, dates, IDs, numbers, etc.
	•	Exportable as TFLite (<40MB) for on-device use.
	•	Image Privacy:
	•	OpenCV to blur sensitive regions.
	•	OCR (Tesseract/Google Vision API) for text detection.
	•	Face/ID anonymization before storage.
	•	Tracing & Debugging
	•	LangSmith logs every conversation turn, including redactions.
	•	Storage (Supabase)
	•	Postgres: Chat history (chat_messages table).
	•	Storage Buckets:
	•	prismchat/ → raw uploads.
	•	prismguard-redacted/{conversation_id}/ → blurred/redacted versions.

⸻

🛠️ Tech Stack

Frontend
	•	Next.js 14 (React + SSR/SSG)
	•	TypeScript
	•	Tailwind CSS (dark ChatGPT-style UI)
	•	React Markdown Renderer

Backend
	•	FastAPI (Python, async API)
	•	Docker
	•	LangChain (prompt building, Gemini calls)
	•	LangGraph (state orchestration)
	•	LangSmith (tracing & debugging)

Privacy Models
	•	TinyBERT General 4L-312D (NER for PII)
	•	Fine-tuned with AI4Privacy dataset.
	•	Trained using Hugging Face Transformers.
	•	Optimized for mobile + edge.
	•	Vision Redaction Pipeline
	•	OCR (text extraction).
	•	OpenCV blurring.
	•	Optional face detection.

Infra
	•	Supabase (Postgres + Storage + Auth)
	•	Google Gemini API

⸻

📦 Setup

1. Clone repo

git clone https://github.com/your-org/prismchat.git
cd prismchat

2. Configure env vars

Backend .env:

SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
PG_CONN_STR=postgresql://user:pass@host:5432/dbname
GOOGLE_API_KEY=your-gemini-api-key
LANGCHAIN_API_KEY=your-langsmith-key

Frontend .env.local:

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

3. Run backend

cd prismchatbackend
docker-compose up --build

4. Run frontend

cd prismchatfrontend
cd prismchat
npm install
npm run dev


⸻

🔐 PrismGuard Training
	•	Dataset: AI4Privacy PII-Masking (300k examples).
	•	Framework: Hugging Face Transformers (PyTorch).
	•	NER Setup: Character spans → IOB tags.
	•	Model: TinyBERT 4L-312D (small, efficient).
	•	Training: AdamW (lr=3e-5), 4 epochs, early stopping.
	•	GPU: A100 on Google Colab.
	•	Metrics: Precision 80%, Recall 77%, F1 78%.


⸻

📊 Example Flow
	1.	User input:
"My name is John Doe and my phone number is 555-1234."
	2.	PrismGuard Text Model →
"My name is [NAME] and my phone number is [PHONE]."
	3.	Image (if uploaded) → blurred regions stored in Supabase.
	4.	Safe prompt → Gemini LLM.
	5.	LangSmith logs → full trace of redaction + LLM response.

⸻

🖥️ Future Work
	•	Add dashboard for auditing redacted conversations.
	•	Extend Vision to video + audio.
	•	Deploy TinyBERT as Firebase TFLite for mobile privacy.
	•	Add Supabase Auth RBAC for fine-grained controls.

⸻

👥 Team Notes
	•	Built during ByteDance TechJam 2025.
	•	Highlights responsible AI — using AI itself to enforce privacy.
	•	Combines state-of-the-art NLP, CV, and infra into a production-ready system.

⸻
