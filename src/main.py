
import flet as ft
import os
import sys
import threading
from functools import partial
from flet import (
    TextField,
    Dropdown,
    ElevatedButton,
    Text,
    Card,
    Column,
    Row,
    Container,
    ProgressBar,
    Tabs,
    Tab,
    FilePicker,
    FilePickerResultEvent,
    MainAxisAlignment,
    alignment,
    FontWeight,
)
from apikey_validator import core, config



def main(page: ft.Page):

    page.title = "API Security Scanner"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLUE_GREY_900

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, 'apikey_validator', 'config.json')
        PATTERNS = config.charger_patterns(config_path)
    except Exception as e:
        page.add(ft.Text(f"Erreur fatale à l'initialisation : {e}"))
        return

    if not PATTERNS:
        page.add(ft.Text("Erreur: Impossible de charger la configuration des secrets depuis config.json."))
        return

    def create_task_runner(target_func, controls_to_manage, pause_button, cancel_button, pause_event, cancel_event, **kwargs):
        def task_wrapper():
            # Active les contrôles de la tâche (barre de progression, boutons pause/annuler)
            for control in controls_to_manage.values():
                if isinstance(control, (ProgressBar, Text)):
                    control.visible = True
            pause_button.visible = True
            cancel_button.visible = True
            page.update()
            
            try:
                target_func(patterns=PATTERNS, pause_event=pause_event, cancel_event=cancel_event, **kwargs)
            finally:
                # Masque les contrôles de la tâche une fois terminée
                if not cancel_event.is_set():
                    for c in controls_to_manage['buttons_to_disable']:
                        c.disabled = False
                    for control in controls_to_manage.values():
                        if isinstance(control, (ProgressBar, Text)):
                            control.visible = False
                    pause_button.visible = False
                    cancel_button.visible = False
                    page.update()

        return task_wrapper

    # --- Définition des Callbacks pour l'UI ---
    def ui_progress_callback(progress_bar: ProgressBar, status_text: Text, current: int, total: int, message: str):
        if total > 0:
            progress_bar.value = current / total
        status_text.value = message
        page.update()

    def ui_result_callback(result_log: TextField, result: dict):
        status = "VALIDE" if result.get('is_valid') else "INVALIDE"
        color = ft.colors.GREEN if result.get('is_valid') else ft.colors.RED
        
        # Tronquer la clé pour la sécurité
        key_display = f"{result['key'][:4]}...{result['key'][-4:]}" if len(result['key']) > 8 else result['key']
        
        log_entry = f"[{result['timestamp']}] {result['service']} - {status} - Clé: {key_display} (Source: {result['source_type']} @ {result['source_info']})\n"
        
        # Pour Flet, il est plus sûr de mettre à jour les contrôles de cette manière
        result_log.value += log_entry
        page.update()

    # --- Onglet Validation ---
    api_key_input = TextField(label="Clé API", width=450, password=True, can_reveal_password=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    validate_button = ElevatedButton(text="Valider", icon=ft.Icons.SECURITY, bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    result_text = Text(size=16, weight=ft.FontWeight.BOLD)

    def validate_key_click(e):
        key = api_key_input.value
        service = service_dropdown.value
        if not key or not service:
            result_text.value = "Veuillez fournir une clé et un service."
            result_text.color = ft.Colors.ORANGE
            page.update()
            return

        validator = PATTERNS[service]["validator"]
        is_valid = validator(key, silencieux=True)
        if is_valid:
            result_text.value = f"SUCCÈS : La clé pour {service} est VALIDE."
            result_text.color = ft.Colors.GREEN
        else:
            result_text.value = f"ÉCHEC : La clé pour {service} est INVALIDE."
            result_text.color = ft.Colors.RED
        page.update()
    validate_button.on_click = validate_key_click

    # --- Fonctions génériques pour les tâches asynchrones ---
    def start_task(e, task_config):
        # Vérification des prérequis
        if task_config['pre_check'] and not task_config['pre_check']():
            # Affiche un message d'erreur dans le log correspondant
            task_config['result_log'].value = f"[!] Erreur: {task_config.get('error_message', 'Veuillez vérifier les champs.')}"
            page.update()
            return
        
        # Réinitialisation des logs et événements
        task_config['result_log'].value = f"[*] Démarrage de la tâche: {task_config['name']}\n"
        task_config['pause_event'].set()
        task_config['cancel_event'].clear()

        # Désactivation des boutons
        for btn in task_config['controls_to_disable']:
            btn.disabled = True
        
        # Création des callbacks avec les contrôles UI spécifiques
        progress_cb = partial(ui_progress_callback, task_config['progress_bar'], task_config['status_text'])
        result_cb = partial(ui_result_callback, task_config['result_log'])
        
        # Préparation des arguments pour la fonction core
        core_args = task_config['get_core_args']()
        core_args['progress_callback'] = progress_cb
        core_args['result_callback'] = result_cb

        # Configuration du task runner
        runner_controls = {
            'buttons_to_disable': task_config['controls_to_disable'],
            'progress_bar': task_config['progress_bar'],
            'status_text': task_config['status_text']
        }
        
        task = create_task_runner(
            task_config['target_func'], 
            runner_controls,
            task_config['pause_button'], 
            task_config['cancel_button'],
            task_config['pause_event'], 
            task_config['cancel_event'],
            **core_args
        )
        threading.Thread(target=task, daemon=True).start()

    def pause_task(e, pause_event, pause_button, status_text, task_name):
        if pause_button.text == "Pause":
            pause_event.clear()
            pause_button.text = "Reprendre"
            status_text.value = f"[*] {task_name} en pause..."
        else:
            pause_event.set()
            pause_button.text = "Pause"
            status_text.value = f"[*] Reprise de {task_name}..."
        page.update()

    def cancel_task(e, cancel_event, controls_to_disable, pause_button, cancel_button, status_text, task_name):
        cancel_event.set()
        status_text.value = f"[*] Annulation de {task_name}..."
        for btn in controls_to_disable:
            btn.disabled = False
        pause_button.visible = False
        cancel_button.visible = False
        pause_button.text = "Pause"
        page.update()

    # --- Onglet Scan de Fichiers ---
    scan_path_text = Text()
    scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_folder_button = ElevatedButton("Sélectionner un Répertoire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_scan_button = ElevatedButton("Lancer le Scan", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
    cancel_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
    scan_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    scan_status_text = Text("", visible=False)
    scan_pause_event = threading.Event()
    scan_cancel_event = threading.Event()

    def pick_folder_action(e):
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                scan_path_text.value = result.path
                page.update()
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
    pick_folder_button.on_click = pick_folder_action

    scan_task_config = {
        'name': "Scan de fichiers",
        'target_func': core.mode_scan,
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
    start_scan_button.on_click = partial(start_task, task_config=scan_task_config)
    pause_scan_button.on_click = partial(pause_task, pause_event=scan_pause_event, pause_button=pause_scan_button, status_text=scan_status_text, task_name="Scan de fichiers")
    cancel_scan_button.on_click = partial(cancel_task, cancel_event=scan_cancel_event, controls_to_disable=scan_task_config['controls_to_disable'], pause_button=pause_scan_button, cancel_button=cancel_scan_button, status_text=scan_status_text, task_name="Scan de fichiers")

    # --- Onglet Devinette (Brute-force) ---
    brute_force_key_input = TextField(label="Clé partielle", width=300, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_depth_input = TextField(label="Profondeur", width=100, value="2", filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_button = ElevatedButton("Lancer Brute-force", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_brute_force_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
    cancel_brute_force_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
    brute_force_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    brute_force_status_text = Text("", visible=False)
    brute_force_result_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_pause_event = threading.Event()
    brute_force_cancel_event = threading.Event()

    brute_force_task_config = {
        'name': "Brute-force",
        'target_func': core.mode_brute_force,
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
            'depth': int(brute_force_depth_input.value)
        }
    }
    brute_force_button.on_click = partial(start_task, task_config=brute_force_task_config)
    pause_brute_force_button.on_click = partial(pause_task, pause_event=brute_force_pause_event, pause_button=pause_brute_force_button, status_text=brute_force_status_text, task_name="Brute-force")
    cancel_brute_force_button.on_click = partial(cancel_task, cancel_event=brute_force_cancel_event, controls_to_disable=brute_force_task_config['controls_to_disable'], pause_button=pause_brute_force_button, cancel_button=cancel_brute_force_button, status_text=brute_force_status_text, task_name="Brute-force")

    # --- Onglet Devinette (Dictionnaire) ---
    dict_key_input = TextField(label="Clé partielle", width=300, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    dict_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    dict_wordlist_path_text = Text()
    pick_wordlist_button = ElevatedButton("Sélectionner un dictionnaire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    dict_button = ElevatedButton("Lancer l'Attaque", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_dict_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
    cancel_dict_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
    dict_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    dict_status_text = Text("", visible=False)
    dict_result_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    dict_pause_event = threading.Event()
    dict_cancel_event = threading.Event()

    def pick_wordlist_action(e):
        def on_result(result: ft.FilePickerResultEvent):
            if result.files:
                dict_wordlist_path_text.value = result.files[0].path
                page.update()
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.pick_files()
    pick_wordlist_button.on_click = pick_wordlist_action

    dict_task_config = {
        'name': "Attaque par dictionnaire",
        'target_func': core.mode_dictionnaire,
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
    dict_button.on_click = partial(start_task, task_config=dict_task_config)
    pause_dict_button.on_click = partial(pause_task, pause_event=dict_pause_event, pause_button=pause_dict_button, status_text=dict_status_text, task_name="Attaque Dictionnaire")
    cancel_dict_button.on_click = partial(cancel_task, cancel_event=dict_cancel_event, controls_to_disable=dict_task_config['controls_to_disable'], pause_button=pause_dict_button, cancel_button=cancel_dict_button, status_text=dict_status_text, task_name="Attaque Dictionnaire")

    # --- Onglet Scan Git ---
    git_scan_path_text = Text()
    git_remote_url_input = TextField(label="URL du dépôt distant (ex: https://github.com/user/repo.git)", expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    git_scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_git_folder_button = ElevatedButton("Sélectionner un Dépôt Local", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_local_git_scan_button = ElevatedButton("Lancer Scan Local", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_remote_git_scan_button = ElevatedButton("Lancer Scan Distant", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_git_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
    cancel_git_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
    git_scan_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    git_scan_status_text = Text("", visible=False)
    git_scan_pause_event = threading.Event()
    git_scan_cancel_event = threading.Event()

    def pick_git_folder_action(e):
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                git_scan_path_text.value = f"Dépôt local sélectionné : {result.path}"
                git_scan_path_text.data = result.path
                page.update()
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
    pick_git_folder_button.on_click = pick_git_folder_action

    git_local_task_config = {
        'name': "Scan Git Local",
        'target_func': core.mode_scan_git,
        'result_log': git_scan_results_log,
        'pause_event': git_scan_pause_event,
        'cancel_event': git_scan_cancel_event,
        'controls_to_disable': [start_local_git_scan_button, start_remote_git_scan_button, pick_git_folder_button, git_remote_url_input],
        'progress_bar': git_scan_progress,
        'status_text': git_scan_status_text,
        'pause_button': pause_git_scan_button,
        'cancel_button': cancel_git_scan_button,
        'pre_check': lambda: git_scan_path_text.data and os.path.isdir(git_scan_path_text.data),
        'error_message': "Veuillez sélectionner un dépôt local valide.",
        'get_core_args': lambda: {'repo_path': git_scan_path_text.data}
    }
    start_local_git_scan_button.on_click = partial(start_task, task_config=git_local_task_config)

    git_remote_task_config = {
        'name': "Scan Git Distant",
        'target_func': core.mode_scan_remote_git,
        'result_log': git_scan_results_log,
        'pause_event': git_scan_pause_event,
        'cancel_event': git_scan_cancel_event,
        'controls_to_disable': [start_local_git_scan_button, start_remote_git_scan_button, pick_git_folder_button, git_remote_url_input],
        'progress_bar': git_scan_progress,
        'status_text': git_scan_status_text,
        'pause_button': pause_git_scan_button,
        'cancel_button': cancel_git_scan_button,
        'pre_check': lambda: git_remote_url_input.value,
        'error_message': "Veuillez saisir une URL de dépôt distant.",
        'get_core_args': lambda: {'repo_url': git_remote_url_input.value}
    }
    start_remote_git_scan_button.on_click = partial(start_task, task_config=git_remote_task_config)
    
    pause_git_scan_button.on_click = partial(pause_task, pause_event=git_scan_pause_event, pause_button=pause_git_scan_button, status_text=git_scan_status_text, task_name="Scan Git")
    cancel_git_scan_button.on_click = partial(cancel_task, cancel_event=git_scan_cancel_event, controls_to_disable=git_local_task_config['controls_to_disable'], pause_button=pause_git_scan_button, cancel_button=cancel_git_scan_button, status_text=git_scan_status_text, task_name="Scan Git")

    # --- Onglet Scan par Entropie ---
    entropy_scan_path_text = Text()
    entropy_scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    entropy_threshold_input = TextField(label="Seuil", width=100, value="4.0", filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_entropy_folder_button = ElevatedButton("Sélectionner un Répertoire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_entropy_scan_button = ElevatedButton("Lancer le Scan", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_entropy_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
    cancel_entropy_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
    entropy_scan_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    entropy_scan_status_text = Text("", visible=False)
    entropy_scan_pause_event = threading.Event()
    entropy_scan_cancel_event = threading.Event()

    def pick_entropy_folder_action(e):
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                entropy_scan_path_text.value = result.path
                page.update()
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
    pick_entropy_folder_button.on_click = pick_entropy_folder_action

    entropy_task_config = {
        'name': "Scan par Entropie",
        'target_func': core.mode_scan_entropy,
        'result_log': entropy_scan_results_log,
        'pause_event': entropy_scan_pause_event,
        'cancel_event': entropy_scan_cancel_event,
        'controls_to_disable': [start_entropy_scan_button, pick_entropy_folder_button, entropy_threshold_input],
        'progress_bar': entropy_scan_progress,
        'status_text': entropy_scan_status_text,
        'pause_button': pause_entropy_scan_button,
        'cancel_button': cancel_entropy_scan_button,
        'pre_check': lambda: entropy_scan_path_text.value and os.path.isdir(entropy_scan_path_text.value),
        'error_message': "Veuillez sélectionner un répertoire valide.",
        'get_core_args': lambda: {
            'scan_path': entropy_scan_path_text.value,
            'threshold': float(entropy_threshold_input.value)
        }
    }
    start_entropy_scan_button.on_click = partial(start_task, task_config=entropy_task_config)
    pause_entropy_scan_button.on_click = partial(pause_task, pause_event=entropy_scan_pause_event, pause_button=pause_entropy_scan_button, status_text=entropy_scan_status_text, task_name="Scan par Entropie")
    cancel_entropy_scan_button.on_click = partial(cancel_task, cancel_event=entropy_scan_cancel_event, controls_to_disable=entropy_task_config['controls_to_disable'], pause_button=pause_entropy_scan_button, cancel_button=cancel_entropy_scan_button, status_text=entropy_scan_status_text, task_name="Scan par Entropie")

    page.add(
        Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                Tab(
                    text="Validation",
                    icon=ft.Icons.KEY,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Row([api_key_input, service_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                                    Row([validate_button], alignment=ft.MainAxisAlignment.CENTER),
                                    Row([result_text], alignment=ft.MainAxisAlignment.CENTER)
                                ], spacing=20),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        alignment=ft.alignment.center
                    )
                ),
                Tab(
                    text="Scan Fichiers",
                    icon=ft.Icons.FOLDER_OPEN,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Row([pick_folder_button, start_scan_button, pause_scan_button, cancel_scan_button], alignment=ft.MainAxisAlignment.CENTER),
                                    scan_path_text,
                                    scan_progress,
                                    scan_status_text,
                                    scan_results_log
                                ], expand=True, scroll=ft.ScrollMode.ALWAYS),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        expand=True
                    )
                ),
                Tab(
                    text="Devinette",
                    icon=ft.Icons.CASINO,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Text("Brute-force", size=20),
                                    Row([brute_force_key_input, brute_force_service_dropdown, brute_force_depth_input], alignment=ft.MainAxisAlignment.CENTER),
                                    Row([brute_force_button, pause_brute_force_button, cancel_brute_force_button], alignment=ft.MainAxisAlignment.CENTER),
                                    brute_force_progress,
                                    brute_force_status_text,
                                    brute_force_result_log,
                                    Text("Attaque par Dictionnaire", size=20),
                                    Row([dict_key_input, dict_service_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                                    Row([pick_wordlist_button, dict_wordlist_path_text], alignment=ft.MainAxisAlignment.CENTER),
                                    Row([dict_button, pause_dict_button, cancel_dict_button], alignment=ft.MainAxisAlignment.CENTER),
                                    dict_progress,
                                    dict_status_text,
                                    dict_result_log,
                                ], spacing=20, scroll=ft.ScrollMode.ALWAYS),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        alignment=ft.alignment.center
                    )
                ),
                Tab(
                    text="Scan Git",
                    icon=ft.Icons.TRAVEL_EXPLORE,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Text("Scan de Dépôt Local", weight=FontWeight.BOLD),
                                    Row([pick_git_folder_button, start_local_git_scan_button], alignment=MainAxisAlignment.START),
                                    git_scan_path_text,
                                    ft.Divider(),
                                    Text("Scan de Dépôt Distant", weight=FontWeight.BOLD),
                                    Row([git_remote_url_input, start_remote_git_scan_button], alignment=MainAxisAlignment.START),
                                    ft.Divider(),
                                    Row([pause_git_scan_button, cancel_git_scan_button], alignment=MainAxisAlignment.CENTER),
                                    git_scan_progress,
                                    git_scan_status_text,
                                    git_scan_results_log
                                ], expand=True, scroll=ft.ScrollMode.ALWAYS),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        expand=True
                    )
                ),
                Tab(
                    text="Scan Entropie",
                    icon=ft.Icons.FLARE,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Row([pick_entropy_folder_button, start_entropy_scan_button, pause_entropy_scan_button, cancel_entropy_scan_button, entropy_threshold_input], alignment=ft.MainAxisAlignment.CENTER),
                                    entropy_scan_path_text,
                                    entropy_scan_progress,
                                    entropy_scan_status_text,
                                    entropy_scan_results_log
                                ], expand=True, scroll=ft.ScrollMode.ALWAYS),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        expand=True
                    )
                ),
                Tab(
                    text="Aide",
                    icon=ft.Icons.HELP_OUTLINE,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Text("Guide d'utilisation de l'Outil de Sécurité pour Clés API", size=24, weight=ft.FontWeight.BOLD),
                                    Text("Cet outil vous permet de valider, trouver et récupérer des clés API potentielles à des fins de sécurité.", size=16),
                                    ft.Divider(),
                                    Text("Onglet 'Validation':", size=20, weight=ft.FontWeight.BOLD),
                                    Text("- Saisissez une clé API et sélectionnez un service pour vérifier si la clé est valide pour ce service.", size=16),
                                    Text("- Utile pour tester rapidement une clé individuelle.", size=16),
                                    ft.Divider(),
                                    Text("Onglet 'Scan Fichiers':", size=20, weight=ft.FontWeight.BOLD),
                                    Text("- Sélectionnez un répertoire à scanner. L'outil recherchera des clés API potentielles dans les fichiers texte.", size=16),
                                    Text("- Les clés trouvées seront validées et les résultats affichés.", size=16),
                                    ft.Divider(),
                                    Text("Onglet 'Devinette':", size=20, weight=ft.FontWeight.BOLD),
                                    Text("  - 'Brute-force': Tente de compléter une clé partielle en ajoutant des caractères aléatoires jusqu'à une certaine profondeur.", size=16),
                                    Text("  - 'Attaque par Dictionnaire': Tente de compléter une clé partielle en utilisant une liste de mots fournie.", size=16),
                                    Text("- Nécessite une clé partielle et un service cible.", size=16),
                                    ft.Divider(),
                                    Text("Onglet 'Scan Git':", size=20, weight=ft.FontWeight.BOLD),
                                    Text("- Scanne l'historique d'un dépôt Git local à la recherche de clés API exposées dans les commits.", size=16),
                                    Text("- Très utile pour identifier les fuites passées.", size=16),
                                    ft.Divider(),
                                    Text("Onglet 'Scan Entropie':", size=20, weight=ft.FontWeight.BOLD),
                                    Text("- Scanne un répertoire pour trouver des chaînes de caractères à haute entropie, qui pourraient être des secrets.", size=16),
                                    Text("- Un seuil d'entropie peut être défini. Les résultats nécessitent une vérification manuelle.", size=16),
                                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.ALWAYS),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_GREY_800
                            )
                        ),
                        expand=True,
                        alignment=ft.alignment.center
                    )
                ),
            ],
            expand=1,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)

