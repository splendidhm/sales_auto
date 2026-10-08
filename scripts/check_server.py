"""Start a temporary loopback server, check health, then terminate our process."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


root = Path(__file__).resolve().parents[1]
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
with tempfile.TemporaryDirectory() as directory:
    env = os.environ.copy()
    env["AFFILIATE_HUB_HOME"] = directory
    env["PYTHONUTF8"] = "1"
    with (Path(directory) / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(root / "app.py"),
             "--server.address", "127.0.0.1", "--server.port", str(port),
             "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=root, env=env, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Server exited before becoming healthy")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as response:
                        if response.status == 200:
                            print("PASS: loopback Streamlit health returned HTTP 200")
                            break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.25)
            else:
                raise RuntimeError("Server health timed out")
        finally:
            if os.name == "nt" and process.poll() is None:
                # The venv executable is a redirector on Windows; terminate its own tree.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            elif process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
print("Temporary server stopped; production data untouched.")
