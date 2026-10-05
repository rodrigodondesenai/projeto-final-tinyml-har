"""Split oficial de teste; validacao interna por voluntario, nunca por janela."""
import hashlib
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from .common import RAW, PROCESSED, REPORTS, CHANNELS, CLASSES, FEATURE_NAMES, SEED, save_json
from .features import extract_features, fit_scaler, normalize


def load_split(root, split):
    folder = root / split
    arrays = [np.loadtxt(folder / "Inertial Signals" / f"{c}_{split}.txt", dtype=np.float32) for c in CHANNELS]
    windows = np.stack(arrays, axis=-1)
    labels = np.loadtxt(folder / f"y_{split}.txt", dtype=np.int64) - 1
    subjects = np.loadtxt(folder / f"subject_{split}.txt", dtype=np.int64)
    if windows.shape != (len(labels), 128, 6) or len(subjects) != len(labels):
        raise ValueError("Dimensoes invalidas no dataset")
    if set(labels) != set(range(6)) or not np.isfinite(windows).all():
        raise ValueError("Classes ou sinais invalidos")
    return windows, labels, subjects


def main():
    root = RAW / "UCI HAR Dataset"
    train, y, subjects = load_split(root, "train")
    test, y_test, test_subjects = load_split(root, "test")
    assert set(subjects).isdisjoint(test_subjects)
    fit_idx, val_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(train, y, subjects))
    features = extract_features(train)
    mean, scale = fit_scaler(features[fit_idx])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PROCESSED / "features.npz",
        x_train=normalize(features[fit_idx], mean, scale), y_train=y[fit_idx],
        x_val=normalize(features[val_idx], mean, scale), y_val=y[val_idx],
        x_test=normalize(extract_features(test), mean, scale), y_test=y_test,
        mean=mean, scale=scale, train_indices=fit_idx, val_indices=val_idx)
    # Escolha anterior a inferencia: primeira janela de cada classe, sem cherry-picking.
    replay_indices = np.array([np.flatnonzero(y_test == i)[0] for i in range(6)])
    np.savez_compressed(PROCESSED / "replay.npz", windows=test[replay_indices],
                        labels=y_test[replay_indices], indices=replay_indices,
                        subjects=test_subjects[replay_indices])
    report = {"seed": SEED, "sample_hz": 50, "window": 128, "stride": 64,
        "channels": CHANNELS, "features": FEATURE_NAMES, "classes": CLASSES,
        "n_fit": len(fit_idx), "n_validation": len(val_idx), "n_test": len(test),
        "fit_subjects": sorted(map(int, set(subjects[fit_idx]))),
        "validation_subjects": sorted(map(int, set(subjects[val_idx]))),
        "test_subjects": sorted(map(int, set(test_subjects))),
        "replay_test_indices_zero_based": replay_indices.tolist(),
        "features_sha256": hashlib.sha256((PROCESSED / "features.npz").read_bytes()).hexdigest()}
    save_json(REPORTS / "data_split.json", report)
    print(f"Preparado: fit={len(fit_idx)}, val={len(val_idx)}, test={len(test)}")


if __name__ == "__main__":
    main()
