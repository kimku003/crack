# -*- coding: utf-8 -*-
"""
Kit d'Outils de Sécurité pour Clés API

Outil en ligne de commande pour valider, trouver et récupérer des clés API.
Développé à des fins éducatives en cybersécurité.
"""
import argparse
import getpass
import itertools
import json
import os
import re
import string
import sys
import time
import requests
import csv
import threading
import concurrent.futures
import math

try:
    import git
except ImportError:
    print("[!] Erreur: La librairie GitPython n'est pas installée. Veuillez exécuter 'pip install GitPython'")
    sys.exit(1)

# --- VARIABLES GLOBALES ET VERROUS ---
resultats_trouves = []
result_lock = threading.Lock()

# --- CONSTANTES ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
GITHUB_API_URL = "https://api.github.com/user"
CHARSET = string.ascii_letters + string.digits + "-_"
MAX_WORKERS = 10
POTENTIAL_SECRET_REGEX = re.compile(r'([a-zA-Z0-9\-_/+]{20,64})')

# --- FONCTIONS DE VALIDATION SPÉCIFIQUES ---
# Ces fonctions sont les "plugins" de validation de notre outil.

def tester_cle_api_gemini(api_key: str, silencieux: bool = False) -> bool:
    if not silencieux:
        print(f"[*] Test de la clé (Google) : {api_key[:4]}...{api_key[-4:]}")
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": "test"}]}]}
    url_with_key = f"{GEMINI_API_URL}?key={api_key}"
    try:
        time.sleep(0.1)
        response = requests.post(url_with_key, headers=headers, json=payload, timeout=10)
        if response.status_code == 200: return True
        elif response.status_code == 429:
            if not silencieux: print("[!] Rate limit atteint pour l'API Gemini. Pause de 60 secondes.")
            time.sleep(60)
            return tester_cle_api_gemini(api_key, silencieux)
        return False
    except requests.exceptions.RequestException:
        return False

def tester_cle_github(api_key: str, silencieux: bool = False) -> bool:
    if not silencieux:
        print(f"[*] Test du token (GitHub) : {api_key[:4]}...{api_key[-4:]}")
    headers = {"Authorization": f"token {api_key}"}
    try:
        time.sleep(0.1)
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# --- CHARGEMENT DE LA CONFIGURATION ---

PATTERNS = {}

def charger_patterns(config_path):
    """Charge les patterns de secrets depuis un fichier de configuration spécifié."""
    validator_functions = {
        "tester_cle_api_gemini": tester_cle_api_gemini,
        "tester_cle_github": tester_cle_github,
    }
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        patterns = {}
        for secret in config.get("secrets", []):
            validator_func = validator_functions.get(secret["validator"])
            if validator_func:
                patterns[secret["name"]] = {
                    "regex": secret["regex"],
                    "validator": validator_func
                }
        return patterns
    except Exception as e:
        print(f"[!] Erreur critique lors du chargement de '{config_path}': {e}")
        return {}

# ... (Le reste du code reste identique : ajouter_resultat, valider_et_rapporter, tous les modes, etc.)
# --- FONCTION UTILITAIRE POUR LES RAPPORTS ---

def ajouter_resultat(service: str, cle: str, est_valide: bool, source_type: str, source_info: str):
    """Ajoute une entrée à la liste globale des résultats de manière thread-safe."""
    resultat = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": service,
        "key": cle,
        "is_valid": est_valide,
        "source_type": source_type,
        "source_info": source_info,
    }
    with result_lock:
        resultats_trouves.append(resultat)

# --- WORKER POUR LA VALIDATION ---

def valider_et_rapporter(validator, service, cle, source_type, source_info):
    """Fonction exécutée par chaque thread. Valide la clé et affiche le résultat."""
    est_valide = validator(cle, silencieux=True)
    with result_lock:
        print(f"\n[*] Clé potentielle ({service}) trouvée dans : {source_info}")
        if est_valide:
            print(f"[+] SUCCÈS ! La clé trouvée est VALIDE : {cle}")
        else:
            print("[-] La clé potentielle est invalide.")
        sys.stdout.flush()
    ajouter_resultat(service, cle, est_valide, source_type, source_info)

# --- MODULES DE L'OUTIL ---

