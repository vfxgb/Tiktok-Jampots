# prismguard_vision/wrapper.py
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image
import tempfile, shutil, subprocess, yaml, glob, os

ROOT = Path(__file__).resolve().parents[1]
DASHCAM = ROOT / "prismguard_vision" / "dashcam_anonymizer"
MODEL_PATH = DASHCAM / "model" / "best.pt"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

def _latest_labels_dir(prefix: str) -> str:
    # Handles Ultralytics auto-incremented runs dirs (yolo_images_pred2, etc.)
    candidates = glob.glob(f"runs/detect/{prefix}*")
    if not candidates:
        return f"runs/detect/{prefix}/labels/"
    return os.path.join(max(candidates, key=os.path.getmtime), "labels")

def anonymize_image(pil_img: Image.Image) -> Dict[str, Any]:
    work = Path(tempfile.mkdtemp(prefix="pg_img_"))
    in_dir = work / "in"; out_dir = work / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    inp = in_dir / "image.png"
    pil_img.save(inp)
    w, h = pil_img.size

    cfg = {
        "model_path": str(MODEL_PATH),
        "images_path": str(in_dir),
        "output_folder": str(out_dir),
        "img_format": ".png",
        "img_width": w,
        "img_height": h,
        "detection_conf_thresh": 0.35,
        "gpu_avail": False,
        "blur_radius": 51,
    }
    cfg_path = work / "img_cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    # Clean vendor temp dirs so Ultralytics uses yolo_images_pred (not yolo_images_pred2/3/…)
    subprocess.run(
        [
            "python", "-c",
            "import shutil,glob,os;"
            "shutil.rmtree('annot_txt', ignore_errors=True);"
            "[shutil.rmtree(p, ignore_errors=True) for p in glob.glob('runs/detect/yolo_images_pred*')];"
            "os.makedirs('annot_txt', exist_ok=True)"
        ],
        check=True, cwd=str(DASHCAM)
    )

    # Run vendor script
    subprocess.run(["python", "blur_images.py", "--config", str(cfg_path)], check=True, cwd=str(DASHCAM))

    # Try to find a produced image; if none, fall back to original
    out_img = next(out_dir.rglob("*.jpg"), None) or next(out_dir.rglob("*.png"), None)
    if out_img:
        red = Image.open(out_img).convert("RGB")
    else:
        red = pil_img.copy()  # no detections -> return original

    # Collect entities if any
    entities = []
    ann = DASHCAM / "annot_txt"
    if ann.exists():
        for t in ann.glob("*.txt"):
            for line in t.read_text().strip().splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    x1, y1, x2, y2 = map(float, parts[:4])
                    entities.append({"label": "object", "bbox": [x1, y1, x2, y2], "conf": 1.0})

    return {"image": red, "entities": entities}

def anonymize_video(video_path: str) -> Tuple[str, dict]:
    work = Path(tempfile.mkdtemp(prefix="pg_vid_"))
    in_dir = work / "in"; out_dir = work / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    local = in_dir / Path(video_path).name
    shutil.copy2(video_path, local)

    cfg = {
        "model_path": str(MODEL_PATH),
        "videos_path": str(in_dir),
        "output_folder": str(out_dir),
        "generate_detections": True,
        "generate_jsons": True,
        "detection_conf_thresh": 0.35,
        "gpu_avail": False,
        "blur_radius": 15,
    }
    cfg_path = work / "vid_cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    # Run vendor script
    subprocess.run(
        ["python", "blur_videos.py", "--config", str(cfg_path)],
        check=True, cwd=str(DASHCAM)
    )

    out_vid = next(out_dir.rglob("*.mp4"), None)
    if not out_vid:
        raise FileNotFoundError("No redacted video produced by dashcam_anonymizer")
    return str(out_vid), {"entities": []}
