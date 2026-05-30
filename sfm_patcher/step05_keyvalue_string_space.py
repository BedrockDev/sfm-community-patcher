# -*- coding: utf-8 -*-
"""
Step 5 — KeyValues string pool (vstdlib.dll).

Engine error: "Out of keyvalue string space"

The shared string table for KeyValues names/paths lives in vstdlib.dll.
When the fixed buffer cannot grow, SFM shows this dialog and exits.

Patch: remove the hard cap check in the grow helper (ja -> nop).
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
from lib.apply_patches import apply_planned_patches  # noqa: E402
from lib.patch_defs import KEYVALUE_STRING_PATCHES  # noqa: E402

TARGET = "vstdlib.dll"
ERROR_STRING = b"Out of keyvalue string space"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SFM Step 5: KeyValues string space (vstdlib.dll)"
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
        log("WARNING: error string not found — wrong vstdlib.dll build?")

    planned = plan_signature_patches(data, KEYVALUE_STRING_PATCHES)
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
        raise PatchError("vstdlib.dll file size changed!")
    log(f"Done: applied {len(planned)} patch(es). Restart SFM.")


if __name__ == "__main__":
    try:
        main()
    except PatchError as exc:
        fail(str(exc))
