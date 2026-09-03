"use client";

import { useState } from "react";
import {
  Mail,
  Truck,
  FileText,
  CreditCard,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { DomainEvent, AgentActivity } from "@/lib/types";

interface FeedItem {
  id: string;
  type: "event" | "activity";
  timestamp: string;
  data: DomainEvent | AgentActivity;
}

export function UnifiedFeed({
  events = [],
  activities = [],
}: {
  events?: DomainEvent[];
  activities?: AgentActivity[];
}) {
  const [filter, setFilter] = useState<"all" | "actions" | "events">("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Combine and sort chronologically
  const items: FeedItem[] = [
    ...events.map((e) => ({
      id: `evt-${e.id || Math.random()}`,
      type: "event" as const,
      timestamp: e.created_at,
      data: e,
    })),
    ...activities.map((a) => ({
      id: `act-${a.id || Math.random()}`,
      type: "activity" as const,
      timestamp: a.created_at,
      data: a,
    })),
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const filteredItems = items.filter((item) => {
    if (filter === "actions") return item.type === "activity";
    if (filter === "events") return item.type === "event";
    return true;
  });

  const formatTraceTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "00:00:00";
    }
  };

  const getEventTitle = (evt: DomainEvent) => {
    switch (evt.event_type) {
      case "order_created":
        return "Order Placed & Supervisor Assigned";
      case "payment_confirmed":
        return `Payment Verified ($${evt.payload?.amount || "189.97"})`;
      case "payment_failed":
        return "Payment Authorization Declined";
      case "shipment_created":
        return `Shipment Dispatched (${evt.payload?.carrier || "FedEx Express"})`;
      case "shipment_delayed":
        return `Carrier Delay Alert (${evt.payload?.carrier || "FedEx Express"})`;
      case "delivery_attempt_failed":
      case "customer_not_home":
        return "Delivery Attempt Failed (NDR - Customer Not Home)";
      case "delivered":
        return "Parcel Confirmed Delivered";
      case "refund_requested":
        return "Customer Refund / Return Requested";
      case "customer_message_received":
        return "Inbound Customer Inquiry Received";
      case "no_update_for_n_hours":
        return `Tracking Stalled (${evt.payload?.hours || 24}h Without Update)`;
      case "manual_instruction":
        return "Human Operator Guidance Injected";
      default:
        return evt.event_type.replace(/_/g, " ");
    }
  };

  const getEventDescription = (evt: DomainEvent) => {
    if (evt.payload?.message) return evt.payload.message;
    if (evt.payload?.reason) return evt.payload.reason;
    if (evt.payload?.instruction) return evt.payload.instruction;
    if (evt.event_type === "order_created") return "New order received from checkout. Dedicated workflow spawned.";
    if (evt.event_type === "delivered") return "Carrier confirmed drop-off at delivery address.";
    return JSON.stringify(evt.payload || {});
  };

  const getActivityTitle = (act: AgentActivity) => {
    switch (act.activity_type) {
      case "message_customer":
        return "Dispatched Customer Email Notification";
      case "message_logistics_team":
        return "Opened Courier Escalation Ticket";
      case "message_fulfillment_team":
        return "Notified Warehouse Fulfillment Team";
      case "message_payments_team":
        return "Initiated Finance Action / Refund Authorization";
      case "create_internal_note":
        return "Logged Operational Audit Note";
      default:
        return act.activity_type.replace(/_/g, " ");
    }
  };

  return (
    <div className="space-y-4">
      {/* Header & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#3a3a3a]">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">Execution & Activity Trace</h2>
          <p className="text-xs text-[#a0a0a0]">
            Autonomous agent decision chain and operational event stream
          </p>
        </div>

        <div className="flex gap-1 p-1 rounded-[8px] bg-[#1a1a1a] self-start sm:self-auto border border-[#333333]">
          {(
            [
              { id: "all", label: `All (${items.length})` },
              { id: "events", label: `Events (${events.length})` },
              { id: "actions", label: `Actions (${activities.length})` },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilter(tab.id)}
              className={`text-xs px-3 py-1 rounded-[6px] font-medium transition-colors cursor-pointer ${
                filter === tab.id
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-[#a0a0a0] hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Connected Trace Timeline */}
      {filteredItems.length === 0 ? (
        <div className="p-12 text-center text-[#a0a0a0] text-xs rounded-[12px] bg-[#1a1a1a] border border-[#333333]">
          No execution trace recorded yet. Trigger an event from the simulator sidebar to begin.
        </div>
      ) : (
        <div className="relative pl-7 space-y-4 before:absolute before:left-[11px] before:top-3 before:bottom-3 before:w-[2px] before:bg-[#2e2e2e]">
          {filteredItems.map((item) => {
            const isActivity = item.type === "activity";
            const act = isActivity ? (item.data as AgentActivity) : null;
            const evt = !isActivity ? (item.data as DomainEvent) : null;
            const isExpanded = expandedId === item.id;
            const p = act?.payload || {};

            return (
              <div key={item.id} className="relative group">
                {/* Minimal Rail Dot */}
                <div
                  className={`absolute -left-[22px] top-4 w-2.5 h-2.5 rounded-full z-10 ring-4 ring-[#141414] transition-all ${
                    isActivity ? "bg-white" : "bg-[#555555]"
                  }`}
                />

                {/* Execution Trace Card */}
                <div
                  className={`p-4 rounded-[12px] border transition-all ${
                    isActivity
                      ? "bg-[#202020] border-[#383838]"
                      : "bg-[#181818] border-[#2c2c2c]"
                  }`}
                >
                  <div className="space-y-2.5">
                    {/* Top Row: Timestamp, Tag, and Title */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-mono text-[#888888] font-medium">
                          {formatTraceTime(item.timestamp)}
                        </span>

                        <span
                          className={`text-[9px] px-2 py-0.5 rounded-[4px] uppercase font-mono font-bold tracking-wider ${
                            isActivity
                              ? "bg-white/10 text-white border border-white/20"
                              : "bg-[#121212] text-[#888888] border border-[#333333]"
                          }`}
                        >
                          {isActivity ? "ACTION" : "EVENT"}
                        </span>

                        <span className="text-xs font-semibold text-white">
                          {isActivity ? getActivityTitle(act!) : getEventTitle(evt!)}
                        </span>
                      </div>

                      {/* Tool identifier or status */}
                      <span className="text-[10px] text-[#777777] font-mono whitespace-nowrap">
                        {isActivity ? act?.activity_type : evt?.source || "domain_signal"}
                      </span>
                    </div>

                    {/* Action Previews */}
                    {isActivity && act?.activity_type === "message_customer" && (
                      <div className="p-3 rounded-[8px] bg-[#121212] space-y-1.5 border border-[#2a2a2a]">
                        <div className="flex items-center gap-2 text-[11px] text-white font-medium">
                          <Mail className="w-3.5 h-3.5 text-neutral-400" />
                          <span>Subject: {p.subject || "Order Update"}</span>
                        </div>
                        <p className="text-xs text-[#b8b8b8] leading-relaxed">
                          {p.body || p.message_body || "Notification dispatched to customer."}
                        </p>
                      </div>
                    )}

                    {isActivity && act?.activity_type === "message_logistics_team" && (
                      <div className="p-3 rounded-[8px] bg-[#121212] space-y-1.5 border border-[#2a2a2a]">
                        <div className="flex items-center justify-between text-[11px]">
                          <div className="flex items-center gap-2 text-white font-medium">
                            <Truck className="w-3.5 h-3.5 text-neutral-400" />
                            <span>Carrier Escalation: {p.carrier || "FedEx"}</span>
                          </div>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono uppercase">
                            Ticket Opened
                          </span>
                        </div>
                        <p className="text-xs text-[#b8b8b8] leading-relaxed font-mono">
                          Tracking: {p.tracking_number || "FX-99881122"} | Reason: {p.issue || p.reason}
                        </p>
                      </div>
                    )}

                    {isActivity && act?.activity_type === "message_payments_team" && (
                      <div className="p-3 rounded-[8px] bg-[#121212] space-y-1.5 border border-[#2a2a2a]">
                        <div className="flex items-center gap-2 text-[11px] text-purple-300 font-medium">
                          <CreditCard className="w-3.5 h-3.5 text-purple-400" />
                          <span>Action Required: {p.action_required || "Payment & Refund Review"}</span>
                        </div>
                        <p className="text-xs text-[#b8b8b8] leading-relaxed">
                          {p.issue_description || p.reason || "Payment exception escalated to finance."}
                        </p>
                      </div>
                    )}

                    {isActivity && act?.activity_type === "create_internal_note" && (
                      <div className="p-3 rounded-[8px] bg-[#121212] text-xs text-[#b8b8b8] border border-[#2a2a2a] space-y-1">
                        <div className="flex items-center gap-1.5 text-[10px] text-neutral-400 font-mono uppercase font-semibold">
                          <FileText className="w-3 h-3 text-neutral-500" />
                          <span>Audit Note: {p.category || "GENERAL"}</span>
                        </div>
                        <p className="leading-relaxed font-mono text-[11px] text-neutral-300">
                          {p.note || "Operational state updated."}
                        </p>
                      </div>
                    )}

                    {/* External Event Payload Summary */}
                    {!isActivity && (
                      <div className="text-xs text-[#a0a0a0] leading-relaxed pl-1">
                        {getEventDescription(evt!)}
                      </div>
                    )}

                    {/* Collapsible AI Reasoning Drawer */}
                    {isActivity && act?.reasoning && (
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={() => setExpandedId(isExpanded ? null : item.id)}
                          className="text-[11px] text-[#888888] hover:text-white flex items-center gap-1 cursor-pointer transition-colors"
                        >
                          <span>{isExpanded ? "Hide Supervisor Decision" : "View Supervisor Decision"}</span>
                          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>

                        {isExpanded && (
                          <div className="mt-2 p-3 rounded-[8px] bg-[#121212] border border-[#2a2a2a] text-xs text-[#d0d0d0] leading-relaxed animate-in fade-in duration-200">
                            <span className="text-[9px] uppercase font-mono text-neutral-400 font-bold block mb-1">
                              DECISION TRACE:
                            </span>
                            {act.reasoning}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
