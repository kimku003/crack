"""
Modules des onglets de l'application
"""

from .validation_tab import create_validation_tab
from .scan_tab import create_scan_tab
from .brute_force_tab import create_brute_force_tab
from .git_scan_tab import create_git_scan_tab
from .entropy_scan_tab import create_entropy_scan_tab
from .find_tab import create_find_tab
from .help_tab import create_help_tab
from .test_tab import create_test_tab

__all__ = [
    'create_validation_tab',
    'create_scan_tab',
    'create_brute_force_tab',
    'create_git_scan_tab',
    'create_entropy_scan_tab',
    'create_find_tab',
    'create_help_tab',
    'create_test_tab'
]