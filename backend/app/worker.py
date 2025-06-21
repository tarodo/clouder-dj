# This file is the entrypoint for the taskiq worker.
# It imports the broker and all tasks to register them.

from app.broker import broker  # noqa: F401
from app.tasks import *  # noqa: F401, F403
