"""
Onglet de test manuel des clés API
"""

import os
import threading
import flet as ft
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ui_theme import (
    Colors, Spacing, create_button, create_text_field, create_card,
    create_responsive_row, create_text
)
from ui_extensions import MaterialIcons
from apikey_validator import core


def create_test_tab(patterns: dict, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de test manuel des clés API
    
    Args:
        patterns: Dictionnaire des patterns de validation
        page: Page Flet
        
    Returns:
        Tab configuré pour les tests manuels
    """
    
    # Composants de l'onglet
    test_api_key_input = create_text_field(
        label="Clé API à tester (Gemini ou OpenAI)", 
        password=True, 
        can_reveal_password=True
    )
    test_api_key_input.semantic_label = "Clé API à tester avec l'API réelle"
    
    test_service_dropdown = ft.Dropdown(
        label="Service à tester",
        options=[ft.dropdown.Option("Gemini"), ft.dropdown.Option("OpenAI")],
        value="Gemini",
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
    )
    test_service_dropdown.semantic_label = "Service à utiliser pour le test"
    
    test_result_text = create_text("", size=16, weight=ft.FontWeight.BOLD)
    test_button = create_button(
        "Tester la clé avec l'API", 
        icon=MaterialIcons.PLAY, 
        hierarchy="primary"
    )

    def run_gemini_test(api_key):
        """Teste une clé Gemini avec l'API réelle"""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": "What is the capital of France?"}
                    ]
                }
            ]
        }
        try:
            r = requests.post(url, headers=headers, json=data, timeout=15)
            if r.status_code == 200 and "candidates" in r.json():
                response_json = r.json()
                # Extraire la réponse générée par Gemini
                try:
                    answer = response_json["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    answer = "Réponse non trouvée dans la réponse API."
                return f"Clé Gemini VALIDE\\nRéponse Gemini : {answer}"
            elif r.status_code == 401:
                return "Clé Gemini INVALIDE ou non autorisée"
            elif r.status_code == 429:
                return "Limite de requêtes Gemini atteinte"
            else:
                return f"Erreur Gemini: {r.status_code} - {r.text}"
        except requests.exceptions.RequestException as e:
            return f"Erreur lors de l'appel Gemini: {e}"

    def test_api_key(e):
        """Gestionnaire de test de clé API"""
        key = test_api_key_input.value
        service = test_service_dropdown.value
        
        # Validation basique du format
        import re
        if not key or not re.match(r"^[a-zA-Z0-9_-]{30,100}$", key):
            test_result_text.value = "Clé invalide (mauvais format)"
            test_result_text.color = Colors.ERROR
            page.update()
            return
        
        # Affichage du statut de test
        test_result_text.value = "Test en cours..."
        test_result_text.color = Colors.WARNING
        test_button.disabled = True
        page.update()
        
        def worker():
            """Worker thread pour le test API"""
            try:
                if service == "Gemini":
                    result = run_gemini_test(key)
                else:
                    result = core.tester_cle_openai(key)
                
                # Mise à jour de l'interface
                test_result_text.value = result
                test_result_text.color = Colors.SUCCESS if "VALIDE" in result and not result.startswith("Erreur") else Colors.ERROR
                
            except Exception as ex:
                test_result_text.value = f"Erreur lors du test: {str(ex)}"
                test_result_text.color = Colors.ERROR
            
            finally:
                test_button.disabled = False
                page.update()
        
        threading.Thread(target=worker, daemon=True).start()
    
    test_button.on_click = test_api_key

    return ft.Tab(
        text="Test",
        icon=ft.Icons.BUG_REPORT,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    # En-tête
                    create_text("Test d'une clé Gemini ou OpenAI", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Testez une clé API en effectuant un appel réel à l'API du service sélectionné.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    
                    ft.Divider(),
                    
                    # Configuration du test
                    create_text("Configuration du Test", size=16, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 6}, controls=[test_service_dropdown]),
                    ]),
                    test_api_key_input,
                    
                    # Informations sur les tests
                    ft.Container(
                        content=ft.Column([
                            create_text("ℹ️ Informations sur les tests :", size=14, weight=ft.FontWeight.BOLD),
                            create_text("• OpenAI : Teste l'accès à l'API /v1/models", size=12),
                            create_text("• Gemini : Teste la génération de contenu avec une question simple", size=12),
                            create_text("• Les tests utilisent les APIs réelles (consomment des crédits)", size=12),
                            create_text("• Timeout : 15 secondes maximum par test", size=12),
                        ], spacing=Spacing.XS),
                        bgcolor=Colors.SURFACE_CONTAINER,
                        padding=Spacing.MD,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.SM)
                    ),
                    
                    ft.Divider(),
                    
                    # Action et résultat
                    create_text("Test", size=16, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 4}, controls=[test_button]),
                    ]),
                    
                    # Zone de résultat
                    ft.Container(
                        content=ft.Column([
                            create_text("Résultat du Test", size=14, weight=ft.FontWeight.BOLD),
                            test_result_text
                        ], spacing=Spacing.SM),
                        bgcolor=Colors.SURFACE_VARIANT,
                        padding=Spacing.LG,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.MD)
                    ),
                    
                    # Aide au dépannage
                    ft.Container(
                        content=ft.Column([
                            create_text("🔧 Dépannage :", size=14, weight=ft.FontWeight.BOLD),
                            create_text("• Erreur 401 : Clé invalide ou expirée", size=12),
                            create_text("• Erreur 429 : Limite de requêtes atteinte", size=12),
                            create_text("• Timeout : Problème de connexion réseau", size=12),
                            create_text("• Format invalide : Vérifiez la longueur et les caractères", size=12),
                        ], spacing=Spacing.XS),
                        bgcolor=Colors.ERROR_CONTAINER,
                        padding=Spacing.MD,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.SM)
                    ),
                    
                ], spacing=Spacing.LG, scroll=ft.ScrollMode.ALWAYS),
                padding=Spacing.XL
            ),
            expand=True,
            alignment=ft.alignment.center
        )
    )