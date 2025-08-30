import { useMemo, useState } from '@lynx-js/react';
import './App.css';

import Sidebar from './components/Sidebar.js';
import MessageList from './components/MessageList.js';
import MessageInput from './components/MessageInput.js';

import type { ChatMessage, RouteMode } from './types/chat.js';
import { getConversation, sendMessage } from './lib/api.js';

export function App(props: { onRender?: () => void }) {
  props.onRender?.();
  console.log('[PrismChat] App render start');
  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    const w = (globalThis as any)?.innerWidth ?? 1024;
    return w >= 900; // open on desktop, closed on mobile
  });

  // Chat state
  const [conversationId, setConversationId] = useState<string | undefined>(
    undefined,
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [route, setRoute] = useState<RouteMode>('prismguard');
  const [loading, setLoading] = useState(false);

  async function loadConversation(id: string) {
    setConversationId(id);
    // Auto-close sidebar on small screens after selecting a chat
    const w = (globalThis as any)?.innerWidth ?? 1024;
    if (w < 900) setSidebarOpen(false);
    setLoading(true);
    try {
      const msgs = await getConversation(id);
      setMessages(msgs);
    } catch (e) {
      console.error(e);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setConversationId(undefined);
    setMessages([]);
  }

  async function handleSend(text: string, files: File[]) {
    setLoading(true);
    try {
      const res = await sendMessage({
        conversationId,
        route,
        text,
        imageFiles: files,
      });
      if (!conversationId) setConversationId(res.conversationId);
      setMessages(res.messages);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const title = useMemo(() => {
    if (!messages.length) return 'New chat';
    const first = messages.find((m) => m.role === 'user');
    return first?.content?.slice(0, 42) || 'Conversation';
  }, [messages]);

  return (
    <view className="app">
      <Sidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
        activeId={conversationId}
        onSelect={loadConversation}
        onNewChat={newChat}
      />

      <view className="main">
        <view className="topbar">
          <view
            className="ghost only-mobile"
            bindtap={() => setSidebarOpen(true)}
          >
            <text>☰</text>
          </view>
          <text className="truncate">{title}</text>
        </view>

        <view className="chat">
          {loading && messages.length === 0 ? (
            <view className="muted pad">
              <text>Loading…</text>
            </view>
          ) : null}
          {!loading && messages.length === 0 ? (
            <view className="muted pad">
              <text>
                Start a conversation by sending a message or an image.
              </text>
            </view>
          ) : null}
          {messages.length ? <MessageList messages={messages} /> : null}
        </view>

        <view className="footer">
          <MessageInput
            disabled={loading}
            route={route}
            onRouteChange={setRoute}
            onSend={handleSend}
          />
        </view>
      </view>
    </view>
  );
}

export default App;
