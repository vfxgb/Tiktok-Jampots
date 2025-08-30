FROM python:3.11-slim
WORKDIR /app

# curl is used by the compose healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# copy only the gateway code
COPY . /app

# deps used by your app.py
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx python-multipart pydantic

# If you will verify Firebase ID tokens:
# RUN pip install --no-cache-dir firebase-admin

EXPOSE 8080
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8080"]
