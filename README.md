# Clone Voice 6 - Qwen3-TTS

Projet de voice cloning centre uniquement sur `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.

Qwen a donne les meilleurs resultats dans les tests locaux. Les autres backends ont ete retires pour garder le projet simple.

## Installation

```powershell
.\scripts\setup_qwen.ps1
```

## Preparer une reference

Place une voix source dans `voices/`, puis genere et transcris des extraits courts:

```powershell
.\scripts\prepare_qwen_refs.ps1
.\scripts\transcribe_qwen_refs.ps1
```

Les references sont dans `outputs\qwen_refs\`.

## Generer une voix

```powershell
.\scripts\clone_qwen.ps1 `
  -ReferenceAudio "outputs\qwen_refs\simon_bs_roformer_mt_81_vocals.wav" `
  -ReferenceText "de mon activité présentation de la gestion de projet." `
  -Text "Bonjour, ceci est un essai de clonage vocal avec Qwen trois T T S en français." `
  -OutputFile "simon_qwen.wav"
```

Les sorties sont dans `outputs\qwen\`.

## Trouver le meilleur extrait

```powershell
.\scripts\qwen_shootout.ps1
```

Le shootout decoupe plusieurs references, les transcrit, genere la meme phrase avec chacune, puis ecrit un `manifest.csv` dans `outputs\qwen_shootout\`.

## Conseils

- Utilise 3 a 5 secondes de reference claire.
- Corrige `ReferenceText` a la main si Whisper se trompe.
- Evite les artefacts de separation voix/musique si possible.
- Garde une phrase cible naturelle pour juger la voix.

Voir aussi `README_QWEN.md` pour les options avancees.
