"use client";
import { useEffect, useState } from "react";
import { listConversations } from "@/lib/api";
import type { ConversationSummary } from "@/types/chat";

export default function Sidebar({
  open,
  activeId,
  onToggle,
  onSelect,
  onNewChat,
  refreshKey,
}: {
  open: boolean;
  activeId?: string;
  onToggle: () => void;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  refreshKey?: number;
}) {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const list = await listConversations();
        setItems(list);
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshKey]);

  return (
    <aside
      className={`bg-[#0f1320] border-r border-slate-800 h-screen transition-all overflow-hidden
      ${open ? "w-72" : "w-0 md:w-72"}`}
    >
      <div className="flex items-center gap-2 p-3 border-b border-slate-800">
        <button
          onClick={onToggle}
          className="px-2 py-1 border border-slate-700 rounded text-slate-200"
          type="button"
        >
          ☰
        </button>
        <h2 className="text-slate-100 text-sm">PrismChat</h2>
      </div>

      <div className="p-3 border-b border-slate-800">
        <button
          onClick={onNewChat}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded px-3 py-2 text-sm"
          type="button"
        >
          + New chat
        </button>
      </div>

      <div className="p-2 overflow-y-auto h-[calc(100vh-110px)]">
        {loading && <div className="text-slate-400 text-sm p-2">Loading…</div>}
        {!loading && items.length === 0 && (
          <div className="text-slate-500 text-sm p-2">
            No conversations yet.
          </div>
        )}
        {items.map((c) => (
          <button
            key={c.id}
            onClick={() => {
              onSelect(c.id);
              if (window.innerWidth < 768) onToggle();
            }}
            className={`w-full text-left rounded p-2 mb-1 ${
              c.id === activeId
                ? "border border-indigo-500"
                : "hover:bg-[#141a2a]"
            }`}
            type="button"
          >
            <div className="text-slate-200 text-sm">
              {c.title || "Untitled"}
            </div>
            <div className="text-slate-500 text-xs">
              {new Date(c.updatedAt).toLocaleString()}
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}
