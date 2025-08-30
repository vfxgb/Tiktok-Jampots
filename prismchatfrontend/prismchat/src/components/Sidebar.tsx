// src/components/Sidebar.tsx
import { useEffect, useState } from '@lynx-js/react';
import type { ConversationSummary } from '../types/chat.js';
import { listConversations } from '../lib/api.js';

interface SidebarProps {
  open: boolean;
  onToggle(): void;
  activeId?: string;
  onSelect(conversationId: string): void;
  onNewChat(): void;
}

export default function Sidebar({
  open,
  onToggle,
  activeId,
  onSelect,
  onNewChat,
}: SidebarProps) {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const list = await listConversations();
        if (mounted) setItems(list);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <view className={`sidebar ${open ? 'open' : 'closed'}`}>
      <view className="sidebar-header">
        <view className="ghost" bindtap={onToggle}>
          ☰
        </view>
        <text>PrismChat</text>
      </view>

      <view className="sidebar-actions">
        <view className="primary" bindtap={onNewChat}>
          + New chat
        </view>
      </view>

      <view className="sidebar-list">
        {loading && <view className="muted">Loading…</view>}
        {!loading && items.length === 0 && (
          <view className="muted">No conversations yet.</view>
        )}
        {items.map((c) => (
          <view
            key={c.id}
            className={`list-item ${c.id === activeId ? 'active' : ''}`}
            bindtap={() => onSelect(c.id)}
          >
            <view className="title">{c.title || 'Untitled'}</view>
            <view className="time">
              {new Date(c.updatedAt).toLocaleString()}
            </view>
          </view>
        ))}
      </view>
    </view>
  );
}
