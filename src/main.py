
import flet as ft
import os
import threading
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
from apikey_validator import valider_cle_gemini

class UILogger:
    def __init__(self, result_log: TextField, progress_bar: ProgressBar, page: ft.Page, status_text: Text):
        self.result_log = result_log
        self.progress_bar = progress_bar
        self.page = page
        self.buffer = ""
        self.status_text = status_text

    def write(self, message: str):
        self.buffer += message
        if "\n" in self.buffer:
            self.result_log.value += self.buffer
            self.buffer = ""
            self.page.update()
        
        last_line = message.strip().split('\n')[-1]
        if last_line:
            self.status_text.value = last_line
            self.page.update()

    def flush(self):
        pass

def main(page: ft.Page):

    page.title = "Outil de Sécurité pour Clés API"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLUE_GREY_900

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, 'apikey_validator', 'config.json')
        valider_cle_gemini.PATTERNS = valider_cle_gemini.charger_patterns(config_path)
    except Exception as e:
        page.add(ft.Text(f"Erreur fatale à l'initialisation : {e}"))
        return

    if not valider_cle_gemini.PATTERNS:
        page.add(ft.Text("Erreur: Impossible de charger la configuration des secrets."))
        return

    def create_task_runner(target_func, controls_to_disable, progress_bar, result_log, status_text, pause_event, cancel_event, *args):
        def task_wrapper():
            progress_bar.visible = True
            status_text.visible = True
            for c in controls_to_disable:
                c.disabled = True
            page.update()
            
            original_stdout = valider_cle_gemini.sys.stdout
            valider_cle_gemini.sys.stdout = UILogger(result_log, progress_bar, page, status_text)
            
            try:
                target_func(*args, pause_event, cancel_event)
            finally:
                valider_cle_gemini.sys.stdout = original_stdout
                progress_bar.visible = False
                status_text.visible = False
                for c in controls_to_disable:
                    c.disabled = False
                    if isinstance(c, ft.ElevatedButton) and (c.text == "Pause" or c.text == "Annuler"):
                        c.visible = False
                page.update()

        return task_wrapper

    # --- Onglet Validation ---
    api_key_input = TextField(label="Clé API", width=450, password=True, can_reveal_password=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in valider_cle_gemini.PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
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

        validator = valider_cle_gemini.PATTERNS[service]["validator"]
        is_valid = validator(key, silencieux=True)
        if is_valid:
            result_text.value = f"SUCCÈS : La clé pour {service} est VALIDE."
            result_text.color = ft.Colors.GREEN
        else:
            result_text.value = f"ÉCHEC : La clé pour {service} est INVALIDE."
            result_text.color = ft.Colors.RED
        page.update()
    validate_button.on_click = validate_key_click

    # --- Onglet Scan de Fichiers ---
    scan_path_text = Text()
    scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_folder_button = ElevatedButton("Sélectionner un Répertoire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_scan_button = ElevatedButton("Lancer le Scan", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    cancel_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, disabled=True, visible=False)
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

    def start_scan_click(e):
        path = scan_path_text.value
        if not path or not os.path.isdir(path):
            scan_results_log.value = "Erreur: Veuillez sélectionner un répertoire valide."
            page.update()
            return
        scan_results_log.value = f"[*] Démarrage du scan dans : {path}\n"
        scan_pause_event.clear()
        scan_cancel_event.clear()
        start_scan_button.disabled = True
        pick_folder_button.disabled = True
        pause_scan_button.disabled = False
        cancel_scan_button.disabled = False
        pause_scan_button.visible = True
        cancel_scan_button.visible = True
        page.update()
        task = create_task_runner(valider_cle_gemini.mode_scan, [start_scan_button, pick_folder_button, pause_scan_button, cancel_scan_button], scan_progress, scan_results_log, scan_status_text, scan_pause_event, scan_cancel_event, type('Args', (), {'path': path}))
        threading.Thread(target=task, daemon=True).start()
    start_scan_button.on_click = start_scan_click

    def pause_scan_click(e):
        if pause_scan_button.text == "Pause":
            scan_pause_event.set()
            pause_scan_button.text = "Reprendre"
            scan_status_text.value = "[*] Scan en pause..."
        else:
            scan_pause_event.clear()
            pause_scan_button.text = "Pause"
            scan_status_text.value = "[*] Reprise du scan..."
        page.update()
    pause_scan_button.on_click = pause_scan_click

    def cancel_scan_click(e):
        scan_cancel_event.set()
        scan_status_text.value = "[*] Annulation du scan..."
        start_scan_button.disabled = False
        pick_folder_button.disabled = False
        pause_scan_button.disabled = True
        cancel_scan_button.disabled = True
        pause_scan_button.text = "Pause"
        page.update()
    cancel_scan_button.on_click = cancel_scan_click

    start_scan_button.on_click = start_scan_click

    # --- Onglet Devinette ---
    brute_force_key_input = TextField(label="Clé partielle", width=300, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in valider_cle_gemini.PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_depth_input = TextField(label="Profondeur", width=100, value="2", filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    brute_force_button = ElevatedButton("Lancer Brute-force", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_brute_force_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    cancel_brute_force_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    brute_force_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    brute_force_status_text = Text("", visible=False)

    brute_force_pause_event = threading.Event()
    brute_force_cancel_event = threading.Event()
    brute_force_result_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)

    dict_key_input = TextField(label="Clé partielle", width=300, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    dict_service_dropdown = Dropdown(label="Service", options=[ft.dropdown.Option(key) for key in valider_cle_gemini.PATTERNS.keys()], width=200, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    dict_wordlist_path_text = Text()
    pick_wordlist_button = ElevatedButton("Sélectionner un dictionnaire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    dict_button = ElevatedButton("Lancer l'Attaque", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_dict_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    cancel_dict_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    dict_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    dict_status_text = Text("", visible=False)

    dict_pause_event = threading.Event()
    dict_cancel_event = threading.Event()
    dict_result_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)

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

    def start_brute_force_click(e):
        key = brute_force_key_input.value
        service = brute_force_service_dropdown.value
        depth = int(brute_force_depth_input.value)
        if not key or not service:
            brute_force_result_log.value = "Erreur: Veuillez fournir une clé partielle et un service."
            page.update()
            return
        brute_force_result_log.value = f"[*] Démarrage du brute-force pour {service}...\n"
        brute_force_pause_event.clear()
        brute_force_cancel_event.clear()
        brute_force_button.disabled = True
        pause_brute_force_button.disabled = False
        cancel_brute_force_button.disabled = False
        pause_brute_force_button.visible = True
        cancel_brute_force_button.visible = True
        page.update()
        task = create_task_runner(valider_cle_gemini.mode_brute_force, [brute_force_button, pause_brute_force_button, cancel_brute_force_button], brute_force_progress, brute_force_result_log, brute_force_status_text, brute_force_pause_event, brute_force_cancel_event, type('Args', (), {'partial_key': key, 'type': service, 'depth': depth}))
        threading.Thread(target=task, daemon=True).start()
    brute_force_button.on_click = start_brute_force_click

    def pause_brute_force_click(e):
        if pause_brute_force_button.text == "Pause":
            brute_force_pause_event.set()
            pause_brute_force_button.text = "Reprendre"
            brute_force_status_text.value = "[*] Brute-force en pause..."
        else:
            brute_force_pause_event.clear()
            pause_brute_force_button.text = "Pause"
            brute_force_status_text.value = "[*] Reprise du brute-force..."
        page.update()
    pause_brute_force_button.on_click = pause_brute_force_click

    def cancel_brute_force_click(e):
        brute_force_cancel_event.set()
        brute_force_status_text.value = "[*] Annulation du brute-force..."
        brute_force_button.disabled = False
        pause_brute_force_button.disabled = True
        cancel_brute_force_button.disabled = True
        pause_brute_force_button.text = "Pause"
        page.update()
    cancel_brute_force_button.on_click = cancel_brute_force_click

    def start_dict_attack_click(e):
        key = dict_key_input.value
        service = dict_service_dropdown.value
        wordlist = dict_wordlist_path_text.value
        if not key or not service or not wordlist:
            dict_result_log.value = "Erreur: Veuillez fournir une clé partielle, un service et un dictionnaire."
            page.update()
            return
        dict_result_log.value = f"[*] Démarrage de l'attaque par dictionnaire pour {service}...\n"
        dict_pause_event.clear()
        dict_cancel_event.clear()
        dict_button.disabled = True
        pick_wordlist_button.disabled = True
        pause_dict_button.disabled = False
        cancel_dict_button.disabled = False
        pause_dict_button.visible = True
        cancel_dict_button.visible = True
        page.update()
        task = create_task_runner(valider_cle_gemini.mode_dictionnaire, [dict_button, pick_wordlist_button, pause_dict_button, cancel_dict_button], dict_progress, dict_result_log, dict_status_text, dict_pause_event, dict_cancel_event, type('Args', (), {'partial_key': key, 'type': service, 'wordlist': wordlist}))
        threading.Thread(target=task, daemon=True).start()
    dict_button.on_click = start_dict_attack_click

    def pause_dict_click(e):
        if pause_dict_button.text == "Pause":
            dict_pause_event.set()
            pause_dict_button.text = "Reprendre"
            dict_status_text.value = "[*] Attaque par dictionnaire en pause..."
        else:
            dict_pause_event.clear()
            pause_dict_button.text = "Pause"
            dict_status_text.value = "[*] Reprise de l'attaque par dictionnaire..."
        page.update()
    pause_dict_button.on_click = pause_dict_click

    def cancel_dict_click(e):
        dict_cancel_event.set()
        dict_status_text.value = "[*] Annulation de l'attaque par dictionnaire..."
        dict_button.disabled = False
        pick_wordlist_button.disabled = False
        pause_dict_button.disabled = True
        cancel_dict_button.disabled = True
        pause_dict_button.text = "Pause"
        page.update()
    cancel_dict_button.on_click = cancel_dict_click

    # --- Onglet Scan Git ---
    git_scan_path_text = Text()
    git_scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_git_folder_button = ElevatedButton("Sélectionner un Dépôt Git", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_git_scan_button = ElevatedButton("Lancer le Scan Git", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_git_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    cancel_git_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    git_scan_progress = ProgressBar(visible=False, color=ft.Colors.LIGHT_BLUE_ACCENT_400, bgcolor=ft.Colors.BLUE_GREY_700)
    git_scan_status_text = Text("", visible=False)

    git_scan_pause_event = threading.Event()
    git_scan_cancel_event = threading.Event()

    def pick_git_folder_action(e):
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                git_scan_path_text.value = result.path
                page.update()
        file_picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
    pick_git_folder_button.on_click = pick_git_folder_action

    def start_git_scan_click(e):
        path = git_scan_path_text.value
        if not path or not os.path.isdir(path):
            git_scan_results_log.value = "Erreur: Veuillez sélectionner un dépôt Git valide."
            page.update()
            return
        git_scan_results_log.value = f"[*] Démarrage du scan Git dans : {path}\n"
        git_scan_pause_event.clear()
        git_scan_cancel_event.clear()
        start_git_scan_button.disabled = True
        pick_git_folder_button.disabled = True
        pause_git_scan_button.disabled = False
        cancel_git_scan_button.disabled = False
        pause_git_scan_button.visible = True
        cancel_git_scan_button.visible = True
        page.update()
        task = create_task_runner(valider_cle_gemini.mode_scan_git, [start_git_scan_button, pick_git_folder_button, pause_git_scan_button, cancel_git_scan_button], git_scan_progress, git_scan_results_log, git_scan_status_text, git_scan_pause_event, git_scan_cancel_event, type('Args', (), {'path': path}))
        threading.Thread(target=task, daemon=True).start()
    start_git_scan_button.on_click = start_git_scan_click

    def pause_git_scan_click(e):
        if pause_git_scan_button.text == "Pause":
            git_scan_pause_event.set()
            pause_git_scan_button.text = "Reprendre"
            git_scan_status_text.value = "[*] Scan Git en pause..."
        else:
            git_scan_pause_event.clear()
            pause_git_scan_button.text = "Pause"
            git_scan_status_text.value = "[*] Reprise du scan Git..."
        page.update()
    pause_git_scan_button.on_click = pause_git_scan_click

    def cancel_git_scan_click(e):
        git_scan_cancel_event.set()
        git_scan_status_text.value = "[*] Annulation du scan Git..."
        start_git_scan_button.disabled = False
        pick_git_folder_button.disabled = False
        pause_git_scan_button.disabled = True
        cancel_git_scan_button.disabled = True
        pause_git_scan_button.text = "Pause"
        page.update()
    cancel_git_scan_button.on_click = cancel_git_scan_click

    # --- Onglet Scan par Entropie ---
    entropy_scan_path_text = Text()
    entropy_scan_results_log = TextField(multiline=True, read_only=True, expand=True, filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    entropy_threshold_input = TextField(label="Seuil", width=100, value="4.0", filled=True, bgcolor=ft.Colors.BLUE_GREY_700, border_color=ft.Colors.TRANSPARENT)
    pick_entropy_folder_button = ElevatedButton("Sélectionner un Répertoire", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    start_entropy_scan_button = ElevatedButton("Lancer le Scan par Entropie", bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
    pause_entropy_scan_button = ElevatedButton("Pause", icon=ft.Icons.PAUSE, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, disabled=True, visible=False)
    cancel_entropy_scan_button = ElevatedButton("Annuler", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, disabled=True, visible=False)
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

    def start_entropy_scan_click(e):
        path = entropy_scan_path_text.value
        threshold = float(entropy_threshold_input.value)
        if not path or not os.path.isdir(path):
            entropy_scan_results_log.value = "Erreur: Veuillez sélectionner un répertoire valide."
            page.update()
            return
        entropy_scan_results_log.value = f"[*] Démarrage du scan par entropie dans : {path}\n"
        entropy_scan_pause_event.clear()
        entropy_scan_cancel_event.clear()
        start_entropy_scan_button.disabled = True
        pick_entropy_folder_button.disabled = False
        pause_entropy_scan_button.disabled = False
        cancel_entropy_scan_button.disabled = False
        pause_entropy_scan_button.visible = True
        cancel_entropy_scan_button.visible = True
        page.update()
        task = create_task_runner(valider_cle_gemini.mode_scan_entropy, [start_entropy_scan_button, pick_entropy_folder_button, pause_entropy_scan_button, cancel_entropy_scan_button], entropy_scan_progress, entropy_scan_results_log, entropy_scan_status_text, entropy_scan_pause_event, entropy_scan_cancel_event, type('Args', (), {'path': path, 'threshold': threshold}))
        threading.Thread(target=task, daemon=True).start()
    start_entropy_scan_button.on_click = start_entropy_scan_click

    def pause_entropy_scan_click(e):
        if pause_entropy_scan_button.text == "Pause":
            entropy_scan_pause_event.set()
            pause_entropy_scan_button.text = "Reprendre"
            entropy_scan_status_text.value = "[*] Scan par entropie en pause..."
        else:
            entropy_scan_pause_event.clear()
            pause_entropy_scan_button.text = "Pause"
            entropy_scan_status_text.value = "[*] Reprise du scan par entropie..."
        page.update()
    pause_entropy_scan_button.on_click = pause_entropy_scan_click

    def cancel_entropy_scan_click(e):
        entropy_scan_cancel_event.set()
        entropy_scan_status_text.value = "[*] Annulation du scan par entropie..."
        start_entropy_scan_button.disabled = False
        pick_entropy_folder_button.disabled = False
        pause_entropy_scan_button.disabled = True
        cancel_entropy_scan_button.disabled = True
        pause_entropy_scan_button.text = "Pause"
        page.update()
    cancel_entropy_scan_button.on_click = cancel_entropy_scan_click

    def build_tab_content():
        # ... (Le code pour construire les autres onglets sera ajouté ici)
        pass

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
                # Les autres onglets seront ajoutés ici
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
                    icon=ft.Icons.HISTORY,
                    content=Container(
                        content=Card(
                            content=Container(
                                content=Column([
                                    Row([pick_git_folder_button, start_git_scan_button, pause_git_scan_button, cancel_git_scan_button], alignment=ft.MainAxisAlignment.CENTER),
                                    git_scan_path_text,
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
