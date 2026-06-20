# -*- coding: utf-8 -*-
"""
ШАГ 3 — CUtlRBTree overflow (engine.dll).

Ошибка в SFM: «CUtlRBTree overflow!» (не «CUtlRBTree: overflow error» из старого ТЗ).

Снимает 16-битную маску индекса (and ecx, 0xFFFF → and ecx, 0x7FFFFFFF)
во всех шаблонах Insert, привязанных к этой строке.

В sfm.exe этой строки нет — патчится только engine.dll.

Использование:
    py -3 sfm_patcher\\step03_rbtree_overflow.py
    py -3 sfm_patcher\\step03_rbtree_overflow.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from lib.apply_patches import apply_planned_patches, plan_signature_patches  # noqa: E402
from lib.binary_patch import (  # noqa: E402
    PatchError,
    ensure_backup,
    restore_backup,
    ensure_file_exists,
    fail,
    log,
    read_all,
    resolve_bin_dir,
    write_all,
)
from lib.patch_defs import RBTREE_PATCHES  # noqa: E402

TARGET = "engine.dll"
ERROR_STRING = b"CUtlRBTree overflow!"


def patch_file(path: str, dry_run: bool) -> int:
    ensure_file_exists(path)
    data = read_all(path)
    if ERROR_STRING not in data:
        log(f"  Skip {os.path.basename(path)}: RBTree error string not found")
        return 0

    planned = plan_signature_patches(data, RBTREE_PATCHES)
    if not planned:
        log(f"  {os.path.basename(path)}: no changes (already patched?)")
        return 0

    log(f"\n=== {os.path.basename(path)} ===")
    for off, old_b, new_b, pid in planned:
        log(f"  0x{off:08X} [{pid}]")

    if dry_run:
        return len(planned)

    ensure_backup(path)
    buf = bytearray(data)
    n = apply_planned_patches(buf, planned)
    write_all(path, bytes(buf))
    log(f"  Applied: {n}")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="SFM Step 3: CUtlRBTree overflow")
    parser.add_argument("--bin-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    bin_dir = os.path.abspath(args.bin_dir or resolve_bin_dir(_SCRIPT_DIR))
    engine = os.path.join(bin_dir, TARGET)

    if args.restore:
        if restore_backup(engine):
            log(f"Restored: {engine}")
        else:
            log(f"No backup in bin\\backups\\ for {TARGET}")
        return

    total = patch_file(engine, args.dry_run)
    if total == 0 and not args.dry_run:
        log("No patches applied.")
    elif not args.dry_run:
        log(f"\nTotal replacements in engine.dll: {total}")


if __name__ == "__main__":
    try:
        main()
    except PatchError as exc:
        fail(str(exc))
