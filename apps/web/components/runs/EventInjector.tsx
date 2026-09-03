"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Truck,
  CreditCard,
  MessageSquare,
  Home,
  Send,
  Clock,
  RotateCcw,
  Package,
} from "lucide-react";
import { api } from "@/lib/api";
import { DomainEvent } from "@/lib/types";

interface EventPreset {
  label: string;
  type: string;
  desc: string;
  group: "shipping" | "payments" | "customer";
  category: "critical" | "informational" | "terminal";
  icon: any;
  payload: Record<string, any>;
  expectedActions: string;
}

const EVENT_PRESETS: EventPreset[] = [
  {
    label: "Payment Verified",
    type: "payment_confirmed",
    desc: "Card captured successfully ($189.97)",
    group: "payments",
    category: "informational",
    icon: CreditCard,
    payload: {
      transaction_id: "tx_live_998811",
      method: "credit_card",
      amount: 189.97,
    },
    expectedActions: "Notifies warehouse team to pack, sends receipt to customer",
  },
  {
    label: "Payment Declined",
    type: "payment_failed",
    desc: "Card authorization failed ($189.97)",
    group: "payments",
    category: "critical",
    icon: AlertTriangle,
    payload: {
      reason: "insufficient_funds",
      amount: 189.97,
      gateway: "Stripe",
    },
    expectedActions: "Alerts billing department, sends payment retry link to customer",
  },
  {
    label: "Shipment Dispatched",
    type: "shipment_created",
    desc: "Package handed to courier with tracking",
    group: "shipping",
    category: "informational",
    icon: Package,
    payload: {
      carrier: "FedEx Express",
      tracking_number: "FX-99881122",
    },
    expectedActions: "Captures tracking number, sends dispatch email with tracking link",
  },
  {
    label: "Carrier Delay Alert",
    type: "shipment_delayed",
    desc: "48h regional hub blizzard delay",
    group: "shipping",
    category: "critical",
    icon: Truck,
    payload: {
      carrier: "FedEx Express",
      tracking_number: "FX-99881122",
      reason: "Severe winter blizzard at sorting hub",
      delay_hours: 48,
    },
    expectedActions: "Opens carrier ticket, emails customer proactive update, logs note",
  },
  {
    label: "Customer Not Home (NDR)",
    type: "delivery_attempt_failed",
    desc: "1st delivery attempt failed at address",
    group: "shipping",
    category: "critical",
    icon: Home,
    payload: {
      reason: "Customer not available at destination address",
      carrier: "FedEx Express",
      tracking_number: "FX-99881122",
      attempt_number: 1,
    },
    expectedActions: "Sends 3 reschedule slots, requests 24h FedEx hold, logs audit note",
  },
  {
    label: "No Tracking Update (24h)",
    type: "no_update_for_n_hours",
    desc: "No movement recorded at courier depot",
    group: "shipping",
    category: "critical",
    icon: Clock,
    payload: {
      hours: 24,
      last_location: "Memphis Regional Hub",
    },
    expectedActions: "Pings carrier tracking API, logs operational review note",
  },
  {
    label: "Customer Inquiry",
    type: "customer_message_received",
    desc: "Inbound customer query about status",
    group: "customer",
    category: "critical",
    icon: MessageSquare,
    payload: {
      message: "Hi, when is my package expected to arrive? I need it before Friday.",
    },
    expectedActions: "Reads inquiry and sends status & tracking update to customer",
  },
  {
    label: "Refund Requested",
    type: "refund_requested",
    desc: "Customer requested cancellation / return",
    group: "payments",
    category: "terminal",
    icon: RotateCcw,
    payload: {
      reason: "Customer requested cancellation / return",
    },
    expectedActions: "Halts fulfillment, alerts finance, confirms refund with customer",
  },
  {
    label: "Parcel Delivered",
    type: "delivered",
    desc: "Carrier confirmed delivery (Terminal)",
    group: "shipping",
    category: "terminal",
    icon: CheckCircle,
    payload: {
      signature: "Alex Johnson",
      location: "Front Porch",
    },
    expectedActions: "Sends delivery confirmation, generates post-mortem AI report",
  },
];