def mode_validation(args):
    print("--- Mode Validation ---")
    api_key = args.key or getpass.getpass("Veuillez saisir votre clé API/token : ")
    service_specifie = args.type

    if service_specifie:
        if service_specifie not in PATTERNS:
            print(f"[!] Erreur : le type de service '{service_specifie}' n'est pas supporté.")
            return
        
        validator = PATTERNS[service_specifie]["validator"]
        est_valide = validator(api_key)
        ajouter_resultat(service_specifie, api_key, est_valide, "manual", "N/A")
        if est_valide:
            print(f"\n[+] SUCCÈS ! La clé pour le service '{service_specifie}' est valide.")
        else:
            print(f"\n[-] ÉCHEC. La clé pour le service '{service_specifie}' est invalide.")
    else:
        print("[*] Aucun type de service spécifié. Test sur tous les services supportés...")
        cle_valide_trouvee = False
        for service, details in PATTERNS.items():
            est_valide = details["validator"](api_key, silencieux=True)
            if est_valide:
                print(f"\n[+] SUCCÈS ! La clé est valide pour le service : {service}")
                ajouter_resultat(service, api_key, True, "manual", "N/A")
                cle_valide_trouvee = True
                break
        if not cle_valide_trouvee:
            print("\n[-] ÉCHEC. La clé est invalide pour tous les services supportés.")
            ajouter_resultat("Unknown", api_key, False, "manual", "N/A")

def mode_brute_force(args, pause_event: threading.Event, cancel_event: threading.Event):
    print("--- Mode Brute-Force ---")
    cle_partielle = args.partial_key
    service_specifie = args.type

    if not service_specifie or service_specifie not in PATTERNS:
        print(f"[!] Erreur : l'argument --type est requis. Types supportés : {', '.join(PATTERNS.keys())}")
        return

    validator = PATTERNS[service_specifie]["validator"]
    print(f"[*] Lancement de la recherche pour {args.depth} caractère(s) manquant(s) pour le service {service_specifie}.")
    
    try:
        for longueur in range(1, args.depth + 1):
            if cancel_event.is_set():
                print("\n[!] Opération annulée.")
                return
            combinaisons = itertools.product(CHARSET, repeat=longueur)
            num_combinaisons = len(CHARSET)**longueur
            print(f"[*] Test des combinaisons à {longueur} caractère(s) ({num_combinaisons} possibilités)...")
            
            for i, combo in enumerate(combinaisons):
                if cancel_event.is_set():
                    print("\n[!] Opération annulée.")
                    return
                pause_event.wait()

                suffixe = "".join(combo)
                cle_candidate = cle_partielle + suffixe
                
                sys.stdout.write(f"\r[*] Essai {i+1}/{num_combinaisons} : {cle_candidate}")
                sys.stdout.flush()

                if validator(cle_candidate, silencieux=True):
                    sys.stdout.write("\n")
                    print("\n[+] SUCCÈS ! Clé valide trouvée !")
                    print(f"    Clé complète : {cle_candidate}")
                    ajouter_resultat(service_specifie, cle_candidate, True, "brute-force", f"Partial key: {cle_partielle}")
                    return
        
        print("\n\n[-] Recherche terminée. Aucune clé valide trouvée.")

    except KeyboardInterrupt:
        print("\n\n[!] Opération annulée par l'utilisateur.")


def mode_dictionnaire(args, pause_event: threading.Event, cancel_event: threading.Event):
    print("--- Mode Attaque par Dictionnaire ---")
    cle_partielle = args.partial_key
    wordlist_path = args.wordlist
    service_specifie = args.type

    if not service_specifie or service_specifie not in PATTERNS:
        print(f"[!] Erreur : l'argument --type est requis. Types supportés : {', '.join(PATTERNS.keys())}")
        return

    if not os.path.exists(wordlist_path):
        print(f"[!] Erreur : le fichier '{wordlist_path}' est introuvable.")
        return

    validator = PATTERNS[service_specifie]["validator"]
    with open(wordlist_path, 'r') as f:
        mots = [line.strip() for line in f if line.strip()]
    
    print(f"[*] Chargement de {len(mots)} mots depuis la liste pour le service {service_specifie}.")
    
    for i, mot in enumerate(mots):
        if cancel_event.is_set():
            print("\n[!] Opération annulée.")
            return
        pause_event.wait()

        cle_candidate = cle_partielle + mot
        sys.stdout.write(f"\r[*] Essai {i+1}/{len(mots)} : {cle_candidate}")
        sys.stdout.flush()
        if validator(cle_candidate, silencieux=True):
            sys.stdout.write("\n")
            print(f"\n[+] SUCCÈS ! Clé valide trouvée avec le mot '{mot}' !")
            print(f"    Clé complète : {cle_candidate}")
            ajouter_resultat(service_specifie, cle_candidate, True, "dictionary", f"Wordlist: {wordlist_path}")
            return
            
    print("\n\n[-] Recherche terminée. Aucune clé valide trouvée avec cette liste.")


