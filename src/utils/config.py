from pathlib import Path
import yaml

def get_project_root() -> Path:
    # .../src/utils/config.py -> src/utils -> src -> root
    return Path(__file__).resolve().parents[2]

class Config(dict):
    @property
    def root(self) -> Path:
        return get_project_root()
    def abs(self, *parts: str) -> Path:
        return self.root.joinpath(*parts).resolve()

def load_config(rel_path: str = "configs/app.yaml") -> "Config":
    root = get_project_root()
    cfg_path = root / rel_path
    if not cfg_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    cfg = Config(raw)

    paths = raw.get("paths", {})
    data_raw_dir = root / paths.get("data_raw_dir", "data/raw")
    data_processed_dir = root / paths.get("data_processed_dir", "data/processed")
    models_dir = root / paths.get("models_dir", "models")
    dataset_filename = paths.get("dataset_filename", "dataset.csv")

    cfg["abs_paths"] = {
        "data_raw_dir": str(data_raw_dir.resolve()),
        "data_processed_dir": str(data_processed_dir.resolve()),
        "models_dir": str(models_dir.resolve()),
        "dataset": str((data_raw_dir / dataset_filename).resolve()),
    }
    return cfg
config = load_config()
# usage: from src.utils.configs import config
#        print(config["abs_paths"]["data_raw_dir"])