from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

import requests


def find_chromium_binary(candidates: list[str]) -> str:
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError(
        "Could not find Chromium. Tried: " + ", ".join(candidates)
    )


def render_dom_chromium(
    url: str,
    timeout_ms: int,
    chromium_binaries: list[str],
    user_agent: str = "Mozilla/5.0",
) -> str:
    binary = find_chromium_binary(chromium_binaries)
    with tempfile.TemporaryDirectory(prefix="technomarket_chromium_") as user_data_dir:
        cmd = [
            binary,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-first-run",
            f"--user-data-dir={user_data_dir}",
            f"--virtual-time-budget={timeout_ms}",
            "--dump-dom",
            url,
        ]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    return result.stdout


def render_dom(
    url: str,
    timeout_ms: int,
    chromium_binaries: list[str],
    user_agent: str = "Mozilla/5.0",
) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": user_agent},
            timeout=max(timeout_ms / 1000, 5),
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return render_dom_chromium(url, timeout_ms, chromium_binaries, user_agent)
