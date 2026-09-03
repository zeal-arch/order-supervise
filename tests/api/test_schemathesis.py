from unittest.mock import AsyncMock, patch

import pytest
import schemathesis

from apps.api.app.db.database import create_db_tables
from apps.api.app.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app=app)


@pytest.fixture(autouse=True)
async def setup_db():
    await create_db_tables()


@schema.parametrize()
def test_api_no_500_crashes(case: schemathesis.Case):
    """Schemathesis fuzzes all FastAPI endpoints to ensure zero 500 server crashes under random inputs."""
    with patch("apps.api.app.services.temporal.TemporalService.start_order_workflow", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_event_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_instruction_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_pause_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.send_resume_signal", new_callable=AsyncMock), \
         patch("apps.api.app.services.temporal.TemporalService.terminate_workflow", new_callable=AsyncMock):

        response = case.call()
        assert response.status_code < 500, f"Endpoint {case.path} crashed with status {response.status_code}: {response.text}"
