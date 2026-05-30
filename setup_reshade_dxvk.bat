@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

title SFM — ReShade + DXVK setup

echo.
echo  ReShade + DXVK chain setup
echo  ========================
echo.
echo  Requires:
echo    - bin\d3d9_vlk.dll  ^(DXVK, renamed^)
echo    - bin\d3d9.dll OR bin\d3d9_reshade.dll  ^(ReShade proxy^)
echo.
echo  This will:
echo    1. Ensure shaderapidx9 loads d3d9.dll ^(ReShade^)
echo    2. Set ReShade.ini [PROXY] -^> d3d9_vlk.dll ^(DXVK^)
echo    3. Enable ReShade as bin\d3d9.dll
echo.
echo  After setup, start SFM from Steam as usual.
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

py -3 sfm_patcher\configure_reshade_dxvk.py
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo OK. Start Source Filmmaker from Steam.
pause
