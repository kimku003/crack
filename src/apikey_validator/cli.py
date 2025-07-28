# -*- coding: utf-8 -*-
"""
Point d'entrée en ligne de commande (CLI) pour l'outil de scan de secrets.
Ce module gère le parsing des arguments et appelle la logique métier
définie dans le module `core`.
"""
import argparse
import os
import sys
import threading
import time

# Ajouter le répertoire parent au path pour permettre les imports relatifs
# même si le script est exécuté directement.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apikey_validator import config, core

def main():
    """Fonction principale du CLI."""
    # Déterminer le chemin du fichier de configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    
    # Charger les patterns de secrets
    patterns = config.charger_patterns(config_path)
    if not patterns:
        print("[!] Arrêt du programme car la configuration des secrets n'a pas pu être chargée.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Outil de Sécurité pour Clés API - Scanne, valide et trouve des secrets.",
        epilog="Utilisez cet outil de manière responsable et uniquement sur des systèmes autorisés."
    )
    parser.add_argument("-o", "--output-file", type=str, help="Chemin du fichier pour sauvegarder les résultats.")
    parser.add_argument("-f", "--output-format", type=str, choices=['json', 'csv'], default='json', help="Format du fichier de sortie (défaut: json).")

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles", required=True)

    # Les choix pour --type sont dynamiques, basés sur le config.json
    valid_types = list(patterns.keys())

    # --- Commande 'validate' ---
    parser_validate = subparsers.add_parser("validate", help="Valider une clé API complète.")
    parser_validate.add_argument("--key", type=str, help="La clé API ou le token à tester (si omis, sera demandé).")
    parser_validate.add_argument("--type", type=str, choices=valid_types, help="Spécifier le service à tester. Si omis, teste tous les services.")
    
    # --- Commande 'brute-force' ---
    parser_brute = subparsers.add_parser("brute-force", help="Deviner la fin d'une clé incomplète.")
    parser_brute.add_argument("--partial-key", required=True, type=str, help="Le début de la clé API.")
    parser_brute.add_argument("--type", required=True, type=str, choices=valid_types, help="Le service cible pour le brute-force.")
    parser_brute.add_argument("--depth", type=int, default=2, help="Nombre max de caractères à deviner (défaut: 2).")

    # --- Commande 'dictionary' ---
    parser_dict = subparsers.add_parser("dictionary", help="Attaquer une clé avec une liste de mots.")
    parser_dict.add_argument("--partial-key", required=True, type=str, help="Le début de la clé API.")
    parser_dict.add_argument("--type", required=True, type=str, choices=valid_types, help="Le service cible pour l'attaque.")
    parser_dict.add_argument("--wordlist", required=True, type=str, help="Chemin vers le fichier wordlist.")

    # --- Commande 'scan' ---
    parser_scan = subparsers.add_parser("scan", help="Scanner un répertoire à la recherche de clés.")
    parser_scan.add_argument("--path", required=True, type=str, help="Chemin du répertoire à scanner.")

    # --- Commande 'scan-git' ---
    parser_scan_git = subparsers.add_parser("scan-git", help="Scanner l'historique d'un dépôt Git local.")
    parser_scan_git.add_argument("--path", required=True, type=str, help="Chemin du dépôt Git local à scanner.")

    # --- Commande 'scan-remote-git' ---
    parser_scan_remote_git = subparsers.add_parser("scan-remote-git", help="Cloner et scanner un dépôt Git distant.")
    parser_scan_remote_git.add_argument("--url", required=True, type=str, help="URL du dépôt Git distant.")

    # --- Commande 'scan-entropy' ---
    parser_entropy = subparsers.add_parser("scan-entropy", help="Scanner un répertoire pour des chaînes à haute entropie.")
    parser_entropy.add_argument("--path", required=True, type=str, help="Chemin du répertoire à scanner.")
    parser_entropy.add_argument("--threshold", type=float, default=4.0, help="Seuil d'entropie pour signaler un secret (défaut: 4.0).")

    args = parser.parse_args()

    # Événements pour le contrôle des tâches en arrière-plan (pause/annulation)
    pause_event = threading.Event()
    pause_event.set() # Actif par défaut
    cancel_event = threading.Event()

    try:
        # Exécution de la commande correspondante
        if args.command == "validate":
            core.mode_validation(patterns, args.key, args.type)
        elif args.command == "brute-force":
            core.mode_brute_force(patterns, args.partial_key, args.type, args.depth, pause_event, cancel_event)
        elif args.command == "dictionary":
            core.mode_dictionnaire(patterns, args.partial_key, args.type, args.wordlist, pause_event, cancel_event)
        elif args.command == "scan":
            core.mode_scan(patterns, args.path, pause_event, cancel_event)
        elif args.command == "scan-git":
            core.mode_scan_git(patterns, args.path, pause_event, cancel_event)
        elif args.command == "scan-remote-git":
            core.mode_scan_remote_git(patterns, args.url, pause_event, cancel_event)
        elif args.command == "scan-entropy":
            core.mode_scan_entropy(args.path, args.threshold, pause_event, cancel_event)

    except KeyboardInterrupt:
        print("\n\n[!] Opération annulée par l'utilisateur.")
        cancel_event.set()
    finally:
        # Laisser un peu de temps pour que les threads terminent proprement
        time.sleep(1)
        if args.output_file:
            core.enregistrer_resultats(args.output_file, args.output_format)

if __name__ == "__main__":
    main()
