# -*- coding: utf-8 -*-
"""
ШАГ 2 — снятие лимита Hunk-памяти (engine.dll).

Ошибка в SFM: «Engine hunk overflow!»

Патчи (сигнатуры для вашей engine.dll):
  1. Потолок при расчёте размера hunk: 512 MB → 2 GB
  2. Стартовая инициализация: 32/48 MB → 256 MB / 256 MB
  3. Минимальный резерв: 40 MB → 256 MB

Использование:
    py -3 sfm_patcher\\step02_hunk_overflow.py
    py -3 sfm_patcher\\step02_hunk_overflow.py --dry-run
    py -3 sfm_patcher\\step02_hunk_overflow.py --restore
"""

from __future__ import annotations

import argparse
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from lib.apply_patches import plan_signature_patches  # noqa: E402
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
from lib.patch_defs import HUNK_PATCHES  # noqa: E402

TARGET = "engine.dll"
ERROR_STRING = b"Engine hunk overflow!"


def main() -> None:
    parser = argparse.ArgumentParser(description="SFM Step 2: Hunk overflow limits")
    parser.add_argument("--bin-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    bin_dir = os.path.abspath(args.bin_dir or resolve_bin_dir(_SCRIPT_DIR))
    target = os.path.join(bin_dir, TARGET)
    ensure_file_exists(target)

    if args.restore:
        if restore_backup(target):
            log(f"Restored: {target}")
        else:
            fail(f"No backup in bin\\backups\\ for {TARGET}")
        return

    data = read_all(target)
    if ERROR_STRING not in data:
        fail(
            f"String {ERROR_STRING!r} not found — engine.dll version does not match."
        )

    planned = plan_signature_patches(data, HUNK_PATCHES)
    log(f"File: {target}")
    log(f"Error string found: {ERROR_STRING.decode()}")

    if not planned:
        log("No changes (patch may already be applied).")
        return

    for off, old_b, new_b, pid in planned:
        log(f"  [{pid}] 0x{off:08X}: {old_b.hex()} -> {new_b.hex()}")

    if args.dry_run:
        log("(dry-run: file not modified)")
        return

    ensure_backup(target)
    buf = bytearray(data)
    original_size = len(buf)
    from lib.apply_patches import apply_planned_patches

    apply_planned_patches(buf, planned)
    write_all(target, bytes(buf))
    if os.path.getsize(target) != original_size:
        raise PatchError("engine.dll file size changed!")
    log(f"Done: applied {len(planned)} patch(es)")


if __name__ == "__main__":
    try:
        main()
    except PatchError as exc:
        fail(str(exc))
