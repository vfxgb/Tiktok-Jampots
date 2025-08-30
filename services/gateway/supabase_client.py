import os
from supabase import create_client
import pathlib, time


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET", "prismguard-redacted")


sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def log_privacy(user_id: str, media_type: str, entities: list, policy: dict, attestation_id: str):
    sb.table("privacy_logs").insert({
    "user_id": user_id,
    "media_type": media_type,
    "entity": entities,
    "policy": policy,
    "attestation_id": attestation_id,
    }).execute()


def upload_and_sign(path: str, folder: str) -> str:
    p = pathlib.Path(path)
    dest = f"{folder}/{int(time.time())}-{p.name}"
    sb.storage.from_(BUCKET).upload(dest, p.read_bytes(), {"x-upsert": "true"})
    url = sb.storage.from_(BUCKET).create_signed_url(dest, 3600)
    return url["signedURL"]