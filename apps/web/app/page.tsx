"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Run, Supervisor } from "@/lib/types";
import { RunCard } from "@/components/runs/RunCard";
import { ArrowRight, Settings2, Shield, Activity, Plus } from "lucide-react";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [runs, setRuns] = useState<Run[]>([]);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [loading, setLoading] = useState(true);
  const [newOrderId, setNewOrderId] = useState("");
  const [selectedSup, setSelectedSup] = useState("");
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    try {
      const [runsData, supsData] = await Promise.all([
        api.getRuns().catch(() => []),
        api.getSupervisors().catch(() => []),
      ]);
      setRuns(runsData);
      setSupervisors(supsData);
      
      const supParam = searchParams.get("supervisor");
      if (supParam && supsData.some((s) => s.id === supParam)) {
        setSelectedSup(supParam);
      } else if (supsData.length > 0 && !selectedSup) {
        setSelectedSup(supsData[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, [searchParams]);

  const handleStartRun = async (e: React.FormEvent, withAutoplay = true) => {
    e.preventDefault();
    const orderId = newOrderId.trim() || `ORD-${Math.floor(1000 + Math.random() * 9000)}`;
    setCreating(true);
    try {
      const newRun = await api.createRun({
        order_id: orderId,
        supervisor_id: selectedSup || undefined,
      });
      router.push(`/runs/${newRun.id}${withAutoplay ? "" : "?mode=manual"}`);
    } catch (e: any) {
      alert(`Error starting run: ${e.message}`);
      setCreating(false);
    }
  };

  const activeCount = runs.filter((r) => r.status === "RUNNING" || r.status === "SLEEPING").length;
  const completedCount = runs.filter((r) => r.status === "COMPLETED").length;
  const activeSupervisor = supervisors.find((s) => s.id === selectedSup) || supervisors[0];

  return (
    <div className="space-y-10">
      {/* Header & Order Creator */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 pb-8 border-b border-[#2e2e2e]">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[#888888] text-xs font-mono uppercase tracking-wider">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Autonomous E-Commerce Operations</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-white">
            Order Supervisor
          </h1>
          <p className="text-[#888888] text-sm max-w-xl leading-relaxed">
            Durable Temporal AI agent overseeing customer order lifecycles from creation to completion.
          </p>
        </div>

        {/* Order Creator with Supervisor Template Selection */}
        <form
          onSubmit={(e) => handleStartRun(e, true)}
          className="bg-[#1a1a1a] border border-[#2e2e2e] p-5 rounded-[12px] space-y-3 w-full lg:w-auto min-w-[420px]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Launch Supervised Order</span>
            <button
              type="button"
              onClick={() => setNewOrderId(`ORD-${Math.floor(1000 + Math.random() * 9000)}`)}
              className="text-[11px] text-neutral-400 hover:text-white font-mono transition-colors cursor-pointer"
            >
              + Random ID
            </button>
          </div>

          <div className="space-y-2.5">
            <input
              type="text"
              placeholder="Order ID (e.g. ORD-9021)"
              value={newOrderId}
              onChange={(e) => setNewOrderId(e.target.value)}
              className="text-xs px-3.5 py-2.5 rounded-[8px] bg-[#121212] border border-[#2e2e2e] text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-400 w-full font-mono"
            />

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-mono text-[#888888] font-bold block">
                Supervisor Template:
              </label>
              <select
                value={selectedSup}
                onChange={(e) => setSelectedSup(e.target.value)}
                className="text-xs px-3 py-2.5 rounded-[8px] bg-[#121212] border border-[#2e2e2e] text-white focus:outline-none focus:border-neutral-400 cursor-pointer w-full font-mono"
              >
                {supervisors.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.wake_sensitivity} • {s.model_name || "gpt-4o-mini"})
                  </option>
                ))}
              </select>
            </div>

            {/* Action Buttons: Default Autoplay + Manual Mode Option */}
            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                disabled={creating}
                className="flex-1 py-2.5 px-3 rounded-[8px] bg-white text-black text-xs font-semibold hover:bg-neutral-200 transition-colors disabled:opacity-50 whitespace-nowrap cursor-pointer flex items-center justify-center gap-1.5"
              >
                <span>{creating ? "Launching..." : "Launch Order (Autoplay)"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                type="button"
                disabled={creating}
                onClick={(e) => handleStartRun(e, false)}
                className="py-2.5 px-3 rounded-[8px] bg-[#141414] text-neutral-300 border border-neutral-700 text-xs font-semibold hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-50 whitespace-nowrap cursor-pointer flex items-center justify-center gap-1.5"
                title="Launch order in manual mode to trigger individual events by hand"
              >
                <span>Manual</span>
              </button>
            </div>
          </div>

          {activeSupervisor && (
            <div className="p-2.5 rounded-[6px] bg-[#121212] border border-[#262626] text-[10px] text-[#888888] flex items-center justify-between font-mono">
              <span>Wake: {activeSupervisor.wake_sensitivity} ({activeSupervisor.default_wake_delay_seconds ? `${activeSupervisor.default_wake_delay_seconds / 60}m` : "60m"})</span>
              <Link href="/supervisors" className="text-white hover:underline flex items-center gap-1">
                <Settings2 className="w-3 h-3" />
                <span>Manage Templates</span>
              </Link>
            </div>
          )}
        </form>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-1">
          <div className="text-[#888888] text-xs font-mono uppercase tracking-wider">Active Supervisors</div>
          <div className="text-2xl sm:text-3xl font-semibold text-white">{activeCount}</div>
        </div>

        <div className="p-5 rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-1">
          <div className="text-[#888888] text-xs font-mono uppercase tracking-wider">Completed Orders</div>
          <div className="text-2xl sm:text-3xl font-semibold text-white">{completedCount}</div>
        </div>

        <div className="p-5 rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-1">
          <div className="flex items-center justify-between">
            <div className="text-[#888888] text-xs font-mono uppercase tracking-wider">Supervisor Profiles</div>
            <Link href="/supervisors" className="text-[11px] text-white hover:underline font-mono">
              Manage →
            </Link>
          </div>
          <div className="text-2xl sm:text-3xl font-semibold text-white">{supervisors.length || 3}</div>
        </div>

        <div className="p-5 rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-1">
          <div className="text-[#888888] text-xs font-mono uppercase tracking-wider">Inference Triggers</div>
          <div className="text-2xl sm:text-3xl font-semibold text-white font-mono">3 / 3 Active</div>
        </div>
      </div>

      {/* Active Orders Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-white">Supervised Order Runs</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-[4px] bg-[#1a1a1a] text-[#888888] border border-[#2e2e2e] font-mono">
              {runs.length} Total
            </span>
          </div>
          <Link href="/runs" className="text-xs font-medium text-[#888888] hover:text-white transition-colors">
            View All Runs →
          </Link>
        </div>

        {runs.length === 0 ? (
          <div className="p-16 text-center rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-2">
            <p className="text-white text-sm font-medium">No order workflows currently running</p>
            <p className="text-[#888888] text-xs">
              Enter an Order ID above and click &quot;Launch&quot; to test a live lifecycle.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {runs.slice(0, 6).map((run) => (
              <RunCard key={run.id} run={run} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="p-8 text-neutral-500">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
