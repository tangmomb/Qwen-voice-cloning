param(
    [string]$VoiceDir = "voices",
    [string]$RefsDir = "outputs\qwen_shootout_refs",
    [string]$OutputDir = "outputs\qwen_shootout",
    [string]$Text = "Salut, c'est moi. On dirait que cette fois la voix est plus stable et plus naturelle.",
    [int[]]$StartSeconds = @(20, 45, 90),
    [double[]]$Durations = @(3.2, 5.0),
    [ValidateSet("tiny", "base", "small", "medium", "large")]
    [string]$WhisperModel = "small",
    [int]$MaxNewTokens = 768
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VoiceRoot = Join-Path $ProjectRoot $VoiceDir
$RefsRoot = Join-Path $ProjectRoot $RefsDir
$OutRoot = Join-Path $ProjectRoot $OutputDir
$PythonExe = Join-Path $ProjectRoot ".venv-qwen\Scripts\python.exe"
$CloneScript = Join-Path $PSScriptRoot "clone_qwen.ps1"

if (-not (Test-Path $PythonExe)) {
    throw "Environnement Qwen introuvable. Lance d'abord .\scripts\setup_qwen.ps1"
}

if (-not (Test-Path $VoiceRoot)) {
    throw "Dossier voix introuvable: $VoiceRoot"
}

New-Item -ItemType Directory -Force -Path $RefsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

$manifestPath = Join-Path $OutRoot "manifest.csv"
"voice,start_seconds,duration_seconds,reference_audio,reference_text,output_audio" | Set-Content -Path $manifestPath -Encoding UTF8

Get-ChildItem $VoiceRoot -File | ForEach-Object {
    $voiceFile = $_
    $voiceName = [IO.Path]::GetFileNameWithoutExtension($voiceFile.Name)

    foreach ($start in $StartSeconds) {
        foreach ($duration in $Durations) {
            $durationTag = [string]$duration
            $durationTag = $durationTag.Replace(",", ".").Replace(".", "p")
            $refName = "${voiceName}_s${start}_d${durationTag}.wav"
            $refPath = Join-Path $RefsRoot $refName
            $txtPath = [IO.Path]::ChangeExtension($refPath, ".txt")
            $outName = "${voiceName}_s${start}_d${durationTag}_qwen.wav"
            $outPath = Join-Path $OutRoot $outName

            if (-not (Test-Path $refPath)) {
                ffmpeg -y -ss $start -t $duration -i $voiceFile.FullName -af "loudnorm,apad=pad_dur=0.2" -ar 24000 -ac 1 $refPath
            }

            if (-not (Test-Path $txtPath)) {
                & $PythonExe -m whisper $refPath --language French --model $WhisperModel --output_dir $RefsRoot --output_format txt
            }

            $referenceText = (Get-Content -Path $txtPath -Raw -Encoding UTF8).Trim()
            if (-not $referenceText) {
                Write-Warning "Transcription vide pour $refPath, generation ignoree."
                continue
            }

            if (-not (Test-Path $outPath)) {
                & $CloneScript `
                    -ReferenceAudio $refPath `
                    -ReferenceText $referenceText `
                    -Text $Text `
                    -OutputDir $OutputDir `
                    -OutputFile $outName `
                    -MaxNewTokens $MaxNewTokens
            }

            $safeText = $referenceText.Replace('"', '""').Replace("`r", " ").Replace("`n", " ")
            """$voiceName"",$start,$duration,""$refPath"",""$safeText"",""$outPath""" | Add-Content -Path $manifestPath -Encoding UTF8
        }
    }
}

Write-Host "Shootout Qwen termine: $OutRoot"
Write-Host "Manifest: $manifestPath"
