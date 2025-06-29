from __future__ import annotations

import functools
from typing import Any, Callable, Coroutine, TypeVar

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def transactional(func: F) -> F:
    """
    Decorator to wrap a service method in a database transaction.

    It assumes the decorated function is a method of a class where the first
    argument is `self`, and `self` has a `db` attribute of type `AsyncSession`.
    It automatically handles commit on success and rollback on any exception.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(self, "db") or not isinstance(self.db, AsyncSession):
            raise TypeError(
                "Transactional decorator requires the instance to have a 'db' "
                "attribute of type AsyncSession."
            )

        db_session: AsyncSession = self.db

        try:
            result = await func(self, *args, **kwargs)
            await db_session.commit()
            log.debug("Transaction committed", function=func.__name__)
            return result
        except Exception as e:
            log.error(
                "Transaction failed, rolling back", function=func.__name__, exc_info=e
            )
            await db_session.rollback()
            raise

    return wrapper  # type: ignore
