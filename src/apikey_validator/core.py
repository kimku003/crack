# -*- coding: utf-8 -*-
"""
Module principal contenant la logique métier de l'outil de scan de secrets.
Toutes les fonctions ici sont conçues pour être indépendantes de l'interface
(CLI ou GUI) et être réutilisables.
"""
import concurrent.futures
import csv
import getpass
import itertools
import json
import math
import os
import re
import shutil
import string
import sys
import tempfile
import threading
import time
from typing import Callable

try:
    import git
except ImportError:
    git = None

# --- VARIABLES GLOBALES ET VERROUS ---
resultats_trouves = []
result_lock = threading.Lock()

# --- CONSTANTES ---
CHARSET = string.ascii_letters + string.digits + "-_"
MAX_WORKERS = 10
POTENTIAL_SECRET_REGEX = re.compile(r'([a-zA-Z0-9\-_/+]{20,64})')

# --- TYPES DE CALLBACKS ---
# ProgressCallback = Callable[[int, int, str], None]  # current, total, message
# ResultCallback = Callable[[dict], None]

# --- FONCTIONS UTILITAIRES ---

def ajouter_resultat(resultat: dict):
    """Ajoute une entrée à la liste globale des résultats de manière thread-safe."""
    with result_lock:
        resultats_trouves.append(resultat)

def valider_et_rapporter(validator, service, cle, source_type, source_info, result_callback=None):
    """Valide une clé et rapporte le résultat via callback ou print."""
    est_valide = validator(cle, silencieux=True)
    
    resultat = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": service,
        "key": cle,
        "is_valid": est_valide,
        "source_type": source_type,
        "source_info": source_info,
    }
    
    if result_callback:
        result_callback(resultat)
    else:
        with result_lock:
            print(f"\n[*] Clé potentielle ({service}) trouvée dans : {source_info}")
            if est_valide:
                print(f"[+] SUCCÈS ! La clé trouvée est VALIDE : {cle}")
            else:
                print("[-] La clé potentielle est invalide.")
            sys.stdout.flush()
            
    ajouter_resultat(resultat)

def calculate_entropy(s: str) -> float:
    """Calcule l'entropie de Shannon pour une chaîne de caractères."""
    if not s: return 0.0
    freq_map = {c: s.count(c) for c in set(s)}
    entropy = 0.0
    str_len = len(s)
    for char in freq_map:
        freq = freq_map[char] / str_len
        entropy -= freq * math.log2(freq)
    return entropy

# --- MODES DE SCAN ---

