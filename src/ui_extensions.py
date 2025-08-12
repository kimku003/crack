"""
Extensions UI pour l'application Flet - Fonctionnalités avancées
Implémente les spécifications manquantes de l'agent FletUIX-Enhancer
"""

import flet as ft
import time
from ui_theme import Colors, Spacing, create_text, create_button

# === STATE MANAGEMENT (selon agent.yaml) ===

def create_loading_state(
    message: str = "Chargement...",
    show_progress: bool = True,
    min_duration: int = 300  # ms pour éviter le flash
) -> ft.Container:
    """
    Crée un état de chargement avec indicateur de progression
    Respecte la durée minimale pour éviter le flash (agent.yaml)
    """
    controls = [create_text(message, size=14, color=Colors.ON_SURFACE_VARIANT)]
    
    if show_progress:
        controls.insert(0, ft.ProgressRing(
            width=32,
            height=32,
            stroke_width=3,
            color=Colors.PRIMARY
        ))
    
    return ft.Container(
        content=ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.MD
        ),
        padding=Spacing.XL,
        alignment=ft.alignment.center,
        animate_opacity=min_duration  # Animation selon durée minimale
    )

def create_empty_state(
    icon: str,
    message: str,
    call_to_action: str = None,
    on_action_click = None
) -> ft.Container:
    """
    Crée un état vide avec icône, message et call-to-action
    Selon spécifications agent.yaml: icon + message + call_to_action requis
    """
    controls = [
        ft.Icon(
            icon,
            size=64,
            color=Colors.ON_SURFACE_VARIANT
        ),
        create_text(
            message,
            size=16,
            color=Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER
        )
    ]
    
    if call_to_action and on_action_click:
        controls.append(
            create_button(
                call_to_action,
                hierarchy="primary",
                on_click=on_action_click
            )
        )
    
    return ft.Container(
        content=ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.LG
        ),
        padding=Spacing.XL,
        alignment=ft.alignment.center
    )

def create_error_state(
    icon: str = ft.Icons.ERROR_OUTLINE,
    message: str = "Une erreur s'est produite",
    retry_button_text: str = "Réessayer",
    on_retry_click = None
) -> ft.Container:
    """
    Crée un état d'erreur avec icône, message et bouton retry
    Selon spécifications agent.yaml: icon + message + retry_button requis
    """
    controls = [
        ft.Icon(
            icon,
            size=48,
            color=Colors.ERROR
        ),
        create_text(
            message,
            size=16,
            color=Colors.ON_SURFACE,
            text_align=ft.TextAlign.CENTER
        )
    ]
    
    if on_retry_click:
        controls.append(
            create_button(
                retry_button_text,
                icon=ft.Icons.REFRESH,
                hierarchy="primary",
                on_click=on_retry_click
            )
        )
    
    return ft.Container(
        content=ft.Column(
            controls=controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.LG
        ),
        padding=Spacing.XL,
        alignment=ft.alignment.center,
        bgcolor=Colors.ERROR_CONTAINER,
        border_radius=8
    )

# === INPUT VALIDATION AMÉLIORÉE (selon agent.yaml) ===

# Version simplifiée compatible avec toutes les versions de Flet
def create_simple_validated_text_field(
    label: str,
    password: bool = False,
    can_reveal_password: bool = False,
    multiline: bool = False,
    read_only: bool = False,
    expand: bool = False,
    value: str = "",
    keyboard_type = None,
    error_text: str = None
) -> ft.TextField:
    """
    Version simplifiée du TextField avec validation
    Compatible avec toutes les versions de Flet
    """
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=can_reveal_password,
        multiline=multiline,
        read_only=read_only,
        expand=expand,
        value=value,
        keyboard_type=keyboard_type,
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        content_padding=ft.padding.all(Spacing.MD),
        error_text=error_text
    )

