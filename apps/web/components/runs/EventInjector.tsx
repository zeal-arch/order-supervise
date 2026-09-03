"use client";

import { useEffect, useRef, useState } from "react";
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
  Play,
  Pause,
  FastForward,
  Sparkles,
  Wrench,
  Zap,
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

// Complete realistic lifecycle scenario sequence for automated autopilot
const AUTOPLAY_SEQUENCE = [
  "payment_confirmed",
  "shipment_created",
  "shipment_delayed",
  "customer_message_received",
  "delivered",
];

export function EventInjector({
  runId,
  events = [],
  status = "RUNNING",
  initialAutoplay = true, // Autoplay is ON by default for every order
  onEventSent,
}: {
  runId: string;
  events?: DomainEvent[];
  status?: string;
  initialAutoplay?: boolean;
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
  const isTerminal = status === "COMPLETED" || status === "TERMINATED" || isDelivered;

  // Determine the next event in the automated scenario that hasn't fired yet
  const nextAutoplayType = AUTOPLAY_SEQUENCE.find((t) => !eventTypes.has(t)) || null;
  const nextAutoplayPreset = EVENT_PRESETS.find((p) => p.type === nextAutoplayType);

  // Automated Simulation / Autoplay State (default to true if not terminal)
  const [isAutoplayRunning, setIsAutoplayRunning] = useState(
    initialAutoplay && !isTerminal && nextAutoplayPreset !== undefined
  );
  const [autoplayIntervalSeconds, setAutoplayIntervalSeconds] = useState(30);
  const [secondsRemaining, setSecondsRemaining] = useState(30);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const getEventDisabledReason = (preset: EventPreset): string | null => {
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
      case "customer_not_home":
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

  // Autoplay countdown timer tick (auto progresses every 30 seconds)
  useEffect(() => {
    if (!isAutoplayRunning) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    if (!nextAutoplayPreset) {
      setIsAutoplayRunning(false);
      setStatusMsg("Scenario completed. All lifecycle milestones reached!");
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          // Trigger next event
          if (nextAutoplayPreset) {
            handleInject(nextAutoplayPreset);
          }
          return autoplayIntervalSeconds;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isAutoplayRunning, nextAutoplayPreset, autoplayIntervalSeconds]);

  const switchToManualMode = () => {
    setIsAutoplayRunning(false);
    if (timerRef.current) clearInterval(timerRef.current);
    setStatusMsg("Manual Verification Mode activated. Click any button below to trigger events.");
  };

  const resumeAutopilot = () => {
    if (!nextAutoplayPreset) {
      setStatusMsg("Order has already reached its final delivery milestone.");
      return;
    }
    setSecondsRemaining(autoplayIntervalSeconds);
    setIsAutoplayRunning(true);
    setStatusMsg(`Autopilot resumed. Next event in ${autoplayIntervalSeconds}s.`);
  };

  const skipNextAutoplayEvent = () => {
    if (nextAutoplayPreset) {
      handleInject(nextAutoplayPreset);
      setSecondsRemaining(autoplayIntervalSeconds);
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
      {/* Header & Mode Switcher */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-sm text-white tracking-tight">Signal & Event Simulator</h3>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-[4px] font-mono font-bold uppercase tracking-wider ${
                isAutoplayRunning
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "bg-white/10 text-white border border-white/20"
              }`}
            >
              {isAutoplayRunning ? "AUTOPLAY (30s)" : "MANUAL MODE"}
            </span>
          </div>

          {/* Quick Manual / Autoplay Mode Toggle Button */}
          {isAutoplayRunning ? (
            <button
              type="button"
              onClick={switchToManualMode}
              className="px-2.5 py-1 rounded-[6px] bg-[#141414] hover:bg-[#282828] text-white text-xs font-semibold border border-[#3a3a3a] transition-colors cursor-pointer flex items-center gap-1.5 shadow-sm"
              title="Pause automation and switch to manual verification"
            >
              <Wrench className="w-3 h-3 text-amber-400" />
              <span>Manual</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={resumeAutopilot}
              disabled={!nextAutoplayPreset}
              className="px-2.5 py-1 rounded-[6px] bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-semibold border border-amber-500/30 transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
              title="Resume automatic 30s event progression"
            >
              <Zap className="w-3 h-3 text-amber-400" />
              <span>Autoplay (30s)</span>
            </button>
          )}
        </div>
        <p className="text-xs text-[#a0a0a0] mt-0.5">
          {isAutoplayRunning
            ? "Autopilot is advancing the order through all milestone events with a 30s gap."
            : "Manual mode enabled. Trigger events or type custom messages below."}
        </p>
      </div>

      {/* Autopilot Status & Controls Card */}
      <div className="p-3 rounded-[10px] bg-[#161616] border border-[#303030] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
            <span className="text-xs font-semibold text-white">
              {isAutoplayRunning ? "Autopilot Active (Lifecycle Simulation)" : "Autopilot Paused"}
            </span>
          </div>

          {/* Speed interval selector */}
          <div className="flex items-center gap-1 bg-[#101010] p-0.5 rounded border border-[#282828]">
            {([5, 10, 30] as const).map((sec) => (
              <button
                key={sec}
                type="button"
                onClick={() => {
                  setAutoplayIntervalSeconds(sec);
                  if (secondsRemaining > sec) setSecondsRemaining(sec);
                }}
                className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium transition-colors cursor-pointer ${
                  autoplayIntervalSeconds === sec
                    ? "bg-white text-black font-bold"
                    : "text-[#888888] hover:text-white"
                }`}
              >
                {sec}s
              </button>
            ))}
          </div>
        </div>

        {nextAutoplayPreset ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] text-[#a0a0a0]">
              <span>
                Next Event: <strong className="text-white">{nextAutoplayPreset.label}</strong>
              </span>
              {isAutoplayRunning ? (
                <span className="font-mono text-amber-400 font-bold">
                  {secondsRemaining}s remaining
                </span>
              ) : (
                <span className="text-neutral-500 font-mono">Paused (Manual Mode)</span>
              )}
            </div>

            {/* Progress Bar */}
            {isAutoplayRunning && (
              <div className="w-full h-1 bg-[#222222] rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-400 transition-all duration-1000 ease-linear"
                  style={{
                    width: `${((autoplayIntervalSeconds - secondsRemaining) / autoplayIntervalSeconds) * 100}%`,
                  }}
                />
              </div>
            )}

            {/* Controls */}
            <div className="flex gap-1.5 pt-0.5">
              {isAutoplayRunning ? (
                <button
                  type="button"
                  onClick={switchToManualMode}
                  className="flex-1 py-1.5 px-3 rounded-[6px] text-xs font-semibold bg-white text-black hover:bg-neutral-200 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <Wrench className="w-3 h-3" />
                  <span>Manual Verification</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={resumeAutopilot}
                  className="flex-1 py-1.5 px-3 rounded-[6px] text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>Resume Autopilot ({autoplayIntervalSeconds}s)</span>
                </button>
              )}

              <button
                type="button"
                onClick={skipNextAutoplayEvent}
                disabled={loadingType !== null}
                title="Trigger next milestone immediately"
                className="py-1.5 px-2.5 rounded-[6px] bg-[#222222] hover:bg-[#303030] text-neutral-300 text-xs font-semibold border border-[#333333] transition-colors cursor-pointer flex items-center gap-1 disabled:opacity-40"
              >
                <FastForward className="w-3 h-3" />
                <span>Skip</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="text-[11px] text-neutral-400 flex items-center gap-1.5 py-1">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>All 5 scenario milestones completed (Delivered).</span>
          </div>
        )}
      </div>

      {/* Manual Verification Section (Tabs & Individual Event Buttons) */}
      <div className="space-y-3 pt-1 border-t border-[#2a2a2a]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-white">Manual Event Injection</span>
          <span className="text-[10px] text-neutral-400 font-mono">Interactive</span>
        </div>

        {/* Filter Tabs */}
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
        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
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
                onClick={() => {
                  switchToManualMode(); // auto switch to manual when user clicks single event
                  handleInject(preset);
                }}
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
      </div>

      {statusMsg && (
        <div className="text-[11px] font-medium text-white text-center p-2 rounded-[6px] bg-[#141414] border border-[#2e2e2e]">
          {statusMsg}
        </div>
      )}
    </div>
  );
}
