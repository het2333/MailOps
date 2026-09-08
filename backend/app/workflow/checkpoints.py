import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def sqlite_checkpointer(database_url: str) -> SqliteSaver:
    """Create LangGraph's SQLite checkpointer beside the MailOps database."""

    if not database_url.startswith("sqlite:///"):
        raise ValueError("The MailOps MVP supports SQLite checkpoints only")
    raw_path = database_url.removeprefix("sqlite:///")
    path = Path(raw_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    return saver
