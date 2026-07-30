# -*- coding: utf-8 -*-
"""
Unified setup process: detect SFM -> download deps -> install -> configure -> patch.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

from .downloader import download_dxvk, download_reshade
from .reshade_installer import install_reshade
from .sfm_detector import detect_sfm_game_dir, validate_game_dir

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from lib.apply_patches import apply_planned_patches, plan_signature_patches
from lib.binary_patch import (
    PatchError,
    ensure_backup,
    ensure_file_exists,
    log as _log,
    read_all,
    resolve_bin_dir,
    write_all,
    restore_backup,
)
from lib.patch_defs import (
    HUNK_PATCHES,
    RBTREE_PATCHES,
    FCVAR_PATCHES,
    KEYVALUE_STRING_PATCHES,
    MAP_BRUSH_PATCHES,
    MAP_PLANE_PATCHES,
    EDICT_PATCHES,
)
from configure_reshade_dxvk import configure_reshade_ini, DXVK_PROXY_DLL


@dataclass
class SetupConfig:
    game_dir: str = ""
    install_dxvk: bool = True
    install_reshade: bool = True
    apply_hunk: bool = True
    apply_rbtree: bool = True
    apply_fcvar: bool = True
    apply_keyvalues: bool = True
    apply_brushes: bool = True
    apply_planes: bool = True
    apply_edicts: bool = False
    dry_run: bool = False


@dataclass
class SetupResult:
    success: bool = False
    sfm_path: str = ""
    dxvk_installed: bool = False
    reshade_installed: bool = False
    patches_applied: int = 0
    errors: list[str] = field(default_factory=list)


def _patch_binary(
    bin_dir: str,
    filename: str,
    patches: list,
    error_string: bytes,
    log_cb: Callable[[str], None],
    dry_run: bool,
) -> int:
    """Apply signature patches to a binary file. Returns count of applied patches."""
    target = os.path.join(bin_dir, filename)
    if not os.path.isfile(target):
        log_cb(f"  SKIP: {filename} not found")
        return 0

    data = read_all(target)
    if error_string not in data:
        log_cb(f"  SKIP {filename}: error string not found (already patched?)")
        return 0

    planned = plan_signature_patches(data, patches)
    if not planned:
        log_cb(f"  {filename}: no changes needed")
        return 0

    for off, old_b, new_b, pid in planned:
        log_cb(f"  [{pid}] 0x{off:08X}: {old_b.hex()} -> {new_b.hex()}")

    if dry_run:
        return len(planned)

    ensure_backup(target)
    buf = bytearray(data)
    original_size = len(buf)
    count = apply_planned_patches(buf, planned)
    write_all(target, bytes(buf))
    if os.path.getsize(target) != original_size:
        raise PatchError(f"{filename} file size changed after patching!")
    log_cb(f"  Applied {count} patch(es) to {filename}")
    return count


def run_setup(
    config: SetupConfig,
    log_cb: Optional[Callable[[str], None]] = None,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> SetupResult:
    result = SetupResult()

    def log(msg: str) -> None:
        if log_cb:
            log_cb(msg)
        else:
            print(msg, flush=True)

    # Step 1: Find SFM
    log("=== Step 1: Finding Source Filmmaker ===")
    game_dir = config.game_dir
    if not game_dir:
        game_dir = detect_sfm_game_dir() or ""
    if game_dir:
        valid, msg = validate_game_dir(game_dir)
        if valid:
            log(f"Found SFM: {game_dir}")
            result.sfm_path = game_dir
        else:
            log(f"ERROR: {msg}")
            result.errors.append(msg)
            return result
    else:
        log("ERROR: Could not find Source Filmmaker installation.")
        result.errors.append("SFM not found")
        return result

    bin_dir = os.path.join(game_dir, "bin")

    # Step 2: Download DXVK
    if config.install_dxvk:
        log("\n=== Step 2: DXVK (Vulkan) ===")
        try:
            dxvk_path = os.path.join(bin_dir, DXVK_PROXY_DLL)
            if os.path.isfile(dxvk_path):
                log(f"DXVK already installed: {dxvk_path}")
                result.dxvk_installed = True
            else:
                log("Downloading DXVK x32...")
                download_dxvk(bin_dir, progress_cb)
                log(f"Installed: {dxvk_path}")
                result.dxvk_installed = True
        except Exception as e:
            msg = f"DXVK download failed: {e}"
            log(f"WARNING: {msg}")
            result.errors.append(msg)

    # Step 3: Download & install ReShade
    if config.install_reshade:
        log("\n=== Step 3: ReShade (Post-processing) ===")
        try:
            d3d9_path = os.path.join(bin_dir, "d3d9.dll")
            if os.path.isfile(d3d9_path) and os.path.getsize(d3d9_path) > 3_000_000:
                log(f"ReShade already installed: {d3d9_path}")
                result.reshade_installed = True
            else:
                log("Downloading ReShade...")
                cache_dir = os.path.join(os.path.dirname(bin_dir), ".patcher_cache")
                os.makedirs(cache_dir, exist_ok=True)
                setup_path = download_reshade(cache_dir, progress_cb)
                log("Installing ReShade to dmxedit.exe (D3D9, 32-bit)...")

                dmxedit = os.path.join(bin_dir, "dmxedit.exe")
                if not os.path.isfile(dmxedit):
                    log("WARNING: dmxedit.exe not found, trying sfm.exe...")
                    dmxedit = os.path.join(os.path.dirname(bin_dir), "sfm.exe")

                success = install_reshade(setup_path, dmxedit, "d3d9", log_cb)
                if success:
                    log("ReShade installed successfully")
                    result.reshade_installed = True
                else:
                    log("WARNING: ReShade installation may have failed")
                    result.errors.append("ReShade install failed")
        except Exception as e:
            msg = f"ReShade setup failed: {e}"
            log(f"WARNING: {msg}")
            result.errors.append(msg)

    # Step 4: Configure ReShade proxy
    if result.reshade_installed or result.dxvk_installed:
        log("\n=== Step 4: Configure ReShade proxy chain ===")
        try:
            reshade_ini = os.path.join(bin_dir, "ReShade.ini")
            game_ini = os.path.join(os.path.dirname(bin_dir), "ReShade.ini")

            if result.dxvk_installed:
                configure_reshade_ini(reshade_ini, DXVK_PROXY_DLL, config.dry_run)
                if os.path.isfile(game_ini):
                    configure_reshade_ini(game_ini, DXVK_PROXY_DLL, config.dry_run)
            else:
                log("Skipping proxy config (DXVK not installed)")
        except Exception as e:
            msg = f"Proxy config failed: {e}"
            log(f"WARNING: {msg}")
            result.errors.append(msg)

    # Step 5: Apply engine patches
    log("\n=== Step 5: Engine patches ===")
    step_defs = []
    if config.apply_hunk:
        step_defs.append(("step02_hunk_overflow", "engine.dll", HUNK_PATCHES, b"Engine hunk overflow!"))
    if config.apply_rbtree:
        step_defs.append(("step03_rbtree_overflow", "engine.dll", RBTREE_PATCHES, b"CUtlRBTree overflow!"))
    if config.apply_fcvar:
        step_defs.append(("step04_fcv_flags", "engine.dll", FCVAR_PATCHES, b"FCVAR_CHEAT"))
    if config.apply_keyvalues:
        step_defs.append(("step05_keyvalue_string_space", "vstdlib.dll", KEYVALUE_STRING_PATCHES, b"keyvalue string"))
    if config.apply_brushes:
        step_defs.append(("step06_map_brush_limit", "engine.dll", MAP_BRUSH_PATCHES, b"too many brushes"))
    if config.apply_planes:
        step_defs.append(("step07_map_plane_limit", "engine.dll", MAP_PLANE_PATCHES, b"too many planes"))
    if config.apply_edicts:
        step_defs.append(("step08_edict_limit", "engine.dll", EDICT_PATCHES, b"no free edicts"))

    try:
        for step_name, target_file, patches, err_str in step_defs:
            log(f"\n>>> {step_name}")
            try:
                count = _patch_binary(bin_dir, target_file, patches, err_str, log, config.dry_run)
                result.patches_applied += 1 if count > 0 or config.dry_run else 0
            except PatchError as e:
                log(f"WARNING: {step_name} failed: {e}")
            except Exception as e:
                log(f"WARNING: {step_name} error: {e}")

    except Exception as e:
        msg = f"Patching failed: {e}"
        log(f"ERROR: {msg}")
        result.errors.append(msg)

    # Summary
    log("\n" + "=" * 50)
    log("=== Setup Complete ===")
    log(f"SFM: {result.sfm_path}")
    log(f"DXVK: {'OK' if result.dxvk_installed else 'Skipped'}")
    log(f"ReShade: {'OK' if result.reshade_installed else 'Skipped'}")
    total_steps = len(step_defs)
    log(f"Patches: {result.patches_applied}/{total_steps}")
    if result.errors:
        log(f"Errors: {len(result.errors)}")
        for err in result.errors:
            log(f"  - {err}")
    log("=" * 50)

    result.success = len(result.errors) == 0 or result.patches_applied > 0
    return result
