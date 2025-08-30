// src/components/ChatMessage.tsx
import type { ChatMessage as Msg } from '../types/chat.js';

export default function ChatMessage({ msg }: { msg: Msg }) {
  const isUser = msg.role === 'user';
  return (
    <view className={`bubble ${isUser ? 'user' : 'assistant'}`}>
      <view className="bubble-meta">
        <text className="who">{isUser ? 'You' : 'Assistant'}</text>
        <text className="time">
          {new Date(msg.createdAt).toLocaleTimeString()}
        </text>
      </view>

      {msg.content ? <text className="bubble-text">{msg.content}</text> : null}

      {msg.images && msg.images.length ? (
        <view className="bubble-images">
          {msg.images.map((url, i) => (
            <image
              key={`${msg.id}-img-${i}`}
              src={url}
              className="bubble-image"
            />
          ))}
        </view>
      ) : null}
    </view>
  );
}
