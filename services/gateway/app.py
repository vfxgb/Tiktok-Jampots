import os, base64, uuid, json, time, collections
import httpx
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ---- config
VISION_URL = os.getenv("VISION_URL", "http://prismguard-vision:8081")
LLM_URL    = os.getenv("LLM_URL", "http://prismguard-llm:8082")  
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "prismguard-redacted")

# Firebase admin 
VERIFY_TOKENS = True if os.getenv("FIREBASE_ADMIN_CREDENTIALS_FILE") else False
if VERIFY_TOKENS:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth
    cred = credentials.Certificate(os.getenv("FIREBASE_ADMIN_CREDENTIALS_FILE"))
    firebase_admin.initialize_app(cred)

app = FastAPI(title="PrismGuard Gateway", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

async def verify_auth(authorization: str | None) -> str | None:
    """
    Returns user_id (uid) if verified, else None in dev.
    Accepts Firebase ID token in 'Authorization: Bearer <token>'.
    """
    if not VERIFY_TOKENS:
        return "dev-user"
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        decoded = fb_auth.verify_id_token(token, check_revoked=True)
        return decoded.get("uid")
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

async def supabase_insert_audit(uid: str | None, event_type: str, entities: list, timing_ms: float):
    if not (SUPABASE_URL and SUPABASE_KEY):
        return
    # build simple histogram by label
    counts = collections.Counter([e.get("label","object") for e in (entities or [])])
    payload = {
        "user_id": uid,
        "event_type": event_type,
        "entity_counts": dict(counts),
        "timing_ms": timing_ms,
        "version": "gateway-0.1.0",
    }
    async with httpx.AsyncClient(timeout=10) as cli:
        r = await cli.post(f"{SUPABASE_URL}/rest/v1/audit_logs",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
            json=payload)
        r.raise_for_status()

async def supabase_upload_png(uid: str, b64: str) -> str | None:
    import base64, uuid, httpx, os
    if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_BUCKET):
        return None
    key = f"{uid}/images/{uuid.uuid4().hex}.png"
    data = base64.b64decode(b64)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30) as cli:
        up = await cli.post(
            f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{key}",
            headers={**headers, "Content-Type": "image/png", "x-upsert": "true"},
            content=data,
        )
        up.raise_for_status()
        sign = await cli.post(
            f"{SUPABASE_URL}/storage/v1/object/sign/{SUPABASE_BUCKET}/{key}",
            headers=headers,
            json={"expiresIn": 3600},
        )
        sign.raise_for_status()
        signed_path = sign.json().get("signedURL")
        return f"{SUPABASE_URL}/storage/v1/{signed_path}"

@app.get("/health")
def health(): return {"ok": True}

@app.post("/v1/gateway/image")
async def gateway_image(authorization: str | None = Header(None), file: UploadFile = File(...)):
    uid = await verify_auth(authorization)
    t0 = time.time()
    async with httpx.AsyncClient(timeout=120) as cli:
        files = {"file": (file.filename, await file.read(), file.content_type or "image/png")}
        vr = await cli.post(f"{VISION_URL}/v1/anonymize/image", files=files)
        if vr.status_code != 200:
            raise HTTPException(502, f"Vision error: {vr.text}")
        data = vr.json()
    timing_ms = data.get("timing_ms", (time.time()-t0)*1000.0)
    # optional: upload redacted artifact
    url = None
    if data.get("redacted_image_b64") and uid:
        try:
            url = await supabase_upload_png(uid, data["redacted_image_b64"])
        except Exception:
            url = None
    try:
        await supabase_insert_audit(uid, "image", data.get("entities", []), timing_ms)
    except Exception:
        pass
    return {
        "redacted_image_b64": data.get("redacted_image_b64"),
        "entities": data.get("entities", []),
        "timing_ms": timing_ms,
        "storage_url": url,
        "attestation": "v1",
    }

@app.post("/v1/gateway/text")
async def gateway_text(authorization: str | None = Header(None), body: dict = {}):
    uid = await verify_auth(authorization)
    payload = {"text": body.get("text",""), "mode": body.get("mode","smart")}
    # if you don't have the LLM service yet, return passthrough:
    if not LLM_URL:
        return {"redacted_text": payload["text"], "entities": [], "timing_ms": 0.0, "attestation": "v1"}
    t0 = time.time()
    async with httpx.AsyncClient(timeout=60) as cli:
        lr = await cli.post(f"{LLM_URL}/v1/anonymize/text", json=payload)
        if lr.status_code != 200:
            raise HTTPException(502, f"LLM error: {lr.text}")
        data = lr.json()
    try:
        await supabase_insert_audit(uid, "text", data.get("entities", []), data.get("timing_ms", (time.time()-t0)*1000.0))
    except Exception:
        pass
    data["attestation"] = "v1"
    return data
