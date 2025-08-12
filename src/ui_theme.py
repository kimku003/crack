"""
UI Theme pour l'application Flet - Material Design 3
Conforme aux spécifications de l'agent FletUIX-Enhancer
"""

import flet as ft
import time
import asyncio

# Système d'espacement 8pt selon la configuration agent.yaml
class Spacing:
    """Système d'espacement basé sur une grille 8pt"""
    XS = 4   # 0.5 * 8 - Espacement très petit
    SM = 8   # 1 * 8   - Espacement petit  
    MD = 12  # 1.5 * 8 - Espacement moyen
    LG = 16  # 2 * 8   - Espacement large
    XL = 24  # 3 * 8   - Espacement très large

# Palette Material Design 3 (mode sombre optimisé)
class Colors:
    """Couleurs Material Design 3 avec contraste APCA optimisé"""
    
    # Couleurs primaires
    PRIMARY = "#6750A4"
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#4F378B"
    ON_PRIMARY_CONTAINER = "#EADDFF"
    
    # Couleurs secondaires  
    SECONDARY = "#625B71"
    ON_SECONDARY = "#FFFFFF"
    SECONDARY_CONTAINER = "#4A4458"
    ON_SECONDARY_CONTAINER = "#E8DEF8"
    
    # Couleurs tertiaires
    TERTIARY = "#7D5260"
    ON_TERTIARY = "#FFFFFF"
    TERTIARY_CONTAINER = "#633B48"
    ON_TERTIARY_CONTAINER = "#FFD8E4"
    
    # Couleurs de surface (fond sombre)
    SURFACE = "#141218"
    ON_SURFACE = "#E6E0E9"
    SURFACE_VARIANT = "#49454F"
    ON_SURFACE_VARIANT = "#CAC4D0"
    SURFACE_CONTAINER = "#211F26"
    SURFACE_CONTAINER_HIGH = "#2B2930"
    
    # Couleurs d'erreur
    ERROR = "#F2B8B5"
    ON_ERROR = "#601410"
    ERROR_CONTAINER = "#8C1D18"
    ON_ERROR_CONTAINER = "#F9DEDC"
    
    # Couleurs de succès et d'avertissement (custom)
    SUCCESS = "#4CAF50"
    SUCCESS_CONTAINER = "#1B5E20"
    ON_SUCCESS_CONTAINER = "#C8E6C9"
    
    WARNING = "#FF9800"
    WARNING_CONTAINER = "#E65100"
    ON_WARNING_CONTAINER = "#FFE0B2"
    
    # Couleurs d'outline
    OUTLINE = "#938F99"
    OUTLINE_VARIANT = "#49454F"

# Breakpoints responsive selon la configuration
class Breakpoints:
    """Points de rupture pour le design responsive"""
    MOBILE = 360
    TABLET = 768
    DESKTOP = 1200

def create_button(
    text: str, 
    icon: str = None, 
    style: str = "filled_tonal", 
    on_click = None, 
    disabled: bool = False,
    hierarchy: str = "primary"
) -> ft.ElevatedButton:
    """
    Crée un bouton unifié selon Material Design 3
    
    Args:
        text: Texte du bouton
        icon: Icône optionnelle
        style: Style du bouton (filled_tonal, filled, outlined, text)
        on_click: Fonction de callback
        disabled: État désactivé
        hierarchy: Hiérarchie (primary, secondary, tertiary)
    """
    
    # Configuration selon la hiérarchie
    if hierarchy == "primary":
        bg_color = Colors.PRIMARY_CONTAINER
        text_color = Colors.ON_PRIMARY_CONTAINER
    elif hierarchy == "secondary":
        bg_color = Colors.SECONDARY_CONTAINER
        text_color = Colors.ON_SECONDARY_CONTAINER
    else:  # tertiary
        bg_color = Colors.TERTIARY_CONTAINER
        text_color = Colors.ON_TERTIARY_CONTAINER
    
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        bgcolor=bg_color,
        color=text_color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4),  # rounded:4 selon config
            padding=ft.padding.symmetric(
                horizontal=Spacing.LG, 
                vertical=Spacing.SM
            ),
            elevation={"": 1, "hovered": 3, "pressed": 0}
        ),
        on_click=on_click,
        disabled=disabled,
        height=48,  # Taille minimale 48px pour l'accessibilité
        width=None
    )

