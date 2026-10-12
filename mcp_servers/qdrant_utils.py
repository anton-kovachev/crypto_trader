import socket
import subprocess
import time
from pathlib import Path
from datetime import datetime


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def ensure_qdrant_docker(project_dir: str):
    """Ensure a Qdrant Docker container is running and listening on localhost:6333.

    Attempts to start a container named `qdrant_local` if the port is not open.
    """
    qdrant_port = 6333
    if is_port_open("127.0.0.1", qdrant_port):
        print("Qdrant appears to be running on localhost:6333")
        return

    print(
        "Qdrant not found on localhost:6333 — attempting to start Docker container 'qdrant_local'"
    )
    data_dir = Path(project_dir) / "memory" / "qdrant"
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "docker",
                "start",
                "qdrant_local",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "qdrant_local",
                "-p",
                "6333:6333",
                "-v",
                f"{data_dir.resolve()}:/qdrant/storage",
                "qdrant/qdrant:latest",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(20):
            if is_port_open("127.0.0.1", qdrant_port):
                print("Qdrant Docker container is now available at localhost:6333")
                return
            time.sleep(0.5)

        print("Warning: attempted to start Qdrant Docker but port 6333 is still closed")
    except FileNotFoundError:
        print(
            "Docker not available; please start a Qdrant server manually on localhost:6333"
        )