def mode_scan(args, pause_event: threading.Event, cancel_event: threading.Event):
    print("--- Mode Scan de Fichiers (Multithread) ---")
    scan_path = args.path
    if not os.path.isdir(scan_path):
        print(f"[!] Erreur : le chemin '{scan_path}' n'est pas un répertoire valide.")
        return

    print(f"[*] Démarrage du scan dans : {scan_path} (avec jusqu'à {MAX_WORKERS} threads)")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for root, dirs, files in os.walk(scan_path):
            if cancel_event.is_set():
                print("\n[!] Opération annulée.")
                break
            pause_event.wait()

            dirs[:] = [d for d in dirs if d not in ['.git', '.venv', 'node_modules', '__pycache__']]
            
            for file in files:
                if cancel_event.is_set():
                    print("\n[!] Opération annulée.")
                    break
                pause_event.wait()

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        for nom_cle, details in PATTERNS.items():
                            for match in re.finditer(details["regex"], content):
                                futures.append(executor.submit(valider_et_rapporter, details["validator"], nom_cle, match.group(0), "scan", file_path))
                except (IOError, OSError):
                    pass
        
        for future in concurrent.futures.as_completed(futures):
            if cancel_event.is_set():
                break
            pause_event.wait()
            # Optionally handle results or exceptions from futures if needed

    print(f"\n[*] Scan terminé.")


