import os
from pathlib import Path


def get_session_db_path(filename: str) -> Path:
    configured_directory = os.getenv("SESSION_DB_DIR")
    if configured_directory:
        session_directory = Path(configured_directory)
    elif os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        session_directory = Path("/tmp/crypto-trader/sessions")
    else:
        session_directory = Path(__file__).parent.parent / "sessions"

    session_directory.mkdir(parents=True, exist_ok=True)
    database_path = session_directory / filename
    database_path.touch(exist_ok=True)
    return database_path