def create_text_field(
    label: str,
    password: bool = False,
    can_reveal_password: bool = False,
    multiline: bool = False,
    read_only: bool = False,
    expand: bool = False,
    value: str = "",
    keyboard_type = None
) -> ft.TextField:
    """
    Crée un TextField unifié avec style Material Design 3
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
        label_style=ft.TextStyle(color=Colors.ON_SURFACE_VARIANT),
        text_style=ft.TextStyle(color=Colors.ON_SURFACE),
        content_padding=ft.padding.all(Spacing.MD)
    )

def create_dropdown(
    label: str,
    options: list,
    value: str = None
) -> ft.Dropdown:
    """
    Crée un Dropdown unifié avec style Material Design 3
    """
    return ft.Dropdown(
        label=label,
        options=options,
        value=value,
        filled=True,
        bgcolor=Colors.SURFACE_CONTAINER,
        border_color=Colors.OUTLINE_VARIANT,
        focused_border_color=Colors.PRIMARY,
        label_style=ft.TextStyle(color=Colors.ON_SURFACE_VARIANT),
        text_style=ft.TextStyle(color=Colors.ON_SURFACE),
        content_padding=ft.padding.all(Spacing.MD)
    )

def create_card(content, padding: int = None) -> ft.Card:
    """
    Crée une Card unifié avec style Material Design 3
    """
    if padding is None:
        padding = Spacing.LG
        
    return ft.Card(
        content=ft.Container(
            content=content,
            padding=padding,
            bgcolor=Colors.SURFACE_CONTAINER
        ),
        elevation=2,
        color=Colors.SURFACE_CONTAINER
    )

def create_container(
    content,
    padding: int = None,
    bgcolor: str = None,
    expand: bool = False,
    alignment = None
) -> ft.Container:
    """
    Crée un Container unifié avec espacement standardisé
    """
    if padding is None:
        padding = Spacing.LG
    if bgcolor is None:
        bgcolor = Colors.SURFACE_CONTAINER_HIGH
        
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=bgcolor,
        expand=expand,
        alignment=alignment
    )

def create_progress_bar(visible: bool = False) -> ft.ProgressBar:
    """
    Crée une ProgressBar avec couleurs Material Design 3
    """
    return ft.ProgressBar(
        visible=visible,
        color=Colors.PRIMARY,
        bgcolor=Colors.SURFACE_VARIANT
    )

def create_text(
    text: str,
    size: int = 14,  # Taille minimale selon agent.yaml
    weight = None,
    color: str = None,
    text_align = None,
    visible: bool = True
) -> ft.Text:
    """
    Crée un Text avec style unifié
    Taille minimale 14px selon agent.yaml accessibility.checks.font.min_size
    """
    if color is None:
        color = Colors.ON_SURFACE
    
    # Assurer la taille minimale de 14px selon agent.yaml
    if size < 14:
        size = 14
        
    return ft.Text(
        text,
        size=size,
        weight=weight,
        color=color,
        text_align=text_align,
        visible=visible,
        selectable=True  # Améliore l'accessibilité
    )

def create_responsive_row(controls: list, alignment = None) -> ft.ResponsiveRow:
    """
    Crée une ResponsiveRow avec alignement standardisé
    """
    if alignment is None:
        alignment = ft.MainAxisAlignment.CENTER
        
    return ft.ResponsiveRow(
        controls,
        alignment=alignment,
        spacing=Spacing.SM
    )

# Configuration du thème global de la page
def configure_page_theme(page: ft.Page):
    """
    Configure le thème global de la page selon Material Design 3
    """
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = Colors.SURFACE
    
    # Configuration du thème Material Design 3
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=Colors.ON_PRIMARY,
            primary_container=Colors.PRIMARY_CONTAINER,
            on_primary_container=Colors.ON_PRIMARY_CONTAINER,
            secondary=Colors.SECONDARY,
            on_secondary=Colors.ON_SECONDARY,
            secondary_container=Colors.SECONDARY_CONTAINER,
            on_secondary_container=Colors.ON_SECONDARY_CONTAINER,
            tertiary=Colors.TERTIARY,
            on_tertiary=Colors.ON_TERTIARY,
            tertiary_container=Colors.TERTIARY_CONTAINER,
            on_tertiary_container=Colors.ON_TERTIARY_CONTAINER,
            error=Colors.ERROR,
            on_error=Colors.ON_ERROR,
            error_container=Colors.ERROR_CONTAINER,
            on_error_container=Colors.ON_ERROR_CONTAINER,
            surface=Colors.SURFACE,
            on_surface=Colors.ON_SURFACE,
            surface_variant=Colors.SURFACE_VARIANT,
            on_surface_variant=Colors.ON_SURFACE_VARIANT,
            outline=Colors.OUTLINE,
            outline_variant=Colors.OUTLINE_VARIANT
        )
    )

# Styles spécialisés pour les boutons d'action
def create_action_button(text: str, icon: str, color_type: str = "primary") -> ft.ElevatedButton:
    """
    Crée des boutons d'action spécialisés (pause, cancel, etc.)
    """
    color_map = {
        "primary": (Colors.PRIMARY_CONTAINER, Colors.ON_PRIMARY_CONTAINER),
        "warning": (Colors.WARNING_CONTAINER, Colors.ON_WARNING_CONTAINER),
        "error": (Colors.ERROR_CONTAINER, Colors.ON_ERROR_CONTAINER),
        "success": (Colors.SUCCESS_CONTAINER, Colors.ON_SUCCESS_CONTAINER)
    }
    
    bg_color, text_color = color_map.get(color_type, color_map["primary"])
    
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        bgcolor=bg_color,
        color=text_color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4),
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM)
        ),
        height=48,
        visible=False  # Par défaut masqué pour les boutons d'action
    )