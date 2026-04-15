param(
    [Parameter(Mandatory = $true)]
    [string]$ReferenceAudio,

    [Parameter(Mandatory = $true)]
    [string]$ReferenceText,

    [string]$Text = "",

    [string]$TextFile = "",

    [string]$OutputFile = "qwen_clone.wav",

    [string]$OutputDir = "outputs\qwen",

    [string]$Language = "French",

    [ValidateSet("cpu", "auto", "cuda", "cuda:0")]
    [string]$Device = "cpu",

    [ValidateSet("float32", "float16", "bfloat16")]
    [string]$DType = "float32",

    [ValidateSet("eager", "sdpa", "flash_attention_2")]
    [string]$Attention = "eager",

    [int]$MaxNewTokens = 1024,

    [switch]$XVectorOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $ProjectRoot ".venv-qwen\Scripts\python.exe"
$App = Join-Path $ProjectRoot "app\qwen_clone.py"
$OutputPath = Join-Path $ProjectRoot (Join-Path $OutputDir $OutputFile)

if (-not (Test-Path $PythonExe)) {
    throw "Environnement Qwen introuvable. Lance d'abord .\scripts\setup_qwen.ps1"
}

$ArgsList = @(
    $App,
    "--ref-audio", $ReferenceAudio,
    "--ref-text", $ReferenceText,
    "--output", $OutputPath,
    "--language", $Language,
    "--device", $Device,
    "--dtype", $DType,
    "--attn", $Attention,
    "--max-new-tokens", "$MaxNewTokens"
)

if ($TextFile) {
    $ArgsList += @("--text-file", $TextFile)
} else {
    $ArgsList += @("--text", $Text)
}

if ($XVectorOnly) {
    $ArgsList += "--x-vector-only"
}

& $PythonExe @ArgsList
