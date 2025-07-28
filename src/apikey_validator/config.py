# -*- coding: utf-8 -*-
"""
Module pour la gestion de la configuration, notamment le chargement
des patterns de secrets à partir d'un fichier JSON.
"""
import json
from . import validators

def charger_patterns(config_path: str) -> dict:
    """
    Charge les patterns de secrets depuis un fichier de configuration spécifié.

    Associe les regex de détection aux fonctions de validation correspondantes.
    """
    # Dictionnaire qui mappe les noms de validateurs du JSON aux fonctions Python
    validator_functions = {
        "tester_cle_api_gemini": validators.tester_cle_api_gemini,
        "tester_cle_github": validators.tester_cle_github,
    }
    
    try:
        # L'encodage utf-8-sig gère le cas où le fichier JSON aurait une BOM (Byte Order Mark)
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config_data = json.load(f)
        
        patterns = {}
        for secret in config_data.get("secrets", []):
            validator_name = secret.get("validator")
            validator_func = validator_functions.get(validator_name)
            
            if validator_func:
                patterns[secret["name"]] = {
                    "regex": secret["regex"],
                    "validator": validator_func
                }
            else:
                print(f"[!] Avertissement: Validateur '{validator_name}' non trouvé pour le secret '{secret['name']}'.")
                
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
