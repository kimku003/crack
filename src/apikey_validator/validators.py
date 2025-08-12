# -*- coding: utf-8 -*-
"""
Module contenant les fonctions de validation spécifiques pour chaque service API.
"""
import time
import requests
import re

# --- CONSTANTES ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GITHUB_API_URL = "https://api.github.com/user"

# --- FONCTIONS DE VALIDATION SPÉCIFIQUES ---

def validate_regex(key: str, pattern: str, silencieux: bool = False) -> bool:
    """Valide une clé en utilisant une expression régulière."""
    if not silencieux:
        print(f"[*] Validation regex pour la clé : {key[:4]}...{key[-4:]}")
    return re.fullmatch(pattern, key) is not None

def tester_cle_api_gemini(api_key: str, silencieux: bool = False) -> bool:
    """Teste une clé API Google Gemini."""
    if not silencieux:
        print(f"[*] Test de la clé (Google) : {api_key[:4]}...{api_key[-4:]}")
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "test"
                    }
                ]
            }
        ]
    }
    
    try:
        # Une petite pause pour éviter de surcharger les services
        time.sleep(0.1)
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            if not silencieux:
                print("[!] Rate limit atteint pour l'API Gemini. Pause de 60 secondes.")
            time.sleep(60)
            # Nouvelle tentative après la pause
            return tester_cle_api_gemini(api_key, silencieux)
        elif response.status_code == 400:
            # Vérifier si c'est une erreur de clé invalide
            try:
                error_data = response.json()
                if "error" in error_data and "details" in error_data["error"]:
                    for detail in error_data["error"]["details"]:
                        if detail.get("reason") == "API_KEY_INVALID":
                            return False
            except:
                pass
            return False
        return False
    except requests.exceptions.RequestException:
        return False

def tester_cle_github(api_key: str, silencieux: bool = False) -> bool:
    """Teste un token d'accès personnel GitHub."""
    if not silencieux:
        print(f"[*] Test du token (GitHub) : {api_key[:4]}...{api_key[-4:]}")
    headers = {"Authorization": f"token {api_key}"}
    try:
        # Une petite pause pour éviter de surcharger les services
        time.sleep(0.1)
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False