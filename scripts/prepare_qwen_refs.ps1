param(
    [string]$VoiceDir = "inputs",
    [string]$OutputDir = "generated_refs",
    [int]$StartSeconds = 20,
    [double]$DurationSeconds = 3.2
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VoiceRoot = Join-Path $ProjectRoot $VoiceDir
$OutRoot = Join-Path $ProjectRoot $OutputDir

if (-not (Test-Path $VoiceRoot)) {
    throw "Dossier voix introuvable: $VoiceRoot"
}

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

Get-ChildItem $VoiceRoot -File | ForEach-Object {
    $safeName = [IO.Path]::GetFileNameWithoutExtension($_.Name)
    $outPath = Join-Path $OutRoot "$safeName.wav"
    ffmpeg -y -ss $StartSeconds -t $DurationSeconds -i $_.FullName -af "loudnorm,apad=pad_dur=0.2" -ar 24000 -ac 1 $outPath
    Write-Host "Reference Qwen: $outPath"
}
