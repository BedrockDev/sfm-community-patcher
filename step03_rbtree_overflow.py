# -*- coding: utf-8 -*-
"""
ШАГ 1 — нативная интеграция DXVK (переименование цели LoadLibrary).

Заменяет строку загрузки Direct3D 9:
    d3d9.dll      ->  d3d9_vlk.dll

Старая строка:  64 33 64 39 2E 64 6C 6C           (8 байт)
Новая строка:   64 33 64 39 5F 76 6C 6B 2E 64 6C 6C  (12 байт)

Размер PE не меняется: дополнительные 4 байта берутся только из нулевого
паддинга сразу после строки в секции данных (проверяется автоматически).

Архитектура Source (SFM): LoadLibrary("d3d9.dll") живёт в shaderapidx9.dll,
а не в materialsystem.dll. По умолчанию патчим shaderapidx9.dll.

Использование (из папки game, где лежит sfm_patcher):
    py -3 sfm_patcher\\step01_dxvk_loadlibrary.py
    py -3 sfm_patcher\\step01_dxvk_loadlibrary.py --dry-run
    py -3 sfm_patcher\\step01_dxvk_loadlibrary.py --restore

Перед запуском положите переименованный DXVK как bin\\d3d9_vlk.dll
(копия d3d9.dll из пакета DXVK). Имя d3d9.dll в bin оставьте для ReShade.
"""

from __future__ import annotations

import argparse
import os
import sys

# Позволяем запускать скрипт напрямую, без установки пакета
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from lib.binary_patch import (  # noqa: E402
    PatchError,
    apply_replacements,
    can_expand_into_padding,
    ensure_backup,
    restore_backup,
    ensure_file_exists,
    fail,
    find_all,
    log,
    read_all,
    resolve_bin_dir,
    write_all,
)

# --- Константы патча (как в ТЗ) --------------------------------------------

OLD_STRING = bytes.fromhex("64 33 64 39 2E 64 6C 6C")  # b"d3d9.dll"
NEW_STRING = bytes.fromhex("64 33 64 39 5F 76 6C 6B 2E 64 6C 6C")  # b"d3d9_vlk.dll"

# Реальная цель для SFM / Source 1 (DX9 shader backend)
PRIMARY_DLL = "shaderapidx9.dll"

# В materialsystem.dll строки d3d9.dll обычно нет — опционально для других сборок
LEGACY_DLL = "materialsystem.dll"


def plan_patches(data: bytes) -> list[tuple[int, bytes, bytes]]:
    """
    Собирает список замен для всех безопасных вхождений OLD_STRING.

    Пропускает вхождения, уже пропатченные (NEW_STRING).
    Пропускает вхождения без достаточного нулевого паддинга.
    """
    patches: list[tuple[int, bytes, bytes]] = []

    for offset in find_all(data, OLD_STRING):
        if data[offset : offset + len(NEW_STRING)] == NEW_STRING:
            log(f"  [skip] 0x{offset:X}: already d3d9_vlk.dll")
            continue

        if not can_expand_into_padding(
            data, offset, len(OLD_STRING), len(NEW_STRING)
        ):
            log(
                f"  [skip] 0x{offset:X}: not enough zero padding after string "
                f"(cannot expand safely)"
            )
            continue

        patches.append((offset, OLD_STRING, NEW_STRING))

    return patches


def patch_one_dll(bin_dir: str, dll_name: str, dry_run: bool) -> int:
    """Патчит один DLL в bin_dir. Возвращает число замен."""
    target = os.path.join(bin_dir, dll_name)
    ensure_file_exists(target)

    log(f"\n=== {dll_name} ===")
    log(f"Path: {target}")

    original_size = os.path.getsize(target)
    data = bytearray(read_all(target))

    planned = plan_patches(bytes(data))
    if not planned:
        log("No replacements planned (d3d9.dll not found or unsafe to patch).")
        return 0

    log(f"Planned replacements: {len(planned)}")
    for off, old_b, new_b in planned:
        log(f"  0x{off:08X}: {old_b.decode('ascii')} -> {new_b.decode('ascii')}")

    if dry_run:
        log("(--dry-run: backups\\ not created, file not modified)")
        return len(planned)

    bak = ensure_backup(target)
    log(f"Backup: {bak}")

    count = apply_replacements(data, planned)
    write_all(target, bytes(data))

    new_size = os.path.getsize(target)
    if new_size != original_size:
        raise PatchError(
            f"File size changed ({original_size} -> {new_size}) — restore from bin\\backups\\"
        )

    log(f"Done: {count} replacement(s), file size: {new_size} bytes")
    return count


def restore_dll(bin_dir: str, dll_name: str) -> None:
    target = os.path.join(bin_dir, dll_name)
    if restore_backup(target):
        log(f"{dll_name}: restored from backups\\")
    else:
        log(f"{dll_name}: backup not found, skipped")


def check_dxvk_present(bin_dir: str) -> None:
    """Предупреждение, если переименованный DXVK ещё не лежит в bin."""
    dxvk = os.path.join(bin_dir, "d3d9_vlk.dll")
    if os.path.isfile(dxvk):
        log(f"DXVK found: {dxvk}")
    else:
        log(
            "WARNING: bin\\d3d9_vlk.dll not found. "
            "Copy d3d9.dll from the DXVK package here and rename it to d3d9_vlk.dll."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SFM Step 1: d3d9.dll -> d3d9_vlk.dll for LoadLibrary"
    )
    parser.add_argument(
        "--bin-dir",
        default=None,
        help="bin folder (default: game/bin or SFM_BIN_DIR)",
    )
    parser.add_argument(
        "--legacy-materialsystem",
        action="store_true",
        help="Also check materialsystem.dll (usually no d3d9.dll in SFM)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show offsets only, do not write files",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore files from bin\\backups\\",
    )
    args = parser.parse_args()

    bin_dir = os.path.abspath(args.bin_dir or resolve_bin_dir(_SCRIPT_DIR))
    if not os.path.isdir(bin_dir):
        fail(f"bin folder not found: {bin_dir}")

    log(f"Working bin folder: {bin_dir}")

    targets = [PRIMARY_DLL]
    if args.legacy_materialsystem:
        targets.append(LEGACY_DLL)

    if args.restore:
        for name in targets:
            restore_dll(bin_dir, name)
        return

    check_dxvk_present(bin_dir)

    total = 0
    try:
        for name in targets:
            total += patch_one_dll(bin_dir, name, args.dry_run)
    except PatchError as exc:
        fail(str(exc))

    if total == 0:
        log(
            "\nd3d9.dll string not found (or already d3d9_vlk.dll). "
            "Check shaderapidx9.dll version or restore from bin\\backups\\."
        )

    if total > 0 and not args.dry_run:
        log(
            "\nSuccess. Restart SFM. ReShade can use bin\\d3d9.dll, "
            "the engine loads bin\\d3d9_vlk.dll."
        )


if __name__ == "__main__":
    main()
