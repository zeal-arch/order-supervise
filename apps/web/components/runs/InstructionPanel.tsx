"use client";

import { useState } from "react";
import { Send, Compass, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { Instruction } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const SAMPLE_DIRECTIVES = [
  "Prioritize speed over cost for this order",
  "Escalate courier delays directly to logistics lead",
  "Offer 15% refund credit if customer complains about delay",
  "Do not dispatch customer email without manual confirmation",
];

export function InstructionPanel({
  runId,
  instructions = [],
  onInstructionSent,
}: {
  runId: string;
  instructions?: Instruction[];
  onInstructionSent?: () => void;
}) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    try {
      await api.injectInstruction(runId, text.trim());
      setText("");
      if (onInstructionSent) onInstructionSent();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-5 rounded-[16px] bg-[#202020] border border-[#333333] space-y-4">
      <div>
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-white" />
          <h3 className="text-sm font-semibold text-white tracking-tight">Human Operator Guidance</h3>
        </div>
        <p className="text-xs text-[#a0a0a0] mt-0.5">
          Inject runtime instructions into the supervisor&apos;s active decision context.
        </p>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="space-y-1.5">
        <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
          QUICK DIRECTIVES:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_DIRECTIVES.map((sample, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setText(sample)}
              className="text-[11px] px-2.5 py-1.5 rounded-[6px] bg-[#141414] text-[#d0d0d0] text-left border border-[#2e2e2e] hover:border-[#444444] cursor-pointer transition-colors"
            >
              + &quot;{sample}&quot;
            </button>
          ))}
        </div>
      </div>

      {/* Form Input */}
      <form onSubmit={handleSubmit} className="flex gap-2 pt-1">
        <input
          type="text"
          placeholder="e.g. Prioritize speed over cost..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="flex-1 text-xs px-3 py-2 rounded-[6px] bg-[#141414] border border-[#2e2e2e] text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-400"
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="px-3.5 py-2 rounded-[6px] bg-white text-black text-xs font-semibold disabled:opacity-50 cursor-pointer flex items-center gap-1.5 whitespace-nowrap"
        >
          <span>{loading ? "Steering..." : "Steer AI"}</span>
          <Send className="w-3 h-3" />
        </button>
      </form>

      {/* Existing active instructions */}
      {instructions && instructions.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-[#2e2e2e]">
          <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
            ACTIVE DIRECTIVES IN CONTEXT:
          </span>
          {instructions.map((inst, i) => (
            <div
              key={i}
              className="p-2.5 rounded-[6px] bg-[#141414] border border-[#2e2e2e] text-xs flex items-start justify-between gap-3"
            >
              <p className="text-[#d0d0d0] leading-relaxed flex items-start gap-1.5">
                <span className="text-neutral-500">•</span>
                <span>{inst.instruction}</span>
              </p>
              <span className="text-[10px] text-[#777777] font-mono whitespace-nowrap shrink-0">
                {formatDateTime(inst.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
