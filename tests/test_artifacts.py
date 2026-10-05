import hashlib
import json
import numpy as np
import pytest
from ml.src.common import ROOT, MODELS, REPORTS
from ml.src.features import extract_features, normalize


def test_no_subject_leakage():
    report = json.loads((REPORTS / "data_split.json").read_text(encoding="utf-8"))
    a, b, c = [set(report[f"{name}_subjects"]) for name in ("fit", "validation", "test")]
    assert a.isdisjoint(b) and a.isdisjoint(c) and b.isdisjoint(c)
    assert len(a | b | c) == 30
    assert report["n_fit"] + report["n_validation"] == 7352
    assert report["n_test"] == 2947


def test_model_golden_hash_and_exported_bytes(golden):
    import re
    blob = (MODELS / "har_int8.tflite").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == golden["model_sha256"]
    source = (ROOT / "firmware/main/generated/model_data.cc").read_text()
    exported = bytes(int(v, 16) for v in re.findall(r"0x([0-9a-f]{2})", source))
    assert exported == blob


def test_quantized_model_contract_and_replay(golden):
    tf = pytest.importorskip("tensorflow")
    from ml.src.evaluate import tflite_predict
    interpreter = tf.lite.Interpreter(model_path=str(MODELS / "har_int8.tflite"))
    interpreter.allocate_tensors()
    inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    assert inp["dtype"] == out["dtype"] == np.int8
    assert list(inp["shape"]) == [1, 36] and list(out["shape"]) == [1, 6]
    assert not any(t["dtype"] == np.float32 for t in interpreter.get_tensor_details())
    ops = {op["op_name"] for op in interpreter._get_ops_details()} - {"DELEGATE"}
    assert ops == {"FULLY_CONNECTED", "SOFTMAX"}
    f = extract_features(np.asarray(golden["windows"][:6], np.float32))
    z = normalize(f, np.asarray(golden["mean"], np.float32), np.asarray(golden["scale"], np.float32))
    p = tflite_predict(MODELS / "har_int8.tflite", z)
    np.testing.assert_allclose(p, golden["replay_probabilities"], atol=1e-7)
    np.testing.assert_allclose(p.sum(1), 1, atol=6 / 256)


def test_zip_path_traversal_is_rejected(tmp_path):
    import zipfile
    from scripts.download_dataset import safe_extract
    archive = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError):
        safe_extract(archive, tmp_path / "out")
