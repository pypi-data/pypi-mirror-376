# Cartes de dictée

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ce programme génère des cartes de dictée imprimables (format A4) à partir d'un fichier CSV contenant des listes de mots et leur groupe de couleur.

## 🚀 Installation

### Avec uv (recommandé)
```bash
# Installation globale
uv tool install cartes-dictee

# Ou utilisation directe
uvx cartes-dictee dictee1.csv
```

### Depuis PyPI
```bash
pip install cartes-dictee
```

### Depuis les sources avec uv
```bash
git clone https://github.com/votrenom/cartes-dictee.git
cd cartes-dictee
uv sync --no-dev
```

## 📖 Utilisation

### En ligne de commande
```bash
cartes-dictee dictee1.csv
```

### En tant que module Python
```python
from cartes_dictee import generate_cards_html

generate_cards_html("dictee1.csv", "mes_cartes.html")
```

## 📋 Format du fichier CSV

Le fichier CSV doit contenir deux colonnes : `Mots` et `Groupe`.

Exemple de fichier CSV (`dictee1.csv`) :

```csv
Mots;Groupe
le peintre, la couleur, le bleu, le jaune, le rouge, le vert, le marron, l'orange, le violet, le rose, le blanc, le noir;Jaune
primaire;Jaune
utiliser;Jaune
une forme, un carré, un rond, un triangle, la ligne;Vert
droit, courbe;Vert
peindre;Vert
comme, ainsi que;Vert
le centre, la toile, le fond, l'artiste, la réalité;Violet
se mélanger, chercher, montrer;Violet
plusieurs;Violet
```

## ✨ Fonctionnalités

- ✅ **Format A4** optimisé pour l'impression
- ✅ **Cartes colorées** selon les groupes (Jaune, Vert, Violet, Gris)
- ✅ **Ouverture automatique** dans le navigateur
- ✅ **12 cartes par page** (3×4)
- ✅ **Dimensions précises** : 70mm × 50mm par carte
- ✅ **Police grande** (24px) pour une bonne lisibilité
- ✅ **Protection anti-coupure** lors de l'impression

## 🎯 Utilisation

Le fichier HTML généré porte le même nom que le fichier CSV, mais avec l'extension `.html`.
Par exemple : `dictee1.csv` → `dictee1.html`

Le fichier s'ouvre automatiquement dans votre navigateur par défaut, prêt pour l'impression (Ctrl+P / Cmd+P).

## 🏗️ Développement

```bash
git clone https://github.com/votrenom/cartes-dictee.git
cd cartes-dictee
uv sync --no-dev
```

### Construire le paquet
```bash
uv build
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
