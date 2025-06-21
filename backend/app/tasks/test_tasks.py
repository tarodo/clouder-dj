import structlog

from app.broker import broker

log = structlog.get_logger(__name__)


@broker.task
async def collect_beatport_charts_task(
    bp_token: str, style_id: int, date_from: str, date_to: str
) -> dict[str, str]:
    """A stub task to collect music from beatport."""
    log.info(
        "Beatport collection task running!",
        bp_token=bp_token,
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
    )
    return {"status": "ok", "message": "Task started"}
