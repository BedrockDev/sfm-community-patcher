# -*- coding: utf-8 -*-
"""
Diagnostics: collect system info for troubleshooting.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class DiagInfo:
    os_version: str = ""
    python_version: str = ""
    sfm_path: str = ""
    sfm_version: str = ""
    gpu_name: str = ""
    gpu_driver: str = ""
    dxvk_installed: bool = False
    reshade_installed: bool = False
    reshade_version: str = ""
    patches_applied: list[str] = field(default_factory=list)
    engine_dll_size: int = 0
    vstdlib_dll_size: int = 0
    shaderapi_dll_size: int = 0
    backups_exist: bool = False
    reshade_ini_exists: bool = False
    proxy_configured: bool = False
    errors: list[str] = field(default_factory=list)


def _get_gpu_info() -> tuple[str, str]:
    """Get GPU name and driver version via WMI."""
    try:
        import json
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return "Unknown", "Unknown"
        data = json.loads(r.stdout)
        if isinstance(data, list):
            data = data[0]
        return data.get("Name", "Unknown"), data.get("DriverVersion", "Unknown")
    except Exception:
        return "Unknown", "Unknown"


def _get_sfm_version(sfm_path: str) -> str:
    for sub in ["", "bin"]:
        path = os.path.join(sfm_path, sub, "steam.inf")
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        low = line.lower()
                        if "appversion" in low or "version" in low:
                            return line.strip()
            except Exception:
                pass

    engine = os.path.join(sfm_path, "bin", "engine.dll")
    if os.path.isfile(engine):
        return f"engine.dll: {os.path.getsize(engine)} bytes"
    return "Unknown"


def _check_patches(bin_dir: str) -> list[str]:
    applied = []
    engine = os.path.join(bin_dir, "engine.dll")
    if not os.path.isfile(engine):
        return applied

    try:
        with open(engine, "rb") as f:
            data = f.read()
    except Exception:
        return applied

    checks = [
        ("Hunk 2GB", b"\x3D\x00\x00\x00\x80"),
        ("Hunk 256MB", b"\x68\x00\x00\x00\x10\x68\x00\x00\x01\x00\xBE\x00\x00\x00\x10"),
        ("RBTree 31-bit", b"\x81\xE1\xFF\xFF\xFF\x7F"),
        ("FCVAR bypass", b"\xB8\x01\x00\x00\x00\xEB"),
        ("Brushes 16k", b"\x81\xFE\x00\x40\x00\x00\x7E\x0D"),
        ("Planes 128k", b"\x81\xFF\x00\x00\x02\x00\x7E\x0D"),
    ]

    for name, pattern in checks:
        if pattern in data:
            applied.append(name)

    vstdlib = os.path.join(bin_dir, "vstdlib.dll")
    if os.path.isfile(vstdlib):
        try:
            with open(vstdlib, "rb") as f:
                vs_data = f.read()
            if b"\x3B\x57\x08\x90\x90" in vs_data:
                applied.append("KeyValues no cap")
        except Exception:
            pass

    return applied


def collect_diagnostics(game_dir: str = "") -> DiagInfo:
    info = DiagInfo()

    try:
        info.os_version = f"{platform.system()} {platform.release()} ({platform.version()})"
    except Exception:
        info.os_version = "Unknown"

    info.python_version = sys.version.split()[0] if not getattr(sys, "frozen", False) else "bundled"

    if not game_dir:
        try:
            from core.sfm_detector import detect_sfm_game_dir
            game_dir = detect_sfm_game_dir() or ""
        except Exception:
            game_dir = ""

    if game_dir:
        info.sfm_path = game_dir
        try:
            info.sfm_version = _get_sfm_version(game_dir)
        except Exception:
            info.sfm_version = "Unknown"

        bin_dir = os.path.join(game_dir, "bin")

        engine = os.path.join(bin_dir, "engine.dll")
        vstdlib = os.path.join(bin_dir, "vstdlib.dll")
        shaderapi = os.path.join(bin_dir, "shaderapidx9.dll")

        try:
            if os.path.isfile(engine):
                info.engine_dll_size = os.path.getsize(engine)
            if os.path.isfile(vstdlib):
                info.vstdlib_dll_size = os.path.getsize(vstdlib)
            if os.path.isfile(shaderapi):
                info.shaderapi_dll_size = os.path.getsize(shaderapi)
        except Exception:
            pass

        info.dxvk_installed = os.path.isfile(os.path.join(bin_dir, "d3d9_vlk.dll"))
        try:
            reshade_dll = os.path.join(bin_dir, "d3d9.dll")
            info.reshade_installed = (
                os.path.isfile(reshade_dll)
                and os.path.getsize(reshade_dll) > 3_000_000
            )
        except Exception:
            info.reshade_installed = False

        reshade_ini = os.path.join(bin_dir, "ReShade.ini")
        info.reshade_ini_exists = os.path.isfile(reshade_ini)
        if info.reshade_ini_exists:
            try:
                with open(reshade_ini, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                info.proxy_configured = "EnableProxyLibrary=1" in content
            except Exception:
                pass

        info.backups_exist = os.path.isdir(os.path.join(bin_dir, "backups"))
        try:
            info.patches_applied = _check_patches(bin_dir)
        except Exception:
            info.patches_applied = []

        reshade_log = os.path.join(bin_dir, "ReShade.log")
        if os.path.isfile(reshade_log):
            try:
                with open(reshade_log, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if "version" in line.lower() and "reshade" in line.lower():
                            info.reshade_version = line.strip()[:80]
                            break
            except Exception:
                pass
    else:
        info.errors.append("SFM not found")

    try:
        info.gpu_name, info.gpu_driver = _get_gpu_info()
    except Exception:
        info.gpu_name, info.gpu_driver = "Unknown", "Unknown"

    return info


def format_diagnostics(info: DiagInfo) -> str:
    lines = [
        "=== SFM Community Patcher v3.2 ===",
        "",
        f"OS: {info.os_version}",
        f"GPU: {info.gpu_name}",
        f"GPU Driver: {info.gpu_driver}",
        "",
        f"SFM Path: {info.sfm_path or 'Not found'}",
        f"SFM Version: {info.sfm_version}",
        f"engine.dll size: {info.engine_dll_size}",
        f"vstdlib.dll size: {info.vstdlib_dll_size}",
        f"shaderapidx9.dll size: {info.shaderapi_dll_size}",
        "",
        f"DXVK installed: {info.dxvk_installed}",
        f"ReShade installed: {info.reshade_installed}",
        f"ReShade version: {info.reshade_version or 'N/A'}",
        f"ReShade.ini: {info.reshade_ini_exists}",
        f"Proxy configured: {info.proxy_configured}",
        "",
        f"Backups: {info.backups_exist}",
        f"Patches: {', '.join(info.patches_applied) if info.patches_applied else 'None'}",
    ]

    if info.errors:
        lines.append("")
        lines.append("Errors:")
        for err in info.errors:
            lines.append(f"  - {err}")

    return "\n".join(lines)