def mode_scan_git(args, pause_event: threading.Event, cancel_event: threading.Event):
    print("--- Mode Scan de l'Historique Git (Multithread) ---")
    repo_path = args.path
    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        print(f"[!] Erreur : '{repo_path}' n'est pas un dépôt Git valide.")
        return
    except git.exc.NoSuchPathError:
        print(f"[!] Erreur : Le chemin '{repo_path}' n'existe pas.")
        return

    print(f"[*] Démarrage du scan de l'historique pour : {repo_path} (avec jusqu'à {MAX_WORKERS} threads)")
    
    commits = list(repo.iter_commits('--all'))
    print(f"[*] {len(commits)} commits à analyser...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for commit in commits:
            if cancel_event.is_set():
                print("\n[!] Opération annulée.")
                break
            pause_event.wait()

            try:
                parent = commit.parents[0] if commit.parents else git.NULL_TREE
                diffs = parent.diff(commit, create_patch=True)

                for d in diffs:
                    if cancel_event.is_set():
                        print("\n[!] Opération annulée.")
                        break
                    pause_event.wait()

                    diff_content = d.diff.decode('utf-8', errors='ignore')
                    
                    for nom_cle, details in PATTERNS.items():
                        for match in re.finditer(details["regex"], diff_content):
                            cle_potentielle = match.group(0)
                            source_info = f"commit: {commit.hexsha[:7]}, file: {d.a_path or d.b_path}"
                            
                            futures.append(executor.submit(valider_et_rapporter, details["validator"], nom_cle, cle_potentielle, "git-history", source_info))
            except Exception:
                pass
        
        for future in concurrent.futures.as_completed(futures):
            if cancel_event.is_set():
                break
            pause_event.wait()
            # Optionally handle results or exceptions from futures if needed

    print(f"\n[*] Scan de l'historique terminé.")

def calculate_entropy(s: str) -> float:
    """Calcule l'entropie de Shannon pour une chaîne de caractères."""
    if not s:
        return 0.0
    freq_map = {c: s.count(c) for c in set(s)}
    entropy = 0.0
    for char in freq_map:
        freq = freq_map[char] / len(s)
        entropy -= freq * math.log2(freq)
    return entropy

def mode_scan_entropy(args, pause_event: threading.Event, cancel_event: threading.Event):
    print("--- Mode Scan par Entropie ---")
    scan_path = args.path
    threshold = args.threshold

    if not os.path.isdir(scan_path):
        print(f"[!] Erreur : le chemin '{scan_path}' n'est pas un répertoire valide.")
        return

    print(f"[*] Démarrage du scan par entropie dans : {scan_path} (seuil > {threshold})")
    
    secrets_potentiels = 0
    for root, dirs, files in os.walk(scan_path):
        if cancel_event.is_set():
            print("\n[!] Opération annulée.")
            return
        pause_event.wait()

        dirs[:] = [d for d in dirs if d not in ['.git', '.venv', 'node_modules', '__pycache__']]
        
        for file in files:
            if cancel_event.is_set():
                print("\n[!] Opération annulée.")
                return
            pause_event.wait()

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                    for potential_secret in POTENTIAL_SECRET_REGEX.finditer(content):
                        secret_str = potential_secret.group(0)
                        entropy = calculate_entropy(secret_str)
                        
                        if entropy > threshold:
                            source_info = f"file: {file_path}"
                            if any(r['key'] == secret_str and r['source_info'] == source_info for r in resultats_trouves):
                                continue

                            secrets_potentiels += 1
                            print(f"\n[*] Secret potentiel (entropie: {entropy:.2f}) trouvé dans : {file_path}")
                            print(f"    Chaîne : {secret_str}")
                            ajouter_resultat("Entropy", secret_str, False, "entropy-scan", source_info)

            except (IOError, OSError):
                pass
    
    print(f"\n[*] Scan par entropie terminé. {secrets_potentiels} secret(s) potentiel(s) trouvé(s).")
    print("[!] Note: Les résultats d'entropie ne sont pas validés automatiquement. Une vérification manuelle est requise.")


# --- GESTION DES SORTIES ---

def enregistrer_resultats(output_file, output_format):
    if not output_file or not resultats_trouves:
        return
    print(f"\n[*] Enregistrement de {len(resultats_trouves)} résultat(s) dans '{output_file}'...")
    try:
        with open(output_file, 'w', newline='') as f:
            if output_format == 'json':
                json.dump(resultats_trouves, f, indent=4)
            elif output_format == 'csv':
                if not resultats_trouves: return
                writer = csv.DictWriter(f, fieldnames=resultats_trouves[0].keys())
                writer.writeheader()
                writer.writerows(resultats_trouves)
        print("[+] Enregistrement terminé.")
    except IOError as e:
        print(f"[!] Erreur lors de l'écriture du fichier : {e}")

# --- PARSEUR D'ARGUMENTS ET POINT D'ENTRÉE ---

def main():
    global PATTERNS
    PATTERNS = charger_patterns()

    parser = argparse.ArgumentParser(
        description="Kit d'Outils de Sécurité pour Clés API, configurable et performant.",
        epilog="Modifiez 'config.json' pour ajouter de nouveaux types de secrets."
    )
    parser.add_argument("-o", "--output-file", type=str, help="Chemin du fichier pour sauvegarder les résultats.")
    parser.add_argument("-f", "--output-format", type=str, choices=['json', 'csv'], default='json', help="Format du fichier de sortie.")

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles", required=True)

    # Les choix pour --type sont maintenant dynamiques, basés sur le config.json
    valid_types = list(PATTERNS.keys())

    parser_validate = subparsers.add_parser("validate", help="Valider une clé API complète.")
    parser_validate.add_argument("--key", type=str, help="La clé API ou le token à tester.")
    parser_validate.add_argument("--type", type=str, choices=valid_types, help="Spécifier le service à tester. Si omis, teste tous les services.")
    parser_validate.set_defaults(func=mode_validation)

    parser_brute = subparsers.add_parser("brute-force", help="Deviner la fin d'une clé incomplète.")
    parser_brute.add_argument("--partial-key", required=True, type=str, help="Le début de la clé API.")
    parser_brute.add_argument("--type", required=True, type=str, choices=valid_types, help="Le service cible pour le brute-force.")
    parser_brute.add_argument("--depth", type=int, default=2, help="Nombre max de caractères à deviner (défaut: 2).")
    parser_brute.set_defaults(func=mode_brute_force)

    parser_dict = subparsers.add_parser("dictionary", help="Attaquer une clé avec une liste de mots.")
    parser_dict.add_argument("--partial-key", required=True, type=str, help="Le début de la clé API.")
    parser_dict.add_argument("--type", required=True, type=str, choices=valid_types, help="Le service cible pour l'attaque.")
    parser_dict.add_argument("--wordlist", required=True, type=str, help="Chemin vers le fichier wordlist.")
    parser_dict.set_defaults(func=mode_dictionnaire)

    parser_scan = subparsers.add_parser("scan", help="Scanner un répertoire à la recherche de clés (rapide, multithread).")
    parser_scan.add_argument("--path", required=True, type=str, help="Chemin du répertoire à scanner.")
    parser_scan.set_defaults(func=mode_scan)

    parser_scan_git = subparsers.add_parser("scan-git", help="Scanner l'historique d'un dépôt Git (rapide, multithread).")
    parser_scan_git.add_argument("--path", required=True, type=str, help="Chemin du dépôt Git local à scanner.")
    parser_scan_git.set_defaults(func=mode_scan_git)

    parser_entropy = subparsers.add_parser("scan-entropy", help="Scanner un répertoire à la recherche de chaînes à haute entropie.")
    parser_entropy.add_argument("--path", required=True, type=str, help="Chemin du répertoire à scanner.")
    parser_entropy.add_argument("--threshold", type=float, default=4.0, help="Seuil d'entropie pour signaler un secret (défaut: 4.0).")
    parser_entropy.set_defaults(func=mode_scan_entropy)

    args = None
    try:
        args = parser.parse_args()
        if hasattr(args, 'func'):
            args.func(args)
    except KeyboardInterrupt:
        print("\n\n[!] Opération annulée par l'utilisateur.")
    finally:
        time.sleep(1)
        if args:
            enregistrer_resultats(args.output_file, args.output_format)

if __name__ == "__main__":
    main()