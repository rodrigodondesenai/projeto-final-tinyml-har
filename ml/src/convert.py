"""Flatbuffers FP32 e INT8 puro; calibracao exclusivamente no treino."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import hashlib
import numpy as np
import tensorflow as tf
from .common import PROCESSED, MODELS, REPORTS, SEED, save_json


def main():
    model = tf.keras.models.load_model(MODELS / "har_fp32.keras", compile=False)
    data = np.load(PROCESSED / "features.npz")
    # Congelar pesos como constantes evita incompatibilidades de variaveis Keras 3/TF 2.16.
    from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
    fn = tf.function(lambda x: model(x, training=False))
    concrete = fn.get_concrete_function(tf.TensorSpec([1, 36], tf.float32, name="features"))
    frozen = convert_variables_to_constants_v2(concrete)
    selected = np.random.default_rng(SEED).choice(len(data["x_train"]), min(512, len(data["x_train"])), replace=False)

    def representative():
        for i in selected:
            yield [data["x_train"][i:i + 1].astype(np.float32)]

    report = {"calibration_source": "fit subjects only", "calibration_count": len(selected), "models": {}}
    for name in ("har_fp32.tflite", "har_int8.tflite"):
        converter = tf.lite.TFLiteConverter.from_concrete_functions([frozen])
        if "int8" in name:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.representative_dataset = representative
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
        blob = converter.convert()
        (MODELS / name).write_bytes(blob)
        interpreter = tf.lite.Interpreter(model_content=blob)
        interpreter.allocate_tensors()
        inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
        ops = [op["op_name"] for op in interpreter._get_ops_details() if op["op_name"] != "DELEGATE"]
        if "int8" in name:
            assert inp["dtype"] == out["dtype"] == np.int8
            assert set(ops) <= {"FULLY_CONNECTED", "SOFTMAX"}, ops
            assert not any(t["dtype"] == np.float32 for t in interpreter.get_tensor_details())
        report["models"][name] = {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "operators": ops, "input_dtype": str(inp["dtype"]), "output_dtype": str(out["dtype"]),
            "input_quantization": list(inp["quantization"]), "output_quantization": list(out["quantization"])}
    save_json(REPORTS / "conversion.json", report)
    print("Conversao FP32 e INT8 concluida")


if __name__ == "__main__":
    main()
