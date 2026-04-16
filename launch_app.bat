@echo off
setlocal

cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ui_qwen.ps1"

if errorlevel 1 (
    echo.
    echo L'app s'est arretee avec une erreur.
    pause
)
