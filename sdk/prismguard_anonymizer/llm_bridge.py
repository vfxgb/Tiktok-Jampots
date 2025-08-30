import os, requests
from typing import Optional

class LlmBridge:
    """
    Low-level client for LLM service or Gateway->LLM.
    By default, uses the Gateway endpoint /v1/gateway/text.
    Set use_gateway=False to call LLM directly at /v1/anonymize/text (when you add it).
    """

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        llm_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 60,
        use_gateway: bool = True,
    ):
        self.use_gateway = use_gateway
        if use_gateway:
            self.base_url = gateway_url or os.getenv("GATEWAY_URL", "http://localhost:8080")
        else:
            self.base_url = llm_url or os.getenv("LLM_URL", "http://localhost:8082")

        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    def anonymize_text(self, text: str, mode: str = "smart") -> dict:
        url = (
            f"{self.base_url}/v1/gateway/text"
            if self.use_gateway
            else f"{self.base_url}/v1/anonymize/text"
        )
        r = self.session.post(url, json={"text": text, "mode": mode}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
