import type {
  ConversationSummary,
  ChatMessage,
  SendResult,
  SendPayload,
} from "@/types/chat";
import { v4 as uuidv4 } from "uuid";

const BASE = "http://localhost:8000";

export async function listConversations(): Promise<ConversationSummary[]> {
  const res = await fetch(`${BASE}/v1/conversations`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load conversations");
  const data = await res.json();
  return data.conversations as ConversationSummary[];
}

export async function getConversation(
  conversationId: string
): Promise<ChatMessage[]> {
  const res = await fetch(`${BASE}/v1/conversations/${conversationId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load conversation");
  const data = await res.json();
  return (data.messages as any[]).map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
    images: m.images || [],
    createdAt: m.created_at || m.createdAt,
  })) as ChatMessage[];
}

export async function uploadImages(files: File[]): Promise<string[]> {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  const res = await fetch(`${BASE}/v1/upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error("Upload failed");
  const data = await res.json();
  return data.urls as string[];
}

export async function sendMessage(payload: SendPayload): Promise<SendResult> {
  const conversationId = (payload as any).conversationId ?? uuidv4();
  const body = {
    conversation_id: conversationId,
    route: (payload as any).route || "direct",
    text: (payload as any).text ?? "",
    images: (payload as any).images ?? [],
  };

  const res = await fetch(`${BASE}/v1/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errTxt = await res.text().catch(() => "");
    throw new Error(`Chat failed: ${res.status} ${errTxt}`);
  }
  const data = await res.json();
  return {
    conversationId: data.conversationId || conversationId,
    messages: (data.messages as any[]).map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      images: m.images || [],
      createdAt: m.created_at || m.createdAt,
    })) as ChatMessage[],
  } as SendResult;
}