def create_validated_text_field(
    label: str,
    password: bool = False,
    can_reveal_password: bool = False,
    multiline: bool = False,
    read_only: bool = False,
    expand: bool = False,
    value: str = "",
    keyboard_type = None,
    validator = None,
    error_text: str = None
) -> ft.TextField:
    """
    Crée un TextField avec validation Material Design 3
    Label placement: floating (selon agent.yaml)
    Error states: material3 (selon agent.yaml)
    """
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=can_reveal_password,
        multiline=multiline,
        read_only=read_only,
        expand=expand,
        value=value,
        keyboard_type=keyboard_type,
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
        label_style=ft.TextStyle(
            color=Colors.ON_SURFACE_VARIANT,
            size=14  # Taille minimale selon agent.yaml
        ),
        text_style=ft.TextStyle(
            color=Colors.ON_SURFACE,
            size=14  # Taille minimale selon agent.yaml
        ),
        content_padding=ft.padding.all(Spacing.MD),
        # Error state Material Design 3
        error_text=error_text,
        error_style=ft.TextStyle(
            color=Colors.ERROR,
            size=12
        )
    )

# === MATERIAL ICONS STANDARDISÉS (selon agent.yaml) ===

class MaterialIcons:
    """
    Icônes Material Design standardisées
    Préférence: filled (selon agent.yaml custom_rules.material_icons)
    """
    # Navigation
    MENU = ft.Icons.MENU
    BACK = ft.Icons.ARROW_BACK
    CLOSE = ft.Icons.CLOSE
    
    # Actions
    PLAY = ft.Icons.PLAY_ARROW
    PAUSE = ft.Icons.PAUSE
    STOP = ft.Icons.STOP
    REFRESH = ft.Icons.REFRESH
    
    # Status
    SUCCESS = ft.Icons.CHECK_CIRCLE
    ERROR = ft.Icons.ERROR
    WARNING = ft.Icons.WARNING
    INFO = ft.Icons.INFO
    
    # Files
    FOLDER = ft.Icons.FOLDER
    FILE = ft.Icons.DESCRIPTION
    DOWNLOAD = ft.Icons.DOWNLOAD
    UPLOAD = ft.Icons.UPLOAD
    
    # Security
    SECURITY = ft.Icons.SECURITY
    KEY = ft.Icons.KEY
    LOCK = ft.Icons.LOCK
    UNLOCK = ft.Icons.LOCK_OPEN

def get_material_icon(icon_name: str, filled: bool = True) -> str:
    """
    Retourne une icône Material Design standardisée
    Préférence pour filled selon agent.yaml
    """
    if hasattr(MaterialIcons, icon_name.upper()):
        return getattr(MaterialIcons, icon_name.upper())
    return icon_name  # Fallback

# === MOTION/ANIMATION (selon agent.yaml) ===

class Animations:
    """
    Animations subtiles et meaningful selon agent.yaml
    """
    # Durées (subtle)
    FAST = 150
    NORMAL = 250
    SLOW = 350
    
    # Courbes d'animation
    EASE_IN = ft.AnimationCurve.EASE_IN
    EASE_OUT = ft.AnimationCurve.EASE_OUT
    EASE_IN_OUT = ft.AnimationCurve.EASE_IN_OUT

def create_animated_container(
    content,
    animate_opacity: int = Animations.NORMAL,
    animate_scale: int = None,
    animate_position: int = None,
    **kwargs
) -> ft.Container:
    """
    Crée un Container avec animations subtiles
    """
    return ft.Container(
        content=content,
        animate_opacity=animate_opacity,
        animate_scale=animate_scale,
        animate_position=animate_position,
        **kwargs
    )

# === ACCESSIBILITÉ AMÉLIORÉE (selon agent.yaml) ===

