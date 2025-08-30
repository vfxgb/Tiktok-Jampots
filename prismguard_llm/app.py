# prismguard_llm/app.py
import os, time
from typing import List, Dict, Any, Literal

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForTokenClassification

# --- config
MODEL_DIR = os.getenv("MODEL_DIR", "/app/model")  
MAX_LEN = int(os.getenv("MAX_LEN", "128"))

DEVICE = "cpu"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))

# 
try:
    tok = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True, local_files_only=True)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR, local_files_only=True).to(DEVICE)
    model.eval()
    ID2LABEL = model.config.id2label
except Exception as e:
    raise RuntimeError(f"Failed to load model from {MODEL_DIR}: {e}")

app = FastAPI(title="PrismGuard LLM (Text Anonymizer)", version="0.1.0")

class TextReq(BaseModel):
    text: str
    mode: Literal["smart", "strict"] = "smart" 

def _predict(text: str) -> Dict[str, Any]:
    """
    Run token classification → char-level mask → redact to [REDACTED].
    Returns redacted_text and simple spans (start,end,label).
    """
    with torch.inference_mode():
        enc = tok(
            text,
            return_offsets_mapping=True,
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        offsets = enc.pop("offset_mapping")[0].tolist()  # keep on CPU
        enc = {k: v.to(DEVICE) for k, v in enc.items()}
        logits = model(**enc).logits  # (1, seq_len, num_labels)
        pred_ids = logits.argmax(-1)[0].tolist()

    n_chars = len(text)

    # Build char-level mask
    char_mask = [0] * n_chars
    for (a, b), lab_id in zip(offsets, pred_ids):
        # specials like [CLS]/[SEP] usually have (0,0) or b==0
        if a is None or b is None or b == 0:
            continue
        label = ID2LABEL[int(lab_id)]
        if label != "O":
            aa = max(0, min(a, n_chars))
            bb = max(aa, min(b, n_chars))
            for i in range(aa, bb):
                char_mask[i] = 1

    # Merge contiguous 1s into spans
    spans: List[List[int]] = []
    i = 0
    while i < n_chars:
        if char_mask[i] == 1:
            j = i + 1
            while j < n_chars and char_mask[j] == 1:
                j += 1
            spans.append([i, j])
            i = j
        else:
            i += 1

    # Redact
    redacted_parts = []
    last = 0
    for a, b in spans:
        if a > last:
            redacted_parts.append(text[last:a])
        redacted_parts.append("[REDACTED]")
        last = b
    if last < n_chars:
        redacted_parts.append(text[last:])
    redacted_text = "".join(redacted_parts)

    # Entities (consider omitting text for privacy)
    entities = [{"label": "PII", "start": a, "end": b} for a, b in spans]

    return {"redacted_text": redacted_text, "entities": entities}

@app.get("/health")
def health():
    return {"ok": True, "device": DEVICE}

@app.post("/v1/anonymize/text")
def anonymize_text(req: TextReq):
    try:
        t0 = time.time()
        out = _predict(req.text or "")
        out["timing_ms"] = (time.time() - t0) * 1000.0
        # Gateway adds attestation + logs audit
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
