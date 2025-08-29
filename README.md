# Tiktok-Jampots

We are the Tiktok-Jampot and we have decided to tackle issues pertaining to Personally Identifiable Information pertaining to LLM-powered Applications. In this case, we decided to look at chatbots that send text or image prompts to external LLM APIs. Our solution is called PrismGuard.

# 🛡 PrismGuard
**Multi-Modal Privacy Firewall for the AI Era**

PrismGuard is a two-layer system that protects Personally Identifiable Information (PII) before it ever reaches an external AI service.  
Think of it as a **VPN for your prompts and images**: everything you send to an LLM or AI API first passes through PrismGuard, where sensitive details are detected, anonymized, and logged transparently.

---

## Features

- **Text Privacy Shield**  
  - Regex + AI NER detection for names, emails, phone numbers, IDs.  
  - Modes:  
    - **Strict** → replace PII with `[REDACTED]`.  
    - **Smart** → replace with plausible pseudonyms.  

- **Image Privacy Shield**  
  - Detects faces, license plates, and ID cards using YOLO.  
  - Blurs or masks sensitive regions automatically.  
  - Optional OCR to catch text in photos (name tags, documents).  

- **Two-Backend Architecture**  
  - **Gateway** (edge): performs all redaction, never logs raw PII, signs requests with a *Privacy-Attestation*.  
  - **Orchestrator** (core): handles LLM calls, only accepts sanitized requests, enforces zero-trust separation.  

- **Two Frontends (built with Lynx)**  
  - **Privacy Chat**: a user-facing chatbot UI to demo safe prompts and blurred images.  
  - **Privacy Control Center**: an admin dashboard with metrics, entity distribution, policy sliders, and audit logs.  

- **Explainable Privacy**  
  - Side-by-side before/after view for text and images.  
  - Heatmap highlighting which spans/regions were flagged.  
  - Transparent logs: entity type + confidence, never the raw value.  

---

## Architecture

```plaintext
Frontend A (Privacy Chat)  →  Gateway Backend  →  Orchestrator Backend  →  LLM Provider
Frontend B (Control Center) ↗︎
