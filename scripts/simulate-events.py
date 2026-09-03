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
from rich.panel import Panel
from rich.table import Table

console = Console()
API_BASE = "http://localhost:8000/api"

EVENT_PRESETS = {
    "1": ("payment_confirmed", {"transaction_id": "tx_live_7721", "method": "credit_card", "amount": 189.97}),
    "2": ("payment_failed", {"reason": "insufficient_funds", "decline_code": "do_not_honor"}),
    "3": ("shipment_created", {"carrier": "FedEx Express", "tracking_number": "FX-99881122", "service": "Priority Overnight"}),
    "4": ("shipment_delayed", {"carrier": "FedEx Express", "tracking_number": "FX-99881122", "reason": "Severe winter blizzard at sorting hub", "delay_hours": 48}),
    "5": ("delivery_attempt_failed", {"carrier": "FedEx Express", "tracking_number": "FX-99881122", "reason": "Customer not available at destination address", "attempt_number": 1}),
    "6": ("customer_message_received", {"message": "Hello, when is my package expected to arrive? I need it before Friday."}),
    "7": ("no_update_for_n_hours", {"hours": 24, "last_location": "Memphis Regional Hub"}),
    "8": ("refund_requested", {"reason": "Customer requested cancellation / return", "requested_by": "customer"}),
    "9": ("delivered", {"signature": "A. Johnson", "location": "Front Porch"}),
}

AUTOMATED_SCENARIO = [
    ("payment_confirmed", {"transaction_id": "tx_live_7721", "method": "credit_card", "amount": 189.97}, "Payment Verified & Captured"),
    ("shipment_created", {"carrier": "FedEx Express", "tracking_number": "FX-99881122"}, "Shipment Dispatched with Tracking"),
    ("shipment_delayed", {"carrier": "FedEx Express", "tracking_number": "FX-99881122", "reason": "Severe winter blizzard at sorting hub", "delay_hours": 48}, "Carrier Hub Delay Alert (48h Blizzard)"),
    ("customer_message_received", {"message": "Hi, when is my package expected to arrive? I need it before Friday."}, "Inbound Customer Status Inquiry"),
    ("delivered", {"signature": "Alex Johnson", "location": "Front Porch"}, "Final Delivery Confirmed & Post-Mortem Generated"),
]


async def run_automated_simulation(client: httpx.AsyncClient, run_id: str, interval: int):
    console.print(Panel.fit(
        f"[bold cyan]Starting Automated Order Lifecycle Simulation[/bold cyan]\n"
        f"Target Run: [bold white]{run_id}[/bold white] | Event Interval: [bold yellow]{interval}s gap[/bold yellow]\n"
        f"Sequence: Payment -> Dispatch -> Carrier Delay -> Customer Inquiry -> Delivered",
        border_style="cyan"
    ))

    for idx, (event_type, payload, desc) in enumerate(AUTOMATED_SCENARIO, 1):
        console.print(f"\n[bold yellow]─── Step {idx}/{len(AUTOMATED_SCENARIO)}: Injecting '{event_type}' ───[/bold yellow]")
        console.print(f"  [dim]{desc}[/dim]")
        console.print(f"  Payload: {json.dumps(payload)}")

        try:
            res = await client.post(
                f"/runs/{run_id}/events",
                json={
                    "event_type": event_type,
                    "payload": payload,
                    "source": "cli_autopilot",
                },
            )
            if res.status_code in [200, 201]:
                console.print("  [bold green][OK] Signal delivered to Temporal workflow.[/bold green]")
            else:
                console.print(f"  [bold red][!] HTTP {res.status_code}: {res.text}[/bold red]")
        except Exception as e:
            console.print(f"  [bold red][!] Failed to send event: {e}[/bold red]")

        # Wait a moment for agent processing and fetch activity
        await asyncio.sleep(2)
        try:
            run_data = (await client.get(f"/runs/{run_id}")).json()
            activities = run_data.get("activities", [])
            if activities:
                latest_act = activities[-1]
                console.print("  [bold cyan]🤖 AI Agent Reaction:[/bold cyan]")
                console.print(f"     Reasoning: [italic]{latest_act.get('reasoning')}[/italic]")
                for a in latest_act.get("result", {}).get("actions_executed", []):
                    console.print(f"     Tool Called: [bold green]{a.get('tool')}[/bold green] -> {a.get('summary')}")
        except Exception:
            pass

        # Countdown to next event if not final
        if idx < len(AUTOMATED_SCENARIO):
            console.print(f"\n[bold magenta]⏳ Waiting {interval} seconds before next event (Agent dormant/sleeping in zero-cost state)...[/bold magenta]")
            for remaining in range(interval, 0, -1):
                sys.stdout.write(f"\r   Next event in {remaining}s... (Press Ctrl+C to stop) ")
                sys.stdout.flush()
                await asyncio.sleep(1)
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()

    console.print("\n[bold green]✅ Full Order Lifecycle Automated Simulation Completed Successfully![/bold green]\n")


async def main():
    parser = argparse.ArgumentParser(description="Order Supervisor Event Simulation CLI (Manual & Automated)")
    parser.add_argument("--run-id", type=str, help="Specific run ID or order ID to target")
    parser.add_argument("--auto", action="store_true", help="Run automated full lifecycle simulation with intervals")
    parser.add_argument("--interval", type=int, default=30, help="Delay in seconds between automated events (default: 30)")
    parser.add_argument("--event", type=str, help="Event type name for single injection")
    parser.add_argument("--payload", type=str, help="JSON payload string")
    parser.add_argument("--instruction", type=str, help="Inject live instruction")
    args = parser.parse_args()

    async with httpx.AsyncClient(base_url=API_BASE, timeout=15.0) as client:
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

        # Automated Simulation Mode
        if args.auto:
            await run_automated_simulation(client, run_id, args.interval)
            return

        # Instruction injection
        if args.instruction:
            console.print(f"[bold blue]Injecting instruction to run {run_id}:[/bold blue] '{args.instruction}'")
            res = await client.post(f"/runs/{run_id}/instructions", json={"instruction": args.instruction})
            console.print(f"[green][OK] Injected successfully:[/green] {res.json()}")
            return

        # Manual Interactive Event Selection
        event_type = args.event
        event_payload = {}

        if not event_type:
            console.print("[bold cyan]Select Simulation Mode:[/bold cyan]")
            console.print("  [bold magenta]A[/bold magenta]. [bold]Auto-Play Full Lifecycle (30s gaps between all events)[/bold]")
            console.print("  [bold yellow]1-9[/bold yellow]. [bold]Inject Single Event Manually[/bold]")
            for key, (name, _) in EVENT_PRESETS.items():
                console.print(f"      {key}. {name}")

            choice = input("\nEnter choice [A or 1-9]: ").strip()
            if choice.upper() == "A":
                await run_automated_simulation(client, run_id, args.interval)
                return
            elif choice in EVENT_PRESETS:
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Simulation cancelled by user.[/yellow]")
