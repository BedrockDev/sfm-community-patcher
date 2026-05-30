# SFM Community Patcher — Installation Guide

An all-in-one optimization patcher for **Source Filmmaker** (Steam). It automatically expands internal engine memory limits, prevents frequent memory crashes, and configures an advanced **DXVK (Vulkan)** + **ReShade** graphics pipeline for maximum stability and visual fidelity.

---

## Features & Benefits

| Feature | Impact |
|---------|--------|
| **Engine Hunk Optimization** | Completely resolves `Engine hunk overflow!` crashes on large, asset-heavy maps. |
| **CUtlRBTree Expansion** | Removes the native 16-bit limit on the maximum number of models, bones, and animation keys (`CUtlRBTree overflow!`). |
| **Command Bypass** | Unlocks restricted cinematic console commands without forcing cheat flags or breaking engine compliance. |
| **Vulkan API Render** | Translates outdated Direct3D 9 to modern Vulkan via DXVK, eliminating micro-stutters and boosting performance. |
| **ReShade Seamless Integration** | Allows you to use modern post-processing effects directly inside the upgraded engine viewport. |

> **Safety Note:** All modifications are applied as precise byte-level edits. PE file sizes remain untouched. Unmodified original Steam DLLs are safely backed up to the `bin\backups\` directory automatically upon the first run.

---

## Requirements
* Windows 10 / 11 (64-bit)
* **Source Filmmaker** installed via Steam
* **Python 3** added to your system PATH environment variables (required to execute the patching scripts)

---

## Step 1. Unpack the Patcher

Extract all files from the patcher archive directly into the root **`game`** folder of your Source Filmmaker directory (where `sfm.exe` is located):
SourceFilmmaker\game

├── sfm.exe
├── patch_sfm.bat
├── setup_reshade_dxvk.bat
├── instruction_ru.md
├── instruction_eng.md
└── sfm_patcher\


---

## Step 2. Install Graphics Components (DXVK & ReShade)

1. **DXVK:** Download the latest **DXVK** release (32-bit build, `x32` folder). Copy `d3d9.dll` from the archive into your `game\bin\` directory and rename it to **`d3d9_vlk.dll`**.
2. **ReShade:** Install ReShade for Source Filmmaker targeting Direct3D 9. Ensure that the original ReShade `d3d9.dll` file is successfully generated inside your `game\bin\` folder.

---

## Step 3. Run the Patcher

1. **Close Source Filmmaker completely** before proceeding.
2. Run **`patch_sfm.bat`** (as Administrator if required).
3. Select **Option [1]** from the interactive menu to automatically apply all engine optimizations and link the graphics libraries.
4. *(Optional)* Use **Option [2] (Dry-Run)** to simulate the patching process and verify files safely without modifying anything on your disk.

The patcher automatically links everything into a seamless execution chain:
Launch Game → Load ReShade (d3d9.dll) → Load High-Performance Vulkan (d3d9_vlk.dll)


---

## Step 4. Verification

Launch Source Filmmaker and confirm the following components:
* A `sfm_d3d9.log` file appears in your root `game` directory, displaying your GPU specs and Vulkan runtime version.
* Pressing the **Home** key (or your custom shortcut) inside SFM opens the fully functional ReShade overlay.
* Complex scenes that previously triggered immediate memory overflows now load smoothly and remain stable.

---

## Uninstallation & Restore

If you ever need to revert back to the vanilla Steam layout:
1. Run **`patch_sfm.bat`** and select **Option [3] (Restore Original Steam DLLs)**. Your backup files will be restored instantly.
2. Alternatively, you can use the standard Steam client option: *Properties → Installed Files → Verify integrity of game files*.

---
*SFM Community Patcher is an independent community-driven project created to improve workflow stability for 3D animators. It is not affiliated with or endorsed by Valve Corporation.*
---
