"""
Onglet de scan de fichiers
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


def create_scan_tab(patterns: dict, task_manager, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de scan de fichiers
    
    Args:
        patterns: Dictionnaire des patterns de validation
        task_manager: Gestionnaire de tâches
        page: Page Flet
        
    Returns:
        Tab configuré pour le scan de fichiers
    """
    
    # Composants de l'onglet
    scan_path_text = create_text("")
    scan_results_log = create_text_field(
        label="Résultats du scan", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    pick_folder_button = create_button("Sélectionner un Répertoire", hierarchy="secondary")
    start_scan_button = create_button("Lancer le Scan", hierarchy="primary")
    pause_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    scan_progress = create_progress_bar(visible=False)
    scan_status_text = create_text("", visible=False)
    
    # Événements de contrôle
    scan_pause_event = threading.Event()
    scan_cancel_event = threading.Event()

    def pick_folder_action(e):
        """Gestionnaire de sélection de dossier"""
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                scan_path_text.value = result.path
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
    
    pick_folder_button.on_click = pick_folder_action

    # Configuration de la tâche de scan
    scan_task_config = {
        'name': "Scan de fichiers",
        'target_func': lambda **kwargs: core.mode_scan(patterns=patterns, **kwargs),
        'result_log': scan_results_log,
        'pause_event': scan_pause_event,
        'cancel_event': scan_cancel_event,
        'controls_to_disable': [start_scan_button, pick_folder_button],
        'progress_bar': scan_progress,
        'status_text': scan_status_text,
        'pause_button': pause_scan_button,
        'cancel_button': cancel_scan_button,
        'pre_check': lambda: scan_path_text.value and os.path.isdir(scan_path_text.value),
        'error_message': "Veuillez sélectionner un répertoire valide.",
        'get_core_args': lambda: {'scan_path': scan_path_text.value}
    }
    
    # Liaison des événements
    start_scan_button.on_click = partial(task_manager.start_task, task_config=scan_task_config)
    pause_scan_button.on_click = partial(
        task_manager.pause_task, 
        pause_event=scan_pause_event, 
        pause_button=pause_scan_button, 
        status_text=scan_status_text, 
        task_name="Scan de fichiers"
    )
    cancel_scan_button.on_click = partial(
        task_manager.cancel_task, 
        cancel_event=scan_cancel_event, 
        controls_to_disable=scan_task_config['controls_to_disable'], 
        pause_button=pause_scan_button, 
        cancel_button=cancel_scan_button, 
        status_text=scan_status_text, 
        task_name="Scan de fichiers"
    )

    return ft.Tab(
        text="Scan Fichiers",
        icon=MaterialIcons.FOLDER,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    create_responsive_row([
                        ft.Column(col={"sm": 6, "md": 3}, controls=[pick_folder_button]),
                        ft.Column(col={"sm": 6, "md": 3}, controls=[start_scan_button]),
                        ft.Column(col={"sm": 6, "md": 3}, controls=[pause_scan_button]),
                        ft.Column(col={"sm": 6, "md": 3}, controls=[cancel_scan_button]),
                    ]),
                    scan_path_text,
                    scan_progress,
                    scan_status_text,
                    scan_results_log
                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=Spacing.MD),
                padding=Spacing.XL
            ),
            expand=True
        )
    )