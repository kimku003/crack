import flet as ft
import os
import threading
from functools import partial
from flet import TextField, Dropdown, ElevatedButton, Text, Column
from apikey_validator import core

# Ce fichier contient les fonctions pour créer tous les dialogues de l'application.

def create_scan_dialog(start_task_func, result_callback_func, file_picker, close_dialog_func):
    path_text = ft.Text()
    status_text = ft.Text(visible=False, color=ft.Colors.RED)
    pause_event, cancel_event = threading.Event(), threading.Event()

    task_config = {
        'name': "Scan Fichiers",
        'target_func': core.mode_scan,
        'pause_event': pause_event,
        'cancel_event': cancel_event,
        'dialog_status_text': status_text,
        'pre_check': lambda: path_text.value and os.path.isdir(path_text.value),
        'error_message': "Répertoire invalide.",
        'get_core_args': lambda: {'scan_path': path_text.value},
        'result_callback_func': result_callback_func
    }

    def on_result(r):
        path_text.value = r.path or ""
        dialog.content.update()

    file_picker.on_result = on_result

    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Scanner un répertoire"),
        content=Column([
            ElevatedButton("Sélectionner Répertoire", on_click=lambda _: file_picker.get_directory_path()),
            path_text,
            status_text
        ], tight=True, height=120),
        actions=[
            ElevatedButton("Lancer", on_click=partial(start_task_func, task_config=task_config)),
            ft.TextButton("Fermer", on_click=close_dialog_func)
        ]
    )
    return dialog

def create_git_dialog(start_task_func, result_callback_func, file_picker, patterns, close_dialog_func):
    path_text = ft.Text()
    remote_url_input = ft.TextField(label="URL du dépôt distant")
    status_text = ft.Text(visible=False, color=ft.Colors.RED)
    pause_event, cancel_event = threading.Event(), threading.Event()

    local_cfg = {'name':"Scan Git Local", 'target_func':core.mode_scan_git, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: hasattr(path_text, 'data') and path_text.data, 'error_message':"Dépôt local invalide.", 'get_core_args':lambda: {'repo_path':path_text.data}, 'result_callback_func':result_callback_func}
    remote_cfg = {'name':"Scan Git Distant", 'target_func':core.mode_scan_remote_git, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: remote_url_input.value, 'error_message':"URL distante invalide.", 'get_core_args':lambda: {'repo_url':remote_url_input.value}, 'result_callback_func':result_callback_func}

    def on_result(r):
        path_text.value = f"Dépôt: {r.path}" if r.path else ""
        path_text.data = r.path
        dialog.content.update()
    
    file_picker.on_result = on_result

    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Scanner un dépôt Git"),
        content=Column([
            Text("Scan Local"),
            ElevatedButton("Sélectionner Dépôt", on_click=lambda _: file_picker.get_directory_path()),
            path_text,
            ElevatedButton("Lancer Scan Local", on_click=partial(start_task_func, task_config=local_cfg)),
            ft.Divider(),
            Text("Scan Distant"),
            remote_url_input,
            ElevatedButton("Lancer Scan Distant", on_click=partial(start_task_func, task_config=remote_cfg)),
            status_text
        ], tight=True, height=280),
        actions=[ft.TextButton("Fermer", on_click=close_dialog_func)]
    )
    return dialog

def create_guess_dialog(start_task_func, result_callback_func, file_picker, patterns, close_dialog_func):
    bf_key_input = TextField(label="Clé partielle")
    bf_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(k) for k in patterns.keys()])
    bf_depth_input = TextField(label="Profondeur", value="2")
    dict_key_input = TextField(label="Clé partielle")
    dict_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(k) for k in patterns.keys()])
    dict_wordlist_path_text = Text()
    status_text = Text(visible=False, color=ft.Colors.RED)
    pause_event, cancel_event = threading.Event(), threading.Event()

    bf_cfg = {'name':"Brute-force", 'target_func':core.mode_brute_force, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: bf_key_input.value and bf_service_dropdown.value, 'error_message':"Clé et service requis.", 'get_core_args':lambda: {'cle_partielle':bf_key_input.value, 'service_specifie':bf_service_dropdown.value, 'depth':int(bf_depth_input.value)}, 'result_callback_func':result_callback_func}
    dict_cfg = {'name':"Attaque Dictionnaire", 'target_func':core.mode_dictionnaire, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: dict_key_input.value and dict_service_dropdown.value and dict_wordlist_path_text.value, 'error_message':"Clé, service et wordlist requis.", 'get_core_args':lambda: {'cle_partielle':dict_key_input.value, 'service_specifie':dict_service_dropdown.value, 'wordlist_path':dict_wordlist_path_text.value}, 'result_callback_func':result_callback_func}

    def on_result(r):
        dict_wordlist_path_text.value = r.files[0].path if r.files else ""
        dialog.content.update()

    file_picker.on_result = on_result

    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Devinette de Clé"),
        content=Column([
            Text("Brute-force"), bf_key_input, bf_service_dropdown, bf_depth_input,
            ElevatedButton("Lancer Brute-force", on_click=partial(start_task_func, task_config=bf_cfg)),
            ft.Divider(),
            Text("Attaque Dictionnaire"), dict_key_input, dict_service_dropdown,
            ElevatedButton("Sélectionner Dictionnaire", on_click=lambda _: file_picker.pick_files()),
            dict_wordlist_path_text,
            ElevatedButton("Lancer Attaque", on_click=partial(start_task_func, task_config=dict_cfg)),
            status_text
        ], scroll=ft.ScrollMode.ALWAYS, height=350),
        actions=[ft.TextButton("Fermer", on_click=close_dialog_func)]
    )
    return dialog

