"""
Application Flet refactorisée - API Security Scanner
Version modulaire avec séparation des responsabilités
"""

import flet as ft
import os
import sys

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apikey_validator import config
from ui_theme import configure_page_theme
from ui.task_manager import TaskManager
from ui.tabs import (
    create_validation_tab,
    create_scan_tab,
    create_brute_force_tab,
    create_git_scan_tab,
    create_entropy_scan_tab,
    create_find_tab,
    create_help_tab,
    create_test_tab
)
from ui_extensions import PerformanceMonitor

# Constantes pour l'analyse cognitive (amélioration qualité code)
MAX_TABS = 8
CONTROLS_PER_TAB = 6


class APISecurityScannerApp:
    """Application principale pour le scanner de sécurité API"""
    
    def __init__(self):
        self.patterns = None
        self.task_manager = None
        self.page = None
    
    def initialize_patterns(self) -> bool:
        """
        Initialise les patterns de validation des clés API
        
        Returns:
            bool: True si l'initialisation réussit, False sinon
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, 'apikey_validator', 'config.json')
            self.patterns = config.charger_patterns(config_path)
            return bool(self.patterns)
        except Exception as e:
            print(f"Erreur lors de l'initialisation des patterns : {e}")
            return False
    
    def setup_page(self, page: ft.Page):
        """
        Configure la page principale de l'application
        
        Args:
            page: Page Flet à configurer
        """
        self.page = page
        page.title = "API Security Scanner"
        
        # Configuration du thème Material Design 3
        configure_page_theme(page)
        
        # Initialisation du gestionnaire de tâches
        self.task_manager = TaskManager(page)
    
    def create_tabs(self) -> list:
        """
        Crée la liste des onglets de l'application
        
        Returns:
            list: Liste des onglets Flet
        """
        tabs = []
        
        # Onglet de validation
        tabs.append(create_validation_tab(self.patterns, self.page))
        
        # Onglet de scan de fichiers
        tabs.append(create_scan_tab(self.patterns, self.task_manager, self.page))
        
        # Onglet de brute force et dictionnaire
        tabs.append(create_brute_force_tab(self.patterns, self.task_manager, self.page))
        
        # Onglet de scan Git
        tabs.append(create_git_scan_tab(self.patterns, self.task_manager, self.page))
        
        # Onglet de scan par entropie
        tabs.append(create_entropy_scan_tab(self.patterns, self.task_manager, self.page))
        
        # Onglet de génération de clés
        tabs.append(create_find_tab(self.patterns, self.task_manager, self.page))
        
        # Onglet d'aide
        tabs.append(create_help_tab())
        
        # Onglet de test
        tabs.append(create_test_tab(self.patterns, self.page))
        
        return tabs
    
    def show_error(self, message: str):
        """
        Affiche un message d'erreur à l'utilisateur
        
        Args:
            message: Message d'erreur à afficher
        """
        self.page.add(ft.Text(f"Erreur: {message}", color=ft.Colors.RED))
    
    @PerformanceMonitor.measure_render_time
    def run(self, page: ft.Page):
        """
        Point d'entrée principal de l'application
        
        Args:
            page: Page Flet fournie par le framework
        """
        self.setup_page(page)
        
        # Initialisation des patterns
        if not self.initialize_patterns():
            self.show_error("Impossible de charger la configuration des secrets depuis config.json.")
            return
        
        # Création des onglets
        tabs = self.create_tabs()
        
        # Analyse de la charge cognitive
        cognitive_load = self.analyze_cognitive_load(len(tabs), CONTROLS_PER_TAB)
        
        # Construction de l'interface principale
        page.add(
            ft.SafeArea(
                content=ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=tabs,
                    expand=1,
                ),
                expand=True
            )
        )
    
    def analyze_cognitive_load(self, tabs_count: int, controls_per_tab: int) -> str:
        """
        Analyse la charge cognitive de l'interface
        
        Args:
            tabs_count: Nombre d'onglets
            controls_per_tab: Nombre moyen de contrôles par onglet
            
        Returns:
            str: Niveau de charge cognitive (LOW, MEDIUM, HIGH)
        """
        # Import local pour éviter les dépendances circulaires
        from ui_extensions import NavigationFlow
        
        cognitive_load = NavigationFlow.calculate_cognitive_load(tabs_count, controls_per_tab)
        
        # Log pour le monitoring (en mode développement)
        if cognitive_load == "HIGH":
            print("⚠️ Charge cognitive élevée détectée - considérer la réorganisation")
        
        return cognitive_load


def main(page: ft.Page):
    """
    Point d'entrée pour Flet
    
    Args:
        page: Page Flet
    """
    app = APISecurityScannerApp()
    app.run(page)


if __name__ == "__main__":
    ft.app(target=main)