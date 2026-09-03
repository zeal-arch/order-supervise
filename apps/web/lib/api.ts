import { Run, Supervisor, DomainEvent, EventType } from "./types";

const isBrowser = typeof window !== "undefined";
const defaultHost = isBrowser ? window.location.hostname : "localhost";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || `http://${defaultHost}:8000/api`;

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`API error (${res.status}): ${errText}`);
  }

  if (res.status === 204) {
    return {} as T;
  }

  const text = await res.text();
  return text ? JSON.parse(text) : ({} as T);
}

export const api = {
  // Supervisors
  getSupervisors: () => fetchJson<Supervisor[]>("/supervisors"),
  createSupervisor: (data: Partial<Supervisor>) =>
    fetchJson<Supervisor>("/supervisors", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteSupervisor: (supervisorId: string) =>
    fetchJson<void>(`/supervisors/${supervisorId}`, {
      method: "DELETE",
    }),

  // Runs
  getRuns: () => fetchJson<Run[]>("/runs"),
  getRun: (runId: string) => fetchJson<Run>(`/runs/${runId}`),
  createRun: (data: { order_id: string; supervisor_id?: string }) =>
    fetchJson<Run>("/runs", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Events & Signals
  injectEvent: (runId: string, event_type: EventType | string, payload: any, source = "ui_simulator") =>
    fetchJson<DomainEvent>(`/runs/${runId}/events`, {
      method: "POST",
      body: JSON.stringify({ event_type, payload, source }),
    }),

  // Dynamic Instructions
  injectInstruction: (runId: string, instruction: string, author = "ui_operator") =>
    fetchJson<{ instruction: string; author: string; timestamp: string }>(
      `/runs/${runId}/instructions`,
      {
        method: "POST",
        body: JSON.stringify({ instruction, author }),
      }
    ),

  // Lifecycle Controls
  interruptRun: (runId: string) => fetchJson<Run>(`/runs/${runId}/interrupt`, { method: "POST" }),
  resumeRun: (runId: string) => fetchJson<Run>(`/runs/${runId}/resume`, { method: "POST" }),
  terminateRun: (runId: string) => fetchJson<Run>(`/runs/${runId}/terminate`, { method: "POST" }),
};
