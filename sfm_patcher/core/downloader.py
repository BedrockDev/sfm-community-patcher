# -*- coding: utf-8 -*-
"""
Download DXVK and ReShade from GitHub releases.

Uses only stdlib (urllib.request). No external dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from typing import Callable, Optional


CACHE_DIR = os.path.join(tempfile.gettempdir(), "sfm_patcher_cache")

DXVK_REPO = "doitsujin/dxvk"
RESHADE_REPO = "crosire/ReShade"

DXVK_DLL_NAME = "d3d9.dll"
DXVK_TARGET_NAME = "d3d9_vlk.dll"


def _github_api(url: str) -> dict:
    """Fetch JSON from GitHub API."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "SFM-Community-Patcher/3.0")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def get_latest_dxvk_release() -> dict:
    """Get latest DXVK release info from GitHub."""
    data = _github_api(f"https://api.github.com/repos/{DXVK_REPO}/releases/latest")
    return {
        "tag": data["tag_name"],
        "assets": [
            {"name": a["name"], "url": a["browser_download_url"], "size": a["size"]}
            for a in data.get("assets", [])
        ],
    }


def get_latest_reshade_release() -> dict:
    """Get latest ReShade release info from GitHub."""
    data = _github_api(f"https://api.github.com/repos/{RESHADE_REPO}/releases/latest")
    return {
        "tag": data["tag_name"],
        "assets": [
            {"name": a["name"], "url": a["browser_download_url"], "size": a["size"]}
            for a in data.get("assets", [])
        ],
    }


def _download_file(
    url: str,
    dest: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Download a file with optional progress callback."""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "SFM-Community-Patcher/3.0")

    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 65536

        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)

    return dest


def download_dxvk(
    target_dir: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Download latest DXVK x32, extract d3d9.dll -> target_dir/d3d9_vlk.dll.
    Returns path to installed DLL.
    """
    release = get_latest_dxvk_release()
    tag = release["tag"]

    target_path = os.path.join(target_dir, DXVK_TARGET_NAME)
    if os.path.isfile(target_path):
        return target_path

    cache_zip = os.path.join(CACHE_DIR, f"dxvk-{tag}.zip")
    if not os.path.isfile(cache_zip):
        x32_asset = None
        for asset in release["assets"]:
            name = asset["name"].lower()
            if "x32" in name and name.endswith(".tar.gz"):
                x32_asset = asset
                break
        if not x32_asset:
            for asset in release["assets"]:
                name = asset["name"].lower()
                if "x32" in name and name.endswith(".zip"):
                    x32_asset = asset
                    break
        if not x32_asset:
            raise FileNotFoundError(f"DXVK x32 asset not found in release {tag}")

        _download_file(x32_asset["url"], cache_zip, progress_cb)

    if cache_zip.endswith(".zip"):
        with zipfile.ZipFile(cache_zip, "r") as zf:
            for name in zf.namelist():
                if name.endswith("x32/d3d9.dll") or (name.endswith("d3d9.dll") and "x32" in name):
                    with zf.open(name) as src, open(os.path.join(target_dir, DXVK_TARGET_NAME), "wb") as dst:
                        dst.write(src.read())
                    return target_dir + "\\" + DXVK_TARGET_NAME
    elif cache_zip.endswith(".tar.gz"):
        import tarfile
        with tarfile.open(cache_zip, "r:gz") as tf:
            for member in tf.getmembers():
                if member.name.endswith("x32/d3d9.dll") or (member.name.endswith("d3d9.dll") and "x32" in member.name):
                    with tf.extractfile(member) as src:
                        dest = os.path.join(target_dir, DXVK_TARGET_NAME)
                        with open(dest, "wb") as dst:
                            dst.write(src.read())
                    return dest

    raise FileNotFoundError("Could not find d3d9.dll in DXVK archive")


def download_reshade(
    target_dir: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Download latest ReShade setup.exe.
    Returns path to downloaded setup file.
    """
    release = get_latest_reshade_release()
    tag = release["tag"]

    setup_name = f"ReShade_Setup_{tag}.exe"
    setup_path = os.path.join(target_dir, setup_name)
    if os.path.isfile(setup_path):
        return setup_path

    setup_asset = None
    for asset in release["assets"]:
        if asset["name"].startswith("ReShade_Setup") and asset["name"].endswith(".exe"):
            setup_asset = asset
            break

    if not setup_asset:
        raise FileNotFoundError(f"ReShade setup not found in release {tag}")

    _download_file(setup_asset["url"], setup_path, progress_cb)
    return setup_path
