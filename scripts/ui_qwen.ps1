param(
    [int]$Port = 7860,
    [string]$HostName = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $ProjectRoot ".venv-qwen\Scripts\python.exe"
$App = Join-Path $ProjectRoot "app\qwen_ui.py"

if (-not (Test-Path $PythonExe)) {
    throw "Environnement Qwen introuvable. Lance d'abord .\scripts\setup_qwen.ps1"
}

$env:GRADIO_SERVER_NAME = $HostName
$env:GRADIO_SERVER_PORT = "$Port"
& $PythonExe $App
