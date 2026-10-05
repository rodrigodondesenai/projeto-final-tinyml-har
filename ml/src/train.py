"""MLP compacta; selecao de epoca somente pela validacao interna."""
import os
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import argparse
import numpy as np
import tensorflow as tf
from .common import PROCESSED, MODELS, REPORTS, SEED, save_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=150)
    args = parser.parse_args()
    tf.keras.utils.set_random_seed(SEED)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    data = np.load(PROCESSED / "features.npz")
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(36,), name="features"),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(6, activation="softmax", name="activities")])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    stop = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=20, restore_best_weights=True)
    history = model.fit(data["x_train"], data["y_train"],
        validation_data=(data["x_val"], data["y_val"]), epochs=args.epochs,
        batch_size=64, shuffle=True, callbacks=[stop], verbose=2)
    MODELS.mkdir(parents=True, exist_ok=True)
    model.save(MODELS / "har_fp32.keras")
    np.savez(MODELS / "scaler.npz", mean=data["mean"], scale=data["scale"])
    save_json(REPORTS / "training.json", {"seed": SEED, "tensorflow": tf.__version__,
        "parameters": model.count_params(), "epochs_run": len(history.history["loss"]),
        "selected_epoch": int(np.argmin(history.history["val_loss"])) + 1,
        "history": history.history})


if __name__ == "__main__":
    main()
