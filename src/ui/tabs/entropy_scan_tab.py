"""
Onglet de scan par entropie
"""

import os
import threading
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
from apikey_validator import core


def create_entropy_scan_tab(patterns: dict, task_manager, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de scan par entropie
    
    Args:
        patterns: Dictionnaire des patterns de validation
        task_manager: Gestionnaire de tâches
        page: Page Flet
        
    Returns:
        Tab configuré pour le scan par entropie
    """
    
    # Composants de l'onglet
    entropy_scan_path_text = create_text("")
    entropy_threshold_input = create_text_field(
        label="Seuil d'entropie", 
        value="4.0", 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    entropy_threshold_input.semantic_label = "Seuil d'entropie minimum pour détecter les secrets"
    
    pick_entropy_folder_button = create_button("Sélectionner un Répertoire", hierarchy="secondary")
    start_entropy_scan_button = create_button("Lancer le Scan", hierarchy="primary")
    pause_entropy_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_entropy_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    
    entropy_scan_progress = create_progress_bar(visible=False)
    entropy_scan_status_text = create_text("", visible=False)
    entropy_scan_results_log = create_text_field(
        label="Résultats scan entropie", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    
    # Événements de contrôle
    entropy_scan_pause_event = threading.Event()
    entropy_scan_cancel_event = threading.Event()

    def pick_entropy_folder_action(e):
        """Gestionnaire de sélection de dossier pour scan entropie"""
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                entropy_scan_path_text.value = f"Répertoire sélectionné : {result.path}"
                entropy_scan_path_text.data = result.path
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path(dialog_title="Sélectionner un répertoire à scanner")
    
    pick_entropy_folder_button.on_click = pick_entropy_folder_action

    # Configuration de la tâche scan entropie
    entropy_scan_task_config = {
        'name': "Scan par entropie",
        'target_func': lambda **kwargs: core.mode_scan_entropy(**kwargs),
        'result_log': entropy_scan_results_log,
        'pause_event': entropy_scan_pause_event,
        'cancel_event': entropy_scan_cancel_event,
        'controls_to_disable': [start_entropy_scan_button, pick_entropy_folder_button, entropy_threshold_input],
        'progress_bar': entropy_scan_progress,
        'status_text': entropy_scan_status_text,
        'pause_button': pause_entropy_scan_button,
        'cancel_button': cancel_entropy_scan_button,
        'pre_check': lambda: (
            hasattr(entropy_scan_path_text, 'data') and 
            entropy_scan_path_text.data and 
            os.path.isdir(entropy_scan_path_text.data) and
            entropy_threshold_input.value and
            entropy_threshold_input.value.replace('.', '').isdigit()
        ),
        'error_message': "Veuillez sélectionner un répertoire valide et un seuil d'entropie numérique.",
        'get_core_args': lambda: {
            'scan_path': entropy_scan_path_text.data,
            'threshold': float(entropy_threshold_input.value) if entropy_threshold_input.value.replace('.', '').isdigit() else 4.0
        }
    }
    
    # Liaison des événements
    start_entropy_scan_button.on_click = partial(task_manager.start_task, task_config=entropy_scan_task_config)
    pause_entropy_scan_button.on_click = partial(
        task_manager.pause_task, 
        pause_event=entropy_scan_pause_event, 
        pause_button=pause_entropy_scan_button, 
        status_text=entropy_scan_status_text, 
        task_name="Scan par entropie"
    )
    cancel_entropy_scan_button.on_click = partial(
        task_manager.cancel_task, 
        cancel_event=entropy_scan_cancel_event, 
        controls_to_disable=entropy_scan_task_config['controls_to_disable'], 
        pause_button=pause_entropy_scan_button, 
        cancel_button=cancel_entropy_scan_button, 
        status_text=entropy_scan_status_text, 
        task_name="Scan par entropie"
    )

    return ft.Tab(
        text="Scan Entropie",
        icon=ft.Icons.FLARE,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    # En-tête explicatif
                    create_text("Scan par Entropie", size=20, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Scanne un répertoire pour trouver des chaînes de caractères à haute entropie, "
                        "qui pourraient être des secrets ou des clés API.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    
                    ft.Divider(),
                    
                    # Configuration
                    create_text("Configuration", size=16, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 6}, controls=[pick_entropy_folder_button]),
                        ft.Column(col={"sm": 12, "md": 3}, controls=[entropy_threshold_input]),
                        ft.Column(col={"sm": 12, "md": 3}, controls=[start_entropy_scan_button]),
                    ]),
                    entropy_scan_path_text,
                    
                    # Informations sur le seuil
                    ft.Container(
                        content=ft.Column([
                            create_text("💡 Aide sur le seuil d'entropie :", size=14, weight=ft.FontWeight.BOLD),
                            create_text("• 3.0-4.0 : Détection sensible (plus de faux positifs)", size=12),
                            create_text("• 4.0-5.0 : Équilibré (recommandé)", size=12),
                            create_text("• 5.0+ : Détection stricte (moins de faux positifs)", size=12),
                        ], spacing=Spacing.XS),
                        bgcolor=Colors.SURFACE_CONTAINER,
                        padding=Spacing.MD,
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=Spacing.SM)
                    ),
                    
                    ft.Divider(),
                    
                    # Contrôles
                    create_text("Contrôles", size=16, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 6}, controls=[pause_entropy_scan_button]),
                        ft.Column(col={"sm": 6}, controls=[cancel_entropy_scan_button]),
                    ]),
                    entropy_scan_progress,
                    entropy_scan_status_text,
                    
                    # Résultats
                    create_text("Résultats", size=16, weight=ft.FontWeight.BOLD),
                    create_text(
                        "⚠️ Les résultats nécessitent une vérification manuelle pour éliminer les faux positifs.",
                        size=12,
                        color=Colors.WARNING
                    ),
                    entropy_scan_results_log
                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=Spacing.MD),
                padding=Spacing.XL
            ),
            expand=True
        )
    )