$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPath = Join-Path $ProjectRoot ".venv-qwen"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    py -3.10 -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip setuptools wheel
& $PythonExe -m pip install -U qwen-tts soundfile openai-whisper

Write-Host "Qwen3-TTS est pret dans .venv-qwen"
Write-Host "Generation: .\scripts\clone_qwen.ps1 -ReferenceAudio outputs\qwen_refs\voice.wav -ReferenceText '...' -Text 'Bonjour'"
