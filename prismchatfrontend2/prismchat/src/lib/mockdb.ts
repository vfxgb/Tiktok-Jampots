// src/lib/mockdb.ts
import { v4 as uuid } from "uuid";
import type { ChatMessage, ConversationSummary } from "@/types/chat";

// In-memory storage
const conversations = new Map<
  string,
  { meta: ConversationSummary; messages: ChatMessage[] }
>();

// List all conversations, sorted by updatedAt desc
export function listConversations(): ConversationSummary[] {
  return Array.from(conversations.values())
    .map((c) => c.meta)
    .sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt));
}

// Get messages for a conversation
export function getConversation(id: string): ChatMessage[] {
  return conversations.get(id)?.messages ?? [];
}

// Ensure a conversation exists, creating one if not
export function ensureConversation(id?: string, title?: string): string {
  if (id && conversations.has(id)) return id;
  const newId = id ?? uuid();
  const now = new Date().toISOString();
  conversations.set(newId, {
    meta: {
      id: newId,
      title: title || "New chat",
      createdAt: now,
      updatedAt: now,
    },
    messages: [],
  });
  return newId;
}

// Add a message to a conversation
export function addMessage(conversationId: string, msg: ChatMessage) {
  const row = conversations.get(conversationId);
  if (!row) return;
  row.messages.push(msg);
  row.meta.updatedAt = msg.createdAt;
  if (row.meta.title === "New chat" && msg.role === "user" && msg.content) {
    row.meta.title = msg.content.slice(0, 40);
  }
}
