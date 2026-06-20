# -*- coding: utf-8 -*-
"""
Общие функции безопасного бинарного патчинга для SFM Community Patcher.

Все патчи открывают файл в rb+, не меняют размер файла.
Резервные копии — в bin\\backups\\ (один раз, до первого патча).
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Iterable, List, Tuple


class PatchError(Exception):
    """Ошибка, при которой файл не должен оставаться в полупатченном состоянии."""


def resolve_bin_dir(script_dir: str | None = None) -> str:
    """
    Папка bin SFM: .../game/bin рядом с sfm_patcher.
    Можно переопределить переменной окружения SFM_BIN_DIR.
    """
    env = os.environ.get("SFM_BIN_DIR")
    if env:
        return os.path.abspath(env)
    if script_dir:
        # Передан каталог sfm_patcher (родитель — game)
        game_dir = os.path.dirname(os.path.abspath(script_dir))
    else:
        # Вызов из lib/*.py: lib -> sfm_patcher -> game
        lib_dir = os.path.dirname(os.path.abspath(__file__))
        game_dir = os.path.dirname(os.path.dirname(lib_dir))
    return os.path.join(game_dir, "bin")


def ensure_file_exists(path: str) -> None:
    if not os.path.isfile(path):
        raise PatchError(f"File not found: {path}")


BACKUP_FOLDER_NAME = "backups"


def backups_dir(original: str) -> str:
    """Папка резервных копий рядом с патчимым файлом (обычно bin\\backups)."""
    return os.path.join(os.path.dirname(os.path.abspath(original)), BACKUP_FOLDER_NAME)


def backup_path(original: str) -> str:
    """Путь к резервной копии: bin\\backups\\engine.dll и т.д."""
    return os.path.join(backups_dir(original), os.path.basename(original))


def _legacy_backup_path(original: str) -> str:
    """Старый формат: engine.dll.bak в той же папке, что и DLL."""
    return original + ".bak"


def ensure_backup(original: str) -> str:
    """
    Создаёт резервную копию в bin\\backups\\, если её ещё нет.
    Подхватывает старые *.bak из папки bin (миграция).
    Возвращает путь к файлу в backups\\.
    """
    original = os.path.abspath(original)
    bak = backup_path(original)
    if os.path.isfile(bak):
        return bak

    dest_dir = backups_dir(original)
    os.makedirs(dest_dir, exist_ok=True)

    legacy = _legacy_backup_path(original)
    if os.path.isfile(legacy):
        shutil.copy2(legacy, bak)
        return bak

    ensure_file_exists(original)
    shutil.copy2(original, bak)
    return bak


def restore_backup(original: str) -> bool:
    """
    Восстанавливает файл из bin\\backups\\ (или из legacy .bak).
    Возвращает True, если копия найдена.
    """
    original = os.path.abspath(original)
    bak = backup_path(original)
    if os.path.isfile(bak):
        shutil.copy2(bak, original)
        return True
    legacy = _legacy_backup_path(original)
    if os.path.isfile(legacy):
        shutil.copy2(legacy, original)
        return True
    return False


def read_all(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_all(path: str, data: bytes) -> None:
    with open(path, "rb+") as f:
        f.seek(0)
        f.write(data)
        f.truncate(len(data))


def find_all(data: bytes, needle: bytes, start: int = 0) -> List[int]:
    """Все смещения вхождения needle в data."""
    out: List[int] = []
    i = start
    while True:
        pos = data.find(needle, i)
        if pos < 0:
            break
        out.append(pos)
        i = pos + 1
    return out


def can_expand_into_padding(
    data: bytes, offset: int, old_len: int, new_len: int
) -> bool:
    """
    Новая строка длиннее старой — разрешаем только если «лишние» байты
    уже нули (типичный паддинг в .rdata PE), чтобы размер файла не менялся.
    """
    if new_len <= old_len:
        return True
    extra = new_len - old_len
    tail = data[offset + old_len : offset + new_len]
    return len(tail) == extra and all(b == 0 for b in tail)


def apply_replacements(
    data: bytearray,
    replacements: Iterable[Tuple[int, bytes, bytes]],
) -> int:
    """
    replacements: (offset, old_bytes, new_bytes).
  Возвращает число применённых замен.
    """
    count = 0
    for offset, old_b, new_b in replacements:
        if data[offset : offset + len(old_b)] != old_b:
            raise PatchError(
                f"Offset 0x{offset:X}: expected {old_b!r}, "
                f"found {bytes(data[offset : offset + len(old_b)])!r}"
            )
        data[offset : offset + len(new_b)] = new_b
        count += 1
    return count


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str, code: int = 1) -> None:
    log(f"ERROR: {msg}")
    sys.exit(code)
