// Who sent a message
export type Role = "user" | "assistant";

// A single chat message
export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  images?: string[]; // array of image URLs (optional)
  createdAt: string; // ISO timestamp
}

// A conversation shown in the sidebar
export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string; // ISO timestamp
  updatedAt: string; // ISO timestamp
}

// Routing mode for messages
export type RouteMode = "direct" | "prismguard";

// Payload to send a message to the API
export interface SendPayload {
  conversationId?: string; // created on first send if not provided
  route: RouteMode;
  text?: string;
  images?: string[]; // URLs returned from /api/upload
}

// API response when sending a message
export interface SendResult {
  conversationId: string; // guaranteed after first send
  messages: ChatMessage[]; // full message list for that conversation
}

// Convenience types for list/get endpoints (optional)
export interface ListConversationsResponse {
  conversations: ConversationSummary[];
}

export interface GetConversationResponse {
  conversationId: string;
  messages: ChatMessage[];
}
