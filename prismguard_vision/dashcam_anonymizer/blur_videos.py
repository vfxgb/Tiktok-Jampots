import os, glob, json, cv2, pybboxes as pbx, yaml, argparse, shutil
from ultralytics import YOLO
from rich.console import Console
from rich.progress import track
from natsort import natsorted
from os.path import join as osj

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, help="path of the configuration file")
args = parser.parse_args()
console = Console()

with open(args.config, "r") as f:
    config = yaml.safe_load(f)

console.print("Loading YOLO Model...", style="bold green")
model = YOLO(config["model_path"])

if config.get("generate_detections", True):
    console.print("Generating YOLO detections...", style="bold green")
    _ = model(
        source=config["videos_path"],
        save=False,
        save_txt=True,
        conf=config["detection_conf_thresh"],
        device="cuda:0" if config.get("gpu_avail") else "cpu",
        project="runs/detect/",
        name="yolo_videos_pred",
    )

videos = natsorted(glob.glob(f"{config['videos_path']}/*.mp4"))

if config.get("generate_jsons", True):
    console.print(f"Generating JSONs for {len(videos)} videos")
    for video in track(videos):
        vid_name = os.path.basename(video).replace(".mp4", "")
        cap = cv2.VideoCapture(video)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

        data = {}
        label_files = natsorted(glob.glob(f"runs/detect/yolo_videos_pred*/labels/{vid_name}_*.txt"))
        for lf in label_files:
            frame_num = int(os.path.basename(lf).replace(".txt", "").split("_")[1])
            with open(lf, "r") as fin:
                for line in fin.readlines():
                    yolo_vals = [float(item) for item in line.split()[1:]]
                    voc = pbx.convert_bbox(yolo_vals, from_type="yolo", to_type="voc", image_size=(w, h))
                    data.setdefault(frame_num, []).append(voc)

        os.makedirs("annot_jsons", exist_ok=True)
        with open(f"annot_jsons/{vid_name}.json", "w") as fout:
            json.dump(data, fout)

def blur_regions(image, regions):
    for x1, y1, x2, y2 in regions:
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        roi = image[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, (config["blur_radius"], config["blur_radius"]), 0)
        image[y1:y2, x1:x2] = blurred
    return image

os.makedirs(config["output_folder"], exist_ok=True)
out_root = config["output_folder"]

for video in track(videos):
    vid_name = os.path.basename(video).replace(".mp4", "")
    json_path = f"annot_jsons/{vid_name}.json"
    if os.path.exists(json_path):
        with open(json_path) as F:
            data = json.load(F)
        cap = cv2.VideoCapture(video)
        out_vid_path = osj(out_root, vid_name + ".mp4")

        fw, fh = int(cap.get(3)), int(cap.get(4))
        fps = round(cap.get(cv2.CAP_PROP_FPS)) or 25
        writer = cv2.VideoWriter(out_vid_path, cv2.VideoWriter_fourcc(*"avc1"), fps, (fw, fh))
        count = 1
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if str(count) in data:
                frame = blur_regions(frame, data[str(count)])
            writer.write(frame)
            count += 1
        cap.release(); writer.release()
        console.print(f"Processed Video {vid_name}", style="bold green")
    else:
        console.print(f"No objects in {video}, copying as is.", style="bold red")
        shutil.copy(video, out_root)

# cleanup
shutil.rmtree("runs/", ignore_errors=True)
shutil.rmtree("annot_jsons/", ignore_errors=True)
console.print(f"Blurred videos are in {out_root}", style="bold yellow")
