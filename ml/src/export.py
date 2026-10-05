"""Exporta modelo real, scaler, janelas REPLAY e golden vectors completos."""
import hashlib
import numpy as np
import tensorflow as tf
from .common import ROOT, MODELS, PROCESSED, GENERATED, CLASSES, save_json
from .features import extract_features, normalize, quantize
from .evaluate import tflite_predict


def float_literal(value):
    text = format(float(np.float32(value)), ".9g")
    if "." not in text and "e" not in text:
        text += ".0"
    return text + "f"


def c_array(name, array, kind="float"):
    a = np.asarray(array)
    dims = "".join(f"[{s}]" for s in a.shape)
    fmt = float_literal if kind == "float" else lambda x: str(int(x))

    def initializer(x):
        if x.ndim == 1:
            return "{" + ", ".join(fmt(v) for v in x) + "}"
        return "{\n" + ",\n".join(initializer(v) for v in x) + "\n}"
    return f"static const {kind} {name}{dims} = {initializer(a)};\n"


def main():
    GENERATED.mkdir(parents=True, exist_ok=True)
    blob = (MODELS / "har_int8.tflite").read_bytes()
    interpreter = tf.lite.Interpreter(model_content=blob)
    interpreter.allocate_tensors()
    inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    assert inp["dtype"] == out["dtype"] == np.int8
    scaler = np.load(MODELS / "scaler.npz")
    mean, scale = scaler["mean"], scaler["scale"]
    replay = np.load(PROCESSED / "replay.npz")
    windows = replay["windows"]
    features = extract_features(windows)
    normalized = normalize(features, mean, scale)
    q = quantize(normalized, *inp["quantization"])
    probs = tflite_predict(MODELS / "har_int8.tflite", normalized)
    header = "// Gerado por python -m ml.src.export. Nao editar.\n#pragma once\n#include <stdint.h>\n"
    (GENERATED / "model_data.h").write_text("#pragma once\n#include <cstddef>\nextern const unsigned char g_har_model[];\nextern const size_t g_har_model_len;\n", encoding="utf-8")
    byte_lines = [", ".join(f"0x{v:02x}" for v in blob[i:i + 16]) for i in range(0, len(blob), 16)]
    (GENERATED / "model_data.cc").write_text('#include "model_data.h"\nalignas(16) const unsigned char g_har_model[] = {\n' + ",\n".join(byte_lines) + "\n};\nconst size_t g_har_model_len = sizeof(g_har_model);\n", encoding="utf-8")
    params = header + c_array("HAR_MEAN", mean) + c_array("HAR_SCALE", scale)
    params += f"static const float HAR_INPUT_SCALE = {float_literal(inp['quantization'][0])};\n"
    params += f"static const int HAR_INPUT_ZERO = {inp['quantization'][1]};\n"
    params += f"static const float HAR_OUTPUT_SCALE = {float_literal(out['quantization'][0])};\n"
    params += f"static const int HAR_OUTPUT_ZERO = {out['quantization'][1]};\n"
    params += "static const char *const HAR_CLASSES[6] = {" + ", ".join(f'"{c}"' for c in CLASSES) + "};\n"
    (GENERATED / "model_params.h").write_text(params, encoding="utf-8")
    replay_h = header + "#define HAR_REPLAY_COUNT 6\n"
    for name, array, kind in [
        ("HAR_REPLAY_WINDOWS", windows, "float"), ("HAR_REPLAY_LABELS", replay["labels"], "int"),
        ("HAR_REPLAY_INDICES", replay["indices"], "int"), ("HAR_REPLAY_FEATURES", features, "float"),
        ("HAR_REPLAY_INPUTS", q, "int8_t"), ("HAR_REPLAY_PROBS", probs, "float")]:
        replay_h += c_array(name, array, kind)
    (GENERATED / "replay_data.h").write_text(replay_h, encoding="utf-8")
    rng = np.random.default_rng(42)
    synthetic = np.stack([np.zeros((128, 6), np.float32), np.ones((128, 6), np.float32),
        np.tile(np.linspace(-1, 1, 128, dtype=np.float32)[:, None], (1, 6)),
        rng.normal(size=(128, 6)).astype(np.float32)])
    golden_windows = np.concatenate([windows, synthetic])
    golden_features = extract_features(golden_windows)
    golden_normalized = normalize(golden_features, mean, scale)
    save_json(ROOT / "tests/golden_vectors.json", {
        "source": "First official test window per class + zero, constant, ramp, seeded noise",
        "model_sha256": hashlib.sha256(blob).hexdigest(), "test_indices": replay["indices"].tolist(),
        "windows": golden_windows.tolist(), "features": golden_features.tolist(),
        "mean": mean.tolist(), "scale": scale.tolist(), "normalized": golden_normalized.tolist(),
        "input_scale": inp["quantization"][0], "input_zero_point": inp["quantization"][1],
        "quantized": quantize(golden_normalized, *inp["quantization"]).tolist(),
        "replay_labels": replay["labels"].tolist(), "replay_probabilities": probs.tolist()})
    save_json(ROOT / "ml/reports/replay_reference.json", {
        "test_indices_zero_based": replay["indices"].tolist(), "subjects": replay["subjects"].tolist(),
        "true_labels": replay["labels"].tolist(), "predicted_labels": probs.argmax(1).tolist(),
        "probabilities": probs.tolist(), "selection": "First test window of each class, before inference",
        "model_sha256": hashlib.sha256(blob).hexdigest()})
    print(f"Exportado modelo de {len(blob)} bytes, 6 janelas REPLAY e 10 golden vectors")


if __name__ == "__main__":
    main()
