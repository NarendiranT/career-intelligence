#!/usr/bin/env python3
"""Start the FastAPI backend and Vue/Vite frontend together."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

BACKEND_CMD = [
    sys.executable,
    "-m",
    "uvicorn",
    "backend.app:app",
    "--reload",
    "--port",
    str(BACKEND_PORT),
]
FRONTEND_CMD = ["npm", "run", "dev"]


def _stream(prefix: str, proc: subprocess.Popen[str]) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(f"{prefix} {line}")
        sys.stdout.flush()


def _stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def main() -> int:
    if not (FRONTEND_DIR / "package.json").exists():
        print("frontend/package.json not found", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    common = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1,
        "env": env,
        "start_new_session": True,
    }

    backend = subprocess.Popen(BACKEND_CMD, cwd=ROOT, **common)
    frontend = subprocess.Popen(FRONTEND_CMD, cwd=FRONTEND_DIR, **common)
    procs = (("backend", backend), ("frontend", frontend))

    for name, proc in procs:
        threading.Thread(
            target=_stream,
            args=(f"[{name}]", proc),
            daemon=True,
        ).start()

    print(f"Backend  http://localhost:{BACKEND_PORT}")
    print(f"Frontend http://localhost:{FRONTEND_PORT}")
    print("Ctrl+C to stop both.\n", flush=True)

    def shutdown(_signum: int | None = None, _frame: object = None) -> None:
        for _, proc in procs:
            _stop(proc)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    exit_code = 0
    try:
        while True:
            for name, proc in procs:
                code = proc.poll()
                if code is not None:
                    if code != 0:
                        print(f"{name} exited with {code}", file=sys.stderr)
                        exit_code = code
                    shutdown()
                    break
            else:
                time.sleep(0.2)
                continue
            break
    except KeyboardInterrupt:
        shutdown()

    for _, proc in procs:
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
