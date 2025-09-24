import sys, os
from pathlib import Path

# --- Bootstrapping du path projet 
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) 
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# -------------------------------------------------------------------

import json
import pandas as pd
import streamlit as st
import joblib
from src.utils.config import load_config


# ==============================================
# paramètres du modèle comme dans le notebook

FEATURES = [
    "study_hours_per_day",
    "attendance_percentage",
    "sleep_hours",
    "mental_health_rating",
    "part_time_job",  # 0/1
]
APP_TITLE = "🎓 Student Exam Score Predictor"
# ==============================================

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _find_model_path(cfg) -> Path | None:
    """Trouve best_model.pkl à des emplacements courants (models/, notebooks/, racine)."""
    root = _project_root()
    candidates = []
    # depuis la config (optionnel)
    direct = cfg.get("model_path")
    if direct:
        candidates.append(Path(direct))
    # dossier models/ défini via config
    abs_paths = cfg.get("abs_paths", {})
    if abs_paths.get("models_dir"):
        candidates.append(Path(abs_paths["models_dir"]) / "best_model.pkl")
    # emplacements classiques
    candidates += [
        root / "models" / "best_model.pkl",
        root / "notebooks" / "best_model.pkl",
        root / "best_model.pkl",
    ]
    for p in candidates:
        if p and p.exists():
            return p
    return None

@st.cache_resource
def _load_model(model_path: Path):
    return joblib.load(model_path)

def _coerce_part_time_job(val):
    """Yes/No → 1/0 ; bool → 1/0 ; numérique → tel quel."""
    if isinstance(val, str):
        m = {"yes": 1, "y": 1, "no": 0, "n": 0}
        return m.get(val.strip().lower(), val)
    if isinstance(val, bool):
        return int(val)
    return val

def _predict_one(model, row_dict: dict) -> float:
    x = dict(row_dict)
    x["part_time_job"] = _coerce_part_time_job(x.get("part_time_job"))
    # cast numériques
    for c in ["study_hours_per_day", "attendance_percentage", "sleep_hours", "mental_health_rating"]:
        x[c] = pd.to_numeric(x.get(c, None), errors="coerce")
    X = pd.DataFrame([x], columns=FEATURES)
    pred = model.predict(X)[0]
    return float(pred)

# ================== UI ==================
st.set_page_config(page_title=APP_TITLE, page_icon="🎓", layout="centered")
st.title(APP_TITLE)
st.caption("Saisis une observation (un étudiant) et obtiens une prédiction.")

cfg = load_config()
model_path = _find_model_path(cfg)
if not model_path:
    st.error(
        "Modèle introuvable (`best_model.pkl`).\n\n"
        "Exécute le notebook jusqu’à la sauvegarde du modèle puis place le fichier dans `models/`, "
        "`notebooks/` ou à la racine du projet."
    )
    st.stop()

try:
    model = _load_model(model_path)
except Exception as e:
    st.error(f"Erreur lors du chargement du modèle : {e}")
    st.stop()

# ---- Formulaire manuel (1 observation) ----
defaults = dict(
    study_hours_per_day=4.0,
    attendance_percentage=85.0,
    sleep_hours=7.0,
    mental_health_rating=6,
    part_time_job="No",
)

st.subheader("Saisie manuelle")
with st.form("inputs_form"):
    c1, c2 = st.columns(2)
    with c1:
        study_hours = st.slider("Study Hours per Day", 0.0, 12.0, float(defaults["study_hours_per_day"]), 0.25)
        attendance = st.slider("Attendance Percentage (%)", 0.0, 100.0, float(defaults["attendance_percentage"]), 1.0)
        sleep_hours = st.slider("Sleep Hours per Night", 0.0, 12.0, float(defaults["sleep_hours"]), 0.25)
    with c2:
        mental_health = st.slider("Mental Health Rating (1-10)", 1, 10, int(defaults["mental_health_rating"]), 1)
        part_time_job = st.radio("Part-Time Job", ["No", "Yes"], index=(0 if defaults["part_time_job"] == "No" else 1))

    submitted = st.form_submit_button("🔮 Predict", use_container_width=True)

if st.button("Reset"):
    st.rerun()

if submitted:
    row = {
        "study_hours_per_day": float(study_hours),
        "attendance_percentage": float(attendance),
        "sleep_hours": float(sleep_hours),
        "mental_health_rating": int(mental_health),
        "part_time_job": 1 if part_time_job == "Yes" else 0,
    }
    try:
        pred = _predict_one(model, row)
    except Exception as e:
        st.error(f"Échec de la prédiction : {e}")
        st.stop()

    st.subheader("Résultat")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Predicted Exam Score", f"{pred:.2f} / 100")
    with c2:
        st.progress(min(max(pred / 100, 0), 1.0))

    st.markdown("**Paramètres utilisés**")
    st.json(row)

st.warning("Cette prédiction est indicative. Peut être moins ajustée pour des profils extrêmes "
        "ou hors domaine d'entraînement.")
