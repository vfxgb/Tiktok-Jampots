from typing import List, Optional
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

    Each history item should include: { role: 'user'|'assistant', content: str, images?: [str] }
    We append image URLs as text references. (Upgrade to true multimodal later.)
    """
    msgs: List = []
    for m in history:
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        content = m.get("content") or ""
        parts: List[str] = [content] if content else []
        imgs = m.get("images") or []
        if imgs:
            parts.append("\n\nUser provided images:\n" + "\n".join(imgs))
        text = "\n\n".join([p for p in parts if p])
        if not text:
            continue
        if role == "user":
            msgs.append(HumanMessage(content=text))
        else:
            msgs.append(AIMessage(content=text))
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

    # Compose current user turn (text + image refs)
    parts: List[str] = []
    if user_text:
        parts.append(user_text)
    if user_images:
        parts.append("\n\nUser provided images:\n" + "\n".join(user_images))
    current_input = "\n\n".join(parts) if parts else ""

    try:
        # Render prompt → list[BaseMessage]
        rendered = prompt.format_messages(history=history_msgs, input=current_input)
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