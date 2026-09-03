import Link from "next/link";
import { formatDateTime } from "@/lib/utils";
import { Run } from "@/lib/types";

export function RunCard({ run }: { run: Run }) {
  const isSleeping = run.status === "SLEEPING";

  return (
    <Link href={`/runs/${run.id}`}>
      <div className="p-6 rounded-[12px] bg-[#2A2A2A] h-full flex flex-col justify-between cursor-pointer">
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <h3 className="font-mono text-lg font-medium text-white">{run.order_id}</h3>
            <span
              className={`text-[10px] font-semibold uppercase px-2 py-1 rounded-[6px] ${
                run.status === "RUNNING" || run.status === "SLEEPING"
                  ? "bg-[#2bd97c] text-black"
                  : "bg-[#1a1a1a] text-[#a0a0a0]"
              }`}
            >
              {run.status}
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <div className="text-[10px] text-[#a0a0a0] uppercase font-medium">Customer</div>
              <div className="text-sm text-white font-medium">
                {run.order_context?.customer_name || "Alex Johnson"}
              </div>
            </div>

            <div>
              <div className="text-[10px] text-[#a0a0a0] uppercase font-medium">Order Value</div>
              <div className="text-sm text-white font-medium">
                ${run.order_context?.total_amount?.toFixed(2) || "189.97"}
              </div>
            </div>

            <div>
              <div className="text-[10px] text-[#a0a0a0] uppercase font-medium">Status</div>
              {isSleeping && run.next_wake_at ? (
                <div className="text-sm text-[#2bd97c] font-medium">
                  Waking: {formatDateTime(run.next_wake_at)}
                </div>
              ) : (
                <div className="text-sm text-[#a0a0a0]">Active</div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-[#3a3a3a] text-[10px] text-[#a0a0a0] font-mono truncate">
          {run.workflow_id}
        </div>
      </div>
    </Link>
  );
}
