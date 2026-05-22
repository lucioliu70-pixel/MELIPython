from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)

    venv_dir = root / ".venv"
    if not venv_dir.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)])

    py = str(venv_dir / "Scripts" / "python.exe") if os.name == "nt" else str(venv_dir / "bin" / "python")
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", "requirements.txt"])

    # Ensure Playwright browser binaries exist (fixes: Executable doesn't exist ... chrome-headless-shell.exe)
    run([py, "-m", "playwright", "install", "chromium"])

    run([py, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
