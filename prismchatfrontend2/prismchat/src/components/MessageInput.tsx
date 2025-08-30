"use client";
import { useRef, useState } from "react";
import RouteToggle from "./RouteToggle";
import type { RouteMode } from "@/types/chat";
import { sendMessage, uploadImages } from "@/lib/api";

export default function MessageInput({
  disabled,
  route,
  onRouteChange,
  conversationId,
  onReply,
}: {
  disabled?: boolean;
  route: RouteMode;
  onRouteChange: (m: RouteMode) => void;
  conversationId?: string;
  onReply: (res: { conversationId: string; messages: any[] }) => void;
}) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  function pickFiles() {
    fileRef.current?.click();
  }
  function handleFiles(list: FileList | null) {
    if (!list) return;
    const arr = Array.from(list).slice(0, 6);
    setFiles((prev) => [...prev, ...arr]);
  }

  async function doSend() {
    if (disabled) return;
    const trimmed = text.trim();
    if (!trimmed && files.length === 0) return;

    let imageUrls: string[] = [];
    if (files.length) {
      imageUrls = await uploadImages(files);
    }
    const res = await sendMessage({
      conversationId,
      route,
      text: trimmed,
      images: imageUrls,
    });
    setText("");
    setFiles([]);
    onReply(res);
    inputRef.current?.focus();
  }

  return (
    <div className="max-w-3xl mx-auto bg-[#141a2a] border border-slate-800 rounded-xl p-2">
      <div className="px-2 py-1">
        <RouteToggle mode={route} onChange={onRouteChange} />
      </div>

      {!!files.length && (
        <div className="flex gap-2 flex-wrap px-2 py-1 text-xs text-slate-400">
          {files.map((f, i) => (
            <span key={i} className="border border-slate-700 rounded px-2 py-1">
              {f.name}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 px-2 pb-2">
        <button
          onClick={pickFiles}
          className="border border-slate-700 rounded px-2 py-1 text-slate-200"
          title="Add images"
          type="button"
        >
          📎
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => handleFiles(e.currentTarget.files)}
          className="hidden"
        />

        <textarea
          ref={inputRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Message PrismChat…"
          className="flex-1 resize-y min-h-[44px] max-h-52 bg-[#0b0e14] border border-slate-700 rounded px-3 py-2 text-slate-100"
        />

        <button
          onClick={doSend}
          disabled={disabled}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded px-3 py-2"
          type="button"
        >
          Send
        </button>
      </div>
    </div>
  );
}
