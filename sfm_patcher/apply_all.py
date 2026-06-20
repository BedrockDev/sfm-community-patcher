# -*- coding: utf-8 -*-
"""
Запуск всех шагов патчера SFM подряд.

    py -3 sfm_patcher\\apply_all.py
    py -3 sfm_patcher\\apply_all.py --dry-run
    py -3 sfm_patcher\\apply_all.py --restore
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    "step01_dxvk_loadlibrary.py",
    "step02_hunk_overflow.py",
    "step03_rbtree_overflow.py",
    "step04_fcv_flags.py",
    "step05_keyvalue_string_space.py",
    "step06_map_brush_limit.py",
    "step07_map_plane_limit.py",
    "step08_edict_limit.py",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="SFM: apply all patches")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--skip-dxvk", action="store_true", help="Skip step 1 (DXVK)")
    parser.add_argument(
        "--skip-edicts",
        action="store_true",
        help="Skip step 8 (experimental edict limit)",
    )
    args = parser.parse_args()

    py = sys.executable
    steps = [s for s in STEPS if not (args.skip_dxvk and s.startswith("step01"))]
    if args.skip_edicts:
        steps = [s for s in steps if not s.startswith("step08")]
    extra = []
    if args.dry_run:
        extra.append("--dry-run")
    if args.restore:
        extra.append("--restore")

    for step in steps:
        path = os.path.join(_SCRIPT_DIR, step)
        log_line = f"\n{'=' * 60}\n>>> {step}\n{'=' * 60}"
        print(log_line, flush=True)
        rc = subprocess.call([py, path, *extra], cwd=os.path.dirname(_SCRIPT_DIR))
        if rc != 0:
            print(f"Step failed with exit code {rc}: {step}", file=sys.stderr)
            sys.exit(rc)

    print("\nAll steps completed.", flush=True)


if __name__ == "__main__":
    main()
