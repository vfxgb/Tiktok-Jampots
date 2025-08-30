// src/types/chat.ts
export type Role = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  images?: string[]; // URLs (after upload)
  createdAt: string; // ISO
}

export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string; // ISO
  updatedAt: string; // ISO
}

export type RouteMode = 'direct' | 'prismguard';

export interface SendPayload {
  conversationId?: string; // undefined on very first send
  route: RouteMode;
  text?: string;
  imageFiles?: File[]; // from input, optional
}

export interface SendResult {
  conversationId: string;
  messages: ChatMessage[];
}

export interface ListResult {
  conversations: ConversationSummary[];
}

export interface GetResult {
  conversationId: string;
  messages: ChatMessage[];
}
