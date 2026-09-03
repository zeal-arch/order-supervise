"use client";

import { useState } from "react";
import { Check, Mail, Truck, Boxes, CreditCard, FileText, Zap, Shield, Crown, Cpu, Clock } from "lucide-react";
import { api } from "@/lib/api";

const PRESETS = [
  {
    name: "VIP Express Supervisor",
    desc: "Aggressive wake-up for high-value orders. Escalates delays immediately.",
    instruction: "Prioritize speed over cost. Proactively notify customer on any carrier delay and escalate directly to senior logistics leads.",
    sensitivity: "aggressive" as const,
    model: "gpt-4o",
    sleepSeconds: 1800,
    tools: [
      "message_fulfillment_team",
      "message_payments_team",
      "message_logistics_team",
      "message_customer",
      "create_internal_note",
    ],
    icon: Crown,
  },
  {
    name: "Standard Retail Guardian",
    desc: "Balanced monitoring for routine e-commerce orders.",
    instruction: "Supervise order from payment to delivery. Handle carrier exceptions gracefully and maintain concise rolling memory.",
    sensitivity: "balanced" as const,
    model: "gpt-4o-mini",
    sleepSeconds: 3600,
    tools: [
      "message_fulfillment_team",
      "message_payments_team",
      "message_logistics_team",
      "message_customer",
      "create_internal_note",
    ],
    icon: Shield,
  },
  {
    name: "Cost-Efficient Logistics",
    desc: "Conservative wake policy to minimize compute and API token usage.",
    instruction: "Only intervene on confirmed carrier bottlenecks or customer direct inquiries. Avoid unnecessary notifications.",
    sensitivity: "conservative" as const,
    model: "gpt-4o-mini",
    sleepSeconds: 7200,
    tools: ["message_logistics_team", "message_customer", "create_internal_note"],
    icon: Zap,
  },
];

const TOOLS = [
  { id: "message_fulfillment_team", label: "Warehouse Alerts", icon: Boxes, desc: "Notify packing & dispatch staff" },
  { id: "message_customer", label: "Customer Email", icon: Mail, desc: "Send status updates to customer" },
  { id: "message_logistics_team", label: "Carrier Escalation", icon: Truck, desc: "Open tickets with FedEx / UPS" },
  { id: "message_payments_team", label: "Payment Verification", icon: CreditCard, desc: "Flag billing & refund issues" },
  { id: "create_internal_note", label: "Internal Audit Log", icon: FileText, desc: "Record operational notes" },
];

import { Supervisor } from "@/lib/types";

