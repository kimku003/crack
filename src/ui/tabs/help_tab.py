"""
Onglet d'aide et documentation
"""

import flet as ft
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ui_theme import (
    Colors, Spacing, create_card, create_text
)


def create_help_tab() -> ft.Tab:
    """
    Crée l'onglet d'aide avec la documentation utilisateur
    
    Returns:
        Tab configuré pour l'aide
    """
    
    return ft.Tab(
        text="Aide",
        icon=ft.Icons.HELP_OUTLINE,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    create_text(
                        "Guide d'utilisation de l'Outil de Sécurité pour Clés API", 
                        size=24, 
                        weight=ft.FontWeight.BOLD
                    ),
                    create_text(
                        "Cet outil vous permet de valider, trouver et récupérer des clés API potentielles à des fins de sécurité.", 
                        size=16
                    ),
                    ft.Divider(),
                    
                    create_text("Onglet 'Validation':", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Saisissez une clé API et sélectionnez un service pour vérifier si la clé est valide pour ce service.", 
                        size=16
                    ),
                    create_text("- Utile pour tester rapidement une clé individuelle.", size=16),
                    ft.Divider(),
                    
                    create_text("Onglet 'Scan Fichiers':", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Sélectionnez un répertoire à scanner. L'outil recherchera des clés API potentielles dans les fichiers texte.", 
                        size=16
                    ),
                    create_text("- Les clés trouvées seront validées et les résultats affichés.", size=16),
                    ft.Divider(),
                    
                    create_text("Onglet 'Devinette':", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "  - 'Brute-force': Tente de compléter une clé partielle en ajoutant des caractères aléatoires jusqu'à une certaine profondeur.", 
                        size=16
                    ),
                    create_text(
                        "  - 'Attaque par Dictionnaire': Tente de compléter une clé partielle en utilisant une liste de mots fournie.", 
                        size=16
                    ),
                    create_text("- Nécessite une clé partielle et un service cible.", size=16),
                    ft.Divider(),
                    
                    create_text("Limitations:", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Le scan de fichiers est limité aux fichiers textes. Les fichiers binaires ne sont pas scannés.", 
                        size=16
                    ),
                    create_text("- Le scan Git peut prendre du temps sur les grands dépôts.", size=16),
                    create_text(
                        "- L'attaque par dictionnaire dépend de la qualité de la liste de mots fournie.", 
                        size=16
                    ),
                    ft.Divider(),
                    
                    create_text("Dépannage:", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Si vous rencontrez des problèmes avec la configuration de la clé API Gemini, vérifiez que vous avez correctement créé le fichier config.json et que la clé est valide.", 
                        size=16
                    ),
                    create_text(
                        "- Si vous rencontrez des erreurs d'installation des dépendances, assurez-vous d'utiliser une version de Python compatible et essayez d'installer les dépendances avec pip ou Poetry.", 
                        size=16
                    ),
                    ft.Divider(),
                    
                    create_text("Onglet 'Scan Git':", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Scanne l'historique d'un dépôt Git local à la recherche de clés API exposées dans les commits.", 
                        size=16
                    ),
                    create_text("- Très utile pour identifier les fuites passées.", size=16),
                    ft.Divider(),
                    
                    create_text("Onglet 'Scan Entropie':", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "- Scanne un répertoire pour trouver des chaînes de caractères à haute entropie, qui pourraient être des secrets.", 
                        size=16
                    ),
                    create_text(
                        "- Un seuil d'entropie peut être défini. Les résultats nécessitent une vérification manuelle.", 
                        size=16
                    ),
                ], 
                spacing=Spacing.SM, 
                horizontal_alignment=ft.CrossAxisAlignment.START, 
                scroll=ft.ScrollMode.ALWAYS
                ),
                padding=Spacing.XL
            ),
            expand=True,
            alignment=ft.alignment.center
        )
    )