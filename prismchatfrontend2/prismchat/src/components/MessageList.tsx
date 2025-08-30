"use client";
import type { ChatMessage } from "@/types/chat";
import ChatMessageView from "./ChatMessage";

export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="h-full overflow-y-auto p-4 bg-[radial-gradient(1200px_600px_at_50%_-10%,rgba(124,92,255,.15),transparent),#0b0e14]">
      {messages.map((m) => (
        <ChatMessageView key={m.id} msg={m} />
      ))}
    </div>
  );
}
