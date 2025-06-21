import structlog

from app.broker import broker

log = structlog.get_logger(__name__)


@broker.task
async def hello_world_task(message: str) -> dict[str, str]:
    """A simple task that logs a message."""
    log.info("Hello world task running!", message=message)
    return {"status": "ok", "message": message}
