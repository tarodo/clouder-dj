import time
from typing import Any

import structlog
from taskiq import Context, TaskiqDepends, TaskiqResult

from app.broker import broker
from app.tasks.deps import get_collection_service

log = structlog.get_logger(__name__)


@broker.task(task_name="collection.collect_bp_tracks")
async def collect_bp_tracks_task(
    bp_token: str,
    style_id: int,
    date_from: str,
    date_to: str,
    context: Context = TaskiqDepends(),
) -> dict[str, Any]:
    """
    Collects and processes Beatport tracks using the CollectionService.

    This task is a thin wrapper that:
    1. Obtains a CollectionService instance with a managed DB session.
    2. Calls the service to collect raw track data from the Beatport API.
    3. Calls the service to process the collected raw data.
    4. Reports progress and final results back to the broker.
    """
    task_id = context.message.task_id
    log.info(
        "Starting Beatport collection task",
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
        task_id=task_id,
    )
    start_time = time.perf_counter()

    async def _update_task_progress(phase: str, progress_data: dict[str, Any]) -> None:
        """Helper to update the task's result in the backend."""
        progress = {"phase": phase, **progress_data}
        elapsed_time = time.perf_counter() - start_time
        await broker.result_backend.set_result(
            task_id,
            TaskiqResult(
                is_err=False,
                execution_time=elapsed_time,
                return_value=progress,
            ),
        )

    try:
        await _update_task_progress(
            "collecting", {"processed": 0, "failed": 0, "total": 0}
        )

        async with get_collection_service() as collection_service:
            # Phase 1: Collect all raw data
            await collection_service.collect_beatport_tracks_raw(
                bp_token=bp_token,
                style_id=style_id,
                date_from=date_from,
                date_to=date_to,
            )

            # Phase 2: Process collected data
            async def batch_progress_callback(progress_data: dict[str, Any]) -> None:
                await _update_task_progress("processing", progress_data)

            processing_results = (
                await collection_service.process_unprocessed_beatport_tracks(
                    batch_progress_callback=batch_progress_callback
                )
            )

    except Exception as e:
        log.exception("Task failed unexpectedly", task_id=task_id, error=str(e))
        final_results = {
            "phase": "failed",
            "error": str(e),
            "processed": 0,
            "failed": 1,
            "total": 0,
        }
        await _update_task_progress("failed", final_results)
        return final_results

    if processing_results.get("failed", 0) > 0:
        final_phase = "failed"
        final_results = {"phase": final_phase, **processing_results}
    else:
        final_phase = "finished"
        final_results = {"phase": final_phase, **processing_results}

    log.info("Task finished", **final_results)
    await _update_task_progress(final_phase, processing_results)
    return final_results
