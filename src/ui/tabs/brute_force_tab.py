"""
Onglet de brute force et attaque par dictionnaire
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


def create_brute_force_tab(patterns: dict, task_manager, page: ft.Page) -> ft.Tab:
    """
    Crée l'onglet de brute force et attaque par dictionnaire
    
    Args:
        patterns: Dictionnaire des patterns de validation
        task_manager: Gestionnaire de tâches
        page: Page Flet
        
    Returns:
        Tab configuré pour les attaques
    """
    
    # === SECTION BRUTE FORCE ===
    brute_force_key_input = create_text_field(label="Clé partielle")
    brute_force_key_input.semantic_label = "Clé partielle pour l'attaque par force brute"
    
    brute_force_service_dropdown = ft.Dropdown(
        label="Service",
        options=[ft.dropdown.Option(key) for key in patterns.keys()],
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
    )
    brute_force_service_dropdown.semantic_label = "Service cible pour l'attaque"
    
    brute_force_depth_input = create_text_field(
        label="Profondeur", 
        value="2", 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    brute_force_depth_input.semantic_label = "Nombre de caractères à deviner"
    
    brute_force_button = create_button("Lancer Brute-force", hierarchy="primary")
    pause_brute_force_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_brute_force_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    
    brute_force_progress = create_progress_bar(visible=False)
    brute_force_status_text = create_text("", visible=False)
    brute_force_result_log = create_text_field(
        label="Résultats brute-force", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    
    # Événements de contrôle brute force
    brute_force_pause_event = threading.Event()
    brute_force_cancel_event = threading.Event()

    # Configuration de la tâche brute force
    brute_force_task_config = {
        'name': "Brute-force",
        'target_func': lambda **kwargs: core.mode_brute_force(patterns=patterns, **kwargs),
        'result_log': brute_force_result_log,
        'pause_event': brute_force_pause_event,
        'cancel_event': brute_force_cancel_event,
        'controls_to_disable': [brute_force_button, brute_force_key_input, brute_force_service_dropdown, brute_force_depth_input],
        'progress_bar': brute_force_progress,
        'status_text': brute_force_status_text,
        'pause_button': pause_brute_force_button,
        'cancel_button': cancel_brute_force_button,
        'pre_check': lambda: brute_force_key_input.value and brute_force_service_dropdown.value,
        'error_message': "Clé partielle et service requis.",
        'get_core_args': lambda: {
            'cle_partielle': brute_force_key_input.value,
            'service_specifie': brute_force_service_dropdown.value,
            'depth': int(brute_force_depth_input.value) if brute_force_depth_input.value.isdigit() else 2
        }
    }
    
    # === SECTION DICTIONNAIRE ===
    dict_key_input = create_text_field(label="Clé partielle")
    dict_key_input.semantic_label = "Clé partielle pour l'attaque par dictionnaire"
    
    dict_service_dropdown = ft.Dropdown(
        label="Service",
        options=[ft.dropdown.Option(key) for key in patterns.keys()],
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
    )
    dict_service_dropdown.semantic_label = "Service cible pour l'attaque par dictionnaire"
    
    dict_wordlist_path_text = create_text("")
    pick_wordlist_button = create_button("Sélectionner un dictionnaire", hierarchy="secondary")
    dict_button = create_button("Lancer l'Attaque", hierarchy="primary")
    pause_dict_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_dict_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    
    dict_progress = create_progress_bar(visible=False)
    dict_status_text = create_text("", visible=False)
    dict_result_log = create_text_field(
        label="Résultats dictionnaire", 
        multiline=True, 
        read_only=True, 
        expand=True
    )
    
    # Événements de contrôle dictionnaire
    dict_pause_event = threading.Event()
    dict_cancel_event = threading.Event()

    def pick_wordlist_action(e):
        """Gestionnaire de sélection de wordlist"""
        def on_result(result: ft.FilePickerResultEvent):
            if result.files:
                dict_wordlist_path_text.value = result.files[0].path
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.pick_files(
            dialog_title="Sélectionner un fichier dictionnaire",
            file_type=ft.FilePickerFileType.ANY
        )
    
    pick_wordlist_button.on_click = pick_wordlist_action

    # Configuration de la tâche dictionnaire
    dict_task_config = {
        'name': "Attaque par dictionnaire",
        'target_func': lambda **kwargs: core.mode_dictionnaire(patterns=patterns, **kwargs),
        'result_log': dict_result_log,
        'pause_event': dict_pause_event,
        'cancel_event': dict_cancel_event,
        'controls_to_disable': [dict_button, dict_key_input, dict_service_dropdown, pick_wordlist_button],
        'progress_bar': dict_progress,
        'status_text': dict_status_text,
        'pause_button': pause_dict_button,
        'cancel_button': cancel_dict_button,
        'pre_check': lambda: dict_key_input.value and dict_service_dropdown.value and dict_wordlist_path_text.value,
        'error_message': "Clé, service et wordlist requis.",
        'get_core_args': lambda: {
            'cle_partielle': dict_key_input.value,
            'service_specifie': dict_service_dropdown.value,
            'wordlist_path': dict_wordlist_path_text.value
        }
    }
    
    # Liaison des événements brute force
    brute_force_button.on_click = partial(task_manager.start_task, task_config=brute_force_task_config)
    pause_brute_force_button.on_click = partial(
        task_manager.pause_task, 
        pause_event=brute_force_pause_event, 
        pause_button=pause_brute_force_button, 
        status_text=brute_force_status_text, 
        task_name="Brute-force"
    )
    cancel_brute_force_button.on_click = partial(
        task_manager.cancel_task, 
        cancel_event=brute_force_cancel_event, 
        controls_to_disable=brute_force_task_config['controls_to_disable'], 
        pause_button=pause_brute_force_button, 
        cancel_button=cancel_brute_force_button, 
        status_text=brute_force_status_text, 
        task_name="Brute-force"
    )
    
    # Liaison des événements dictionnaire
    dict_button.on_click = partial(task_manager.start_task, task_config=dict_task_config)
    pause_dict_button.on_click = partial(
        task_manager.pause_task, 
        pause_event=dict_pause_event, 
        pause_button=pause_dict_button, 
        status_text=dict_status_text, 
        task_name="Attaque Dictionnaire"
    )
    cancel_dict_button.on_click = partial(
        task_manager.cancel_task, 
        cancel_event=dict_cancel_event, 
        controls_to_disable=dict_task_config['controls_to_disable'], 
        pause_button=pause_dict_button, 
        cancel_button=cancel_dict_button, 
        status_text=dict_status_text, 
        task_name="Attaque Dictionnaire"
    )

    return ft.Tab(
        text="Devinette",
        icon=ft.Icons.CASINO,
        content=ft.Container(
            content=create_card(
                content=ft.Column([
                    # Section Brute Force
                    create_text("Brute-force", size=20, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 5}, controls=[brute_force_key_input]),
                        ft.Column(col={"sm": 12, "md": 4}, controls=[brute_force_service_dropdown]),
                        ft.Column(col={"sm": 12, "md": 3}, controls=[brute_force_depth_input]),
                    ]),
                    create_responsive_row([
                        ft.Column(col={"sm": 4}, controls=[brute_force_button]),
                        ft.Column(col={"sm": 4}, controls=[pause_brute_force_button]),
                        ft.Column(col={"sm": 4}, controls=[cancel_brute_force_button]),
                    ]),
                    brute_force_progress,
                    brute_force_status_text,
                    brute_force_result_log,
                    
                    ft.Divider(),
                    
                    # Section Dictionnaire
                    create_text("Attaque par Dictionnaire", size=20, weight=ft.FontWeight.BOLD),
                    create_responsive_row([
                        ft.Column(col={"sm": 12, "md": 6}, controls=[dict_key_input]),
                        ft.Column(col={"sm": 12, "md": 6}, controls=[dict_service_dropdown]),
                    ]),
                    create_responsive_row([
                        ft.Column(col={"sm": 8}, controls=[pick_wordlist_button]),
                        ft.Column(col={"sm": 4}, controls=[dict_wordlist_path_text]),
                    ]),
                    create_responsive_row([
                        ft.Column(col={"sm": 4}, controls=[dict_button]),
                        ft.Column(col={"sm": 4}, controls=[pause_dict_button]),
                        ft.Column(col={"sm": 4}, controls=[cancel_dict_button]),
                    ]),
                    dict_progress,
                    dict_status_text,
                    dict_result_log,
                ], spacing=Spacing.LG, scroll=ft.ScrollMode.ALWAYS),
                padding=Spacing.XL
            ),
            alignment=ft.alignment.center
        )
    )