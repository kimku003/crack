# -*- coding: utf-8 -*-
"""
Module pour la gestion de la configuration, notamment le chargement
des patterns de secrets à partir d'un fichier JSON.
"""
import json
import re
from . import validators

def charger_patterns(config_path: str) -> dict:
    """
    Charge les patterns de secrets depuis un fichier de configuration spécifié.

    Associe les regex de détection aux fonctions de validation correspondantes.
    """
    try:
        # L'encodage utf-8-sig gère le cas où le fichier JSON aurait une BOM (Byte Order Mark)
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config_data = json.load(f)
        
        patterns = {}
        for service_name, details in config_data.items():
            if "pattern" in details:
                # Définir le validateur approprié selon le service
                if service_name == "Gemini":
                    validator = validators.tester_cle_api_gemini
                elif service_name == "GitHub_Personal_Access_Token":
                    validator = validators.tester_cle_github
                else:
                    # Pour les autres services, utiliser la validation regex
                    validator = lambda key, silencieux=False, pattern=details["pattern"]: validators.validate_regex(key, pattern, silencieux)
                
                patterns[service_name] = {
                    "regex": re.compile(details["pattern"]),
                    "validator": validator
                }
            else:
                print(f"[!] Avertissement: Le service '{service_name}' n'a pas de pattern défini.")
                
        return patterns
    except FileNotFoundError:
        print(f"[!] Erreur critique: Le fichier de configuration '{config_path}' est introuvable.")
        return {}
    except json.JSONDecodeError:
        print(f"[!] Erreur critique: Le fichier de configuration '{config_path}' n'est pas un JSON valide.")
        return {}
    except Exception as e:
        print(f"[!] Erreur critique lors du chargement de '{config_path}': {e}")
        return {}
