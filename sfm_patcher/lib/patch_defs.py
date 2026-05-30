# -*- coding: utf-8 -*-
"""Описания сигнатурных патчей для конкретной сборки SFM (engine.dll)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SignaturePatch:
    """Замена байт по уникальной сигнатуре (размер old == new)."""

    patch_id: str
    description: str
    old: bytes
    new: bytes
    max_occurrences: int = 1
    # Если задано — смещение должно лежать в пределах ±window от anchor
    anchor_string: Optional[bytes] = None
    anchor_window: int = 0x8000


# --- Шаг 2: Hunk overflow ---------------------------------------------------

HUNK_PATCHES: list[SignaturePatch] = [
    SignaturePatch(
        patch_id="hunk_map_cap_512mb_to_2gb",
        description="Лимит hunk при загрузке карты: cmp eax, 512MB → 2GB",
        old=bytes.fromhex("3D 00 00 00 20"),
        new=bytes.fromhex("3D 00 00 00 80"),
        max_occurrences=1,
    ),
    SignaturePatch(
        patch_id="hunk_init_defaults",
        description="Стартовый hunk: push 32MB + mov 48MB → push 256MB + mov 1GB",
        old=bytes.fromhex("68 00 00 00 02 68 00 00 01 00 BE 00 00 00 03"),
        new=bytes.fromhex("68 00 00 00 10 68 00 00 01 00 BE 00 00 00 40"),
        max_occurrences=1,
    ),
    SignaturePatch(
        patch_id="hunk_low_reserve_40mb_to_256mb",
        description="Минимальный резерв hunk: cmp esi, 40MB → 256MB",
        old=bytes.fromhex("81 FE 00 00 80 02 7F 07 BE"),
        new=bytes.fromhex("81 FE 00 00 00 10 7F 07 BE"),
        max_occurrences=1,
    ),
]

# --- Шаг 3: CUtlRBTree overflow ---------------------------------------------

RBTREE_PATCHES: list[SignaturePatch] = [
    SignaturePatch(
        patch_id="rbtree_16bit_index_mask",
        description="Снять 16-битную маску индекса: and ecx, 0xFFFF → and ecx, 0x7FFFFFFF",
        old=bytes.fromhex("81 E1 FF FF 00 00 66 89 4D FE"),
        new=bytes.fromhex("81 E1 FF FF FF 7F 66 89 4D FE"),
        max_occurrences=64,  # 24+ в engine.dll
    ),
]

# --- Шаг 4: ConVar / ConCommand flags ---------------------------------------

# --- Шаг 5: KeyValues string table (vstdlib.dll) -----------------------------

KEYVALUE_STRING_PATCHES: list[SignaturePatch] = [
    SignaturePatch(
        patch_id="kv_string_grow_past_cap",
        description=(
            "Out of keyvalue string space: allow CUtlBuffer grow past hard cap "
            "(ja -> nop in KeyValues string pool)"
        ),
        old=bytes.fromhex("3B 57 08 77 3B"),
        new=bytes.fromhex("3B 57 08 90 90"),
        max_occurrences=1,
    ),
]

# --- Шаг 4: ConVar / ConCommand flags ---------------------------------------

FCVAR_PATCHES: list[SignaturePatch] = [
    SignaturePatch(
        patch_id="fcvar_cheat_access_check",
        description="Обход проверки FCVAR_CHEAT (test [esi+0xC], 0x4000 → всегда разрешено)",
        old=bytes.fromhex("F7 46 0C 00 40 00 00 74 14"),
        new=bytes.fromhex("B8 01 00 00 00 EB 18 90 90"),
        max_occurrences=1,
    ),
]
