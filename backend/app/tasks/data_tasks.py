import time
from typing import Any

import structlog
from taskiq import Context, TaskiqDepends

from app.broker import broker
from app.tasks.deps import get_collection_service, get_enrichment_service
from app.tasks.progress import update_task_progress

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

    try:
        await update_task_progress(
            context, start_time, "collecting", {"processed": 0, "failed": 0, "total": 0}
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
                await update_task_progress(
                    context, start_time, "processing", progress_data
                )

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
        await update_task_progress(context, start_time, "failed", final_results)
        return final_results

    if processing_results.get("failed", 0) > 0:
        final_phase = "failed"
    else:
        final_phase = "finished"
    final_results = {"phase": final_phase, **processing_results}

    log.info("Task finished", **final_results)
    await update_task_progress(context, start_time, final_phase, processing_results)
    return final_results


@broker.task(task_name="collection.enrich_spotify_data")
async def enrich_spotify_data_task(
    similarity_threshold: int = 80,
    context: Context = TaskiqDepends(),
) -> dict[str, Any]:
    """
    Finds tracks with ISRC but no Spotify link, searches for them on Spotify,
    and persists the results.
    """
    task_id = context.message.task_id
    log.info("Starting Spotify enrichment task", task_id=task_id)
    start_time = time.perf_counter()

    try:
        async with get_enrichment_service() as enrichment_service:

            async def progress_callback(state: dict[str, Any]) -> None:
                # AC: reported state includes total, processed, found, not_found,
                # and errors.
                await update_task_progress(
                    context,
                    start_time,
                    "enriching",
                    {
                        **state,
                        "errors": 0,
                        "similarity_threshold": similarity_threshold,
                    },
                )

            results = await enrichment_service.enrich_tracks_with_spotify_data(
                progress_callback=progress_callback,
                similarity_threshold=similarity_threshold,
            )

    except Exception as e:
        log.exception("Spotify enrichment task failed", task_id=task_id, error=str(e))
        final_results = {
            "error": str(e),
            "processed": 0,
            "total": -1,
            "found": 0,
            "not_found": 0,
            "errors": 1,
        }
        await update_task_progress(context, start_time, "failed", final_results)
        return {"phase": "failed", **final_results}

    final_phase = "finished"
    final_results = {**results, "errors": 0}

    log.info("Spotify enrichment task finished", **final_results)
    await update_task_progress(context, start_time, final_phase, final_results)
    return {"phase": final_phase, **final_results}


@broker.task(task_name="collection.enrich_spotify_artist_data")
async def enrich_spotify_artist_data_task(
    context: Context = TaskiqDepends(),
) -> dict[str, Any]:
    """
    Finds artists without a Spotify link, matches them using associated track data,
    and persists the results.
    """
    task_id = context.message.task_id
    log.info("Starting Spotify artist enrichment task", task_id=task_id)
    start_time = time.perf_counter()

    try:
        async with get_enrichment_service() as enrichment_service:

            async def progress_callback(state: dict[str, Any]) -> None:
                await update_task_progress(
                    context, start_time, "enriching", {**state, "errors": 0}
                )

            results = await enrichment_service.enrich_artists_with_spotify_data(
                progress_callback=progress_callback
            )

    except Exception as e:
        log.exception(
            "Spotify artist enrichment task failed", task_id=task_id, error=str(e)
        )
        final_results = {
            "error": str(e),
            "processed": 0,
            "total": -1,
            "found": 0,
            "not_found": 0,
            "errors": 1,
        }
        await update_task_progress(context, start_time, "failed", final_results)
        return {"phase": "failed", **final_results}

    final_phase = "finished"
    final_results = {**results, "errors": 0}

    log.info("Spotify artist enrichment task finished", **final_results)
    await update_task_progress(context, start_time, final_phase, final_results)
    return {"phase": final_phase, **final_results}
