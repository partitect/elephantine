import os
import subprocess
from pathlib import Path
from typing import Optional

def detect_project_workspace(start_path: Optional[str] = None) -> str:
    """
    Automatically detects the current project/workspace identity.
    Resolution priority:
    1. ELEPHANTINE_PROJECT / ELEPHANTINE_WORKSPACE env vars
    2. Git root directory name or remote origin repo name
    3. Current working directory folder name
    4. Fallback: default
    """
    env_proj = os.getenv("ELEPHANTINE_PROJECT") or os.getenv("ELEPHANTINE_WORKSPACE")
    if env_proj and env_proj.strip():
        return env_proj.strip()

    cwd = Path(start_path or os.getcwd()).resolve()

    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        if git_root:
            return Path(git_root).name
    except Exception:
        pass

    if cwd.name and cwd.name not in ("", "/", "\\"):
        return cwd.name

    return "default"
