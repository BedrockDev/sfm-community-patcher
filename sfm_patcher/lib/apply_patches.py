# -*- coding: utf-8 -*-
"""Применение списка сигнатурных патчей к буферу PE."""

from __future__ import annotations

from typing import List, Tuple

from .binary_patch import PatchError, find_all
from .patch_defs import SignaturePatch


def _anchor_range(data: bytes, anchor: bytes, window: int) -> Tuple[int, int] | None:
    pos = data.find(anchor)
    if pos < 0:
        return None
    return max(0, pos - window), min(len(data), pos + window)


def plan_signature_patches(
    data: bytes,
    patches: List[SignaturePatch],
) -> List[Tuple[int, bytes, bytes, str]]:
    """
    Возвращает список (offset, old, new, patch_id).
    Пропускает участки, уже совпадающие с new.
    """
    planned: List[Tuple[int, bytes, bytes, str]] = []
    used_ranges: List[Tuple[int, int]] = []

    for spec in patches:
        anchor_rng = None
        if spec.anchor_string:
            anchor_rng = _anchor_range(data, spec.anchor_string, spec.anchor_window)

        found = 0
        for offset in find_all(data, spec.old):
            if anchor_rng and not (anchor_rng[0] <= offset < anchor_rng[1]):
                continue

            end = offset + len(spec.old)
            if data[offset:end] == spec.new:
                continue

            overlap = any(not (end <= s or offset >= e) for s, e in used_ranges)
            if overlap:
                continue

            planned.append((offset, spec.old, spec.new, spec.patch_id))
            used_ranges.append((offset, end))
            found += 1
            if found >= spec.max_occurrences:
                break

        if found == 0 and spec.max_occurrences > 0:
            # не ошибка — возможно уже пропатчено; проверим «уже new»
            already = 0
            for offset in find_all(data, spec.new):
                if anchor_rng and not (anchor_rng[0] <= offset < anchor_rng[1]):
                    continue
                already += 1
                if already >= spec.max_occurrences:
                    break

    return planned


def apply_planned_patches(
    data: bytearray,
    planned: List[Tuple[int, bytes, bytes, str]],
) -> int:
    from .binary_patch import apply_replacements

    replacements = [(off, old, new) for off, old, new, _ in planned]
    return apply_replacements(data, replacements)
