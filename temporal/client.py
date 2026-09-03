import logging

from temporalio.client import Client

from apps.api.app.config import settings

logger = logging.getLogger(__name__)

TEMPORAL_HOST = settings.TEMPORAL_HOST
TEMPORAL_NAMESPACE = settings.TEMPORAL_NAMESPACE

_client_instance: Client | None = None


async def get_temporal_client() -> Client:
    global _client_instance
    if _client_instance is None:
        try:
            logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}, namespace={TEMPORAL_NAMESPACE}...")
            _client_instance = await Client.connect(
                TEMPORAL_HOST,
                namespace=TEMPORAL_NAMESPACE,
            )
            logger.info("Successfully connected to Temporal server.")
        except Exception as e:
            logger.error(f"Failed to connect to Temporal server at {TEMPORAL_HOST}: {e}")
            raise
    return _client_instance
