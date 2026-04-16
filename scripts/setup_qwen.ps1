$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPath = Join-Path $ProjectRoot ".venv-qwen"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    py -3.10 -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip setuptools wheel
& $PythonExe -m pip install -r (Join-Path $ProjectRoot "requirements.txt")

Write-Host "Qwen3-TTS est pret dans .venv-qwen"
Write-Host "Lance l'app avec launch_app.bat"
