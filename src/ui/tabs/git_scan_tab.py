"""
Onglet de scan Git (local et distant)
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


def create_git_scan_tab(patterns: dict, task_manager, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de scan Git (local et distant)
    
    Args:
        patterns: Dictionnaire des patterns de validation
        task_manager: Gestionnaire de tâches
        page: Page Flet
        
    Returns:
        Tab configuré pour le scan Git
    """
    
    # === SECTION SCAN LOCAL ===
    git_scan_path_text = create_text("")
    pick_git_folder_button = create_button("Sélectionner un Dépôt Local", hierarchy="secondary")
    start_local_git_scan_button = create_button("Lancer Scan Local", hierarchy="primary")
    
    # === SECTION SCAN DISTANT ===
    git_remote_url_input = create_text_field(
        label="URL du dépôt distant (ex: https://github.com/user/repo.git)", 
        expand=True
    )
    git_remote_url_input.semantic_label = "URL du dépôt Git distant à scanner"
    start_remote_git_scan_button = create_button("Lancer Scan Distant", hierarchy="primary")
    
    # === CONTRÔLES COMMUNS ===
    pause_git_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_git_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    git_scan_progress = create_progress_bar(visible=False)
    git_scan_status_text = create_text("", visible=False)
    git_scan_results_log = create_text_field(
        label="Résultats scan Git", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    
    # Événements de contrôle
    git_scan_pause_event = threading.Event()
    git_scan_cancel_event = threading.Event()

    def pick_git_folder_action(e):
        """Gestionnaire de sélection de dépôt Git local"""
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                git_scan_path_text.value = f"Dépôt local sélectionné : {result.path}"
                git_scan_path_text.data = result.path
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path(dialog_title="Sélectionner un dépôt Git")
    
    pick_git_folder_button.on_click = pick_git_folder_action

    # Configuration de la tâche scan Git local
    git_local_task_config = {
        'name': "Scan Git Local",
        'target_func': lambda **kwargs: core.mode_scan_git(patterns=patterns, **kwargs),
        'result_log': git_scan_results_log,
        'pause_event': git_scan_pause_event,
        'cancel_event': git_scan_cancel_event,
        'controls_to_disable': [start_local_git_scan_button, start_remote_git_scan_button, pick_git_folder_button, git_remote_url_input],
        'progress_bar': git_scan_progress,
        'status_text': git_scan_status_text,
        'pause_button': pause_git_scan_button,
        'cancel_button': cancel_git_scan_button,
        'pre_check': lambda: hasattr(git_scan_path_text, 'data') and git_scan_path_text.data and os.path.isdir(git_scan_path_text.data),
        'error_message': "Veuillez sélectionner un dépôt local valide.",
        'get_core_args': lambda: {'repo_path': git_scan_path_text.data}
    }

    # Configuration de la tâche scan Git distant
    git_remote_task_config = {
        'name': "Scan Git Distant",
        'target_func': lambda **kwargs: core.mode_scan_remote_git(patterns=patterns, **kwargs),
        'result_log': git_scan_results_log,
        'pause_event': git_scan_pause_event,
        'cancel_event': git_scan_cancel_event,
        'controls_to_disable': [start_local_git_scan_button, start_remote_git_scan_button, pick_git_folder_button, git_remote_url_input],
        'progress_bar': git_scan_progress,
        'status_text': git_scan_status_text,
        'pause_button': pause_git_scan_button,
        'cancel_button': cancel_git_scan_button,
        'pre_check': lambda: git_remote_url_input.value and git_remote_url_input.value.strip(),
        'error_message': "Veuillez saisir une URL de dépôt distant.",
        'get_core_args': lambda: {'repo_url': git_remote_url_input.value.strip()}
    }
    
    # Liaison des événements
    start_local_git_scan_button.on_click = partial(task_manager.start_task, task_config=git_local_task_config)
    start_remote_git_scan_button.on_click = partial(task_manager.start_task, task_config=git_remote_task_config)
    
    pause_git_scan_button.on_click = partial(
        task_manager.pause_task, 
        pause_event=git_scan_pause_event, 
        pause_button=pause_git_scan_button, 
        status_text=git_scan_status_text, 
        task_name="Scan Git"
    )
    cancel_git_scan_button.on_click = partial(
        task_manager.cancel_task, 
        cancel_event=git_scan_cancel_event, 
        controls_to_disable=git_local_task_config['controls_to_disable'], 
        pause_button=pause_git_scan_button, 
        cancel_button=cancel_git_scan_button, 
        status_text=git_scan_status_text, 
        task_name="Scan Git"
    )

    return ft.Tab(
        text="Scan Git",
        icon=ft.Icons.TRAVEL_EXPLORE,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    # Section Scan Local
                    create_text("Scan de Dépôt Local", size=18, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Scanne l'historique d'un dépôt Git local à la recherche de clés API exposées dans les commits.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 6}, controls=[pick_git_folder_button]),
                        ft.Column(col={"sm": 12, "md": 6}, controls=[start_local_git_scan_button]),
                    ]),
                    git_scan_path_text,
                    
                    ft.Divider(),
                    
                    # Section Scan Distant
                    create_text("Scan de Dépôt Distant", size=18, weight=ft.FontWeight.BOLD),
                    create_text(
                        "Clone et scanne un dépôt Git distant. Attention : peut prendre du temps selon la taille du dépôt.",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT
                    ),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 9}, controls=[git_remote_url_input]),
                        ft.Column(col={"sm": 12, "md": 3}, controls=[start_remote_git_scan_button]),
                    ]),
                    
                    ft.Divider(),
                    
                    # Contrôles et résultats
                    create_text("Contrôles", size=16, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 6}, controls=[pause_git_scan_button]),
                        ft.Column(col={"sm": 6}, controls=[cancel_git_scan_button]),
                    ]),
                    git_scan_progress,
                    git_scan_status_text,
                    
                    create_text("Résultats", size=16, weight=ft.FontWeight.BOLD),
                    git_scan_results_log
                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=Spacing.MD),
                padding=Spacing.XL
            ),
            expand=True
        )
    )