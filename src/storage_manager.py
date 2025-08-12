import json
import os
import logging
from typing import List, Dict

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_DIR = "storage/data"
STORAGE_PATH = os.path.join(STORAGE_DIR, "exposures.json")

def save_exposures(exposures: List[Dict]):
    """Sauvegarde la liste des expositions dans le fichier JSON."""
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        with open(STORAGE_PATH, "w") as f:
            json.dump(exposures, f, indent=4)
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des expositions : {e}")

def load_exposures() -> List[Dict]:
    """Charge la liste des expositions depuis le fichier JSON."""
    if not os.path.exists(STORAGE_PATH):
        return []
    
    try:
        with open(STORAGE_PATH, "r") as f:
            data = json.load(f)
            # S'assurer que les données sont bien une liste
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erreur lors du chargement des expositions (le fichier est peut-être corrompu) : {e}")
        return []
