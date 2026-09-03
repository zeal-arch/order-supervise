"use client";

import { useState } from "react";
import { Pause, Play, X, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { RunStatus } from "@/lib/types";

export function RunControls({
  runId,
  status,
  onStateChanged,
}: {
  runId: string;
  status: RunStatus;
  onStateChanged?: () => void;
}) {
  const [loading, setLoading] = useState(false);

  const handlePause = async () => {
    setLoading(true);
    try {
      await api.interruptRun(runId);
      if (onStateChanged) onStateChanged();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      await api.resumeRun(runId);
      if (onStateChanged) onStateChanged();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleTerminate = async () => {
    if (!confirm("Are you sure you want to stop this Order Supervisor?")) return;
    setLoading(true);
    try {
      await api.terminateRun(runId);
      if (onStateChanged) onStateChanged();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const isPaused = status === "PAUSED";
  const isTerminated = status === "TERMINATED" || status === "COMPLETED";

  return (
    <div className="flex items-center gap-2">
      {!isTerminated && (
        <>
          {isPaused ? (
            <button
              onClick={handleResume}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white text-black text-xs font-medium hover:bg-neutral-200 transition-colors disabled:opacity-50"
            >
              <Play className="w-3 h-3 fill-black" />
              <span>Resume</span>
            </button>
          ) : (
            <button
              onClick={handlePause}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#141414] text-neutral-300 border border-neutral-800 hover:text-white hover:border-neutral-600 text-xs font-medium transition-colors disabled:opacity-50"
            >
              <Pause className="w-3 h-3" />
              <span>Pause</span>
            </button>
          )}

          <button
            onClick={handleTerminate}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#141414] text-neutral-500 border border-neutral-800 hover:text-rose-400 hover:border-rose-900 text-xs font-medium transition-colors disabled:opacity-50"
          >
            <X className="w-3 h-3" />
            <span>Stop</span>
          </button>
        </>
      )}

      {onStateChanged && (
        <button
          onClick={onStateChanged}
          title="Refresh State"
          className="p-2 rounded-xl bg-[#141414] hover:bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
