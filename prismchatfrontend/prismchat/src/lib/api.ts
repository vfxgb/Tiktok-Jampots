// src/lib/api.ts
import type {
  ChatMessage,
  ConversationSummary,
  SendPayload,
  SendResult,
} from '../types/chat.js';

// const envAny =
//   (globalThis as any)?.__ENV__ ??
//   (typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined) ??
//   (typeof process !== 'undefined' ? (process as any).env : undefined);

// const BASE: string =
//   envAny?.VITE_API_URL ||
//   envAny?.VITE_API ||
//   envAny?.PRISMCHAT_API_URL ||
//   'http://localhost:8080';

// async function json<T>(res: Response): Promise<T> {
//   if (!res.ok) {
//     const txt = await res.text().catch(() => '');
//     throw new Error(`API ${res.status}: ${txt || res.statusText}`);
//   }
//   return res.json() as Promise<T>;
// }

// List all conversations (for Sidebar)
export async function listConversations(): Promise<ConversationSummary[]> {
  return Promise.resolve([
    {
      id: '1',
      title: 'Demo conversation',
      createdAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: '2',
      title: 'Another chat',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ]);
}

// Load one conversation (messages)
export async function getConversation(
  conversationId: string,
): Promise<ChatMessage[]> {
  return Promise.resolve([
    {
      id: 'm1',
      role: 'user',
      content: 'Hello PrismChat!',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'm2',
      role: 'assistant',
      content: 'Hi there! This is a fake response.',
      createdAt: new Date().toISOString(),
    },
  ]);
}

// Upload images → return array of URLs
export async function uploadImages(files: File[]): Promise<string[]> {
  return Promise.resolve(
    files.map((_, i) => `https://fakeimg.pl/250x100/?text=Image${i + 1}`),
  );
}

// Send a message; if conversationId is undefined, server creates one
export async function sendMessage(payload: SendPayload): Promise<SendResult> {
  return Promise.resolve({
    conversationId: payload.conversationId ?? 'fake-convo-id',
    messages: [
      {
        id: 'u1',
        role: 'user',
        content: payload.text ?? '',
        createdAt: new Date().toISOString(),
      },
      {
        id: 'a1',
        role: 'assistant',
        content: 'This is a fake AI reply.',
        createdAt: new Date().toISOString(),
      },
    ],
  });
}

// Create an empty conversation shell (optional; not used here since we create on first send)
// export async function createConversation(): Promise<{ id: string }> { ... }
