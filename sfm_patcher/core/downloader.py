# -*- coding: utf-8 -*-
"""
Download DXVK and ReShade.

DXVK: GitHub releases (tar.gz, x32 subdirectory)
ReShade: reshade.me direct download
"""

from __future__ import annotations

import json
import os
import re
import tarfile
import tempfile
import urllib.request
import zipfile
from typing import Callable, Optional


CACHE_DIR = os.path.join(tempfile.gettempdir(), "sfm_patcher_cache")

DXVK_REPO = "doitsujin/dxvk"
DXVK_TARGET_NAME = "d3d9_vlk.dll"
RESHADE_URL = "https://reshade.me/downloads/ReShade_Setup_6.7.3.exe"


def _github_api(url: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "SFM-Community-Patcher/3.2")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _download_file(url: str, dest: str, progress_cb: Optional[Callable] = None) -> str:
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "SFM-Community-Patcher/3.2")
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)
    return dest


def download_dxvk(target_dir: str, progress_cb: Optional[Callable] = None) -> str:
    """Download DXVK x32 d3d9.dll -> target_dir/d3d9_vlk.dll"""
    target_path = os.path.join(target_dir, DXVK_TARGET_NAME)
    if os.path.isfile(target_path):
        return target_path

    data = _github_api(f"https://api.github.com/repos/{DXVK_REPO}/releases/latest")
    tag = data["tag_name"]

    tar_asset = None
    for a in data.get("assets", []):
        if a["name"].startswith("dxvk-") and a["name"].endswith(".tar.gz") and "native" not in a["name"]:
            tar_asset = a
            break

    if not tar_asset:
        raise FileNotFoundError(f"DXVK tar.gz not found in release {tag}")

    cache_path = os.path.join(CACHE_DIR, f"dxvk-{tag}.tar.gz")
    if not os.path.isfile(cache_path):
        _download_file(tar_asset["url"], cache_path, progress_cb)

    with tarfile.open(cache_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith("/x32/d3d9.dll") or member.name == "x32/d3d9.dll":
                with tf.extractfile(member) as src:
                    dest = os.path.join(target_dir, DXVK_TARGET_NAME)
                    with open(dest, "wb") as dst:
                        dst.write(src.read())
                return dest

    raise FileNotFoundError("x32/d3d9.dll not found in DXVK archive")


def download_reshade(target_dir: str, progress_cb: Optional[Callable] = None) -> str:
    """Download ReShade setup.exe from reshade.me"""
    os.makedirs(target_dir, exist_ok=True)
    setup_path = os.path.join(target_dir, "ReShade_Setup.exe")

    if os.path.isfile(setup_path) and os.path.getsize(setup_path) > 1_000_000:
        return setup_path

    _download_file(RESHADE_URL, setup_path, progress_cb)
    return setup_path
