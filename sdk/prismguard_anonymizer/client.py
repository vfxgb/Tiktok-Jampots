from typing import Optional
from .vision_bridge import VisionBridge
from .llm_bridge import LlmBridge

class PrismGuard:
    """
    High-level facade that composes Vision + LLM bridges.
    Most users will import and use this single class.
    """

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        gateway_url: Optional[str] = None,
        vision_url: Optional[str] = None,
        llm_url: Optional[str] = None,
        timeout: int = 120,
        use_gateway: bool = True,
    ):
        self.vision = VisionBridge(
            gateway_url=gateway_url,
            vision_url=vision_url,
            token=token,
            timeout=timeout,
            use_gateway=use_gateway,
        )
        self.llm = LlmBridge(
            gateway_url=gateway_url,
            llm_url=llm_url,
            token=token,
            timeout=timeout,
            use_gateway=use_gateway,
        )

    # Facade methods:
    def anonymize_image(self, image_path: str, save_to: Optional[str] = None) -> dict:
        return self.vision.anonymize_image(image_path, save_to=save_to)

    def anonymize_text(self, text: str, mode: str = "smart") -> dict:
        return self.llm.anonymize_text(text, mode=mode)
