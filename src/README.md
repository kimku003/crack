# API Security Scanner

## Important : Notice d'Utilisation Éthique

Cet outil est conçu à des fins de sécurité défensive. Il est destiné à être utilisé par les développeurs et les équipes de sécurité pour auditer **leurs propres applications et dépôts Git** afin de détecter et de prévenir les fuites de secrets et de clés API.

L'utilisation de cet outil pour scanner, tester ou attaquer des systèmes, applications ou dépôts pour lesquels vous n'avez pas une autorisation explicite est **illégale** et **contraire à l'éthique**. Les utilisateurs sont seuls responsables de leurs actions.

## Installation

Pour installer les dépendances du projet, utilisez votre gestionnaire de paquets Python préféré.

Avec `uv` ou `pip` :
```bash
pip install .
```

Avec `Poetry` :
```bash
poetry install
```

## Configuration

Avant de lancer l'application, vous devez configurer votre clé d'API Google Gemini pour que les validateurs de clés fonctionnent correctement.

1.  Naviguez vers le dossier `src/apikey_validator/`.
2.  Créez une copie du fichier `config.example.json` et renommez-la en `config.json`.
3.  Ouvrez `config.json` et remplacez `"VOTRE_CLE_API_GEMINI_ICI"` par votre véritable clé d'API.

Le fichier `config.json` est ignoré par Git pour garantir la sécurité de votre clé.

## Utilisation

Cet outil peut être utilisé via une interface graphique ou en ligne de commande.

### 1. Interface Graphique (GUI)

Pour lancer l'interface graphique de bureau :
```bash
flet run
# ou poetry run flet run
```

Pour lancer l'interface en tant qu'application web :
```bash
flet run --web
# ou poetry run flet run --web
```

### 2. Ligne de Commande (CLI)

L'outil fournit également une interface en ligne de commande puissante pour l'automatisation et l'intégration dans des scripts.

Utilisation de base :
```bash
python -m src.apikey_validator.cli <commande> [options]
```

**Commandes disponibles :**
*   `validate` : Valider une clé API complète.
*   `brute-force` : Deviner la fin d'une clé incomplète.
*   `dictionary` : Attaquer une clé avec une liste de mots.
*   `scan` : Scanner un répertoire local à la recherche de clés.
*   `scan-git` : Scanner l'historique d'un dépôt Git local.
*   `scan-remote-git` : Cloner et scanner un dépôt Git distant.
*   `scan-entropy` : Scanner un répertoire pour des chaînes à haute entropie.

Pour obtenir de l'aide sur une commande spécifique, utilisez l'option `-h` ou `--help`.
```bash
python -m src.apikey_validator.cli scan -h
```

## Build de l'application

Pour créer un exécutable de l'interface graphique pour votre plateforme, utilisez la commande `flet build`.

### Android
```bash
flet build apk -v
```

### iOS
```bash
flet build ipa -v
```

### macOS
```bash
flet build macos -v
```

### Linux
```bash
flet build linux -v
```

### Windows
```bash
flet build windows -v
```
