"use client";
import type { ChatMessage } from "@/types/chat";
import Image from "next/image";
import MarkdownRenderer from "./MarkdownRenderer";

export default function ChatMessageView({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div
      className={`max-w-3xl mx-auto mb-3 rounded-xl border border-slate-800 p-3 ${
        isUser ? "bg-[#1f2b45]" : "bg-[#101827]"
      }`}
    >
      <div className="text-xs text-slate-400 mb-1 flex gap-2">
        <span>{isUser ? "You" : "Assistant"}</span>
        <span>·</span>
        <span>{new Date(msg.createdAt).toLocaleTimeString()}</span>
      </div>

      {msg.content && <MarkdownRenderer content={msg.content} />}

      {!!msg.images?.length && (
        <div className="flex gap-2 mt-2 flex-wrap">
          {msg.images.map((url, i) => (
            <div
              key={i}
              className="rounded border border-slate-800 p-1 overflow-auto max-h-[70vh]"
            >
              <img
                src={url}
                alt={`img-${i}`}
                className="block max-w-full h-auto object-contain rounded"
                loading="lazy"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
