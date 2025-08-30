# prismguard_vision/app.py
import io, base64, time, tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image
from .wrapper import anonymize_image, anonymize_video
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PrismGuard Vision", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Entity(BaseModel):
    label: str
    conf: float
    bbox: List[float]

class ImgResp(BaseModel):
    redacted_image_b64: str
    entities: List[Entity]
    timing_ms: float

class VidResp(BaseModel):
    redacted_video_path: str
    timing_ms: float

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/v1/anonymize/image", response_model=ImgResp)
async def img_endpoint(
    file: UploadFile = File(None),
    image_b64: Optional[str] = Form(None),
):
    # exactly one input required
    if (file is None and not image_b64) or (file is not None and image_b64):
        raise HTTPException(status_code=400, detail="Provide either 'file' or 'image_b64' (exactly one).")

    t0 = time.time()
    data = await file.read() if file else base64.b64decode(image_b64)
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=415, detail="Unsupported or corrupt image")

    res = anonymize_image(img)
    buf = io.BytesIO()
    res["image"].save(buf, format="PNG")

    return ImgResp(
        redacted_image_b64=base64.b64encode(buf.getvalue()).decode(),
        entities=[Entity(**e) for e in res.get("entities", [])],
        timing_ms=(time.time() - t0) * 1000.0,
    )

@app.post("/v1/anonymize/video", response_model=VidResp)
async def vid_endpoint(file: UploadFile = File(...)):
    t0 = time.time()
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        inp = tmp.name
    out_path, _ = anonymize_video(inp)
    return VidResp(redacted_video_path=out_path, timing_ms=(time.time() - t0) * 1000.0)
