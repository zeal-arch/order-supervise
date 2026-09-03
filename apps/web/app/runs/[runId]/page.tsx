"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  PauseCircle,
  Brain,
  Compass,
  ArrowLeft,
  ShoppingBag,
  CreditCard,
  Truck,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";
import { Run } from "@/lib/types";
import { UnifiedFeed } from "@/components/runs/UnifiedFeed";
import { EventInjector } from "@/components/runs/EventInjector";
import { MemoryPanel } from "@/components/runs/MemoryPanel";
import { InstructionPanel } from "@/components/runs/InstructionPanel";
import { RunControls } from "@/components/runs/RunControls";

export default function RunDetailPage({ params }: { params: { runId: string } }) {
  const runId = params.runId;

  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rightPanelTab, setRightPanelTab] = useState<"memory" | "steering">("memory");

  const loadRun = async () => {
    try {
      const data = await api.getRun(runId);
      setRun(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load order run.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRun();
    const interval = setInterval(loadRun, 4000);
    return () => clearInterval(interval);
  }, [runId]);

  if (loading && !run) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-8 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h2 className="text-xl font-semibold text-white">Error Loading Order Run</h2>
        <p className="text-sm text-[#a0a0a0]">{error || "Order run not found."}</p>
        <Link
          href="/runs"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#202020] text-white text-sm hover:bg-[#303030]"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Runs</span>
        </Link>
      </div>
    );
  }

  // Derive Lifecycle Progress
  const eventTypes = new Set((run.events || []).map((e) => e.event_type));
  const isPaid = eventTypes.has("payment_confirmed");
  const isPaymentFailed = eventTypes.has("payment_failed");
  const isShipped = eventTypes.has("shipment_created");
  const isDelivered = eventTypes.has("delivered");
  const isRefunded = eventTypes.has("refund_requested");

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RUNNING":
        return {
          label: "Active Supervisor",
          icon: Clock,
          style: "bg-white/10 text-white border-white/20",
        };
      case "SLEEPING":
        return {
          label: "Dormant (Waiting for Signals)",
          icon: Clock,
          style: "bg-[#181818] text-[#a0a0a0] border-[#333333]",
        };
      case "PAUSED":
        return {
          label: "Paused by Operator",
          icon: PauseCircle,
          style: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        };
      case "COMPLETED":
        return {
          label: "Completed (Terminal)",
          icon: CheckCircle2,
          style: "bg-white/10 text-white border-white/20",
        };
      case "TERMINATED":
        return {
          label: "Terminated",
          icon: AlertCircle,
          style: "bg-red-500/10 text-red-400 border-red-500/20",
        };
      default:
        return {
          label: status,
          icon: Clock,
          style: "bg-[#181818] text-[#a0a0a0] border-[#333333]",
        };
    }
  };

  const statusMeta = getStatusBadge(run.status);
  const StatusIcon = statusMeta.icon;

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#2e2e2e]">
        <div>
          <div className="flex items-center gap-2 text-xs text-[#888888] mb-1.5 font-mono">
            <Link href="/" className="hover:text-white transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <Link href="/runs" className="hover:text-white transition-colors">
              Runs
            </Link>
            <span>/</span>
            <span className="text-white">{run.order_id}</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              {run.order_id}
            </h1>
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusMeta.style}`}
            >
              <StatusIcon className="w-3.5 h-3.5" />
              <span>{statusMeta.label}</span>
            </div>
          </div>
        </div>

        <RunControls runId={run.id} status={run.status} onStateChanged={loadRun} />
      </div>

      {/* Summary Context Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-[14px] bg-[#181818] border border-[#2e2e2e]">
        <div className="space-y-0.5">
          <span className="text-[10px] text-[#777777] uppercase font-mono font-bold tracking-wider">
            Customer
          </span>
          <p className="text-xs font-semibold text-white truncate">
            {run.order_context?.customer_name || "Alex Johnson"}
          </p>
          <p className="text-[11px] text-[#888888] truncate">{run.order_context?.customer_email}</p>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] text-[#777777] uppercase font-mono font-bold tracking-wider">
            Order Value
          </span>
          <p className="text-xs font-semibold text-white font-mono">
            ${run.order_context?.total_amount || 189.97}
          </p>
          <p className="text-[11px] text-[#888888]">
            {run.order_context?.items?.length || 1} Item(s)
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] text-[#777777] uppercase font-mono font-bold tracking-wider">
            AI Wake Schedule
          </span>
          <p className="text-xs font-semibold text-white">
            {run.status === "RUNNING" ? "Actively Processing" : "Dormant (0% CPU)"}
          </p>
          <p className="text-[11px] text-[#888888] truncate">
            Trigger: {run.last_wake_reason || "WORKFLOW_START"}
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] text-[#777777] uppercase font-mono font-bold tracking-wider">
            Workflow ID
          </span>
          <p className="text-xs font-mono text-white truncate">{run.workflow_id}</p>
          <p className="text-[11px] text-[#888888]">Temporal Task Queue</p>
        </div>
      </div>

      {/* Lifecycle Progress Stepper */}
      <div className="p-4 rounded-[14px] bg-[#181818] border border-[#2e2e2e]">
        <span className="text-[10px] uppercase font-mono font-bold text-[#777777] tracking-wider block mb-3">
          ORDER LIFECYCLE PROGRESSION
        </span>
        <div className="grid grid-cols-4 gap-2">
          {/* Step 1: Placed */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div className="w-7 h-7 rounded-full flex items-center justify-center bg-white text-black font-semibold text-xs">
              <Check className="w-3.5 h-3.5 stroke-[3]" />
            </div>
            <span className="text-xs font-semibold text-white">Order Placed</span>
            <span className="text-[10px] text-[#888888]">Cart Checkout</span>
          </div>

          {/* Step 2: Payment */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                isPaid
                  ? "bg-white text-black"
                  : isPaymentFailed
                  ? "bg-red-500/20 text-red-400 border border-red-500/40"
                  : "bg-[#252525] text-[#888888]"
              }`}
            >
              {isPaid ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : <CreditCard className="w-3.5 h-3.5" />}
            </div>
            <span className="text-xs font-semibold text-white">
              {isPaid ? "Payment Verified" : isPaymentFailed ? "Payment Issue" : "Payment Pending"}
            </span>
            <span className="text-[10px] text-[#888888]">
              {isPaid ? "Captured ($189.97)" : isPaymentFailed ? "Declined / Failed" : "Awaiting Auth"}
            </span>
          </div>

          {/* Step 3: Transit */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                isDelivered
                  ? "bg-white text-black"
                  : isShipped
                  ? "bg-white/20 text-white border border-white/40"
                  : "bg-[#252525] text-[#888888]"
              }`}
            >
              {isDelivered ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : <Truck className="w-3.5 h-3.5" />}
            </div>
            <span className="text-xs font-semibold text-white">
              {isDelivered ? "Delivered" : isShipped ? "In Transit" : "Fulfillment"}
            </span>
            <span className="text-[10px] text-[#888888]">
              {isShipped ? "FedEx On Vehicle" : "Warehouse Prep"}
            </span>
          </div>

          {/* Step 4: Terminal */}
          <div className="flex flex-col items-center text-center space-y-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                isDelivered
                  ? "bg-white text-black"
                  : isRefunded
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/40"
                  : "bg-[#252525] text-[#888888]"
              }`}
            >
              {isDelivered ? (
                <Check className="w-3.5 h-3.5 stroke-[3]" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5" />
              )}
            </div>
            <span className="text-xs font-semibold text-white">
              {isDelivered ? "Delivered" : isRefunded ? "Refunded" : "Final Delivery"}
            </span>
            <span className="text-[10px] text-[#888888]">
              {isDelivered ? "Front Porch" : isRefunded ? "Order Cancelled" : "Awaiting Drop-off"}
            </span>
          </div>
        </div>
      </div>

      {/* Terminal Post-Mortem Card */}
      {run.final_output && (
        <div className="p-5 rounded-[14px] bg-[#181818] border border-[#2e2e2e] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-white" />
              <h3 className="text-sm font-semibold text-white tracking-tight">
                Post-Mortem & AI Supervisor Learnings
              </h3>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded bg-white/10 text-white font-mono uppercase font-bold">
              Terminal Report
            </span>
          </div>
          <p className="text-xs text-[#b8b8b8] leading-relaxed">
            {run.final_output.final_summary}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="p-3 rounded-[8px] bg-[#121212] border border-[#262626] space-y-1.5">
              <span className="text-[10px] uppercase font-mono font-bold text-[#888888] tracking-wider block">
                Key Learnings
              </span>
              <ul className="space-y-1 text-xs text-[#a0a0a0]">
                {run.final_output.key_learnings?.map((l: string, i: number) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-neutral-500">•</span>
                    <span>{l}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-3 rounded-[8px] bg-[#121212] border border-[#262626] space-y-1.5">
              <span className="text-[10px] uppercase font-mono font-bold text-purple-400 tracking-wider block">
                Operational Recommendations
              </span>
              <ul className="space-y-1 text-xs text-[#a0a0a0]">
                {run.final_output.feedback_and_recommendations?.map((r: string, i: number) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-purple-400">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Main 2-Panel Balanced Master-Detail Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Activity & Execution Trace (7 cols / ~60% width) */}
        <div className="lg:col-span-7">
          <UnifiedFeed events={run.events || []} activities={run.activities || []} />
        </div>

        {/* Right Column: Sticky Operational Sidebar (5 cols / ~40% width) */}
        <div className="lg:col-span-5 space-y-5 sticky top-20">
          {/* 1. Operational Event Simulator */}
          <EventInjector
            runId={run.id}
            events={run.events || []}
            status={run.status}
            onEventSent={loadRun}
          />

          {/* 2. AI Memory & Human Operator Hub */}
          <div className="space-y-3">
            {/* Hub Selector Tabs */}
            <div className="flex items-center justify-between pb-2 border-b border-[#2e2e2e]">
              <div className="flex gap-1.5 w-full">
                <button
                  type="button"
                  onClick={() => setRightPanelTab("memory")}
                  className={`flex-1 text-[11px] py-1.5 px-2 rounded-[6px] font-medium transition-colors cursor-pointer flex items-center justify-center gap-1.5 ${
                    rightPanelTab === "memory"
                      ? "bg-white text-black font-semibold shadow-sm"
                      : "bg-[#181818] text-[#888888] hover:text-white"
                  }`}
                >
                  <Brain className="w-3.5 h-3.5" />
                  <span>AI Memory State</span>
                </button>

                <button
                  type="button"
                  onClick={() => setRightPanelTab("steering")}
                  className={`flex-1 text-[11px] py-1.5 px-2 rounded-[6px] font-medium transition-colors cursor-pointer flex items-center justify-center gap-1.5 ${
                    rightPanelTab === "steering"
                      ? "bg-white text-black font-semibold shadow-sm"
                      : "bg-[#181818] text-[#888888] hover:text-white"
                  }`}
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>Human Guidance</span>
                </button>
              </div>
            </div>

            {/* Tab View */}
            {rightPanelTab === "memory" ? (
              <MemoryPanel memory={run.current_memory} />
            ) : (
              <InstructionPanel
                runId={run.id}
                instructions={run.additional_instructions || []}
                onInstructionSent={loadRun}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
