# -*- coding: utf-8 -*-
"""
Headless ReShade installer for SFM.

ReShade_Setup.exe supports CLI flags for silent installation.
"""

from __future__ import annotations

import os
import subprocess
from typing import Callable, Optional


def install_reshade(
    setup_path: str,
    target_exe: str,
    api: str = "d3d9",
    log_cb: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    Run ReShade setup silently.

    Args:
        setup_path: Path to ReShade_Setup_*.exe
        target_exe: Full path to game executable (dmxedit.exe)
        api: Graphics API (d3d9, d3d10, d3d11, d3d12, opengl32, vulkan)
        log_cb: Optional callback for log messages

    Returns:
        True if installation succeeded.
    """
    if not os.path.isfile(setup_path):
        raise FileNotFoundError(f"ReShade setup not found: {setup_path}")

    if not os.path.isfile(target_exe):
        raise FileNotFoundError(f"Target executable not found: {target_exe}")

    cmd = [
        setup_path,
        "--silent",
        "--install", target_exe,
        f"--{api}",
    ]

    if log_cb:
        log_cb(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if log_cb:
        if result.stdout.strip():
            log_cb(f"stdout: {result.stdout.strip()}")
        if result.stderr.strip():
            log_cb(f"stderr: {result.stderr.strip()}")

    return result.returncode == 0
