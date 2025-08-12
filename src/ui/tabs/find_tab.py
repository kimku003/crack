"""
Onglet d'analyse et génération de formats de clés API
"""

import os
import threading
import re
import secrets
import string
from functools import partial
import flet as ft
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ui_theme import (
    Colors, Spacing, create_button, create_text_field, create_card,
    create_responsive_row, create_text, create_progress_bar, create_action_button
)
from ui_extensions import MaterialIcons


def create_find_tab(patterns: dict, task_manager, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet d'analyse et génération de formats de clés API
    
    Args:
        patterns: Dictionnaire des patterns de validation
        task_manager: Gestionnaire de tâches
        page: Page Flet
        
    Returns:
        Tab configuré pour l'analyse de formats de clés
    """
    
    # === SECTION ANALYSE DE FORMAT ===
    analyze_key_input = create_text_field(
        label="Clé API à analyser",
        password=True,
        can_reveal_password=True
    )
    analyze_key_input.semantic_label = "Clé API dont vous voulez analyser le format"
    
    analyze_result_text = create_text("", size=14)
    analyze_button = create_button(
        "Analyser le format",
        icon=ft.Icons.ANALYTICS,
        hierarchy="primary"
    )
    
    # === SECTION GÉNÉRATION DE FORMATS DE TEST ===
    service_dropdown = ft.Dropdown(
        label="Service",
        options=[
            ft.dropdown.Option("OpenAI", "OpenAI"),
            ft.dropdown.Option("Gemini", "Gemini"),
            ft.dropdown.Option("GitHub", "GitHub"),
            ft.dropdown.Option("Custom", "Format personnalisé")
        ],
        value="OpenAI",
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
    )
    service_dropdown.semantic_label = "Service pour lequel générer des exemples de format"
    
    custom_pattern_input = create_text_field(
        label="Pattern personnalisé (ex: sk-[20]T3BlbkFJ[20])"
    )
    custom_pattern_input.visible = False
    
    num_examples_input = create_text_field(
        label="Nombre d'exemples",
        value="5",
        keyboard_type=ft.KeyboardType.NUMBER
    )
    
    examples_result_log = create_text_field(
        label="Exemples générés (pour tests uniquement)", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    
    generate_button = create_button(
        "Générer des exemples de format",
        icon=ft.Icons.SCIENCE,
        hierarchy="secondary"
    )
    
    copy_examples_button = create_button(
        "Copier les exemples",
        icon=ft.Icons.CONTENT_COPY,
        hierarchy="secondary"
    )
    
    # Notification de copie
    copy_notification = create_text("", color=Colors.SUCCESS, visible=False)

    def analyze_key_format(e):
        """Analyse le format d'une clé API"""
        key = analyze_key_input.value
        
        if not key:
            analyze_result_text.value = "Veuillez saisir une clé à analyser"
            analyze_result_text.color = Colors.WARNING
            page.update()
            return
        
        # Analyse du format
        analysis = []
        analysis.append(f"📊 Analyse de la clé : {key[:8]}...{key[-4:]}")
        analysis.append(f"📏 Longueur : {len(key)} caractères")
        
        # Détection du type de caractères
        has_letters = bool(re.search(r'[a-zA-Z]', key))
        has_digits = bool(re.search(r'[0-9]', key))
        has_special = bool(re.search(r'[^a-zA-Z0-9]', key))
        
        char_types = []
        if has_letters: char_types.append("lettres")
        if has_digits: char_types.append("chiffres")
        if has_special: char_types.append("caractères spéciaux")
        
        analysis.append(f"🔤 Types de caractères : {', '.join(char_types)}")
        
        # Détection de patterns connus
        if key.startswith('sk-'):
            analysis.append("🎯 Format détecté : OpenAI (sk-...)")
        elif key.startswith('ghp_'):
            analysis.append("🎯 Format détecté : GitHub Personal Access Token")
        elif key.startswith('gho_'):
            analysis.append("🎯 Format détecté : GitHub OAuth Token")
        elif len(key) >= 30 and key.isalnum():
            analysis.append("🎯 Format possible : Gemini/Google API")
        else:
            analysis.append("🎯 Format : Non reconnu ou personnalisé")
        
        # Analyse de l'entropie
        entropy = calculate_entropy(key)
        analysis.append(f"📈 Entropie : {entropy:.2f} bits")
        
        if entropy > 4.5:
            analysis.append("✅ Entropie élevée (bonne sécurité)")
        elif entropy > 3.5:
            analysis.append("⚠️ Entropie moyenne")
        else:
            analysis.append("❌ Entropie faible (sécurité insuffisante)")
        
        # Recommandations de sécurité
        analysis.append("\\n🔒 Recommandations de sécurité :")
        if len(key) < 32:
            analysis.append("• Longueur recommandée : 32+ caractères")
        if not has_special and len(key) < 40:
            analysis.append("• Considérer l'ajout de caractères spéciaux")
        analysis.append("• Stocker de manière sécurisée (variables d'environnement)")
        analysis.append("• Rotation régulière recommandée")
        
        analyze_result_text.value = "\\n".join(analysis)
        analyze_result_text.color = Colors.ON_SURFACE
        page.update()
    
    def calculate_entropy(s):
        """Calcule l'entropie de Shannon d'une chaîne"""
        if not s:
            return 0
        
        import math
        
        # Compter les fréquences
        freq = {}
        for char in s:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculer l'entropie
        entropy = 0
        length = len(s)
        for count in freq.values():
            p = count / length
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def generate_format_examples(e):
        """Génère des exemples de format pour tests"""
        service = service_dropdown.value
        try:
            num_examples = int(num_examples_input.value)
        except:
            num_examples = 5
        
        if num_examples > 20:
            num_examples = 20  # Limite raisonnable
        
        examples = []
        examples.append(f"🧪 Exemples de format pour {service} (TESTS UNIQUEMENT)")
        examples.append("⚠️ Ces clés sont FACTICES et ne fonctionneront pas avec les APIs réelles")
        examples.append("=" * 60)
        
        for i in range(num_examples):
            if service == "OpenAI":
                # Format OpenAI : sk-[20 chars]T3BlbkFJ[20 chars]
                part1 = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
                part2 = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
                fake_key = f"sk-{part1}T3BlbkFJ{part2}"
            elif service == "Gemini":
                # Format Gemini : 39 caractères alphanumériques
                fake_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(39))
            elif service == "GitHub":
                # Format GitHub : ghp_ + 36 caractères
                chars = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
                fake_key = f"ghp_{chars}"
            elif service == "Custom" and custom_pattern_input.value:
                # Pattern personnalisé
                pattern = custom_pattern_input.value
                fake_key = generate_from_pattern(pattern)
            else:
                fake_key = "Sélectionnez un service valide"
            
            examples.append(f"{i+1:2d}. {fake_key}")
        
        examples.append("=" * 60)
        examples.append("📝 Utilisation recommandée :")
        examples.append("• Tests de validation de format")
        examples.append("• Tests d'interface utilisateur")
        examples.append("• Démonstrations et formations")
        examples.append("• Tests de sécurité (détection de fuites)")
        examples.append("")
        examples.append("❌ NE PAS utiliser pour :")
        examples.append("• Tentatives d'accès non autorisé")
        examples.append("• Tests sur des APIs de production")
        examples.append("• Stockage en tant que vraies clés")
        
        examples_result_log.value = "\\n".join(examples)
        page.update()
    
    def generate_from_pattern(pattern):
        """Génère une clé à partir d'un pattern personnalisé"""
        # Pattern simple : [N] = N caractères aléatoires
        import re
        
        def replace_pattern(match):
            n = int(match.group(1))
            return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))
        
        return re.sub(r'\\[(\\d+)\\]', replace_pattern, pattern)
    
    def copy_examples(e):
        """Copie les exemples générés"""
        if examples_result_log.value:
            page.set_clipboard(examples_result_log.value)
            copy_notification.value = "✅ Exemples copiés dans le presse-papier !"
            copy_notification.visible = True
            page.update()
            
            def hide_notification():
                import time
                time.sleep(3)
                copy_notification.visible = False
                page.update()
            
            threading.Thread(target=hide_notification, daemon=True).start()
    
    def on_service_change(e):
        """Gère le changement de service"""
        custom_pattern_input.visible = (service_dropdown.value == "Custom")
        page.update()
    
    # Liaison des événements
    analyze_button.on_click = analyze_key_format
    generate_button.on_click = generate_format_examples
    copy_examples_button.on_click = copy_examples
    service_dropdown.on_change = on_service_change

    return ft.Tab(
        text="Analyser",
        icon=ft.Icons.ANALYTICS,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    # En-tête
                    create_text("Analyse et Génération de Formats de Clés API", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Outil d'analyse de formats de clés et de génération d'exemples pour tests de sécurité légitimes.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    
                    ft.Divider(),
                    
                    # Section Analyse
                    create_text("🔍 Analyse de Format", size=18, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Analysez le format, la longueur et l'entropie d'une clé API existante.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    analyze_key_input,
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 4}, controls=[analyze_button]),
                    ]),
                    
                    # Résultat de l'analyse
                    ft.Container(
                        content=analyze_result_text,
                        bgcolor=Colors.SURFACE_VARIANT,
                        padding=Spacing.MD,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.SM)
                    ),
                    
                    ft.Divider(),
                    
                    # Section Génération d'exemples
                    create_text("🧪 Génération d'Exemples de Test", size=18, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Générez des exemples de clés factices pour vos tests de sécurité et validations.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 6}, controls=[service_dropdown]),
                        ft.Column(col={"sm": 12, "md": 6}, controls=[num_examples_input]),
                    ]),
                    custom_pattern_input,
                    
                    # Avertissement éthique
                    ft.Container(
                        content=ft.Column([
                            create_text("⚖️ Utilisation Éthique", size=14, weight=ft.FontWeight.BOLD),
                            create_text("• Ces exemples sont FACTICES et ne fonctionnent pas avec les APIs", size=12),
                            create_text("• Utilisez uniquement pour des tests légitimes sur vos propres systèmes", size=12),
                            create_text("• Respectez les conditions d'utilisation des services", size=12),
                            create_text("• Ne tentez jamais d'accès non autorisé", size=12),
                        ], spacing=Spacing.XS),
                        bgcolor=Colors.WARNING_CONTAINER,
                        padding=Spacing.MD,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.SM)
                    ),
                    
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 4}, controls=[generate_button]),
                        ft.Column(col={"sm": 12, "md": 4}, controls=[copy_examples_button]),
                    ]),
                    copy_notification,
                    
                    # Résultats
                    create_text("Exemples Générés", size=16, weight=ft.FontWeight.BOLD),
                    examples_result_log,
                    
                    # Guide d'utilisation
                    ft.Container(
                        content=ft.Column([
                            create_text("📚 Cas d'Usage Légitimes", size=14, weight=ft.FontWeight.BOLD),
                            create_text("• Tests de validation de format dans vos applications", size=12),
                            create_text("• Démonstrations et formations en sécurité", size=12),
                            create_text("• Tests d'interface utilisateur avec des données factices", size=12),
                            create_text("• Audit de sécurité : détection de fuites de clés", size=12),
                            create_text("• Développement de systèmes de validation", size=12),
                        ], spacing=Spacing.XS),
                        bgcolor=Colors.SUCCESS_CONTAINER,
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