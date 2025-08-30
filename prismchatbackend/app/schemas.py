
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# A single chat message
class ChatMessage(BaseModel):
    id: uuid.UUID
    role: str  # "user" or "assistant"
    content: str
    images: List[str] = []
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        populate_by_name = True

# Request payload for sending a chat
class SendPayload(BaseModel):
    conversation_id: uuid.UUID
    route: str = "direct"  # "direct" or "prismguard"
    text: Optional[str] = None
    images: List[str] = []

# Response payload from /v1/chat
class SendResult(BaseModel):
    conversationId: uuid.UUID
    messages: List[ChatMessage]

# For retrieval (conversation history)
class ConversationHistory(BaseModel):
    conversationId: uuid.UUID
    messages: List[ChatMessage]