def create_entropy_dialog(start_task_func, result_callback_func, file_picker, close_dialog_func):
    path_text = Text()
    threshold_input = TextField(label="Seuil d'entropie", value="4.0")
    status_text = Text(visible=False, color=ft.Colors.RED)
    pause_event, cancel_event = threading.Event(), threading.Event()

    def entropy_cb(r): result_callback_func({'service':'Entropie', 'key':r['chaine'], 'is_valid':False, 'source_type':'Fichier', 'source_info':r['source_info'], 'timestamp':r.get('timestamp','')})
    
    task_config = {'name':"Scan Entropie", 'target_func':core.mode_scan_entropy, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: path_text.value and os.path.isdir(path_text.value), 'error_message':"Répertoire invalide.", 'get_core_args':lambda: {'scan_path':path_text.value, 'seuil':float(threshold_input.value)}, 'result_callback_func':entropy_cb}

    def on_result(r):
        path_text.value = r.path or ""
        dialog.content.update()

    file_picker.on_result = on_result

    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Scan par Entropie"),
        content=Column([
            ElevatedButton("Sélectionner Répertoire", on_click=lambda _: file_picker.get_directory_path()),
            path_text, threshold_input,
            ElevatedButton("Lancer Scan", on_click=partial(start_task_func, task_config=task_config)),
            status_text
        ], tight=True, height=200),
        actions=[ft.TextButton("Fermer", on_click=close_dialog_func)]
    )
    return dialog

def create_find_dialog(start_task_func, result_callback_func, close_dialog_func):
    service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(k) for k in ["OpenAI", "Gemini"]], value="OpenAI")
    num_keys_input = TextField(label="Nombre de clés", value="10", keyboard_type=ft.KeyboardType.NUMBER)
    status_text = Text(visible=False, color=ft.Colors.RED)
    pause_event, cancel_event = threading.Event(), threading.Event()

    task_config = {'name':"Génération de clés", 'target_func':core.mode_find_keys, 'pause_event':pause_event, 'cancel_event':cancel_event, 'dialog_status_text':status_text, 'pre_check':lambda: service_dropdown.value and num_keys_input.value.isdigit(), 'error_message':"Service et nombre invalides.", 'get_core_args':lambda: {'service_specifie':service_dropdown.value, 'num_keys_to_generate':int(num_keys_input.value)}, 'result_callback_func':result_callback_func}
    
    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Trouver des Clés Valides"),
        content=Column([
            service_dropdown, num_keys_input,
            ElevatedButton("Lancer", on_click=partial(start_task_func, task_config=task_config)),
            status_text
        ], tight=True, height=200),
        actions=[ft.TextButton("Fermer", on_click=close_dialog_func)]
    )
    return dialog

def create_test_dialog(page, close_dialog_func):
    api_key_input = TextField(label="Clé API à tester", password=True, can_reveal_password=True)
    service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option("Gemini"), ft.dropdown.Option("OpenAI")], value="Gemini")
    result_text = Text(weight=ft.FontWeight.BOLD)

    def run_gemini_test(api_key):
        import requests
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}", headers={"Content-Type":"application/json"}, json={"contents":[{"parts":[{"text":"H"}]}]}, timeout=15)
            return f"Clé Gemini VALIDE" if r.status_code == 200 and "candidates" in r.json() else f"Clé Gemini INVALIDE ({r.status_code})"
        except requests.exceptions.RequestException as e: return f"Erreur: {e}"

    def test_api_key_action(e):
        key, service = api_key_input.value, service_dropdown.value
        result_text.value = "Test en cours..."; result_text.color = ft.Colors.AMBER; dialog.content.update()
        def worker():
            result = core.tester_cle_openai(key) if service == "OpenAI" else run_gemini_test(key)
            def update_ui(): result_text.value = result; result_text.color = ft.Colors.GREEN if "VALIDE" in result else ft.Colors.RED; dialog.content.update()
            page.run_thread(target=update_ui)
        threading.Thread(target=worker, daemon=True).start()

    dialog = ft.AlertDialog(
        modal=True,
        title=Text("Test Manuel de Clé API"),
        content=Column([
            service_dropdown, api_key_input,
            ElevatedButton("Tester", on_click=test_api_key_action),
            result_text
        ], tight=True, height=200),
        actions=[ft.TextButton("Fermer", on_click=close_dialog_func)]
    )
    return dialog
