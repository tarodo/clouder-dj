# This file is the entrypoint for the taskiq worker.
# It imports the broker and all tasks to register them.

from app.core.logging import setup_logging

# Initialize structured logging before importing tasks.
setup_logging()

from app.broker import broker  # noqa: E402,F401
from app.tasks import *  # noqa: E402,F401,F403
