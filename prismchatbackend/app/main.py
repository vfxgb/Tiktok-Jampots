

import os
import uuid
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .schemas import SendPayload, SendResult, ConversationHistory
from .db import insert_message, get_messages, upload_image_bytes, get_conn
from psycopg2.extras import RealDictCursor
from .chain import run_chain

app = FastAPI(title="PrismChat Backend", version="0.1.0")

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
async def upload(files: List[UploadFile] = File(...)):
    try:
        urls = []
        for f in files:
            data = await f.read()
            url = upload_image_bytes(f.filename, data, f.content_type or "application/octet-stream")
            urls.append(url)
        return {"urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat", response_model=SendResult)
def chat(payload: SendPayload):
    try:
        conv_id = payload.conversation_id
        if not conv_id:
            raise HTTPException(status_code=400, detail="conversationId is required")

        # 1) Fetch history BEFORE inserting the current user turn
        #    so we don't double-inject the same user text into the LLM
        history = [m.model_dump(by_alias=True) for m in get_messages(conv_id)]

        # 2) Run chain with existing history + current user input (not yet persisted)
        prismguard = payload.route == "prismguard"
        answer = run_chain(history, payload.text, payload.images, prismguard=prismguard)

        # 3) Now persist the current user turn (if present), then the assistant reply
        if payload.text or payload.images:
            insert_message(conv_id, role="user", content=payload.text or "", images=payload.images)

        insert_message(conv_id, role="assistant", content=answer, images=[])

        # 4) Return the updated thread
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