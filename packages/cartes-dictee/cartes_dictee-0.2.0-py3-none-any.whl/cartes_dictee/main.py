"""
Reads CSV files to create printable game cards (A4 format).

Format du CSV attendu :

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
"""

import csv
import argparse
import webbrowser
from pathlib import Path


class Card:
    """Represents a dictation card with a word and a color."""

    def __init__(self, word, color):
        self.word = word.strip()
        self.color = color.lower()

    def to_html(self):
        """Generates the HTML for this card."""
        template = '    <div class="card {color}">\n        <span>{word}</span>\n    </div>'
        return template.format(color=self.color, word=self.word)

    def __repr__(self):
        return f"Card(word='{self.word}', color='{self.color}')"


def read_cards_csv(file):
    """Reads the CSV file and returns a list of cards."""
    cards = []

    try:
        with open(file, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                words = row["Mots"].split(", ")
                color = row["Groupe"]

                # Create a card for each word
                for word in words:
                    if word.strip():  # Make sure the word is not empty
                        cards.append(Card(word, color))

    except FileNotFoundError:
        print(f"Error: The file {file} does not exist.")
        return []
    except KeyError as e:
        print(f"Error: Missing column in CSV: {e}")
        return []

    return cards


def generate_cards_html(csv_file, html_file):
    """Generates an HTML file with colored cards for A4 printing."""

    # CSS for cards and printing
    css = """
    <style>
        @page {
            size: A4;
            margin: 10mm;
        }
        
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        
        .sheet {
            display: flex;
            flex-wrap: wrap;
            gap: 5mm;
            page-break-after: always;
            padding: 10mm;
        }
        
        .card {
            width: 70mm;
            height: 50mm;
            border: 4px solid #333;
            border-radius: 8px;
            padding: 5mm;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            box-sizing: border-box;
            background-color: white;
            color: #333;
            break-inside: avoid;
            page-break-inside: avoid;
        }
        
        .jaune { border-color: #e6ac00; }
        .vert { border-color: #009900; }
        .violet { border-color: #7700aa; }
        .gris { border-color: #666666; }
        
        @media print {
            .card {
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }
        }
    </style>
    """

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cartes de dictée</title>
    {css}
</head>
<body>
"""

    # Read CSV file and create cards
    cards = read_cards_csv(csv_file)
    if not cards:
        return

    # Generate sheets (12 cards per page)
    cards_per_sheet = 12

    for i in range(0, len(cards), cards_per_sheet):
        html_content += '<div class="sheet">\n'

        sheet_cards = cards[i : i + cards_per_sheet]

        # Add cards to the sheet
        for card in sheet_cards:
            html_content += card.to_html() + "\n"

        # Fill with empty cards if necessary
        missing_cards = cards_per_sheet - len(sheet_cards)
        for _ in range(missing_cards):
            empty_card = Card("", "gris")
            html_content += empty_card.to_html() + "\n"

        html_content += "</div>\n"

    html_content += """
</body>
</html>
"""

    # Save HTML file
    with open(html_file, "w", encoding="utf-8") as htmlfile:
        htmlfile.write(html_content)

    print(f"File {html_file} generated with {len(cards)} cards.")
    print("Opening the file in your default browser...")

    # Open the HTML file in the default browser
    webbrowser.open(f"file://{Path(html_file).resolve()}")
    print("You can now print (Ctrl+P / Cmd+P)")


def main():
    """Point d'entrée principal pour la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Generate dictation cards from a CSV file"
    )
    parser.add_argument("csv_file", help="CSV file containing words and groups")

    args = parser.parse_args()

    # Generate output filename automatically
    basename = Path(args.csv_file).stem
    html_file = f"{basename}.html"

    generate_cards_html(args.csv_file, html_file)


if __name__ == "__main__":
    main()