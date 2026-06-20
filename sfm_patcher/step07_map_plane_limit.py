# -*- coding: utf-8 -*-
"""
Step 7 — BSP plane count at map load (engine.dll).

Engine error: "Map has too many planes"

Raises runtime checks in CMod_LoadPlanes from 65536 (0x10000) to 131072 (0x20000).
Does not change VBSP compile limits.
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
from lib.patch_defs import MAP_PLANE_PATCHES  # noqa: E402

TARGET = "engine.dll"
ERROR_STRING = b"Map has too many planes"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SFM Step 7: Map plane limit 65536 -> 131072 (engine.dll)"
    )
    parser.add_argument("--bin-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    bin_dir = os.path.abspath(args.bin_dir or resolve_bin_dir(_SCRIPT_DIR))
    target = os.path.join(bin_dir, TARGET)
    ensure_file_exists(target)

    log(f"Target: {target}")

    if args.restore:
        if restore_backup(target):
            log("Restored from bin\\backups\\")
        else:
            log("No backup found.")
        return

    data = read_all(target)
    if ERROR_STRING not in data:
        fail(
            f"String {ERROR_STRING!r} not found — engine.dll version does not match."
        )

    planned = plan_signature_patches(data, MAP_PLANE_PATCHES)
    if not planned:
        log("Nothing to patch (already applied or signature mismatch).")
        return

    for off, old_b, new_b, pid in planned:
        log(f"  [{pid}] 0x{off:08X}: {old_b.hex()} -> {new_b.hex()}")

    if args.dry_run:
        log("(dry-run: file not modified)")
        return

    ensure_backup(target)
    buf = bytearray(data)
    original_size = len(buf)
    apply_planned_patches(buf, planned)
    write_all(target, bytes(buf))
    if os.path.getsize(target) != original_size:
        raise PatchError("engine.dll file size changed!")
    log("Done: plane limit 65536 -> 131072. Restart SFM.")


if __name__ == "__main__":
    try:
        main()
    except PatchError as exc:
        fail(str(exc))
