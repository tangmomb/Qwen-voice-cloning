# Clone Voice - Qwen/Qwen3-TTS-12Hz-1.7B-Base

![App locale](https://img.shields.io/badge/app-locale-2ea44f)
![Windows](https://img.shields.io/badge/windows-ready-0078d4)
![Qwen3--TTS](https://img.shields.io/badge/model-Qwen3--TTS--12Hz--1.7B--Base-8a63d2)
![Audio rating](https://img.shields.io/badge/explorer-rating-f5b700)

Application locale de clonage vocal avec `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.

Ce projet s'utilise uniquement avec l'app web locale. Les scripts servent seulement a installer et lancer l'app.

---

## Installation

Ouvre PowerShell dans le dossier du projet, puis lance:

```powershell
.\scripts\setup_qwen.ps1
```

Cette commande prepare l'environnement Python et installe les dependances necessaires.

## Lancement

Double-clique sur:

```text
launch_app.bat
```

Tu peux aussi lancer l'app depuis PowerShell avec:

```powershell
.\scripts\ui_qwen.ps1
```

Le navigateur doit s'ouvrir automatiquement. Si rien ne s'ouvre, va sur:

```text
http://127.0.0.1:7860
```

---

## Utilisation

| Etape | Action |
| --- | --- |
| 1 | Ajoute un fichier audio dans `Audio source`. |
| 2 | Choisis le `Nombre de points de reference`. |
| 3 | Choisis `CPU` ou `GPU`. |
| 4 | Ecris le texte a faire dire dans `Texte a dire`. |
| 5 | Clique sur `Generer`. |
| 6 | Ecoute chaque sortie dans son lecteur audio. |
| 7 | Mets une note de 1 a 5 etoiles. |
| 8 | Clique sur `Enregistrer la note`. |

Chaque point de reference produit deux variantes:

- une sortie basee sur une reference courte de 3.2 secondes;
- une sortie basee sur une reference longue de 6.4 secondes.

> Exemple: avec 3 points de reference, l'app peut produire jusqu'a 6 lecteurs audio a ecouter et noter.

## Conseils

| A faire | A eviter |
| --- | --- |
| Utiliser une voix claire et seule. | Musique forte ou bruit de fond. |
| Commencer avec 1 ou 2 points. | Trop de points pour un premier test. |
| Utiliser un texte naturel et court. | Texte tres long pour comparer les voix. |
| Passer en `CPU` si la VRAM manque. | Insister en `GPU` apres une erreur memoire. |

---

## Resultats

L'app genere un WAV original pour chaque sortie, puis cree une copie MP3 a cote.

La copie MP3 sert a l'ecoute dans l'app et a la notation avec les etoiles, car l'Explorateur Windows accepte mieux la propriete `Notation` sur MP3 que sur WAV. L'app ecrit la note dans les metadonnees Windows et dans le tag ID3 utilise par les etoiles des proprietes du fichier.

| Dossier | Contenu |
| --- | --- |
| `inputs/` | Audios sources copies. |
| `generated_refs/` | Extraits de reference crees automatiquement. |
| `outputs/qwen/` | WAV originaux, copies MP3 notables et manifest. |
| `logs/` | Erreurs techniques si l'app plante. |

Tu n'as pas besoin de modifier ces dossiers a la main pour utiliser l'app.

## En Cas De Probleme

Ferme le terminal qui lance l'app, puis relance:

```text
launch_app.bat
```

Si une erreur s'affiche dans l'app, regarde le dernier fichier dans `logs/`.
