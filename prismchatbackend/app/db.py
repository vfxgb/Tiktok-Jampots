import os
import uuid
from typing import List, Optional, Iterator
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, Json

from supabase import create_client, Client

from .schemas import ChatMessage

# --- Environment ---
SUPABASE_DB_URL = os.environ["SUPABASE_DB_URL"]

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "chat-images")

# --- Connection pool (psycopg2) ---
_pool: Optional[ThreadedConnectionPool] = None

def _get_pool() -> ThreadedConnectionPool:
  global _pool
  if _pool is None:
    _pool = ThreadedConnectionPool(
      minconn=1,
      maxconn=10,
      dsn=SUPABASE_DB_URL,
    )
  return _pool

@contextmanager
def get_conn():
  pool = _get_pool()
  conn = pool.getconn()
  try:
    yield conn
    conn.commit()
  except Exception:
    conn.rollback()
    raise
  finally:
    pool.putconn(conn)

# --- Supabase Storage client ---
_sb: Optional[Client] = None

def _sb_client() -> Client:
  global _sb
  if _sb is None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
      raise RuntimeError("Supabase Storage requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    _sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
  return _sb

def ensure_bucket():
  """Create bucket if missing; mark public."""
  sb = _sb_client()
  try:
    buckets = sb.storage.list_buckets()
    names = {b.name for b in buckets}
    if SUPABASE_BUCKET not in names:
      sb.storage.create_bucket(SUPABASE_BUCKET, public=True)
  except Exception as e:
    # Non-fatal in case of race
    print("ensure_bucket() warning:", e)

def upload_image_bytes(filename: str, data: bytes, content_type: str = "application/octet-stream") -> str:
  """Upload bytes to Supabase Storage and return a public URL."""
  ensure_bucket()
  sb = _sb_client()
  safe_name = filename.replace(" ", "_")
  key = f"{uuid.uuid4().hex}-{safe_name}"
  sb.storage.from_(SUPABASE_BUCKET).upload(
    key,
    data,
    {"content-type": content_type, "upsert": False},
  )
  url = sb.storage.from_(SUPABASE_BUCKET).get_public_url(key)
  return url

# --- Chat history helpers (single-table design) ---
def insert_message(conversation_id: uuid.UUID, role: str, content: str, images: Optional[List[str]] = None) -> ChatMessage:
  """Insert a message row and return it as ChatMessage."""
  with get_conn() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
      cur.execute(
        """
        insert into public.chat_history (conversation_id, role, content, images)
        values (%s, %s, %s, %s)
        returning id, role, content, images, created_at;
        """,
        (str(conversation_id), role, content or "", Json(images or [])),
      )
      row = cur.fetchone()
  return ChatMessage(
    id=row["id"],
    role=row["role"],
    content=row["content"],
    images=row.get("images") or [],
    created_at=row["created_at"],
  )

def get_messages(conversation_id: uuid.UUID) -> List[ChatMessage]:
  with get_conn() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
      cur.execute(
        """
        select id, role, content, images, created_at
        from public.chat_history
        where conversation_id = %s
        order by created_at asc;
        """,
        (str(conversation_id),),
      )
      rows = cur.fetchall() or []
  return [
    ChatMessage(
      id=r["id"],
      role=r["role"],
      content=r["content"],
      images=r.get("images") or [],
      created_at=r["created_at"],
    )
    for r in rows
  ]