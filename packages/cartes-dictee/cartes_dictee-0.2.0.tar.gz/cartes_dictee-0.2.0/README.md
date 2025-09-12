# Cartes de dictée

Génère des cartes de dictée imprimables à partir d'un fichier CSV.

## Aperçu

![Aperçu des cartes générées](preview.png)

## Installation

```bash
uvx cartes-dictee dictee1.csv
```

## Format du fichier CSV

Le fichier CSV doit contenir deux colonnes : `Mots` et `Groupe`.

```csv
Mots;Groupe
le peintre, la couleur, le bleu;Jaune
primaire;Jaune
une forme, un carré, un rond;Vert
droit, courbe;Vert
le centre, la toile, le fond;Violet
se mélanger, chercher;Violet
```

## Utilisation

```bash
cartes-dictee fichier.csv
```

Le fichier HTML généré s'ouvre automatiquement dans votre navigateur, prêt pour l'impression (Cmd+P).

- Format A4, 12 cartes par page (70mm × 50mm)
- Cartes colorées selon les groupes
- Police 24px pour une bonne lisibilité

## Licence

MIT
