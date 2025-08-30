import os, base64, requests
from typing import Optional

class VisionBridge:
    """
    Low-level client for Vision or Gateway->Vision.
    By default, uses the Gateway endpoint /v1/gateway/image.
    Set use_gateway=False to call Vision directly at /v1/anonymize/image.
    """

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        vision_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 120,
        use_gateway: bool = True,
    ):
        self.use_gateway = use_gateway
        if use_gateway:
            self.base_url = gateway_url or os.getenv("GATEWAY_URL", "http://localhost:8080")
        else:
            self.base_url = vision_url or os.getenv("VISION_URL", "http://localhost:8081")

        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    def anonymize_image(self, image_path: str, save_to: Optional[str] = None) -> dict:
        url = (f"{self.base_url}/v1/gateway/image"
               if self.use_gateway else f"{self.base_url}/v1/anonymize/image")

        ctype, _ = mimetypes.guess_type(image_path)
        ctype = ctype or "application/octet-stream"

        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, ctype)}
            r = self.session.post(url, files=files, timeout=self.timeout)
        r.raise_for_status()

        data = r.json()
        if save_to and data.get("redacted_image_b64"):
            with open(save_to, "wb") as out:
                out.write(base64.b64decode(data["redacted_image_b64"]))
        return data
