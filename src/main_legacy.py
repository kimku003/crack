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
    CrossAxisAlignment,
    alignment,
    FontWeight,
)
from apikey_validator import core, config
from ui_theme import (
    Colors, Spacing, Breakpoints,
    create_button, create_text_field, create_dropdown, create_card,
    create_container, create_progress_bar, create_text, create_responsive_row,
    create_action_button, configure_page_theme
)
from ui_extensions import (
    create_loading_state, create_empty_state, create_error_state,
    create_simple_validated_text_field, MaterialIcons, get_material_icon,
    Animations, create_animated_container, PerformanceMonitor,
    NavigationFlow, create_shimmer_effect
)

# Constantes pour l'analyse cognitive (amélioration qualité code)
MAX_TABS = 8
CONTROLS_PER_TAB = 6


@PerformanceMonitor.measure_render_time
def main(page: ft.Page):

    page.title = "API Security Scanner"
    
    # Configuration du thème Material Design 3
    configure_page_theme(page)
    
    # Analyse de la charge cognitive (selon agent.yaml)
    tabs_count = MAX_TABS  # Nombre d'onglets
    controls_per_tab = CONTROLS_PER_TAB  # Moyenne des contrôles par onglet
    cognitive_load = NavigationFlow.calculate_cognitive_load(tabs_count, controls_per_tab)
    
    # Note: Charge cognitive élevée détectée mais acceptable pour cette application
    # Les suggestions d'amélioration sont documentées dans IMPLEMENTATION_COMPLETE.md

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
        color = Colors.SUCCESS if result.get('is_valid') else Colors.ERROR
        
        # Tronquer la clé pour la sécurité
        key_display = f"{result['key'][:4]}...{result['key'][-4:]}" if len(result['key']) > 8 else result['key']
        
        log_entry = f"[{result['timestamp']}] {result['service']} - {status} - Clé: {key_display} (Source: {result['source_type']} @ {result['source_info']})\n"
        
        # Pour Flet, il est plus sûr de mettre à jour les contrôles de cette manière
        result_log.value += log_entry
        page.update()

    find_last_key = {'value': ''}

    def find_ui_result_callback(result_log: TextField, result: dict):
        status = "VALIDE" if result.get('is_valid') else "INVALIDE"
        color = Colors.SUCCESS if result.get('is_valid') else Colors.ERROR
        key_display = f"{result['key'][:4]}...{result['key'][-4:]}" if len(result['key']) > 8 else result['key']
        log_entry = f"[{result['timestamp']}] {result['service']} - {status} - Clé: {key_display} (Source: {result['source_type']} @ {result['source_info']})\n"
        result_log.value += log_entry
        if result.get('is_valid'):
            find_last_key['value'] = result['key']
            import sys
            print(f"Clé générée complète : {result['key']}", file=sys.__stdout__, flush=True)
        page.update()

    # Remplacer le bouton copier pour utiliser la méthode Flet asynchrone
    def copy_last_key(e):
        if find_last_key['value']:
            page.set_clipboard(find_last_key['value'])
            import sys
            print(f"Clé copiée dans le presse-papier : {find_last_key['value']}", file=sys.__stdout__)

    find_copy_button = create_button(
        "Copier la clé", icon=ft.Icons.CONTENT_COPY, hierarchy="secondary",
        on_click=copy_last_key
    )

    # --- Onglet Validation ---
    api_key_input = create_simple_validated_text_field(
        label="Clé API", 
        password=True, 
        can_reveal_password=True
    )
    # Amélioration accessibilité : ajout de semantic_label
    api_key_input.semantic_label = "Champ de saisie pour la clé API à valider"
    service_dropdown = create_dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()])
    validate_button = create_button(text="Valider", icon=MaterialIcons.SECURITY, hierarchy="primary")
    result_text = create_text("", size=16, weight=ft.FontWeight.BOLD)

    def validate_key_click(e):
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
            validator = PATTERNS[service]["validator"]
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
        
        # Utilise le callback de résultat spécifique s'il est fourni, sinon le callback par défaut
        result_callback_func = task_config.get('result_callback_func', ui_result_callback)
        result_cb = partial(result_callback_func, task_config['result_log'])
        
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
    scan_path_text = create_text("")
    scan_results_log = create_text_field(label="Résultats du scan", multiline=True, read_only=True, expand=True)
    pick_folder_button = create_button("Sélectionner un Répertoire", hierarchy="secondary")
    start_scan_button = create_button("Lancer le Scan", hierarchy="primary")
    pause_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    scan_progress = create_progress_bar(visible=False)
    scan_status_text = create_text("", visible=False)
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
    brute_force_key_input = create_text_field(label="Clé partielle")
    brute_force_service_dropdown = create_dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()])
    brute_force_depth_input = create_text_field(label="Profondeur", value="2", keyboard_type=ft.KeyboardType.NUMBER)
    brute_force_button = create_button("Lancer Brute-force", hierarchy="primary")
    pause_brute_force_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_brute_force_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    brute_force_progress = create_progress_bar(visible=False)
    brute_force_status_text = create_text("", visible=False)
    brute_force_result_log = create_text_field(label="Résultats brute-force", multiline=True, read_only=True, expand=True)
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
    dict_key_input = create_text_field(label="Clé partielle")
    dict_service_dropdown = create_dropdown(label="Service", options=[ft.dropdown.Option(key) for key in PATTERNS.keys()])
    dict_wordlist_path_text = create_text("")
    pick_wordlist_button = create_button("Sélectionner un dictionnaire", hierarchy="secondary")
    dict_button = create_button("Lancer l'Attaque", hierarchy="primary")
    pause_dict_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_dict_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    dict_progress = create_progress_bar(visible=False)
    dict_status_text = create_text("", visible=False)
    dict_result_log = create_text_field(label="Résultats dictionnaire", multiline=True, read_only=True, expand=True)
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
    git_scan_path_text = create_text("")
    git_remote_url_input = create_text_field(label="URL du dépôt distant (ex: https://github.com/user/repo.git)", expand=True)
    git_scan_results_log = create_text_field(label="Résultats scan Git", multiline=True, read_only=True, expand=True)
    pick_git_folder_button = create_button("Sélectionner un Dépôt Local", hierarchy="secondary")
    start_local_git_scan_button = create_button("Lancer Scan Local", hierarchy="primary")
    start_remote_git_scan_button = create_button("Lancer Scan Distant", hierarchy="primary")
    pause_git_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_git_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    git_scan_progress = create_progress_bar(visible=False)
    git_scan_status_text = create_text("", visible=False)
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
    entropy_scan_path_text = create_text("")
    entropy_scan_results_log = create_text_field(label="Résultats scan entropie", multiline=True, read_only=True, expand=True)
    entropy_threshold_input = create_text_field(label="Seuil", value="4.0", keyboard_type=ft.KeyboardType.NUMBER)
    pick_entropy_folder_button = create_button("Sélectionner un Répertoire", hierarchy="secondary")
    start_entropy_scan_button = create_button("Lancer le Scan", hierarchy="primary")
    pause_entropy_scan_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    cancel_entropy_scan_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")
    entropy_scan_progress = create_progress_bar(visible=False)
    entropy_scan_status_text = create_text("", visible=False)
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

    # --- Onglet Trouver ---
    find_service_dropdown = create_dropdown(
        label="Service",
        options=[ft.dropdown.Option(key) for key in ["OpenAI", "Gemini"]], # Limiter aux services générables
        value="OpenAI" # Valeur par défaut
    )
    find_num_keys_input = create_text_field(
        label="Nombre de clés à générer",
        value="10",
        keyboard_type=ft.KeyboardType.NUMBER
    )
    find_progress = create_progress_bar(visible=False)
    find_status_text = create_text("", visible=False)
    find_result_log = create_text_field(label="Résultats génération", multiline=True, read_only=True, expand=True)
    find_pause_event = threading.Event()
    find_cancel_event = threading.Event()
    find_pause_button = create_action_button("Pause", MaterialIcons.PAUSE, "warning")
    find_cancel_button = create_action_button("Annuler", ft.Icons.CANCEL, "error")

    find_task_config = {
        'name': "Génération de clés",
        'target_func': core.mode_find_keys,
        'result_log': find_result_log,
        'result_callback_func': find_ui_result_callback,
        'pause_event': find_pause_event,
        'cancel_event': find_cancel_event,
        'controls_to_disable': [find_service_dropdown, find_num_keys_input],
        'progress_bar': find_progress,
        'status_text': find_status_text,
        'pause_button': find_pause_button,
        'cancel_button': find_cancel_button,
        'pre_check': lambda: find_service_dropdown.value and find_num_keys_input.value.isdigit() and int(find_num_keys_input.value) > 0,
        'error_message': "Veuillez sélectionner un service et un nombre de clés valide.",
        'get_core_args': lambda: {
            'service_specifie': find_service_dropdown.value,
            'num_keys_to_generate': int(find_num_keys_input.value)
        }
    }

    # --- Onglet Test Gemini & OpenAI ---
    test_api_key_input = create_text_field(label="Clé API à tester (Gemini ou OpenAI)", password=True, can_reveal_password=True)
    test_service_dropdown = create_dropdown(label="Service à tester", options=[ft.dropdown.Option("Gemini"), ft.dropdown.Option("OpenAI")], value="Gemini")
    test_result_text = create_text("", size=16, weight=ft.FontWeight.BOLD)
    test_button = create_button("Tester la clé avec l'API", icon=MaterialIcons.PLAY, hierarchy="primary")

    def run_gemini_test(api_key):
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
                return f"Clé Gemini VALIDE\nRéponse Gemini : {answer}"
            elif r.status_code == 401:
                return "Clé Gemini INVALIDE ou non autorisée"
            elif r.status_code == 429:
                return "Limite de requêtes Gemini atteinte"
            else:
                return f"Erreur Gemini: {r.status_code} - {r.text}"
        except requests.exceptions.RequestException as e:
            return f"Erreur lors de l'appel Gemini: {e}"

    def test_api_key(e):
        key = test_api_key_input.value
        service = test_service_dropdown.value
        import re
        if not key or not re.match(r"^[a-zA-Z0-9_-]{30,100}$", key):
            test_result_text.value = "Clé invalide (mauvais format)"
            test_result_text.color = Colors.ERROR
            page.update()
            return
        test_result_text.value = "Test en cours..."
        test_result_text.color = Colors.WARNING
        page.update()
        def worker():
            if service == "Gemini":
                result = run_gemini_test(key)
            else:
                result = core.tester_cle_openai(key)
            test_result_text.value = result
            test_result_text.color = Colors.SUCCESS if "VALIDE" in result and not result.startswith("Erreur") else Colors.ERROR
            page.update()
        threading.Thread(target=worker, daemon=True).start()
    test_button.on_click = test_api_key

    test_tab = Tab(
        text="Test",
        icon=ft.Icons.BUG_REPORT,
        content=Container(
            content=create_card(
                content=Column([
                    create_text("Test d'une clé Gemini ou OpenAI", size=20, weight=ft.FontWeight.BOLD),
                    test_service_dropdown,
                    test_api_key_input,
                    test_button,
                    test_result_text
                ], spacing=Spacing.LG),
                padding=Spacing.XL
            ),
            expand=True,
            alignment=ft.alignment.center
        )
    )

    page.add(
        ft.SafeArea(
            content=Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    Tab(
                        text="Validation",
                        icon=MaterialIcons.KEY,
                        content=Container(
                            content=create_card(
                                content=Column([
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
                    ),
                    Tab(
                        text="Scan Fichiers",
                        icon=MaterialIcons.FOLDER,
                        content=Container(
                            content=create_card(
                                content=Column([
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
                    ),
                    Tab(
                        text="Devinette",
                        icon=ft.Icons.CASINO,
                        content=Container(
                            content=create_card(
                                content=Column([
                                    create_text("Brute-force", size=20, weight=ft.FontWeight.BOLD),
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 5}, controls=[brute_force_key_input]),
                                        ft.Column(col={"sm": 12, "md": 4}, controls=[brute_force_service_dropdown]),
                                        ft.Column(col={"sm": 12, "md": 3}, controls=[brute_force_depth_input]),
                                    ]),
                                    create_responsive_row([brute_force_button, pause_brute_force_button, cancel_brute_force_button]),
                                    brute_force_progress,
                                    brute_force_status_text,
                                    brute_force_result_log,
                                    create_text("Attaque par Dictionnaire", size=20, weight=ft.FontWeight.BOLD),
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[dict_key_input]),
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[dict_service_dropdown]),
                                    ]),
                                    create_responsive_row([pick_wordlist_button, dict_wordlist_path_text]),
                                    create_responsive_row([dict_button, pause_dict_button, cancel_dict_button]),
                                    dict_progress,
                                    dict_status_text,
                                    dict_result_log,
                                ], spacing=Spacing.LG, scroll=ft.ScrollMode.ALWAYS),
                                padding=Spacing.XL
                            ),
                            alignment=ft.alignment.center
                        )
                    ),
                    Tab(
                        text="Scan Git",
                        icon=ft.Icons.TRAVEL_EXPLORE,
                        content=Container(
                            content=create_card(
                                content=Column([
                                    create_text("Scan de Dépôt Local", weight=FontWeight.BOLD),
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[pick_git_folder_button]),
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[start_local_git_scan_button]),
                                    ]),
                                    git_scan_path_text,
                                    ft.Divider(),
                                    create_text("Scan de Dépôt Distant", weight=FontWeight.BOLD),
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 9}, controls=[git_remote_url_input]),
                                        ft.Column(col={"sm": 12, "md": 3}, controls=[start_remote_git_scan_button]),
                                    ]),
                                    ft.Divider(),
                                    create_responsive_row([pause_git_scan_button, cancel_git_scan_button]),
                                    git_scan_progress,
                                    git_scan_status_text,
                                    git_scan_results_log
                                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=Spacing.MD),
                                padding=Spacing.XL
                            ),
                            expand=True
                        )
                    ),
                    Tab(
                        text="Scan Entropie",
                        icon=ft.Icons.FLARE,
                        content=Container(
                            content=create_card(
                                content=Column([
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 3}, controls=[pick_entropy_folder_button]),
                                        ft.Column(col={"sm": 12, "md": 3}, controls=[start_entropy_scan_button]),
                                        ft.Column(col={"sm": 12, "md": 2}, controls=[pause_entropy_scan_button]),
                                        ft.Column(col={"sm": 12, "md": 2}, controls=[cancel_entropy_scan_button]),
                                        ft.Column(col={"sm": 12, "md": 2}, controls=[entropy_threshold_input]),
                                    ]),
                                    entropy_scan_path_text,
                                    entropy_scan_progress,
                                    entropy_scan_status_text,
                                    entropy_scan_results_log
                                ], expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=Spacing.MD),
                                padding=Spacing.XL
                            ),
                            expand=True
                        )
                    ),
                    Tab(
                        text="Trouver",
                        icon=ft.Icons.SEARCH,
                        content=Container(
                            content=create_card(
                                content=Column([
                                    create_text("Générer une clé API valide pour un service", size=20, weight=ft.FontWeight.BOLD),
                                    create_responsive_row([
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[find_service_dropdown]),
                                        ft.Column(col={"sm": 12, "md": 6}, controls=[find_num_keys_input]),
                                    ]),
                                    create_responsive_row([
                                        create_button("Lancer la génération", icon=MaterialIcons.PLAY, hierarchy="primary", on_click=partial(start_task, task_config=find_task_config)),
                                        find_pause_button,
                                        find_cancel_button,
                                        find_copy_button,
                                    ]),
                                    find_progress,
                                    find_status_text,
                                    find_result_log
                                ], spacing=Spacing.LG, scroll=ft.ScrollMode.ALWAYS),
                                padding=Spacing.XL
                            ),
                            expand=True,
                            alignment=ft.alignment.center
                        )
                    ),
                    Tab(
                        text="Aide",
                        icon=ft.Icons.HELP_OUTLINE,
                        content=Container(
                            content=create_card(
                                content=Column([
                                    create_text("Guide d'utilisation de l'Outil de Sécurité pour Clés API", size=24, weight=ft.FontWeight.BOLD),
                                    create_text("Cet outil vous permet de valider, trouver et récupérer des clés API potentielles à des fins de sécurité.", size=16),
                                    ft.Divider(),
                                    create_text("Onglet 'Validation':", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Saisissez une clé API et sélectionnez un service pour vérifier si la clé est valide pour ce service.", size=16),
                                    create_text("- Utile pour tester rapidement une clé individuelle.", size=16),
                                    ft.Divider(),
                                    create_text("Onglet 'Scan Fichiers':", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Sélectionnez un répertoire à scanner. L'outil recherchera des clés API potentielles dans les fichiers texte.", size=16),
                                    create_text("- Les clés trouvées seront validées et les résultats affichés.", size=16),
                                    ft.Divider(),
                                    create_text("Onglet 'Devinette':", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("  - 'Brute-force': Tente de compléter une clé partielle en ajoutant des caractères aléatoires jusqu'à une certaine profondeur.", size=16),
                                    create_text("  - 'Attaque par Dictionnaire': Tente de compléter une clé partielle en utilisant une liste de mots fournie.", size=16),
                                    create_text("- Nécessite une clé partielle et un service cible.", size=16),
                                    ft.Divider(),
                                    create_text("Limitations:", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Le scan de fichiers est limité aux fichiers textes. Les fichiers binaires ne sont pas scannés.", size=16),
                                    create_text("- Le scan Git peut prendre du temps sur les grands dépôts.", size=16),
                                    create_text("- L'attaque par dictionnaire dépend de la qualité de la liste de mots fournie.", size=16),
                                    ft.Divider(),
                                    create_text("Dépannage:", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Si vous rencontrez des problèmes avec la configuration de la clé API Gemini, vérifiez que vous avez correctement créé le fichier config.json et que la clé est valide.", size=16),
                                    create_text("- Si vous rencontrez des erreurs d'installation des dépendances, assurez-vous d'utiliser une version de Python compatible et essayez d'installer les dépendances avec pip ou Poetry.", size=16),
                                    ft.Divider(),
                                    create_text("Onglet 'Scan Git':", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Scanne l'historique d'un dépôt Git local à la recherche de clés API exposées dans les commits.", size=16),
                                    create_text("- Très utile pour identifier les fuites passées.", size=16),
                                    ft.Divider(),
                                    create_text("Onglet 'Scan Entropie':", size=20, weight=ft.FontWeight.BOLD),
                                    create_text("- Scanne un répertoire pour trouver des chaînes de caractères à haute entropie, qui pourraient être des secrets.", size=16),
                                    create_text("- Un seuil d'entropie peut être défini. Les résultats nécessitent une vérification manuelle.", size=16),
                                ], spacing=Spacing.SM, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.ALWAYS),
                                padding=Spacing.XL
                            ),
                            expand=True,
                            alignment=ft.alignment.center
                        )
                    ),
                    test_tab,
                ],
                expand=1,
            ),
            expand=True
        )
    )





if __name__ == "__main__":
    ft.app(target=main)