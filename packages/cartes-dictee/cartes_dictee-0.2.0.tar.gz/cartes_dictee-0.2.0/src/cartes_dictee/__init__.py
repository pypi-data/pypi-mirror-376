"""
Cartes de dictée - Génère des cartes de dictée imprimables à partir de fichiers CSV.
"""

from .main import Card, read_cards_csv, generate_cards_html, main

__version__ = "0.2.0"
__all__ = ["Card", "read_cards_csv", "generate_cards_html", "main"]