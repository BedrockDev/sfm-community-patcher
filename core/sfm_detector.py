# -*- coding: utf-8 -*-
"""
Auto-detection of Source Filmmaker installation path.

Searches Steam library folders for SourceFilmmaker/game/bin/engine.dll.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional


STEAM_DEFAULT_PATHS = [
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Steam",
    r"D:\Steam",
    r"D:\SteamLibrary",
    r"E:\SteamLibrary",
    r"F:\SteamLibrary",
    r"C:\Games\Steam",
]

GAME_SUBPATH = os.path.join("steamapps", "common", "SourceFilmmaker", "game")
ENGINE_DLL = os.path.join("bin", "engine.dll")


def _parse_libraryfolders(vdf_path: str) -> list[str]:
    """Parse Steam libraryfolders.vdf to get all library paths."""
    paths: list[str] = []
    try:
        with open(vdf_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return paths

    for match in re.finditer(r'"path"\s+"([^"]+)"', content):
        p = match.group(1).replace("\\\\", "\\").replace("/", "\\")
        paths.append(p)

    return paths


def find_steam_libraries() -> list[str]:
    """Find all Steam library root folders."""
    libraries: list[str] = []

    for steam_path in STEAM_DEFAULT_PATHS:
        if os.path.isdir(steam_path):
            libraries.append(steam_path)
            vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.isfile(vdf):
                for lib_path in _parse_libraryfolders(vdf):
                    if lib_path not in libraries:
                        libraries.append(lib_path)

    seen = set()
    unique = []
    for lib in libraries:
        real = os.path.realpath(lib)
        if real not in seen:
            seen.add(real)
            unique.append(lib)

    return unique


def detect_sfm_game_dir() -> Optional[str]:
    """Find SFM game directory by searching Steam libraries. Returns game dir or None."""
    for lib in find_steam_libraries():
        game_dir = os.path.join(lib, GAME_SUBPATH)
        engine = os.path.join(game_dir, ENGINE_DLL)
        if os.path.isfile(engine):
            return game_dir
    return None


def validate_game_dir(path: str) -> tuple[bool, str]:
    """Validate that a path is a valid SFM game directory."""
    if not os.path.isdir(path):
        return False, f"Directory not found: {path}"

    engine = os.path.join(path, "bin", "engine.dll")
    if not os.path.isfile(engine):
        return False, "bin\\engine.dll not found — not a valid SFM game directory"

    has_sfm = os.path.isfile(os.path.join(path, "sfm.exe"))
    has_dmxedit = os.path.isfile(os.path.join(path, "bin", "dmxedit.exe"))

    if not has_sfm and not has_dmxedit:
        return False, "sfm.exe / dmxedit.exe not found — might not be SFM"

    return True, "OK"
