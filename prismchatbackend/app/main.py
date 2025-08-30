import os
import uuid
from typing import List
import base64
import httpx

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .schemas import SendPayload, SendResult, ConversationHistory
from .db import insert_message, get_messages, upload_image_bytes, get_conn
from psycopg2.extras import RealDictCursor
from .chain import run_chain

app = FastAPI(title="PrismChat Backend", version="0.1.0")

PRISMGUARD_GATEWAY = os.getenv("PRISMGUARD_GATEWAY", "http://localhost:8080")

def _gateway_redact_text_sync(text: str, mode: str = "smart") -> str:
    if not text.strip():
        return text
    try:
        r = httpx.post(
            f"{PRISMGUARD_GATEWAY}/v1/gateway/text",
            json={"text": text, "mode": mode},
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("redacted_text", text)
    except Exception:
        # fail open: keep original if the gateway/LLM is down
        return text

async def _gateway_anonymize_text(text: str) -> dict:
    async with httpx.AsyncClient(timeout=120) as cli:
        r = await cli.post(f"{PRISMGUARD_GATEWAY}/v1/gateway/text",
                           json={"text": text})
        r.raise_for_status()
        return r.json()

async def _gateway_anonymize_image(file: UploadFile) -> dict:
    async with httpx.AsyncClient(timeout=120) as cli:
        files = {"file": (file.filename, await file.read(), file.content_type or "image/png")}
        r = await cli.post(f"{PRISMGUARD_GATEWAY}/v1/gateway/image", files=files)
        r.raise_for_status()
        return r.json()

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/v1/upload")
async def upload(files: List[UploadFile] = File(...), route: str = "default"):
    try:
        urls = []
        if route == "prismguard":
            for f in files:
                data = await _gateway_anonymize_image(f)

                if data.get("storage_url"):
                    urls.append(data["storage_url"])
                    continue

                b64 = data.get("redacted_image_b64")
                if not b64:
                    raise HTTPException(status_code=502, detail="Gateway returned no redacted image")
                png_bytes = base64.b64decode(b64)
                url = upload_image_bytes(f"redacted-{f.filename or 'image'}.png", png_bytes, "image/png")
                urls.append(url)
        else:
            for f in files:
                raw = await f.read()
                url = upload_image_bytes(f.filename, raw, f.content_type or "application/octet-stream")
                urls.append(url)
        return {"urls": urls}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat", response_model=SendResult)
def chat(payload: SendPayload):
    try:
        conv_id = payload.conversation_id
        if not conv_id:
            raise HTTPException(status_code=400, detail="conversationId is required")

        # 1) Load history BEFORE persisting the current user turn
        history = [m.model_dump(by_alias=True) for m in get_messages(conv_id)]

        # 2) PrismGuard text redaction (fail-open to original text if gateway fails)
        prismguard = payload.route == "prismguard"
        safe_text = payload.text
        if prismguard and payload.text:
            safe_text = _gateway_redact_text_sync(payload.text, mode="smart")

        # 3) Run LLM with safe_text (if prismguard) and current images
        answer = run_chain(history, safe_text, payload.images, prismguard=prismguard)

        # 4) Persist current user turn (safe_text) then assistant reply
        if safe_text or payload.images:
            insert_message(conv_id, role="user", content=safe_text or "", images=payload.images)
        insert_message(conv_id, role="assistant", content=answer, images=[])

        # 5) Return updated thread
        msgs = get_messages(conv_id)
        return {"conversationId": conv_id, "messages": msgs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/conversations/{conversation_id}", response_model=ConversationHistory)
def conversation_get(conversation_id: str):
    try:
        conv_uuid = uuid.UUID(conversation_id)
        msgs = get_messages(conv_uuid)
        return {"conversationId": conv_uuid, "messages": msgs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoint to list conversation summaries
@app.get("/v1/conversations")
def conversations_list():
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    select
                      conversation_id as id,
                      min(created_at) as created_at,
                      max(created_at) as updated_at,
                      coalesce(
                        (
                          select content from chat_history
                          where conversation_id = ch.conversation_id
                            and role = 'user'
                          order by created_at asc
                          limit 1
                        ),
                        'New chat'
                      ) as title
                    from chat_history ch
                    group by conversation_id
                    order by updated_at desc
                    limit 50;
                    """
                )
                rows = cur.fetchall() or []
        # Normalize keys to camelCase for frontend
        conversations = [
            {
                "id": r["id"],
                "title": r["title"],
                "createdAt": r["created_at"],
                "updatedAt": r["updated_at"],
            }
            for r in rows
        ]
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))