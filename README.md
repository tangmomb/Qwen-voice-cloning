# Clone Voice - Qwen/Qwen3-TTS-12Hz-1.7B-Base

Application locale de clonage vocal avec `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.

Ce projet s'utilise uniquement avec l'app web locale. Les scripts servent seulement a installer et lancer l'app.

## Installation

Ouvre PowerShell dans le dossier du projet.

Puis lance l'installation:

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

Le navigateur doit s'ouvrir automatiquement.

Si rien ne s'ouvre, va manuellement sur:

```text
http://127.0.0.1:7860
```

## Utilisation

Dans l'app:

1. Ajoute un fichier audio dans `Audio source`.
2. Choisis le `Nombre de points de reference`.
3. Choisis le mode de calcul:
   - `CPU`: plus lent, plus compatible;
   - `GPU`: plus rapide si la carte graphique et CUDA sont disponibles.
4. Ecris le texte a faire dire dans `Texte a dire`.
5. Clique sur `Generer`.
6. Ecoute chaque sortie dans son lecteur audio.
7. Mets une note de 1 a 5 etoiles.
8. Clique sur `Enregistrer la note` pour ecrire la note dans la propriete `Notation` de l'Explorateur Windows.

Chaque point de reference produit deux variantes:

- une sortie basee sur une reference courte de 3.2 secondes;
- une sortie basee sur une reference longue de 6.4 secondes.

Exemple: avec 3 points de reference, l'app peut produire jusqu'a 6 lecteurs audio a ecouter et noter.

## Conseils Pour De Bons Resultats

- Utilise un audio clair, avec une voix seule si possible.
- Evite la musique forte, les bruits de fond, l'echo et les voix superposees.
- Commence avec 1 ou 2 points de reference pour tester rapidement.
- Augmente le nombre de points si tu veux comparer plusieurs rendus.
- Si le GPU affiche une erreur de memoire, repasse en `CPU` ou baisse le nombre de points de reference.
- Utilise un texte naturel et pas trop long pour les premiers essais.

## Ou Trouver Les Resultats

L'app genere un WAV original pour chaque sortie, puis cree une copie MP3 a cote.

La copie MP3 sert a l'ecoute dans l'app et a la notation avec les etoiles, car l'Explorateur Windows accepte mieux la propriete `Notation` sur MP3 que sur WAV. L'app ecrit la note dans les metadonnees Windows et dans le tag ID3 utilise par les etoiles des proprietes du fichier.

Elle range aussi automatiquement les fichiers dans le projet:

- `inputs/` contient les audios sources copies;
- `generated_refs/` contient les extraits de reference crees automatiquement;
- `outputs/qwen/` contient les WAV originaux, les copies MP3 notables et le manifest;
- `logs/` contient les erreurs techniques si l'app plante.

Tu n'as pas besoin de modifier ces dossiers a la main pour utiliser l'app.

## En Cas De Probleme

Ferme le terminal qui lance l'app, puis relance:

```text
launch_app.bat
```

Si une erreur s'affiche dans l'app, regarde le dernier fichier dans `logs/`.
