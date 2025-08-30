from fastapi import Header, HTTPException
import jwt


def get_user_id(authorization: str | None = Header(None)) -> str:
if not authorization or not authorization.startswith("Bearer "):
raise HTTPException(401, "Missing auth token")
token = authorization.split(" ", 1)[1]
try:
payload = jwt.decode(token, options={"verify_signature": False})
return payload.get("sub")
except Exception:
raise HTTPException(401, "Invalid token")