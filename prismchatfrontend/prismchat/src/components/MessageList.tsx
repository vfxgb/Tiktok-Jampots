// src/components/MessageList.tsx
import type { ChatMessage } from '../types/chat.js';
import ChatMessageView from './ChatMessage.js';
import { useAutoScroll } from '../hooks/useAutoScroll.js';

export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  const ref = useAutoScroll<HTMLElement>();
  return (
    <view className="messages" ref={ref as any}>
      {messages.map((m) => (
        <ChatMessageView key={m.id} msg={m} />
      ))}
    </view>
  );
}
