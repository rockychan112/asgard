"""Entry point for the packaged desktop extension.

The manifest puts `server/lib` on PYTHONPATH, but a launcher that inherits an
odd environment shouldn't leave the user staring at an ImportError — so the
path goes on explicitly too. Everything past this point is the same code the
CLI runs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from asgard.mcp_server import main  # noqa: E402 — must follow the path insert

if __name__ == "__main__":
    main()
