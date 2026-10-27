@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Windows double-click launcher for the Pygame Richman 4 port.
rem Always uses the existing Anaconda/Conda environment named vt.
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 (
    echo [ERROR] Could not open the game directory.
    pause
    exit /b 1
)

if not exist "assets\manifest.json" (
    echo [ERROR] Missing pygame\assets\manifest.json.
    echo Import your licensed game assets first; see pygame\README.md.
    goto :failed
)

rem Prefer an explicit Conda executable, then PATH, then common installations.
set "CONDA_CMD="
if defined CONDA_EXE if exist "%CONDA_EXE%" set "CONDA_CMD=%CONDA_EXE%"
if not defined CONDA_CMD (
    where conda.bat >nul 2>nul
    if not errorlevel 1 set "CONDA_CMD=conda.bat"
)
if not defined CONDA_CMD (
    where conda.exe >nul 2>nul
    if not errorlevel 1 set "CONDA_CMD=conda.exe"
)
if not defined CONDA_CMD (
    for %%D in (
        "%USERPROFILE%\anaconda3"
        "%USERPROFILE%\miniconda3"
        "%USERPROFILE%\miniforge3"
        "%LOCALAPPDATA%\anaconda3"
        "%LOCALAPPDATA%\miniconda3"
        "%LOCALAPPDATA%\miniforge3"
        "C:\ProgramData\anaconda3"
    ) do if not defined CONDA_CMD (
        if exist "%%~D\condabin\conda.bat" (
            set "CONDA_CMD=%%~D\condabin\conda.bat"
        ) else if exist "%%~D\Scripts\conda.exe" (
            set "CONDA_CMD=%%~D\Scripts\conda.exe"
        )
    )
)
if not defined CONDA_CMD (
    echo [ERROR] Conda was not found. Install Anaconda or Miniconda.
    echo Or add Conda to PATH / set the CONDA_EXE environment variable.
    goto :failed
)

rem The Windows launcher supports Python 3.11+ in the existing vt environment.
rem Never fall back to base/another environment.
echo [CHECK] Checking Conda environment vt ^(Python 3.11 or newer^) ...
call "%CONDA_CMD%" run -n vt --no-capture-output python -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Environment vt is missing, or its Python is older than 3.11.
    echo Install Python 3.11 or newer into the existing vt environment.
    goto :failed
)

rem Import project sources directly so local changes take effect without reinstalling.
set "PYTHONPATH=%CD%\src"
call "%CONDA_CMD%" run -n vt --no-capture-output python -c "import importlib.metadata as m; raise SystemExit(m.version('pygame') != '2.6.1')" >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Installing pinned Pygame dependencies into vt ...
    call "%CONDA_CMD%" run -n vt --no-capture-output python -m pip install --disable-pip-version-check --no-input pygame==2.6.1
    if errorlevel 1 goto :failed
)

rem Native audio was validated on macOS, not Windows. If any required DLL/ABI
rem is unavailable, start the real game in explicit silent mode instead of
rem crashing before a window can be opened.
set "AUDIO_MODE="
call "%CONDA_CMD%" run -n vt --no-capture-output python tools\windows_audio_probe.py >nul 2>nul
if errorlevel 1 (
    echo [WARN] Windows audio libraries are missing or incompatible.
    echo [WARN] The real game will start without sound ^(--silent^).
    set "AUDIO_MODE=--silent"
)

echo [START] Running Richman 4 with Conda environment vt ...
call "%CONDA_CMD%" run -n vt --no-capture-output pythonw.exe -m rich4.game_cli %AUDIO_MODE% %*
if errorlevel 1 goto :failed

popd
endlocal
exit /b 0

:failed
echo.
echo [ERROR] Game launch failed. Review the message above.
pause
popd
endlocal
exit /b 1
