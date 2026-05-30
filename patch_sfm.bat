@echo off

chcp 65001 >nul

setlocal EnableExtensions



REM SFM Community Patcher (DXVK + engine limits)

REM Run from game\ (next to sfm.exe)



cd /d "%~dp0"

title SFM Community Patcher



echo.

echo  === SFM Community Patcher v2.5 ===

echo  Folder: %CD%

echo.



where py >nul 2>&1

if errorlevel 1 (

    echo [ERROR] Python not found. Install Python 3 and add "py" to PATH.

    pause

    exit /b 1

)



if not exist "bin\engine.dll" (

    echo [ERROR] bin\engine.dll not found — run this from Source Filmmaker\game.

    pause

    exit /b 1

)



tasklist /FI "IMAGENAME eq sfm.exe" 2>nul | find /I "sfm.exe" >nul

if not errorlevel 1 (

    echo [WARNING] SFM is running. Close Source Filmmaker before patching.

    pause

)



if not exist "bin\d3d9_vlk.dll" (

    echo [WARNING] bin\d3d9_vlk.dll missing — copy d3d9.dll from DXVK here and rename it.

    echo.

)



echo Select:

echo   1 — Apply all patches

echo   2 — Preview only ^(dry-run^)

echo   3 — Restore from bin\backups\

echo   5 — ReShade + DXVK chain ^(setup_reshade_dxvk.bat^)

echo   4 — Exit

echo.

set /p CHOICE="Choice [1]: "

if "%CHOICE%"=="" set CHOICE=1



if "%CHOICE%"=="5" (
    call setup_reshade_dxvk.bat
    goto :done
)

if "%CHOICE%"=="4" exit /b 0

if "%CHOICE%"=="2" (

    py -3 sfm_patcher\apply_all.py --dry-run --skip-dxvk

    goto :done

)

if "%CHOICE%"=="3" (

    py -3 sfm_patcher\apply_all.py --restore

    goto :done

)



REM Step 1 (d3d9_vlk string) breaks ReShade PROXY — engine patches only
py -3 sfm_patcher\apply_all.py --skip-dxvk

if errorlevel 1 (

    echo.

    echo [ERROR] Patching failed. Check the output above.

    pause

    exit /b 1

)



:done

echo.

echo Done. Backups: bin\backups\

echo Restart SFM.

pause


