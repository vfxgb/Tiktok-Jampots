"use client";
import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import MessageList from "@/components/MessageList";
import MessageInput from "@/components/MessageInput";
import type { ChatMessage, RouteMode } from "@/types/chat";
import { getConversation } from "@/lib/api";

export default function Page() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined") {
      setSidebarOpen(window.innerWidth >= 900);
    }
  }, []);
  const [conversationId, setConversationId] = useState<string | undefined>(
    undefined
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [route, setRoute] = useState<RouteMode>("prismguard");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  async function loadConversation(id: string) {
    setConversationId(id);
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
    setLoading(true);
    try {
      const msgs = await getConversation(id);
      setMessages(msgs);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setConversationId(undefined);
    setMessages([]);
  }

  const title = useMemo(() => {
    if (!messages.length) return "New chat";
    const first = messages.find((m) => m.role === "user");
    return first?.content?.slice(0, 42) || "Conversation";
  }, [messages]);

  return (
    <div className="grid grid-cols-[18rem_1fr] h-screen overflow-hidden bg-[#0b0e14] text-slate-100">
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
        activeId={conversationId}
        onSelect={loadConversation}
        onNewChat={newChat}
        refreshKey={refreshKey}
      />

      <div className="grid grid-rows-[auto_1fr_auto] h-screen min-h-0">
        <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-800 bg-[#0f1320]">
          <button
            className="md:hidden border border-slate-700 rounded px-2 py-1"
            onClick={() => setSidebarOpen(true)}
            type="button"
          >
            ☰
          </button>
          <div className="truncate">{title}</div>
        </div>

        <div className="relative min-h-0 overflow-hidden">
          {!messages.length && !loading && (
            <div className="text-slate-400 text-sm p-4">
              Start a conversation by sending a message or an image.
            </div>
          )}
          {loading && (
            <div className="text-slate-400 text-sm p-4">Loading…</div>
          )}
          {!!messages.length && <MessageList messages={messages} />}
        </div>

        <div className="p-3 border-t border-slate-800 bg-[#0b0e14]">
          <MessageInput
            disabled={loading}
            route={route}
            onRouteChange={setRoute}
            conversationId={conversationId}
            onReply={(res) => {
              if (!conversationId) setConversationId(res.conversationId);
              setMessages(res.messages as ChatMessage[]);
              setRefreshKey((k) => k + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
