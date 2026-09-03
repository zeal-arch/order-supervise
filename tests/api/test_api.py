import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.app.db.database import create_db_tables
from apps.api.app.main import app


@pytest.fixture(autouse=True)
async def init_db():
    await create_db_tables()


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.get("/health")
        assert res1.status_code == 200
        assert res1.json()["status"] == "healthy"

        res2 = await client.get("/api/health")
        assert res2.status_code == 200
        assert res2.json()["service"] == "order-supervisor-api"


@pytest.mark.asyncio
async def test_supervisor_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_name = f"Test Supervisor {uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Integration test supervisor",
            "base_instruction": "Supervise test orders carefully",
            "available_tools": ["message_customer", "create_internal_note"],
            "default_wake_delay_seconds": 1800,
            "wake_sensitivity": "balanced",
            "model_name": "gpt-4o-mini",
        }

        # 1. Create supervisor (201)
        res_create = await client.post("/api/supervisors", json=payload)
        assert res_create.status_code == 201
        created = res_create.json()
        assert created["name"] == unique_name
        sup_id = created["id"]

        # 2. Duplicate supervisor rejection (400)
        res_dup = await client.post("/api/supervisors", json=payload)
        assert res_dup.status_code == 400

        # 3. List supervisors (200)
        res_list = await client.get("/api/supervisors")
        assert res_list.status_code == 200
        sups = res_list.json()
        assert any(s["id"] == sup_id for s in sups)

        # 4. Get by ID (200)
        res_get = await client.get(f"/api/supervisors/{sup_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == sup_id

        # 5. Delete supervisor (204)
        res_del = await client.delete(f"/api/supervisors/{sup_id}")
        assert res_del.status_code == 204

        # 6. Verify 404 after deletion
        res_not_found = await client.get(f"/api/supervisors/{sup_id}")
        assert res_not_found.status_code == 404


@pytest.mark.asyncio
async def test_run_endpoints_with_mocked_temporal():
    transport = ASGITransport(app=app)
    with patch("apps.api.app.services.temporal.TemporalService.start_order_workflow", new_callable=AsyncMock) as mock_start, \
         patch("apps.api.app.services.temporal.TemporalService.send_event_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_instruction_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_pause_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_resume_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.terminate_workflow", new_callable=AsyncMock):

        mock_start.return_value = "order-supervisor-ORD-API-TEST"

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            order_id = f"ORD-API-{uuid.uuid4().hex[:6]}"
            run_payload = {
                "order_id": order_id,
                "initial_instructions": ["Prioritize speed"],
            }

            # 1. Create run (201)
            res_create = await client.post("/api/runs", json=run_payload)
            assert res_create.status_code == 201
            run_data = res_create.json()
            assert run_data["order_id"] == order_id
            run_id = run_data["id"]

            # Duplicate run creation rejection (400)
            res_dup = await client.post("/api/runs", json=run_payload)
            assert res_dup.status_code == 400

            # 2. List runs (200)
            res_list = await client.get("/api/runs")
            assert res_list.status_code == 200
            assert any(r["id"] == run_id for r in res_list.json())

            # 3. Get run details (200)
            res_get = await client.get(f"/api/runs/{run_id}")
            assert res_get.status_code == 200
            detail = res_get.json()
            assert detail["id"] == run_id
            assert len(detail["events"]) >= 1

            # 4. Inject event (201)
            event_payload = {
                "event_type": "shipment_delayed",
                "payload": {"delay_hours": 24, "carrier": "FedEx"},
                "source": "logistics_carrier",
            }
            res_evt = await client.post(f"/api/runs/{run_id}/events", json=event_payload)
            assert res_evt.status_code == 201
            assert res_evt.json()["event_type"] == "shipment_delayed"

            # 5. Inject instruction (201)
            instr_payload = {
                "instruction": "Do not issue refunds exceeding $50 without approval.",
                "author": "manager_alice",
            }
            res_instr = await client.post(f"/api/runs/{run_id}/instructions", json=instr_payload)
            assert res_instr.status_code == 201
            assert res_instr.json()["instruction"] == instr_payload["instruction"]

            # 6. Pause run (200)
            res_pause = await client.post(f"/api/runs/{run_id}/interrupt")
            assert res_pause.status_code == 200
            assert res_pause.json()["status"] == "PAUSED"

            # 7. Resume run (200)
            res_resume = await client.post(f"/api/runs/{run_id}/resume")
            assert res_resume.status_code == 200
            assert res_resume.json()["status"] == "RUNNING"

            # 8. Terminate run (200)
            res_term = await client.post(f"/api/runs/{run_id}/terminate")
            assert res_term.status_code == 200
            assert res_term.json()["status"] == "TERMINATED"

            # 9. Nonexistent run 404 checks
            res_fake = await client.get("/api/runs/run_nonexistent_99999")
            assert res_fake.status_code == 404
