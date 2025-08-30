import os, glob, cv2, pybboxes as pbx, yaml, argparse, shutil
from ultralytics import YOLO

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True, help="path of the configuration file")
args = parser.parse_args()

# Read config
with open(args.config, "r") as f:
    config = yaml.safe_load(f)

# Clean/create annot dir
shutil.rmtree("annot_txt", ignore_errors=True)
os.makedirs("annot_txt", exist_ok=True)

# Load model
model = YOLO(config["model_path"])

# Run YOLO
_ = model(
    source=config["images_path"],
    save=False,
    save_txt=True,
    conf=config["detection_conf_thresh"],
    device="cuda:0" if config.get("gpu_avail") else "cpu",
    project="runs/detect/",
    name="yolo_images_pred",
)

# Handle auto-incremented 'runs' folders (yolo_images_pred, yolo_images_pred2, ...)
candidates = glob.glob("runs/detect/yolo_images_pred*")
annot_dir = os.path.join(max(candidates, key=os.path.getmtime), "labels")

# Convert YOLO -> VOC and write annot_txt
for file in os.listdir(annot_dir):
    if not file.endswith(".txt"):
        continue
    with open(os.path.join(annot_dir, file), "r") as fin:
        for line in fin.readlines():
            yolo_vals = [float(item) for item in line.split()[1:]]
            voc = pbx.convert_bbox(
                yolo_vals, from_type="yolo", to_type="voc",
                image_size=(config["img_width"], config["img_height"])
            )
            with open(os.path.join("annot_txt", os.path.basename(file)), "a") as fout:
                fout.write(" ".join(str(int(v)) for v in voc) + "\n")

def blur_regions(image, regions):
    for x1, y1, x2, y2 in regions:
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        roi = image[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, (config["blur_radius"], config["blur_radius"]), 0)
        image[y1:y2, x1:x2] = blurred
    return image

txt_folder = "annot_txt"
image_folder = config["images_path"]
output_folder = config["output_folder"]
os.makedirs(output_folder, exist_ok=True)

txt_files = [f for f in os.listdir(txt_folder) if f.endswith(".txt")]

for txt_file in txt_files:
    with open(os.path.join(txt_folder, txt_file), "r") as f:
        bboxes = [list(map(int, line.strip().split())) for line in f]

    img_name = txt_file.replace(".txt", config["img_format"])  # keep extension from config
    img_path = os.path.join(image_folder, img_name)
    image = cv2.imread(img_path)

    image = blur_regions(image, bboxes)  # blur once for all boxes
    out_name = txt_file.replace(".txt", "_blurred.jpg")
    cv2.imwrite(os.path.join(output_folder, out_name), image)

print(f"@@ Blurred images saved to {output_folder}")
