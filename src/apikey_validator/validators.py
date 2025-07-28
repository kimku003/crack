# -*- coding: utf-8 -*-
"""
Module contenant les fonctions de validation spécifiques pour chaque service API.
"""
import time
import requests

# --- CONSTANTES ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
GITHUB_API_URL = "https://api.github.com/user"

# --- FONCTIONS DE VALIDATION SPÉCIFIQUES ---

def tester_cle_api_gemini(api_key: str, silencieux: bool = False) -> bool:
    """Teste une clé API Google Gemini."""
    if not silencieux:
        print(f"[*] Test de la clé (Google) : {api_key[:4]}...{api_key[-4:]}")
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": "test"}]}]}
    url_with_key = f"{GEMINI_API_URL}?key={api_key}"
    try:
        # Une petite pause pour éviter de surcharger les services
        time.sleep(0.1)
        response = requests.post(url_with_key, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            if not silencieux:
                print("[!] Rate limit atteint pour l'API Gemini. Pause de 60 secondes.")
            time.sleep(60)
            # Nouvelle tentative après la pause
            return tester_cle_api_gemini(api_key, silencieux)
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
