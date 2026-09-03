"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Supervisor } from "@/lib/types";
import { SupervisorForm } from "@/components/supervisors/SupervisorForm";
import { ArrowRight, Clock, Cpu, ShieldCheck, Trash2 } from "lucide-react";

export default function SupervisorsPage() {
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadSupervisors = async () => {
    try {
      const data = await api.getSupervisors();
      setSupervisors(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSupervisors();
  }, []);

  const handleDelete = async (supId: string, supName: string) => {
    const ok = window.confirm(`Are you sure you want to delete profile "${supName}"?`);
    if (!ok) return;

    setDeletingId(supId);
    try {
      await api.deleteSupervisor(supId);
      await loadSupervisors();
    } catch (err: any) {
      alert(`Error deleting supervisor: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-10">
      <div className="pb-6 border-b border-[#2e2e2e] space-y-2">
        <Link
          href="/"
          className="text-xs text-[#888888] hover:text-white transition-colors"
        >
          ← Back to Dashboard
        </Link>
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-white" />
          <h1 className="text-2xl sm:text-3xl font-semibold text-white tracking-tight">Supervisor Profiles</h1>
        </div>
        <p className="text-xs text-[#888888] max-w-xl">
          Configure agent operating directives, tool permissions, LLM model choice, and wake sensitivity for order workflows.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Templates List */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider font-mono">
              Active Supervisor Profiles
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-[4px] bg-[#1a1a1a] text-[#888888] border border-[#2e2e2e] font-mono">
              {supervisors.length} active
            </span>
          </div>

          <div className="space-y-4">
            {supervisors.map((sup) => (
              <div
                key={sup.id}
                className="p-5 rounded-[12px] bg-[#1a1a1a] border border-[#2e2e2e] space-y-4 hover:border-[#444444] transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <h3 className="text-sm font-semibold text-white">{sup.name}</h3>
                    <p className="text-xs text-[#888888]">{sup.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#101010] text-neutral-300 border border-[#2e2e2e]">
                      {sup.wake_sensitivity}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(sup.id, sup.name)}
                      disabled={deletingId === sup.id}
                      title="Delete profile"
                      className="p-1.5 rounded-[6px] text-neutral-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all cursor-pointer disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="p-3.5 rounded-[8px] bg-[#121212] border border-[#262626] text-xs text-[#d0d0d0] leading-relaxed">
                  <span className="text-[#888888] block mb-1 font-mono uppercase text-[9px] font-bold">
                    CORE DIRECTIVES:
                  </span>
                  &quot;{sup.base_instruction}&quot;
                </div>

                {/* Meta details: Model, Interval & Tools */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-[#888888] font-mono">
                  <div className="flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5 text-neutral-400" />
                    <span>{sup.model_name || "gpt-4o-mini"}</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-neutral-400" />
                    <span>{sup.default_wake_delay_seconds ? `${sup.default_wake_delay_seconds / 60}m sleep` : "60m sleep"}</span>
                  </div>
                </div>

                <div>
                  <span className="text-[9px] font-mono uppercase text-[#888888] block mb-1.5 font-bold">
                    ENABLED TOOLS ({sup.available_tools?.length || 0}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {sup.available_tools?.map((tool) => (
                      <span
                        key={tool}
                        className="px-2 py-0.5 rounded bg-[#121212] text-[10px] font-mono text-neutral-400 border border-[#262626]"
                      >
                        {tool.replace("message_", "").replace("create_", "").replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-3 border-t border-[#262626]">
                  <span className="text-[10px] text-[#666666] font-mono">ID: {sup.id}</span>
                  <Link
                    href={`/?supervisor=${sup.id}`}
                    className="px-3 py-1.5 rounded-[6px] bg-white text-black font-semibold text-xs hover:bg-neutral-200 transition-colors flex items-center gap-1"
                  >
                    <span>Use in New Order</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Form */}
        <div className="lg:col-span-5">
          <SupervisorForm onCreated={loadSupervisors} existingSupervisors={supervisors} />
        </div>
      </div>
    </div>
  );
}
