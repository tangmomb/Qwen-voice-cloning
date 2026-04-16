# Pistes d'amelioration du voice cloning

Le projet actuel garde Qwen3-TTS comme backend principal, car il a donne les meilleurs resultats rapides avec les voix testees.

## Objectif

Passer d'un clonage zero-shot avec quelques secondes de reference a un clonage plus stable base sur 10 a 30 minutes de voix propre.

## Ordre de priorite

### 1. GPT-SoVITS fine-tune

Meilleur prochain test pratique.

- Bon compromis qualite / facilite.
- Workflow pense pour segmentation, transcription et fine-tuning.
- Peut ameliorer la similarite avec quelques minutes, puis davantage avec 10 a 30 minutes propres.
- A tester en premier si on veut un vrai clone entraine.

Lien: https://github.com/RVC-Boss/GPT-SoVITS

### 2. Qwen3-TTS + RVC

Approche hybride interessante:

- Qwen genere une diction/prosodie correcte.
- RVC convertit le timbre vers la voix cible.
- Souvent bon pour renforcer l'identite vocale.
- Demande un dataset voix propre de 10 a 30 minutes.

Lien: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

### 3. Fish Speech / Fish Audio S2

Modele moderne potentiellement tres qualitatif.

- Multilingue.
- Bon clonage vocal court.
- Plus lourd a installer et a faire tourner.
- Licence et ressources GPU a verifier avant d'investir du temps.

Lien: https://github.com/fishaudio/fish-speech

### 4. CosyVoice

Stack TTS multilingue avancee.

- Supporte plusieurs langues dont le francais.
- Interessant pour une approche plus recherche / systeme complet.
- Probablement plus lourd que GPT-SoVITS pour notre besoin immediat.

Lien: https://github.com/FunAudioLLM/CosyVoice

### 5. XTTS-v2 fine-tune

Option historique et pratique, mais moins prioritaire.

- Fine-tuning possible avec quelques minutes a 30 minutes.
- Ecosysteme connu.
- A garder en fallback si GPT-SoVITS/RVC ne donnent pas satisfaction.

Lien: https://github.com/coqui-ai/TTS

## Dataset ideal

Pour passer un cap, il faut creer un vrai dataset voix:

- 10 a 30 minutes de voix seule.
- Pas de musique, pas de bruit de fond.
- Eviter les artefacts de separation type UVR/RoFormer si possible.
- Segments de 3 a 10 secondes.
- Volume homogene.
- Transcriptions propres.
- Pas de phrases coupees en plein mot.
- Prosodie proche de l'usage cible.

## Strategie recommandee

1. Garder Qwen3-TTS comme baseline.
2. Construire un dataset propre de la voix cible.
3. Tester GPT-SoVITS fine-tune.
4. Tester RVC en conversion sur des sorties Qwen.
5. Comparer:
   - similarite de voix;
   - naturel;
   - stabilite sur textes longs;
   - accents / prononciation francaise;
   - temps de generation.

## Contraintes machine

Machine actuelle:

- RTX 2080 avec 8 Go VRAM.
- Environ 32 Go RAM.

Implications:

- Qwen3-TTS CPU fonctionne.
- GPT-SoVITS/RVC peuvent probablement se tenter localement.
- Fish Speech et CosyVoice fine-tune risquent d'etre plus confortables sur cloud GPU.

## Prochaine action concrete

Preparer un dossier dataset:

```text
dataset/
  raw/
  segments/
  transcripts/
  metadata.csv
```

Puis ajouter un script de segmentation/transcription pour produire des clips propres reutilisables par GPT-SoVITS ou RVC.
