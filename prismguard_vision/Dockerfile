FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 wget curl && rm -rf /var/lib/apt/lists/*

# copy code into a package folder
COPY . /app/prismguard_vision

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
      matplotlib pandas scipy seaborn \
      psutil tqdm requests dill py-cpuinfo \
      pybboxes \
      opencv-python-headless \
      numpy==1.25.1 \
      gdown \
      fastapi \
      uvicorn \
      pyyaml \
      rich \
      natsort \
      pillow  \
      python-multipart    

# 2) CPU-only torch + torchvision, pinned below 2.6
RUN pip install --no-cache-dir \
      torch==2.5.1+cpu torchvision==0.20.1+cpu \
      --index-url https://download.pytorch.org/whl/cpu
      
# 3) Ultralytics 
RUN pip install --no-cache-dir ultralytics==8.0.144 --no-deps

# bake model
RUN mkdir -p /app/prismguard_vision/dashcam_anonymizer/model \
 && gdown 1uV8IMuGDbmDabdjyeSy4SUKV9OS-ULbe -O /app/prismguard_vision/dashcam_anonymizer/model/best.pt

EXPOSE 8081
CMD ["uvicorn", "prismguard_vision.app:app", "--host", "0.0.0.0", "--port", "8081"]
