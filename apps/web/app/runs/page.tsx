"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Run } from "@/lib/types";
import { RunCard } from "@/components/runs/RunCard";

export default function RunsCatalogPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [filter, setFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  const loadRuns = async () => {
    try {
      const data = await api.getRuns();
      setRuns(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 4000);
    return () => clearInterval(interval);
  }, []);

  const filteredRuns = runs.filter((r) => {
    if (filter === "ALL") return true;
    if (filter === "ACTIVE") return r.status === "RUNNING" || r.status === "SLEEPING";
    if (filter === "COMPLETED") return r.status === "COMPLETED" || r.status === "TERMINATED";
    if (filter === "PAUSED") return r.status === "PAUSED";
    return true;
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#2A2A2A]">
        <div>
          <div className="flex items-center gap-2 text-xs text-[#a0a0a0] mb-2">
            <Link href="/" className="text-[#a0a0a0]">
              Dashboard
            </Link>
            <span>/</span>
            <span className="text-white">Runs Catalog</span>
          </div>
          <h1 className="text-3xl font-medium tracking-tight text-white">
            Supervised Order Runs
          </h1>
          <p className="text-[#a0a0a0] text-sm mt-1">
            Browse and inspect active and completed Temporal workflow instances.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {["ALL", "ACTIVE", "COMPLETED", "PAUSED"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-[8px] text-sm font-medium ${
                filter === f
                  ? "bg-[#2bd97c] text-black"
                  : "bg-[#2A2A2A] text-[#a0a0a0]"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading && runs.length === 0 ? (
        <div className="p-12 text-center text-[#a0a0a0] text-sm animate-pulse bg-[#2A2A2A] rounded-[12px]">
          Loading order runs...
        </div>
      ) : filteredRuns.length === 0 ? (
        <div className="p-12 text-center text-[#a0a0a0] text-sm bg-[#2A2A2A] rounded-[12px]">
          No orders match this filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRuns.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
