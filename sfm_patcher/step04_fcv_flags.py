# -*- coding: utf-8 -*-
"""
ШАГ 4 — доступ к ConVar / ConCommand с флагом FCVAR_CHEAT.

В этой сборке SFM найдена одна ключевая проверка:
  test dword ptr [esi+0Ch], 4000h  (FCVAR_CHEAT)
  je ...

Патч заменяет блок на mov eax, 1; jmp (всегда «разрешено»).

Полное снятие FCVAR_DEVELOPMENTONLY в этой DLL отдельной сигнатурой
не найдено — при необходимости добавим после анализа другой версии.

Использование:
    py -3 sfm_patcher\\step04_fcv_flags.py
    py -3 sfm_patcher\\step04_fcv_flags.py --dry-run
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
from lib.patch_defs import FCVAR_PATCHES  # noqa: E402

TARGET = "engine.dll"


def main() -> None:
    parser = argparse.ArgumentParser(description="SFM Step 4: FCVAR_CHEAT access")
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
    planned = plan_signature_patches(data, FCVAR_PATCHES)

    log(f"File: {target}")
    if not planned:
        log("No changes (patch already applied or signature not found).")
        return

    for off, old_b, new_b, pid in planned:
        log(f"  [{pid}] 0x{off:08X}")

    if args.dry_run:
        log("(dry-run)")
        return

    ensure_backup(target)
    buf = bytearray(data)
    apply_planned_patches(buf, planned)
    write_all(target, bytes(buf))
    log("Done. You may still need 'sv_cheats 1' in the console for some cheat commands.")


if __name__ == "__main__":
    try:
        main()
    except PatchError as exc:
        fail(str(exc))
