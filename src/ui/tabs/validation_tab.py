"""
Onglet de validation des clés API
"""

import flet as ft
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ui_theme import (
    Colors, Spacing, create_button, create_dropdown, create_card,
    create_responsive_row, create_text
)
from ui_extensions import create_simple_validated_text_field, MaterialIcons


def create_validation_tab(patterns: dict, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de validation des clés API
    
    Args:
        patterns: Dictionnaire des patterns de validation
        page: Page Flet
        
    Returns:
        Tab configuré pour la validation
    """
    
    # Composants de l'onglet
    api_key_input = create_simple_validated_text_field(
        label="Clé API", 
        password=True, 
        can_reveal_password=True
    )
    # Amélioration accessibilité : ajout de semantic_label
    api_key_input.semantic_label = "Champ de saisie pour la clé API à valider"
    
    service_dropdown = create_dropdown(
        label="Service", 
        options=[ft.dropdown.Option(key) for key in patterns.keys()]
    )
    service_dropdown.semantic_label = "Sélection du service pour la validation"
    
    validate_button = create_button(
        text="Valider", 
        icon=MaterialIcons.SECURITY, 
        hierarchy="primary"
    )
    
    result_text = create_text("", size=16, weight=ft.FontWeight.BOLD)

    def validate_key_click(e):
        """Gestionnaire de validation de clé"""
        key = api_key_input.value
        service = service_dropdown.value
        
        # Validation des entrées avec feedback amélioré
        if not key:
            api_key_input.error_text = "Clé API requise"
            page.update()
            return
        elif len(key) < 10:
            api_key_input.error_text = "Clé API trop courte (minimum 10 caractères)"
            page.update()
            return
        else:
            api_key_input.error_text = None
            
        if not service:
            result_text.value = "Veuillez sélectionner un service."
            result_text.color = Colors.WARNING
            page.update()
            return

        try:
            validator = patterns[service]["validator"]
            is_valid = validator(key, silencieux=True)
            if is_valid:
                result_text.value = f"SUCCÈS : La clé pour {service} est VALIDE."
                result_text.color = Colors.SUCCESS
            else:
                result_text.value = f"ÉCHEC : La clé pour {service} est INVALIDE."
                result_text.color = Colors.ERROR
        except Exception as ex:
            result_text.value = f"ERREUR : {str(ex)}"
            result_text.color = Colors.ERROR
        
        page.update()
    
    validate_button.on_click = validate_key_click

    return ft.Tab(
        text="Validation",
        icon=MaterialIcons.KEY,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 8, "lg": 6}, controls=[api_key_input]),
                        ft.Column(col={"sm": 12, "md": 4, "lg": 3}, controls=[service_dropdown]),
                    ]),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "lg": 3}, controls=[validate_button]),
                    ]),
                    create_responsive_row([
                        ft.Column(col=12, controls=[result_text]),
                    ]),
                ], spacing=Spacing.LG),
                padding=Spacing.XL
            ),
            alignment=ft.alignment.center
        )
    )