export function SupervisorForm({
  onCreated,
  existingSupervisors = [],
}: {
  onCreated?: () => void;
  existingSupervisors?: Supervisor[];
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [baseInstruction, setBaseInstruction] = useState(
    "Supervise order lifecycle autonomously. Proactively escalate courier delays, notify customers, and maintain compact rolling memory."
  );
  const [selectedTools, setSelectedTools] = useState<string[]>([
    "message_fulfillment_team",
    "message_payments_team",
    "message_logistics_team",
    "message_customer",
    "create_internal_note",
  ]);
  const [sensitivity, setSensitivity] = useState<"conservative" | "balanced" | "aggressive">("balanced");
  const [modelName, setModelName] = useState("gpt-4o-mini");
  const [defaultWakeDelay, setDefaultWakeDelay] = useState(3600);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const isDuplicate = existingSupervisors.some(
    (s) => s.name.trim().toLowerCase() === name.trim().toLowerCase()
  );

  const applyPreset = (preset: (typeof PRESETS)[0]) => {
    setName(preset.name);
    setDescription(preset.desc);
    setBaseInstruction(preset.instruction);
    setSensitivity(preset.sensitivity);
    setModelName(preset.model);
    setDefaultWakeDelay(preset.sleepSeconds);
    setSelectedTools([...preset.tools]);
  };

  const handleSensitivityChange = (mode: "conservative" | "balanced" | "aggressive") => {
    setSensitivity(mode);
    // Harmonize default wake interval with sensitivity mode to prevent contradictory settings
    if (mode === "aggressive") {
      setDefaultWakeDelay(1800);
    } else if (mode === "conservative") {
      setDefaultWakeDelay(7200);
    } else {
      setDefaultWakeDelay(3600);
    }
  };

  const toggleTool = (id: string) => {
    setSelectedTools((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setMsg(null);
    try {
      await api.createSupervisor({
        name: name.trim(),
        description: description.trim() || "Custom AI Order Supervisor",
        base_instruction: baseInstruction.trim(),
        available_tools: selectedTools,
        default_wake_delay_seconds: Number(defaultWakeDelay),
        wake_sensitivity: sensitivity,
        model_name: modelName,
      });
      setMsg("✓ Supervisor profile saved successfully!");
      setName("");
      setDescription("");
      if (onCreated) onCreated();
    } catch (err: any) {
      setMsg(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 rounded-[16px] bg-[#202020] border border-[#333333] space-y-6">
      <div>
        <h2 className="font-semibold text-lg text-white">Configure Supervisor Profile</h2>
        <p className="text-xs text-[#a0a0a0] mt-1">
          Define agent operating directives, available tool permissions, model choice, and wake sensitivity.
        </p>
      </div>

      {/* Starter Presets */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#888888] block">
          STARTER PRESETS (CLICK TO LOAD)
        </span>
        <div className="grid grid-cols-1 gap-2">
          {PRESETS.map((preset) => {
            const Icon = preset.icon;
            const isMatch = name === preset.name && sensitivity === preset.sensitivity;
            return (
              <button
                key={preset.name}
                type="button"
                onClick={() => applyPreset(preset)}
                className={`p-3 rounded-[8px] text-left transition-all flex items-center justify-between cursor-pointer border ${
                  isMatch
                    ? "bg-[#181818] border-white text-white shadow-sm"
                    : "bg-[#161616] border-[#2e2e2e] hover:border-[#444444] text-[#d0d0d0]"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-neutral-300" />
                  <div>
                    <div className="text-xs font-semibold text-white">{preset.name}</div>
                    <div className="text-[10px] text-[#888888] line-clamp-1">{preset.desc}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded bg-[#101010] text-neutral-300 border border-[#2e2e2e] font-mono capitalize">
                    {preset.sensitivity}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#101010] text-[#888888] font-mono">
                    {preset.tools.length} tools
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Name and Directives */}
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-[11px] font-semibold text-white">Supervisor Profile Name</label>
            {isDuplicate && (
              <span className="text-[10px] text-amber-400 font-mono font-medium">
                ⚠️ A profile named &quot;{name.trim()}&quot; already exists
              </span>
            )}
          </div>
          <input
            type="text"
            required
            placeholder="e.g. VIP High-Priority Supervisor"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={`w-full text-xs px-3.5 py-2.5 rounded-[8px] bg-[#141414] border text-white placeholder-neutral-500 focus:outline-none ${
              isDuplicate
                ? "border-amber-500/50 focus:border-amber-400"
                : "border-[#2e2e2e] focus:border-neutral-400"
            }`}
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-white mb-1">Base Operating Directives</label>
          <textarea
            rows={3}
            value={baseInstruction}
            onChange={(e) => setBaseInstruction(e.target.value)}
            className="w-full text-xs p-3 rounded-[8px] bg-[#141414] border border-[#2e2e2e] text-white focus:outline-none focus:border-neutral-400 leading-relaxed"
          />
        </div>
      </div>

      {/* Model Choice & Default Wake Interval */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Cpu className="w-3.5 h-3.5 text-neutral-400" />
            <label className="text-[11px] font-semibold text-white">LLM Model Choice</label>
          </div>
          <select
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            className="w-full text-xs px-3 py-2.5 rounded-[8px] bg-[#141414] border border-[#2e2e2e] text-white focus:outline-none focus:border-neutral-400 cursor-pointer font-mono"
          >
            <option value="gpt-4o-mini">gpt-4o-mini (Fast & Cost-Efficient)</option>
            <option value="gpt-4o">gpt-4o (High-Precision Reasoning)</option>
            <option value="claude-3-5-sonnet">claude-3-5-sonnet (Extended Context)</option>
            <option value="llama-3-70b">llama-3-70b (Self-Hosted)</option>
          </select>
        </div>

        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Clock className="w-3.5 h-3.5 text-neutral-400" />
            <label className="text-[11px] font-semibold text-white">Default Wake Interval</label>
          </div>
          <select
            value={defaultWakeDelay}
            onChange={(e) => setDefaultWakeDelay(Number(e.target.value))}
            className="w-full text-xs px-3 py-2.5 rounded-[8px] bg-[#141414] border border-[#2e2e2e] text-white focus:outline-none focus:border-neutral-400 cursor-pointer font-mono"
          >
            <option value={900}>900s (15 minutes)</option>
            <option value={1800}>1800s (30 minutes - Fast)</option>
            <option value={3600}>3600s (1 hour - Balanced)</option>
            <option value={7200}>7200s (2 hours - Conservative)</option>
            <option value={14400}>14400s (4 hours - Low Token)</option>
          </select>
        </div>
      </div>

      {/* Wake Sensitivity */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-semibold text-white">Wake Sensitivity (Event Classifier)</label>
          <span className="text-[10px] text-[#888888]">Harmonizes sleep & wake threshold</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {(["conservative", "balanced", "aggressive"] as const).map((mode) => {
            const isActive = sensitivity === mode;
            return (
              <button
                key={mode}
                type="button"
                onClick={() => handleSensitivityChange(mode)}
                className={`py-2 px-3 rounded-[8px] text-xs font-semibold capitalize transition-all cursor-pointer border ${
                  isActive
                    ? "bg-white text-black border-white"
                    : "bg-[#141414] border-[#2e2e2e] text-[#888888] hover:text-white hover:border-[#444444]"
                }`}
              >
                {mode}
              </button>
            );
          })}
        </div>
        <p className="text-[10px] text-[#888888]">
          {sensitivity === "aggressive" && "• Aggressive (1800s sleep): Wakes on every tracking scan, carrier ping, and customer signal."}
          {sensitivity === "balanced" && "• Balanced (3600s sleep): Wakes on critical exceptions, payment issues, delays, and NDRs."}
          {sensitivity === "conservative" && "• Conservative (7200s sleep): Only wakes on major boundary milestones (Created / Delivered)."}
        </p>
      </div>

      {/* Enabled Tools Checklist */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-semibold text-white">Enabled Business Tools</label>
          <span className="text-[10px] text-white font-mono">{selectedTools.length} active</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {TOOLS.map((t) => {
            const Icon = t.icon;
            const checked = selectedTools.includes(t.id);
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleTool(t.id)}
                className={`p-3 rounded-[8px] flex items-start gap-2.5 text-left transition-all cursor-pointer border ${
                  checked
                    ? "bg-[#181818] border-white/50 text-white"
                    : "bg-[#141414] border-[#2e2e2e] text-[#777777] opacity-60"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded mt-0.5 flex items-center justify-center border transition-all ${
                    checked ? "bg-white border-white text-black" : "border-[#444444]"
                  }`}
                >
                  {checked && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 text-xs font-semibold">
                    <Icon className="w-3.5 h-3.5" />
                    <span>{t.label}</span>
                  </div>
                  <p className="text-[10px] text-[#888888] mt-0.5">{t.desc}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {msg && (
        <div className="p-3 rounded-[8px] bg-[#141414] text-xs font-medium text-white text-center border border-[#333333]">
          {msg}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !name.trim() || isDuplicate}
        className="w-full py-3 rounded-[8px] bg-white text-black font-semibold text-xs transition-colors hover:bg-neutral-200 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
      >
        {loading
          ? "Saving Profile..."
          : isDuplicate
          ? "Profile Name Already Exists"
          : "Save Supervisor Profile"}
      </button>
    </form>
  );
}
