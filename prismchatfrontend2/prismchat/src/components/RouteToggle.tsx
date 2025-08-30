"use client";
import type { RouteMode } from "@/types/chat";

export default function RouteToggle({
  mode,
  onChange,
}: {
  mode: RouteMode;
  onChange: (m: RouteMode) => void;
}) {
  const isPG = mode === "prismguard";
  return (
    <div className="inline-flex rounded-md border border-slate-700 overflow-hidden">
      <button
        className={`px-3 py-1 text-sm ${
          !isPG ? "bg-indigo-600 text-white" : "bg-transparent text-slate-200"
        }`}
        onClick={() => onChange("direct")}
        type="button"
      >
        Direct
      </button>
      <button
        className={`px-3 py-1 text-sm ${
          isPG ? "bg-indigo-600 text-white" : "bg-transparent text-slate-200"
        }`}
        onClick={() => onChange("prismguard")}
        type="button"
      >
        PrismGuard
      </button>
    </div>
  );
}