def mode_validation(patterns: dict, api_key: str = None, service_specifie: str = None, result_callback=None):
    """Valide une clé API unique pour un ou plusieurs services."""
    if not result_callback: print("--- Mode Validation ---")
    key_to_test = api_key or getpass.getpass("Veuillez saisir votre clé API/token : ")

    def rapport(service, key, is_valid):
        res = {"service": service, "key": key, "is_valid": is_valid, "source_type": "manual", "source_info": "N/A", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if result_callback: result_callback(res)
        else:
            status = "VALIDE" if is_valid else "INVALIDE"
            print(f"\n[*] Résultat pour '{service}': {status}")
        ajouter_resultat(res)

    if service_specifie:
        if service_specifie not in patterns:
            print(f"[!] Erreur : service '{service_specifie}' non supporté.")
            return
        validator = patterns[service_specifie]["validator"]
        est_valide = validator(key_to_test)
        rapport(service_specifie, key_to_test, est_valide)
    else:
        if not result_callback: print("[*] Test sur tous les services supportés...")
        cle_valide_trouvee = False
        for service, details in patterns.items():
            est_valide = details["validator"](key_to_test, silencieux=True)
            if est_valide:
                rapport(service, key_to_test, True)
                cle_valide_trouvee = True
                break
        if not cle_valide_trouvee:
            rapport("Unknown", key_to_test, False)

def mode_brute_force(patterns: dict, cle_partielle: str, service_specifie: str, depth: int, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if service_specifie not in patterns:
        print(f"[!] Erreur : service '{service_specifie}' non supporté.")
        return

    validator = patterns[service_specifie]["validator"]
    if not progress_callback: print(f"[*] Lancement de la recherche pour {depth} caractère(s) manquant(s).")
    
    try:
        total_combinaisons = sum([len(CHARSET)**l for l in range(1, depth + 1)])
        essais_effectues = 0
        
        for longueur in range(1, depth + 1):
            if cancel_event.is_set(): return
            combinaisons = itertools.product(CHARSET, repeat=longueur)
            num_combinaisons_longueur = len(CHARSET)**longueur
            
            for i, combo in enumerate(combinaisons):
                if cancel_event.is_set(): return
                pause_event.wait()

                cle_candidate = cle_partielle + "".join(combo)
                essais_effectues += 1
                
                if progress_callback:
                    progress_callback(essais_effectues, total_combinaisons, f"Essai: {cle_candidate}")
                else:
                    sys.stdout.write(f"\r[*] Essai {essais_effectues}/{total_combinaisons} : {cle_candidate}")
                    sys.stdout.flush()

                if validator(cle_candidate, silencieux=True):
                    valider_et_rapporter(validator, service_specifie, cle_candidate, "brute-force", f"Partial key: {cle_partielle}", result_callback)
                    return
    except KeyboardInterrupt:
        print("\n\n[!] Opération annulée par l'utilisateur.")

def mode_dictionnaire(patterns: dict, cle_partielle: str, service_specifie: str, wordlist_path: str, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if service_specifie not in patterns:
        print(f"[!] Erreur : service '{service_specifie}' non supporté.")
        return
    if not os.path.exists(wordlist_path):
        print(f"[!] Erreur : le fichier '{wordlist_path}' est introuvable.")
        return

    validator = patterns[service_specifie]["validator"]
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
        mots = [line.strip() for line in f if line.strip()]
    
    total_mots = len(mots)
    if not progress_callback: print(f"[*] Chargement de {total_mots} mots depuis la liste.")
    
    for i, mot in enumerate(mots):
        if cancel_event.is_set(): return
        pause_event.wait()

        cle_candidate = cle_partielle + mot
        
        if progress_callback:
            progress_callback(i + 1, total_mots, f"Essai: {cle_candidate}")
        else:
            sys.stdout.write(f"\r[*] Essai {i+1}/{total_mots} : {cle_candidate}")
            sys.stdout.flush()
            
        if validator(cle_candidate, silencieux=True):
            valider_et_rapporter(validator, service_specifie, cle_candidate, "dictionary", f"Wordlist: {wordlist_path}", result_callback)
            return

def mode_scan(patterns: dict, scan_path: str, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if not os.path.isdir(scan_path):
        print(f"[!] Erreur : '{scan_path}' n'est pas un répertoire valide.")
        return

    if not progress_callback: print(f"[*] Démarrage du scan dans : {scan_path}")
    
    fichiers_a_scanner = [os.path.join(r, file) for r, d, fs in os.walk(scan_path) for file in fs if not any(folder in r for folder in ['.git', '.venv', 'node_modules', '__pycache__'])]
    total_fichiers = len(fichiers_a_scanner)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, file_path in enumerate(fichiers_a_scanner):
            if cancel_event.is_set(): break
            pause_event.wait()
            
            if progress_callback: progress_callback(i + 1, total_fichiers, os.path.basename(file_path))

            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                    for nom_cle, details in patterns.items():
                        for match in re.finditer(details["regex"], content):
                            futures.append(executor.submit(valider_et_rapporter, details["validator"], nom_cle, match.group(0), "scan", file_path, result_callback))
            except (IOError, OSError):
                pass
        concurrent.futures.wait(futures)

def mode_scan_git(patterns: dict, repo_path: str, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if git is None:
        print("[!] Erreur: GitPython non installé.")
        return
    try:
        repo = git.Repo(repo_path)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        print(f"[!] Erreur : '{repo_path}' n'est pas un dépôt Git valide.")
        return

    commits = list(repo.iter_commits('--all'))
    total_commits = len(commits)
    if not progress_callback: print(f"[*] {total_commits} commits à analyser...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, commit in enumerate(commits):
            if cancel_event.is_set(): break
            pause_event.wait()
            
            if progress_callback: progress_callback(i + 1, total_commits, f"Commit {commit.hexsha[:7]}")

            try:
                parent = commit.parents[0] if commit.parents else git.NULL_TREE
                diffs = parent.diff(commit, create_patch=True)
                for d in diffs:
                    diff_content = d.diff.decode('utf-8', errors='ignore')
                    for nom_cle, details in patterns.items():
                        for match in re.finditer(details["regex"], diff_content):
                            source_info = f"commit: {commit.hexsha[:7]}, file: {d.a_path or d.b_path}"
                            futures.append(executor.submit(valider_et_rapporter, details["validator"], nom_cle, match.group(0), "git-history", source_info, result_callback))
            except Exception:
                pass
        concurrent.futures.wait(futures)

def mode_scan_remote_git(patterns: dict, repo_url: str, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if git is None:
        print("[!] Erreur: GitPython non installé.")
        return
    temp_dir = tempfile.mkdtemp()
    if not progress_callback: print(f"[*] Clonage de {repo_url}...")

    try:
        if cancel_event.is_set(): return
        git.Repo.clone_from(repo_url, temp_dir)
        if cancel_event.is_set(): return
        
        mode_scan_git(patterns, temp_dir, pause_event, cancel_event, progress_callback, result_callback)
    except git.exc.GitCommandError as e:
        print(f"\n[!] Erreur de clonage : {e}")
    finally:
        if not progress_callback: print(f"[*] Nettoyage du répertoire temporaire.")
        shutil.rmtree(temp_dir)

def mode_scan_entropy(scan_path: str, threshold: float, pause_event: threading.Event, cancel_event: threading.Event, progress_callback=None, result_callback=None):
    if not os.path.isdir(scan_path):
        print(f"[!] Erreur : '{scan_path}' n'est pas un répertoire valide.")
        return

    fichiers_a_scanner = [os.path.join(r, file) for r, d, fs in os.walk(scan_path) for file in fs if not any(folder in r for folder in ['.git', '.venv', 'node_modules', '__pycache__'])]
    total_fichiers = len(fichiers_a_scanner)
    if not progress_callback: print(f"[*] Démarrage du scan par entropie (seuil > {threshold})")

    for i, file_path in enumerate(fichiers_a_scanner):
        if cancel_event.is_set(): return
        pause_event.wait()
        
        if progress_callback: progress_callback(i + 1, total_fichiers, os.path.basename(file_path))

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
                        
                        res = {"service": "Entropy", "key": secret_str, "is_valid": False, "source_type": "entropy-scan", "source_info": source_info, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                        if result_callback: result_callback(res)
                        else: print(f"\n[*] Secret potentiel (entropie: {entropy:.2f}) trouvé dans : {file_path}")
                        ajouter_resultat(res)
        except (IOError, OSError):
            pass

def enregistrer_resultats(output_file, output_format):
    """Enregistre les résultats trouvés dans un fichier JSON ou CSV."""
    if not output_file or not resultats_trouves:
        return
    
    print(f"\n[*] Enregistrement de {len(resultats_trouves)} résultat(s) dans '{output_file}'...")
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if output_format == 'json':
                json.dump(resultats_trouves, f, indent=4)
            elif output_format == 'csv':
                if not resultats_trouves: return
                fieldnames = resultats_trouves[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(resultats_trouves)
        print("[+] Enregistrement terminé.")
    except IOError as e:
        print(f"[!] Erreur lors de l'écriture du fichier de résultats : {e}")