export function EventInjector({
  runId,
  events = [],
  status = "RUNNING",
  onEventSent,
}: {
  runId: string;
  events?: DomainEvent[];
  status?: string;
  onEventSent?: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"all" | "shipping" | "payments" | "customer">("all");
  const [loadingType, setLoadingType] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [customMsg, setCustomMsg] = useState("");

  // Domain Lifecycle State Inference
  const eventTypes = new Set(events.map((e) => e.event_type));
  const isPaid = eventTypes.has("payment_confirmed");
  const isPaymentFailed = eventTypes.has("payment_failed");
  const isShipped = eventTypes.has("shipment_created");
  const isDelivered = eventTypes.has("delivered");
  const isRefunded = eventTypes.has("refund_requested");

  const getEventDisabledReason = (preset: EventPreset): string | null => {
    // If order was already refunded or terminated, lock all forward actions
    if (isRefunded && preset.type !== "customer_message_received") {
      return "Order Refunded & Closed";
    }

    if (status === "TERMINATED") {
      return "Workflow Terminated";
    }

    switch (preset.type) {
      case "payment_confirmed":
        if (isPaid) return "Payment Already Captured";
        if (isRefunded) return "Order Refunded";
        return null;

      case "payment_failed":
        if (isPaid) return "Invalid: Payment Already Verified";
        if (isPaymentFailed) return "Payment Issue Already Flagged";
        if (isRefunded) return "Order Refunded";
        return null;

      case "shipment_created":
        if (isShipped) return "Shipment Already Created";
        if (isPaymentFailed && !isPaid) return "Cannot Ship: Payment Declined";
        if (isRefunded) return "Cannot Ship: Order Cancelled";
        return null;

      case "shipment_delayed":
      case "delivery_attempt_failed":
      case "no_update_for_n_hours":
        if (!isShipped) return "Requires Shipment Dispatch First";
        if (isDelivered) return "Parcel Already Delivered";
        if (isRefunded) return "Order Cancelled";
        return null;

      case "delivered":
        if (isDelivered) return "Parcel Already Delivered";
        if (!isShipped) return "Requires Shipment Dispatch First";
        if (isRefunded) return "Order Cancelled";
        return null;

      case "refund_requested":
        if (isRefunded) return "Refund Already Processed";
        return null;

      default:
        return null;
    }
  };

  const triggerRefreshCascade = () => {
    if (!onEventSent) return;
    onEventSent();
    setTimeout(onEventSent, 600);
    setTimeout(onEventSent, 1500);
    setTimeout(onEventSent, 3000);
  };

  const handleInject = async (preset: EventPreset) => {
    const disabledReason = getEventDisabledReason(preset);
    if (disabledReason) return;

    setLoadingType(preset.type);
    setStatusMsg(null);
    try {
      await api.injectEvent(runId, preset.type, preset.payload, "ui_simulator");
      setStatusMsg(`Signal '${preset.label}' injected. Supervisor waking up.`);
      setTimeout(() => setStatusMsg(null), 4000);
      triggerRefreshCascade();
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setLoadingType(null);
    }
  };

  const handleSendCustomMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customMsg.trim()) return;
    setLoadingType("custom_message");
    setStatusMsg(null);
    try {
      await api.injectEvent(
        runId,
        "customer_message_received",
        { message: customMsg.trim() },
        "customer_inbound"
      );
      setStatusMsg("Customer message sent. Supervisor reviewing inquiry.");
      setCustomMsg("");
      setTimeout(() => setStatusMsg(null), 4000);
      triggerRefreshCascade();
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setLoadingType(null);
    }
  };

  const filteredPresets = EVENT_PRESETS.filter((p) => {
    if (activeTab === "all") return true;
    return p.group === activeTab;
  });

  return (
    <div className="p-5 rounded-[16px] bg-[#202020] border border-[#333333] space-y-4">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm text-white tracking-tight">Signal & Event Simulator</h3>
          <span className="text-[10px] px-2 py-0.5 rounded-[4px] bg-[#141414] text-neutral-400 font-mono border border-neutral-700">
            Interactive
          </span>
        </div>
        <p className="text-xs text-[#a0a0a0] mt-0.5">
          Trigger domain signals to test autonomous agent decisions in real-time.
        </p>
      </div>

      {/* Scenario Filter Tabs */}
      <div className="flex gap-1 p-1 rounded-[8px] bg-[#141414] border border-[#2a2a2a]">
        {(
          [
            { id: "all", label: "All" },
            { id: "shipping", label: "Shipping" },
            { id: "payments", label: "Payments" },
            { id: "customer", label: "Customer" },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 text-[11px] py-1 rounded-[6px] font-medium transition-colors cursor-pointer text-center ${
              activeTab === t.id
                ? "bg-[#282828] text-white font-semibold shadow-sm"
                : "text-[#888888] hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Preset Action Grid */}
      <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
        {filteredPresets.map((preset) => {
          const Icon = preset.icon;
          const isLoading = loadingType === preset.type;
          const disabledReason = getEventDisabledReason(preset);
          const isDisabled = disabledReason !== null || loadingType !== null;

          return (
            <button
              key={preset.type}
              type="button"
              disabled={isDisabled}
              onClick={() => handleInject(preset)}
              className={`w-full text-left p-2.5 rounded-[8px] border transition-all space-y-1 ${
                isDisabled
                  ? "opacity-35 bg-[#141414] border-[#222222] cursor-not-allowed"
                  : "bg-[#161616] border-[#2e2e2e] hover:border-[#444444] cursor-pointer"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
                  <span className={`text-xs font-semibold ${isDisabled ? "text-neutral-500" : "text-white"}`}>
                    {preset.label}
                  </span>
                </div>

                {disabledReason ? (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#101010] text-neutral-500 border border-neutral-800 font-mono whitespace-nowrap">
                    {disabledReason}
                  </span>
                ) : (
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded-[4px] uppercase font-mono font-bold tracking-wider ${
                      preset.category === "critical"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : preset.category === "terminal"
                        ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                        : "bg-[#101010] text-[#888888] border border-[#2e2e2e]"
                    }`}
                  >
                    {preset.category}
                  </span>
                )}
              </div>

              <p className="text-[11px] text-[#999999] leading-snug">{preset.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Custom Inbound Message Simulator */}
      <form onSubmit={handleSendCustomMessage} className="pt-2 border-t border-[#2e2e2e] space-y-2">
        <label className="block text-[11px] font-semibold text-white">
          Simulate Inbound Customer Message
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="e.g. Please hold at local depot..."
            value={customMsg}
            onChange={(e) => setCustomMsg(e.target.value)}
            disabled={loadingType !== null}
            className="flex-1 text-xs px-3 py-2 rounded-[6px] bg-[#141414] border border-[#2e2e2e] text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-400 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loadingType !== null || !customMsg.trim()}
            className="px-3 py-2 rounded-[6px] bg-white text-black text-xs font-semibold disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
          >
            <Send className="w-3 h-3" />
            <span>Send</span>
          </button>
        </div>
      </form>

      {statusMsg && (
        <div className="text-[11px] font-medium text-white text-center p-2 rounded-[6px] bg-[#141414] border border-[#2e2e2e]">
          {statusMsg}
        </div>
      )}
    </div>
  );
}
