# src/data/load.py
from pathlib import Path
import pandas as pd
from ..utils.config import load_config

def ensure_dirs(cfg):
    """Crée les dossiers processed/ et models/ s'ils n'existent pas."""
    Path(cfg["abs_paths"]["data_processed_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["abs_paths"]["models_dir"]).mkdir(parents=True, exist_ok=True)

def load_dataset(cfg, **read_csv_kwargs) -> pd.DataFrame:
    """
    Charge le CSV indiqué dans la config (paths.dataset).
    - Détection auto du séparateur (sep=None, engine='python')
    - Gère l'encodage UTF-8 avec BOM (utf-8-sig)
    - read_csv_kwargs permet de passer des options (nrows=, dtype=, etc.)
    """
    csv_path = Path(cfg["abs_paths"]["dataset"])
    if not csv_path.exists():
        raise FileNotFoundError(f"Jeu de données introuvable : {csv_path}")

    default_kwargs = dict(sep=None, engine="python", encoding="utf-8-sig")
    default_kwargs.update(read_csv_kwargs or {})
    return pd.read_csv(csv_path, **default_kwargs)
