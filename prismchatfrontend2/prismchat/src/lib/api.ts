import type {
  ConversationSummary,
  ChatMessage,
  SendResult,
  SendPayload,
} from "@/types/chat";
import { v4 as uuidv4 } from "uuid";

const BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type UploadedImage = {
  storageUrl: string;   // what we persist/send to backend
  previewUrl?: string;  // local blob URL for UI preview
};

function toUrlList(images?: (string | UploadedImage)[]): string[] {
  return (images ?? []).map((i) => (typeof i === "string" ? i : i.storageUrl));
}

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

/** Upload files. When prismGuard is true, the server will redact before storing. */
export async function uploadImages(
  files: File[],
  prismGuard = false
): Promise<UploadedImage[]> {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));

  const qs = prismGuard ? "?route=prismguard" : "";
  const res = await fetch(`${BASE}/v1/upload${qs}`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text().catch(() => "Upload failed"));
  const data = (await res.json()) as { urls: string[] };

  return data.urls.map((u, i) => ({
    storageUrl: u,                      // redacted when prismGuard=true
    previewUrl: URL.createObjectURL(files[i]), // original, local-only for UI
  }));
}

/** Send a message; only storage URLs are sent to backend/DB. */
export async function sendMessage(
  payload: Omit<SendPayload, "images"> & { images?: (string | UploadedImage)[] }
): Promise<SendResult> {
  const conversationId = (payload as any).conversationId ?? uuidv4();

  const body = {
    conversation_id: conversationId,
    route: (payload as any).route || "direct", // set "prismguard" when toggle is ON
    text: (payload as any).text ?? "",
    images: toUrlList(payload.images),
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
  };
}
