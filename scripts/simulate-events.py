import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import argparse
import asyncio
import json

import httpx
from rich.console import Console
from rich.table import Table

console = Console()
API_BASE = "http://localhost:8000/api"

EVENT_PRESETS = {
    "1": ("payment_confirmed", {"transaction_id": "tx_live_7721", "method": "credit_card", "amount": 189.97}),
    "2": ("payment_failed", {"reason": "insufficient_funds", "decline_code": "do_not_honor"}),
    "3": ("shipment_created", {"carrier": "FedEx", "tracking_number": "FX-99881122", "service": "Priority Overnight"}),
    "4": ("shipment_delayed", {"carrier": "FedEx", "tracking_number": "FX-99881122", "reason": "Severe winter blizzard at sorting hub", "delay_hours": 48}),
    "5": ("delivered", {"signature": "A. Johnson", "location": "Front Porch"}),
    "6": ("refund_requested", {"reason": "Customer found lower price elsewhere", "requested_by": "customer"}),
    "7": ("customer_message_received", {"message": "Hello, my tracking number has not updated in 2 days. Could you please check?"}),
    "8": ("no_update_for_n_hours", {"elapsed_hours": 24, "status": "stalled_at_customs"}),
}


async def main():
    parser = argparse.ArgumentParser(description="Order Supervisor Event Simulation CLI")
    parser.add_argument("--run-id", type=str, help="Specific run ID or order ID to target")
    parser.add_argument("--event", type=str, help="Event type name")
    parser.add_argument("--payload", type=str, help="JSON payload string")
    parser.add_argument("--instruction", type=str, help="Inject live instruction")
    args = parser.parse_args()

    async with httpx.AsyncClient(base_url=API_BASE, timeout=10.0) as client:
        # Check API health
        try:
            await client.get("/health")
        except Exception:
            console.print("[bold red]❌ Cannot connect to FastAPI backend at http://localhost:8000[/bold red]")
            return

        run_id = args.run_id

        # If no run_id provided, fetch list of active runs
        if not run_id:
            runs_res = await client.get("/runs")
            runs = runs_res.json()
            if not runs:
                console.print("[yellow]No active runs found. Create one first via UI or API.[/yellow]")
                return

            table = Table(title="Active Order Supervisor Runs")
            table.add_column("Run ID", style="cyan")
            table.add_column("Order ID", style="bold green")
            table.add_column("Status", style="magenta")
            table.add_column("Current Summary")

            for r in runs:
                table.add_row(
                    r["id"],
                    r["order_id"],
                    r["status"],
                    (r.get("current_memory", {}) or {}).get("rolling_summary", "")[:60] + "...",
                )
            console.print(table)
            run_id = runs[0]["id"]
            console.print(f"[bold cyan]Auto-selecting latest run: {run_id}[/bold cyan]\n")

        # Instruction injection
        if args.instruction:
            console.print(f"[bold blue]Injecting instruction to run {run_id}:[/bold blue] '{args.instruction}'")
            res = await client.post(f"/runs/{run_id}/instructions", json={"instruction": args.instruction})
            console.print(f"[green][OK] Injected successfully:[/green] {res.json()}")
            return

        # Interactive Event Selection if not passed via flags
        event_type = args.event
        event_payload = {}

        if not event_type:
            console.print("[bold cyan]Select an Event to Inject:[/bold cyan]")
            for key, (name, _) in EVENT_PRESETS.items():
                console.print(f"  [bold yellow]{key}[/bold yellow]. {name}")

            choice = input("\nEnter choice [1-8]: ").strip()
            if choice in EVENT_PRESETS:
                event_type, event_payload = EVENT_PRESETS[choice]
            else:
                event_type = "custom_event"
                event_payload = {"notes": "manual custom event"}
        else:
            if args.payload:
                try:
                    event_payload = json.loads(args.payload)
                except Exception:
                    event_payload = {"raw": args.payload}

        console.print(f"\n[bold yellow]--> Sending Signal '{event_type}' to run {run_id}...[/bold yellow]")
        res = await client.post(
            f"/runs/{run_id}/events",
            json={
                "event_type": event_type,
                "payload": event_payload,
                "source": "cli_simulator",
            },
        )
        if res.status_code in [200, 201]:
            console.print("[bold green][OK] Event successfully signaled into Temporal workflow![/bold green]")
            console.print(json.dumps(res.json(), indent=2))
        else:
            console.print(f"[bold red][ERROR] ({res.status_code}): {res.text}[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
