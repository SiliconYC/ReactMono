@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Double-click in Windows Explorer to start the real Pygame game.
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0" || goto :failed

if not exist "assets\manifest.json" (
  echo Game assets are missing: pygame\assets\manifest.json
  echo Import your licensed assets first. See pygame\README.md.
  goto :failed
)

set "UV=uv"
where uv >nul 2>nul
if errorlevel 1 (
  if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV=%USERPROFILE%\.local\bin\uv.exe"
  ) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
  ) else (
    if exist ".venv\Scripts\rich4-pygame.exe" (
      ".venv\Scripts\rich4-pygame.exe"
      if errorlevel 1 goto :failed
      goto :done
    )
    echo Neither uv nor an installed Pygame environment was found.
    echo Install uv, then follow the one-time setup in pygame\README.md.
    goto :failed
  )
)

"%UV%" run --project "%CD%" --python 3.12 rich4-pygame
if errorlevel 1 goto :failed

:done
popd
exit /b 0

:failed
echo.
echo Game launch failed. Check the messages above.
pause
popd
exit /b 1
