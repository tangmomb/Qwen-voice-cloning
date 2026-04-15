# Clone Voice 6 - Qwen3-TTS

Backend experimental pour `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.

Ce modele Base supporte le voice cloning avec:

- un court audio de reference;
- la transcription exacte de cet audio;
- un texte cible;
- `language="French"` pour nos essais.

## Installation

```powershell
.\scripts\setup_qwen.ps1
```

## Preparer les references

```powershell
.\scripts\prepare_qwen_refs.ps1
.\scripts\transcribe_qwen_refs.ps1
```

Les extraits sont crees dans `outputs\qwen_refs\`.

## Generer

```powershell
.\scripts\clone_qwen.ps1 `
  -ReferenceAudio "outputs\qwen_refs\simon_bs_roformer_mt_81_vocals.wav" `
  -ReferenceText "Transcription exacte de l'extrait." `
  -Text "Bonjour, ceci est un essai avec Qwen trois T T S en français." `
  -OutputFile "simon_qwen.wav"
```

Par defaut, le script force CPU + float32. C'est lent mais plus compatible. Si tu veux tenter la RTX 2080:

```powershell
.\scripts\clone_qwen.ps1 `
  -ReferenceAudio "outputs\qwen_refs\simon_bs_roformer_mt_81_vocals.wav" `
  -ReferenceText "Transcription exacte de l'extrait." `
  -Text "Bonjour depuis Qwen." `
  -OutputFile "simon_qwen_cuda.wav" `
  -Device cuda:0 `
  -DType float16 `
  -Attention sdpa
```

## Notes

La fiche officielle recommande Python 3.12, mais le package `qwen-tts` s'installe ici en Python 3.10. La premiere generation telecharge plusieurs Go de poids.

## Comparer plusieurs references

Pour trouver le meilleur extrait de reference par voix:

```powershell
.\scripts\qwen_shootout.ps1
```

Le script cree plusieurs references dans `outputs\qwen_shootout_refs\`, genere les audios dans `outputs\qwen_shootout\`, puis ecrit un `manifest.csv` avec les timestamps, durees, transcriptions et sorties.
