"""
Gestionnaire de tâches pour l'application Flet
Extrait de main.py pour améliorer la modularité
"""

import threading
from functools import partial
from typing import Dict, Any, Callable
import flet as ft
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui_theme import Colors


class TaskManager:
    """Gestionnaire centralisé pour les tâches asynchrones de l'application"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.active_tasks = {}
    
    def create_task_runner(
        self, 
        target_func: Callable, 
        controls_to_manage: Dict[str, Any], 
        pause_button: ft.ElevatedButton, 
        cancel_button: ft.ElevatedButton, 
        pause_event: threading.Event, 
        cancel_event: threading.Event, 
        **kwargs
    ) -> Callable:
        """
        Crée un wrapper pour exécuter une tâche avec gestion des contrôles UI
        
        Args:
            target_func: Fonction à exécuter
            controls_to_manage: Dictionnaire des contrôles UI à gérer
            pause_button: Bouton de pause
            cancel_button: Bouton d'annulation
            pause_event: Événement de pause
            cancel_event: Événement d'annulation
            **kwargs: Arguments pour la fonction cible
            
        Returns:
            Fonction wrapper pour la tâche
        """
        def task_wrapper():
            # Active les contrôles de la tâche
            for control in controls_to_manage.values():
                if isinstance(control, (ft.ProgressBar, ft.Text)):
                    control.visible = True
            pause_button.visible = True
            cancel_button.visible = True
            self.page.update()
            
            try:
                target_func(
                    pause_event=pause_event, 
                    cancel_event=cancel_event, 
                    **kwargs
                )
            finally:
                # Masque les contrôles de la tâche une fois terminée
                if not cancel_event.is_set():
                    for c in controls_to_manage.get('buttons_to_disable', []):
                        c.disabled = False
                    for control in controls_to_manage.values():
                        if isinstance(control, (ft.ProgressBar, ft.Text)):
                            control.visible = False
                    pause_button.visible = False
                    cancel_button.visible = False
                    self.page.update()

        return task_wrapper
    
    def start_task(self, event, task_config: Dict[str, Any]):
        """
        Démarre une tâche avec la configuration fournie
        
        Args:
            event: Événement Flet
            task_config: Configuration de la tâche
        """
        # Vérification des prérequis
        if task_config.get('pre_check') and not task_config['pre_check']():
            task_config['result_log'].value = f"[!] Erreur: {task_config.get('error_message', 'Veuillez vérifier les champs.')}"
            self.page.update()
            return
        
        # Réinitialisation des logs et événements
        task_config['result_log'].value = f"[*] Démarrage de la tâche: {task_config['name']}\\n"
        task_config['pause_event'].set()
        task_config['cancel_event'].clear()

        # Désactivation des boutons
        for btn in task_config.get('controls_to_disable', []):
            btn.disabled = True
        
        # Création des callbacks avec les contrôles UI spécifiques
        progress_cb = partial(
            self.ui_progress_callback, 
            task_config['progress_bar'], 
            task_config['status_text']
        )
        
        result_callback_func = task_config.get('result_callback_func', self.ui_result_callback)
        result_cb = partial(result_callback_func, task_config['result_log'])
        
        # Préparation des arguments pour la fonction core
        core_args = task_config['get_core_args']()
        core_args['progress_callback'] = progress_cb
        core_args['result_callback'] = result_cb

        # Configuration du task runner
        runner_controls = {
            'buttons_to_disable': task_config.get('controls_to_disable', []),
            'progress_bar': task_config['progress_bar'],
            'status_text': task_config['status_text']
        }
        
        task = self.create_task_runner(
            task_config['target_func'], 
            runner_controls,
            task_config['pause_button'], 
            task_config['cancel_button'],
            task_config['pause_event'], 
            task_config['cancel_event'],
            **core_args
        )
        
        task_thread = threading.Thread(target=task, daemon=True)
        self.active_tasks[task_config['name']] = task_thread
        task_thread.start()

    def pause_task(
        self, 
        event, 
        pause_event: threading.Event, 
        pause_button: ft.ElevatedButton, 
        status_text: ft.Text, 
        task_name: str
    ):
        """Gère la pause/reprise d'une tâche"""
        if pause_button.text == "Pause":
            pause_event.clear()
            pause_button.text = "Reprendre"
            status_text.value = f"[*] {task_name} en pause..."
        else:
            pause_event.set()
            pause_button.text = "Pause"
            status_text.value = f"[*] Reprise de {task_name}..."
        self.page.update()

    def cancel_task(
        self, 
        event, 
        cancel_event: threading.Event, 
        controls_to_disable: list, 
        pause_button: ft.ElevatedButton, 
        cancel_button: ft.ElevatedButton, 
        status_text: ft.Text, 
        task_name: str
    ):
        """Annule une tâche en cours"""
        cancel_event.set()
        status_text.value = f"[*] Annulation de {task_name}..."
        for btn in controls_to_disable:
            btn.disabled = False
        pause_button.visible = False
        cancel_button.visible = False
        pause_button.text = "Pause"
        
        # Retirer de la liste des tâches actives
        if task_name in self.active_tasks:
            del self.active_tasks[task_name]
            
        self.page.update()

    def ui_progress_callback(
        self, 
        progress_bar: ft.ProgressBar, 
        status_text: ft.Text, 
        current: int, 
        total: int, 
        message: str
    ):
        """Callback pour mettre à jour la progression"""
        if total > 0:
            progress_bar.value = current / total
        status_text.value = message
        self.page.update()

    def ui_result_callback(self, result_log: ft.TextField, result: dict):
        """Callback pour afficher les résultats"""
        status = "VALIDE" if result.get('is_valid') else "INVALIDE"
        
        # Tronquer la clé pour la sécurité
        key_display = f"{result['key'][:4]}...{result['key'][-4:]}" if len(result['key']) > 8 else result['key']
        
        log_entry = f"[{result['timestamp']}] {result['service']} - {status} - Clé: {key_display} (Source: {result['source_type']} @ {result['source_info']})\\n"
        
        result_log.value += log_entry
        self.page.update()
    
    def get_active_tasks(self) -> Dict[str, threading.Thread]:
        """Retourne la liste des tâches actives"""
        return self.active_tasks.copy()
    
    def stop_all_tasks(self):
        """Arrête toutes les tâches actives"""
        for task_name, task_thread in self.active_tasks.items():
            if task_thread.is_alive():
                # Note: Pour un arrêt propre, il faudrait utiliser les cancel_events
                pass
        self.active_tasks.clear()