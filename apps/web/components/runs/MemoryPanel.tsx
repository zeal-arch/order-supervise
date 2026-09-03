"use client";

import { useState } from "react";
import { CompactMemory } from "@/lib/types";
import { Brain, Copy, Check, Code, LayoutList } from "lucide-react";

export function MemoryPanel({ memory }: { memory?: CompactMemory }) {
  const [viewMode, setViewMode] = useState<"formatted" | "json">("formatted");
  const [copied, setCopied] = useState(false);

  if (!memory) {
    return (
      <div className="p-5 rounded-[16px] bg-[#202020] border border-[#333333] text-[#a0a0a0] text-xs">
        Memory initializing...
      </div>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(memory, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy memory JSON:", err);
    }
  };

  return (
    <div className="p-5 rounded-[16px] bg-[#202020] border border-[#333333] space-y-4">
      {/* Header with Title and Copy / View Actions */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-white" />
          <h3 className="text-sm font-semibold text-white tracking-tight">AI Memory State</h3>
        </div>

        <div className="flex items-center gap-1.5">
          {/* View Toggle */}
          <div className="flex p-0.5 rounded-[6px] bg-[#141414] border border-[#2e2e2e]">
            <button
              type="button"
              onClick={() => setViewMode("formatted")}
              title="Formatted Summary View"
              className={`px-2 py-1 rounded-[4px] text-[10px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
                viewMode === "formatted"
                  ? "bg-[#282828] text-white font-semibold shadow-sm"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              <LayoutList className="w-3 h-3" />
              <span>Summary</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("json")}
              title="Raw JSON View"
              className={`px-2 py-1 rounded-[4px] text-[10px] font-medium transition-colors cursor-pointer flex items-center gap-1 ${
                viewMode === "json"
                  ? "bg-[#282828] text-white font-semibold shadow-sm"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              <Code className="w-3 h-3" />
              <span>JSON</span>
            </button>
          </div>

          {/* 1-Click Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            className="px-2.5 py-1 rounded-[6px] bg-[#141414] border border-[#2e2e2e] hover:border-[#444444] text-[11px] text-[#d0d0d0] hover:text-white transition-all cursor-pointer flex items-center gap-1 font-mono"
            title="Copy Memory JSON to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400 stroke-[3]" />
                <span className="text-emerald-400 text-[10px] font-semibold">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 text-neutral-400" />
                <span className="text-[10px]">Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* View Mode: Raw JSON */}
      {viewMode === "json" ? (
        <div className="relative">
          <pre className="p-3.5 rounded-[8px] bg-[#121212] border border-[#2e2e2e] text-[11px] font-mono text-neutral-300 leading-relaxed overflow-x-auto max-h-[360px] overflow-y-auto">
            {JSON.stringify(memory, null, 2)}
          </pre>
        </div>
      ) : (
        /* View Mode: Formatted Summary */
        <div className="space-y-3">
          {/* Rolling Summary */}
          <div className="p-3.5 rounded-[8px] bg-[#141414] border border-[#2e2e2e] space-y-1">
            <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
              STATE NARRATIVE
            </span>
            <p className="text-xs text-[#d0d0d0] leading-relaxed">
              {memory.rolling_summary || "Order ingested. Monitoring active lifecycle milestones."}
            </p>
          </div>

          {/* Key Milestones and Actions summary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-[8px] bg-[#141414] border border-[#2e2e2e] space-y-2">
              <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
                MILESTONES RECORDED
              </span>
              {memory.key_events_summary && memory.key_events_summary.length > 0 ? (
                <ul className="space-y-1 text-[#a0a0a0] text-[11px]">
                  {memory.key_events_summary.map((m, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-neutral-500">•</span>
                      <span>{m}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[#666666] text-[11px]">No milestones yet.</p>
              )}
            </div>

            <div className="p-3 rounded-[8px] bg-[#141414] border border-[#2e2e2e] space-y-2">
              <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
                ACTIONS EXECUTED
              </span>
              {memory.actions_taken && memory.actions_taken.length > 0 ? (
                <ul className="space-y-1 text-[#a0a0a0] text-[11px]">
                  {memory.actions_taken.slice(-4).map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-neutral-500">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[#666666] text-[11px]">No actions yet.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
