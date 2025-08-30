// src/components/MessageInput.tsx
import { useRef, useState } from '@lynx-js/react';
import RouteToggle from './RouteToggle.js';
import type { RouteMode } from '../types/chat.js';

interface Props {
  disabled?: boolean;
  route: RouteMode;
  onRouteChange(mode: RouteMode): void;
  onSend(text: string, files: File[]): void;
}

export default function MessageInput({
  disabled,
  route,
  onRouteChange,
  onSend,
}: Props) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);

  function openTextPrompt() {
    const promptFn = (globalThis as any)?.prompt;
    if (typeof promptFn === 'function') {
      const val = promptFn('Message PrismChat…', text) ?? '';
      setText(String(val));
    } else {
      // Fallback: toggle a minimal inline editor state (not implemented)
      // For Lynx runtime, we will replace this with a native picker later.
    }
  }
  function send() {
    const trimmed = text.trim();
    if (!trimmed && files.length === 0) return;
    onSend(trimmed, files);
    setText('');
    setFiles([]);
  }

  return (
    <view className="input-bar">
      <RouteToggle mode={route} onChange={onRouteChange} />

      {files.length ? (
        <view className="thumbs">
          {files.map((f, i) => (
            <view key={`f-${i}`} className="thumb">
              <text>{f.name}</text>
            </view>
          ))}
        </view>
      ) : null}

      <view className="input-row">
        <view className="icon is-disabled">
          <text>📎</text>
        </view>

        <view className="fake-input" bindtap={openTextPrompt}>
          <text className={text ? '' : 'muted'}>
            {text || 'Message PrismChat…'}
          </text>
        </view>

        <view
          className={`primary ${disabled ? 'is-disabled' : ''}`}
          bindtap={disabled ? undefined : send}
        >
          <text>Send</text>
        </view>
      </view>
    </view>
  );
}