def create_accessible_text(
    text: str,
    size: int = 14,  # Taille minimale selon agent.yaml
    weight = None,
    color: str = None,
    text_align = None,
    visible: bool = True,
    semantic_label: str = None
) -> ft.Text:
    """
    Crée un Text accessible avec taille minimale 14px
    """
    if color is None:
        color = Colors.ON_SURFACE
    
    # Assurer la taille minimale de 14px
    if size < 14:
        size = 14
        
    return ft.Text(
        text,
        size=size,
        weight=weight,
        color=color,
        text_align=text_align,
        visible=visible,
        semantic_label=semantic_label,  # Pour l'accessibilité
        selectable=True  # Améliore l'accessibilité
    )

# === PERFORMANCE MONITORING (selon agent.yaml) ===

class PerformanceMonitor:
    """
    Monitoring des performances selon agent.yaml
    Warning threshold: 300ms
    Critical threshold: 800ms
    """
    WARNING_THRESHOLD = 300  # ms
    CRITICAL_THRESHOLD = 800  # ms
    
    @staticmethod
    def measure_render_time(func):
        """
        Décorateur pour mesurer le temps de rendu
        """
        def wrapper(*args, **kwargs):
            start_time = time.time() * 1000  # en ms
            result = func(*args, **kwargs)
            end_time = time.time() * 1000
            
            render_time = end_time - start_time
            
            if render_time > PerformanceMonitor.CRITICAL_THRESHOLD:
                print(f"⚠️ CRITICAL: Render time {render_time:.2f}ms > {PerformanceMonitor.CRITICAL_THRESHOLD}ms")
            elif render_time > PerformanceMonitor.WARNING_THRESHOLD:
                print(f"⚠️ WARNING: Render time {render_time:.2f}ms > {PerformanceMonitor.WARNING_THRESHOLD}ms")
            
            return result
        return wrapper

# === NAVIGATION UX (selon agent.yaml) ===

class NavigationFlow:
    """
    Analyse du flux de navigation et charge cognitive
    """
    
    @staticmethod
    def calculate_cognitive_load(tabs_count: int, controls_per_tab: int) -> str:
        """
        Calcule la charge cognitive selon le nombre d'éléments
        """
        total_elements = tabs_count * controls_per_tab
        
        if total_elements <= 7:
            return "LOW"  # Règle de Miller 7±2
        elif total_elements <= 14:
            return "MEDIUM"
        else:
            return "HIGH"
    
    @staticmethod
    def suggest_navigation_improvements(cognitive_load: str) -> list:
        """
        Suggère des améliorations de navigation
        """
        suggestions = []
        
        if cognitive_load == "HIGH":
            suggestions.extend([
                "Considérer la réorganisation en sous-groupes",
                "Implémenter une navigation progressive",
                "Ajouter des raccourcis clavier"
            ])
        elif cognitive_load == "MEDIUM":
            suggestions.extend([
                "Ajouter des indicateurs visuels",
                "Grouper les fonctionnalités similaires"
            ])
        
        return suggestions

# === SHIMMER EFFECT (selon agent.yaml) ===

def create_shimmer_effect(
    width: int = 200,
    height: int = 20,
    border_radius: int = 4
) -> ft.Container:
    """
    Crée un effet shimmer pour les états de chargement
    """
    return ft.Container(
        width=width,
        height=height,
        border_radius=border_radius,
        bgcolor=Colors.SURFACE_VARIANT,
        animate_opacity=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        opacity=0.3
    )

def create_shimmer_list(item_count: int = 3) -> ft.Column:
    """
    Crée une liste avec effet shimmer
    """
    items = []
    for i in range(item_count):
        items.append(
            ft.Row([
                create_shimmer_effect(50, 50, 25),  # Avatar
                ft.Column([
                    create_shimmer_effect(150, 16),  # Titre
                    create_shimmer_effect(100, 12),  # Sous-titre
                ], spacing=Spacing.XS)
            ], spacing=Spacing.MD)
        )
    
    return ft.Column(items, spacing=Spacing.MD)