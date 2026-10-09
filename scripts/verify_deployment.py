"""Wait for a deployed FastAPI API and compiled React app, not Azure's default page."""

import json
import sys
import time
import urllib.error
import urllib.request


def verify(base_url: str, timeout: float = 240) -> None:
    base_url = base_url.rstrip("/")
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(base_url + "/api/health", timeout=15) as response:
                if json.load(response) != {"status": "ok"}:
                    raise ValueError("API health response is not ready")
            with urllib.request.urlopen(base_url + "/", timeout=15) as response:
                html = response.read(1_000_000).decode("utf-8")
            if 'id="root"' not in html or "/assets/" not in html:
                raise ValueError("Compiled React application is not being served")
            print("Live verification passed: FastAPI health and compiled React application are responding.")
            return
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            if time.monotonic() >= deadline:
                raise SystemExit(
                    "The app did not become healthy. Check App Service startup/deployment logs."
                ) from error
            print("Waiting for the application to start...", flush=True)
            time.sleep(10)


if __name__ == "__main__":
    verify(sys.argv[1])
