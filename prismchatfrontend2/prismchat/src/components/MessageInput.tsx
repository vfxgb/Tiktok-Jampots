"use client";
import { useRef, useState } from "react";
import RouteToggle from "./RouteToggle";
import type { RouteMode } from "@/types/chat";
import { sendMessage, uploadImages, type UploadedImage } from "@/lib/api";

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
    // Allow selecting the same file again right away
    if (fileRef.current) fileRef.current.value = "";
  }

  async function doSend() {
    if (disabled) return;
    const trimmed = text.trim();
    if (!trimmed && files.length === 0) return;

    // 1) Upload; when route===prismguard, server redacts before storing
    let uploaded: UploadedImage[] = [];
    if (files.length) {
      uploaded = await uploadImages(files, route === "prismguard");
    }

    // 2) Send only storage URLs to backend; api.ts strips to storageUrl
    const res = await sendMessage({
      conversationId,
      route,
      text: trimmed,
      images: uploaded, // sendMessage converts to plain URLs
    });

    // 2a) Keep ORIGINAL text in the UI for this just-sent user turn
    if (route === "prismguard" && trimmed) {
      for (let i = res.messages.length - 1; i >= 0; i--) {
        const m = res.messages[i];
        if (m.role === "user") {
          res.messages[i] = { ...m, content: trimmed };
          break;
        }
      }
    }

    // 3) Keep UI showing ORIGINAL image previews for the just-sent user turn
    if (route === "prismguard" && uploaded.length) {
      const previews = uploaded.map((u) => u.previewUrl ?? u.storageUrl);
      for (let i = res.messages.length - 1; i >= 0; i--) {
        const m = res.messages[i];
        if (m.role === "user") {
          res.messages[i] = { ...m, images: previews };
          break;
        }
      }
    }

    // 4) Reset input state so you can attach the same file again
    setText("");
    setFiles([]);
    if (fileRef.current) fileRef.current.value = "";

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
