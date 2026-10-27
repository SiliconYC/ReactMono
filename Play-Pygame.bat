@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Double-click from the repository root to run the Windows Pygame version.
call "%~dp0pygame\start-game.bat" %*
exit /b %errorlevel%
