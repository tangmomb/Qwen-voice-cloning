param(
    [string]$RefsDir = "generated_refs",
    [ValidateSet("tiny", "base", "small", "medium", "large")]
    [string]$WhisperModel = "small"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $ProjectRoot ".venv-qwen\Scripts\python.exe"
$RefsRoot = Join-Path $ProjectRoot $RefsDir

if (-not (Test-Path $PythonExe)) {
    throw "Environnement Qwen introuvable. Lance d'abord .\scripts\setup_qwen.ps1"
}

Get-ChildItem $RefsRoot -Filter *.wav -File | ForEach-Object {
    & $PythonExe -m whisper $_.FullName --language French --model $WhisperModel --output_dir $RefsRoot --output_format txt
}
