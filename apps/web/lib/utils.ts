import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(dateStr?: string | null): string {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return dateStr;
  }
}

export function getStatusBadgeClass(status: string): string {
  switch (status?.toUpperCase()) {
    case "RUNNING":
      return "bg-white text-black border-white";
    case "SLEEPING":
      return "bg-neutral-900 text-neutral-300 border-neutral-700";
    case "PAUSED":
      return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    case "COMPLETED":
      return "bg-neutral-900 text-white border-neutral-600";
    case "TERMINATED":
      return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    default:
      return "bg-neutral-900 text-neutral-400 border-neutral-800";
  }
}
