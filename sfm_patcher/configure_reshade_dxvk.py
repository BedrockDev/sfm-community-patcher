# -*- coding: utf-8 -*-
"""
ReShade 6.7+ + DXVK for SFM (Steam launch, no env vars).

ReShade 6.7 removed RESHADE_MODULE_PATH_OVERRIDE / [INSTALL] ModulePath.
Use [PROXY] instead (ReShade 6.7 release notes):

    [PROXY]
    EnableProxyLibrary=1
    ProxyLibrary=d3d9_vlk.dll

Chain: LoadLibrary("d3d9.dll") -> ReShade (bin\\d3d9.dll) -> DXVK (bin\\d3d9_vlk.dll).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from lib.binary_patch import (  # noqa: E402
    PatchError,
    apply_replacements,
    ensure_file_exists,
    fail,
    find_all,
    log,
    read_all,
    resolve_bin_dir,
    restore_backup,
    write_all,
)
from step01_dxvk_loadlibrary import (  # noqa: E402
    NEW_STRING,
    OLD_STRING,
    PRIMARY_DLL,
)

# DXVK copy in bin (same name as old patcher convention)
DXVK_PROXY_DLL = "d3d9_vlk.dll"
# Alias matching ReShade 6.7 docs examples
DXVK_PROXY_ALIAS = "d3d9_dxvk.dll"


def _read_ini(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _write_ini(path: str, content: str, dry_run: bool) -> None:
    if not content.endswith("\n"):
        content += "\n"
    log(f"ReShade.ini: {path}")
    if not dry_run:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)


def _upsert_section(
    content: str, section: str, values: dict[str, str], remove_keys: tuple[str, ...] = ()
) -> str:
    lines = content.splitlines() if content else []
    out: list[str] = []
    in_section = False
    seen_keys: set[str] = set()

    for raw in lines:
        stripped = raw.strip()
        if stripped == section:
            in_section = True
            if section not in [l.strip() for l in out]:
                out.append(section)
            continue
        if in_section and stripped.startswith("["):
            for key, val in values.items():
                if key not in seen_keys:
                    out.append(f"{key}={val}")
                    seen_keys.add(key)
            in_section = False
        if in_section and any(stripped.startswith(f"{k}=") for k in remove_keys):
            continue
        if in_section:
            key = stripped.split("=", 1)[0] if "=" in stripped else ""
            if key in values:
                if key not in seen_keys:
                    out.append(f"{key}={values[key]}")
                    seen_keys.add(key)
                continue
        out.append(raw)

    if in_section:
        for key, val in values.items():
            if key not in seen_keys:
                out.append(f"{key}={val}")
                seen_keys.add(key)
    elif section not in content:
        if out and out[-1].strip():
            out.append("")
        out.append(section)
        for key, val in values.items():
            out.append(f"{key}={val}")

    return "\n".join(out)


def configure_reshade_ini(ini_path: str, proxy_dll: str, dry_run: bool) -> None:
    content = _read_ini(ini_path)
    content = _upsert_section(
        content,
        "[PROXY]",
        {
            "EnableProxyLibrary": "1",
            "ProxyLibrary": proxy_dll,
        },
    )
    # Obsolete on ReShade 6.7+ — drop so it does not confuse
    content = _upsert_section(
        content,
        "[INSTALL]",
        {},
        remove_keys=("ModulePath",),
    )
    _write_ini(ini_path, content, dry_run)
    log(f"  [PROXY] EnableProxyLibrary=1")
    log(f"  [PROXY] ProxyLibrary={proxy_dll}")


def plan_revert_to_d3d9(data: bytes) -> list[tuple[int, bytes, bytes]]:
    patches: list[tuple[int, bytes, bytes]] = []
    for offset in find_all(data, NEW_STRING):
        if data[offset : offset + len(OLD_STRING)] == OLD_STRING:
            log(f"  [skip] 0x{offset:X}: already d3d9.dll")
            continue
        patches.append((offset, NEW_STRING, OLD_STRING))
    return patches


def revert_shaderapi(bin_dir: str, dry_run: bool) -> bool:
    target = os.path.join(bin_dir, PRIMARY_DLL)
    ensure_file_exists(target)

    log(f"\n=== Revert {PRIMARY_DLL} (d3d9_vlk.dll -> d3d9.dll) ===")

    data_check = read_all(target)
    if NEW_STRING not in data_check and OLD_STRING in data_check:
        log("Already loads d3d9.dll — skip DLL revert.")
        return False

    if restore_backup(target) and not dry_run:
        log("Restored from bin\\backups\\")
        return True

    data = bytearray(read_all(target))
    planned = plan_revert_to_d3d9(bytes(data))
    if not planned:
        if NEW_STRING in data:
            fail("d3d9_vlk.dll present but cannot revert safely — restore backup manually.")
        log("LoadLibrary string is already d3d9.dll (or no patch found).")
        return False

    log(f"Planned revert: {len(planned)} replacement(s)")
    if dry_run:
        return True

    count = apply_replacements(data, planned)
    write_all(target, bytes(data))
    log(f"Reverted {count} string(s) in {PRIMARY_DLL}")
    return True


def ensure_dxvk_dll(bin_dir: str, dry_run: bool) -> str:
    primary = os.path.join(bin_dir, DXVK_PROXY_DLL)
    alias = os.path.join(bin_dir, DXVK_PROXY_ALIAS)
    backend = os.path.join(bin_dir, "dxvk_backend", "d3d9.dll")

    src = primary if os.path.isfile(primary) else backend if os.path.isfile(backend) else None
    if src is None:
        fail(
            f"DXVK missing. Put {DXVK_PROXY_DLL} in bin\\ "
            "(renamed d3d9.dll from DXVK x32 package)."
        )

    log(f"\n=== DXVK ({DXVK_PROXY_DLL}) ===")
    if not dry_run:
        if src != primary:
            shutil.copy2(src, primary)
            log(f"Copied: {src} -> {primary}")
        if not os.path.isfile(alias):
            shutil.copy2(primary, alias)
            log(f"Alias: {DXVK_PROXY_ALIAS}")
        elif os.path.getsize(alias) != os.path.getsize(primary):
            shutil.copy2(primary, alias)
            log(f"Refreshed alias: {DXVK_PROXY_ALIAS}")
    else:
        log(f"Would ensure: {primary}")

    return DXVK_PROXY_DLL


def ensure_reshade_proxy(bin_dir: str, dry_run: bool) -> None:
    proxy = os.path.join(bin_dir, "d3d9.dll")
    reshade = os.path.join(bin_dir, "d3d9_reshade.dll")

    log("\n=== ReShade proxy (bin\\d3d9.dll) ===")

    if os.path.isfile(proxy):
        size = os.path.getsize(proxy)
        if size > 3_000_000:
            log(f"Found ReShade proxy: {proxy} ({size} bytes)")
            return
        log(f"WARNING: {proxy} exists but looks small ({size} B). Reinstall ReShade if needed.")

    if os.path.isfile(reshade):
        log(f"Enabling ReShade: {reshade} -> d3d9.dll")
        if not dry_run:
            if os.path.isfile(proxy):
                fail("Cannot rename: bin\\d3d9.dll already exists.")
            os.rename(reshade, proxy)
        return

    fail(
        "ReShade proxy missing. Install ReShade for bin\\dmxedit.exe (D3D9), "
        "or restore bin\\d3d9_reshade.dll."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ReShade 6.7+ PROXY chain to DXVK (Steam-safe)"
    )
    parser.add_argument("--bin-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    bin_dir = os.path.abspath(args.bin_dir or resolve_bin_dir(_SCRIPT_DIR))
    if not os.path.isdir(bin_dir):
        fail(f"bin folder not found: {bin_dir}")

    log(f"bin: {bin_dir}")

    try:
        revert_shaderapi(bin_dir, args.dry_run)
        proxy_dll = ensure_dxvk_dll(bin_dir, args.dry_run)
        ensure_reshade_proxy(bin_dir, args.dry_run)

        configure_reshade_ini(
            os.path.join(bin_dir, "ReShade.ini"), proxy_dll, args.dry_run
        )
        game_ini = os.path.join(os.path.dirname(bin_dir), "ReShade.ini")
        if os.path.isfile(game_ini):
            configure_reshade_ini(game_ini, proxy_dll, args.dry_run)
    except PatchError as exc:
        fail(str(exc))

    log("\n--- Done ---")
    log("ReShade 6.7+: [PROXY] ProxyLibrary -> bin\\" + DXVK_PROXY_DLL)
    log("Start SFM from Steam. In ReShade.log expect:")
    log("  Installing export hooks for '...\\bin\\d3d9_vlk.dll' ...")
    log("Then check game\\sfm_d3d9.log for DXVK / Vulkan.")


if __name__ == "__main__":
    main()
