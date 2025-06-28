import time
from typing import Any, Dict

from taskiq import Context, TaskiqResult

from app.broker import broker


async def update_task_progress(
    context: Context,
    start_time: float,
    phase: str,
    progress_data: Dict[str, Any],
) -> None:
    """
    Updates the task's result in the backend with current progress.
    """
    progress = {"phase": phase, **progress_data}
    elapsed_time = time.perf_counter() - start_time
    await broker.result_backend.set_result(
        context.message.task_id,
        TaskiqResult(is_err=False, execution_time=elapsed_time, return_value=progress),
    )
