"""Package cartes_dictee - Génère des cartes de dictée imprimables."""

__version__ = "0.1.0"

from .cartes_dictee import Card, read_cards_csv, generate_cards_html, main

__all__ = ["Card", "read_cards_csv", "generate_cards_html", "main"]