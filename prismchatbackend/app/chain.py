from typing import List, Optional
from typing import Union
def _urls_to_gemini_parts(urls: Optional[List[str]]) -> List[dict]:
    parts: List[dict] = []
    if not urls:
        return parts
    for u in urls:
        u = (u or "").strip()
        if not u:
            continue
        parts.append({"type": "image_url", "image_url": u})
    return parts

import traceback

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def _make_model() -> ChatGoogleGenerativeAI:
    """Instantiate the Gemini 2.0 Flash chat model.

    Relies on GOOGLE_API_KEY from environment. LangSmith tracing is picked up
    automatically from env vars if configured (LANGCHAIN_TRACING_V2, etc.).
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
    )


def _history_to_messages(history: List[dict]) -> List:
    """Convert stored message dicts into LangChain messages.

    For user turns, include both text and any prior image URLs as multimodal parts.
    For assistant turns, include text only (Gemini expects assistant text normally).
    Each history item: { role: 'user'|'assistant', content: str, images?: [str] }
    """
    msgs: List = []
    for m in history:
        role = (m.get("role") or "").strip().lower()
        if role not in ("user", "assistant"):
            continue

        content = (m.get("content") or "").strip()
        images = m.get("images") or []

        if role == "user":
            parts: List[dict] = []
            if content:
                parts.append({"type": "text", "text": content})
            for u in images:
                u = (u or "").strip()
                if not u:
                    continue
                parts.append({"type": "image_url", "image_url": u})
            if parts:
                msgs.append(HumanMessage(content=parts))
        else:  # assistant
            if content:
                msgs.append(AIMessage(content=content))
    return msgs


def run_chain(
    history: List[dict],
    user_text: Optional[str],
    user_images: Optional[List[str]],
    prismguard: bool,
) -> str:
    """Run Gemini using a prompt with MessagesPlaceholder for history.

    We ignore tools; we just stitch history into the prompt like your example.
    """
    model = _make_model()

    system_prompt = (
        "You are PrismGuard. Refuse unsafe requests and avoid returning PII. Redact sensitive info."
        if prismguard
        else "You are PrismChat, a helpful assistant."
    )

    # Build prompt with explicit history placeholder
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    # Convert our stored rows to BaseMessages for the history slot
    history_msgs = _history_to_messages(history)

    # Compose current user turn. If images are present, send Gemini multimodal parts.
    if user_images:
        mm_parts: List[dict] = []
        if user_text:
            mm_parts.append({"type": "text", "text": user_text})
        mm_parts.extend(_urls_to_gemini_parts(user_images))
        # Render the conversation up to now (system + history), then append a HumanMessage with parts
        rendered = prompt.format_messages(history=history_msgs, input="")
        rendered.append(HumanMessage(content=mm_parts))
    else:
        # Text-only turn
        current_input = user_text or ""
        rendered = prompt.format_messages(history=history_msgs, input=current_input)

    try:
        # Debug visibility
        try:
            print("[PrismChat] history size:", len(history_msgs))
            print("[PrismChat] rendered types:", [type(m).__name__ for m in rendered])
        except Exception:
            pass

        # Call model
        result = model.invoke(rendered)

    except Exception as e:
        print("[PrismChat] run_chain error:", str(e))
        traceback.print_exc()
        raise

    if isinstance(result, AIMessage):
        return result.content or ""
    content = getattr(result, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(result, str):
        return result
    return ""