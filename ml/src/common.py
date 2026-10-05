"""Caminhos e contrato do modelo (sem efeitos colaterais no import)."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"
MODELS = ROOT / "ml/models"
REPORTS = ROOT / "ml/reports"
GENERATED = ROOT / "firmware/main/generated"
SEED = 42
WINDOW = 128
STRIDE = 64
CHANNELS = ["total_acc_x", "total_acc_y", "total_acc_z",
            "body_gyro_x", "body_gyro_y", "body_gyro_z"]
STATS = ["mean", "std", "rms", "min", "max", "energy"]
CLASSES = ["WALKING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS",
           "SITTING", "STANDING", "LAYING"]
FEATURE_NAMES = [f"{c}_{s}" for c in CHANNELS for s in STATS]


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
