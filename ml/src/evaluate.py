"""Avaliacao unica do split oficial; nao escolhe hiperparametros no teste."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from .common import MODELS, PROCESSED, REPORTS, CLASSES, save_json
from .features import quantize


def tflite_predict(path, x):
    interpreter = tf.lite.Interpreter(model_path=str(path), num_threads=1)
    interpreter.allocate_tensors()
    inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    predictions = []
    for row in x:
        value = row[None].astype(np.float32)
        if inp["dtype"] == np.int8:
            value = quantize(value, *inp["quantization"])
        interpreter.set_tensor(inp["index"], value)
        interpreter.invoke()
        result = interpreter.get_tensor(out["index"])[0]
        if out["dtype"] == np.int8:
            scale, zero = out["quantization"]
            result = (result.astype(np.float32) - zero) * scale
        predictions.append(result)
    return np.asarray(predictions)


def main():
    data = np.load(PROCESSED / "features.npz")
    x, y = data["x_test"], data["y_test"]
    model = tf.keras.models.load_model(MODELS / "har_fp32.keras", compile=False)
    outputs = {"keras_fp32": model.predict(x, batch_size=256, verbose=0),
               "tflite_fp32": tflite_predict(MODELS / "har_fp32.tflite", x),
               "tflite_int8": tflite_predict(MODELS / "har_int8.tflite", x)}
    paths = ["har_fp32.keras", "har_fp32.tflite", "har_int8.tflite"]
    results = {}
    for (name, probs), path in zip(outputs.items(), paths):
        pred = probs.argmax(axis=1)
        results[name] = {"accuracy": accuracy_score(y, pred), "macro_f1": f1_score(y, pred, average="macro"),
            "bytes": (MODELS / path).stat().st_size,
            "confusion_matrix": confusion_matrix(y, pred, labels=range(6)).tolist(),
            "classification_report": classification_report(y, pred, labels=range(6), target_names=CLASSES, output_dict=True, zero_division=0)}
    report = {"test_windows": len(y), "classes": CLASSES, "models": results,
        "accuracy_drop_percentage_points": 100 * (results["tflite_fp32"]["accuracy"] - results["tflite_int8"]["accuracy"]),
        "int8_prediction_agreement": float(np.mean(outputs["tflite_fp32"].argmax(1) == outputs["tflite_int8"].argmax(1))),
        "fp32_max_probability_difference": float(np.max(np.abs(outputs["keras_fp32"] - outputs["tflite_fp32"]))) }
    save_json(REPORTS / "metrics.json", report)
    lines = ["# Resultados medidos no split oficial", "", f"Janelas: {len(y)}. Classes na ordem: {', '.join(CLASSES)}.", "",
             "| Modelo | Bytes do arquivo | Accuracy | Macro F1 |", "|---|---:|---:|---:|"]
    for name, values in results.items():
        lines.append(f"| {name} | {values['bytes']} | {values['accuracy']:.4f} | {values['macro_f1']:.4f} |")
    lines += ["", "O arquivo Keras inclui metadados/estado de treinamento; a comparacao de compressao usa os dois FlatBuffers.", "",
              f"Queda FP32 TFLite -> INT8: {report['accuracy_drop_percentage_points']:.4f} pontos percentuais.", "",
              "## Matriz de confusao INT8", "", "Linhas = verdadeiro; colunas = previsto; ordem de classes acima.", "", "```text"]
    lines += [" ".join(f"{v:4d}" for v in row) for row in results["tflite_int8"]["confusion_matrix"]]
    lines += ["```", "", "Metricas do interpretador desktop. Nao equivalem a validacao LIVE ou medicao no ESP32."]
    (REPORTS / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:10]))


if __name__ == "__main__":
    main()
