import ctypes
import numpy as np
import pytest
from ml.src.features import extract_features, fit_scaler, normalize, quantize
from conftest import FLOAT_PTR


@pytest.mark.parametrize("index", range(10))
def test_real_c_golden_pipeline(core, golden, index):
    window = np.asarray(golden["windows"][index], np.float32)
    expected = np.asarray(golden["features"][index], np.float32)
    mean, scale = (np.asarray(golden[key], np.float32) for key in ("mean", "scale"))
    f, z, q = np.empty(36, np.float32), np.empty(36, np.float32), np.empty(36, np.int8)
    assert core.har_extract(window, f)
    np.testing.assert_allclose(f, expected, rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(extract_features(window), expected, rtol=1e-5, atol=1e-6)
    assert core.har_normalize(f, mean, scale, z)
    np.testing.assert_allclose(z, golden["normalized"][index], rtol=1e-5, atol=1e-5)
    assert core.har_quantize(z, golden["input_scale"], golden["input_zero_point"], q, 36)
    np.testing.assert_array_equal(q, golden["quantized"][index])


def test_known_statistics():
    x = np.ones((128, 6), np.float32) * np.arange(1, 7, dtype=np.float32)
    f = extract_features(x).reshape(6, 6)
    for i in range(6):
        k = i + 1
        np.testing.assert_allclose(f[i], [k, 0, k, k, k, k*k])


def test_std_uses_population_and_channel_order():
    x = np.zeros((128, 6), np.float32)
    x[::2, 2], x[1::2, 2] = -2, 2
    f = extract_features(x).reshape(6, 6)
    np.testing.assert_allclose(f[2], [0, 2, 2, -2, 2, 4])
    assert np.count_nonzero(f[[0, 1, 3, 4, 5]]) == 0


def test_rounding_and_saturation(core):
    x = np.array([-1000, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1000], np.float32)
    expected = np.array([-128, -3, -2, -1, 1, 2, 3, 127], np.int8)
    actual = np.empty_like(expected)
    assert core.har_quantize(x, 0.5, 0, actual, len(x))
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(quantize(x, 0.5, 0), expected)


def test_reject_invalid(core):
    x = np.zeros((128, 6), np.float32)
    x[10, 4] = np.nan
    with pytest.raises(ValueError):
        extract_features(x)
    assert not core.har_extract(x, np.empty(36, np.float32))
    assert not core.har_quantize(np.ones(1, np.float32), 0, 0, np.empty(1, np.int8), 1)
    assert not core.har_normalize(np.zeros(36, np.float32), np.zeros(36, np.float32), np.zeros(36, np.float32), np.empty(36, np.float32))


def test_constant_scaler():
    f = np.ones((10, 36), np.float32)
    mean, scale = fit_scaler(f)
    assert np.isfinite(normalize(f, mean, scale)).all()
    np.testing.assert_array_equal(normalize(f, mean, scale), 0)


class Ring(ctypes.Structure):
    _fields_ = [("samples", ctypes.c_float * 768), ("next", ctypes.c_size_t),
                ("count", ctypes.c_size_t), ("since_emit", ctypes.c_size_t)]


def test_window_overlap_reset_and_order(core):
    core.har_window_reset.argtypes = [ctypes.POINTER(Ring)]
    core.har_window_push.argtypes = [ctypes.POINTER(Ring), FLOAT_PTR, FLOAT_PTR]
    core.har_window_push.restype = ctypes.c_bool
    ring = Ring()
    core.har_window_reset(ctypes.byref(ring))
    output = np.empty((128, 6), np.float32)
    ready_indices = []
    for i in range(400):
        sample = np.arange(6, dtype=np.float32) + i * 10
        if core.har_window_push(ctypes.byref(ring), sample, output):
            ready_indices.append(i)
            expected = np.arange(i - 127, i + 1, dtype=np.float32)[:, None] * 10 + np.arange(6, dtype=np.float32)
            np.testing.assert_array_equal(output, expected)
    assert ready_indices == [127, 191, 255, 319, 383]
    core.har_window_reset(ctypes.byref(ring))
    assert ring.count == ring.next == ring.since_emit == 0


def test_sensor_units_signed_endianness_and_temperature(core):
    import struct
    words = [16384, -16384, 8192, 12345, 131, -131, 0]
    raw = (ctypes.c_uint8 * 14).from_buffer_copy(struct.pack(">7h", *words))
    sample = np.empty(6, np.float32)
    core.har_mpu_decode.argtypes = [ctypes.POINTER(ctypes.c_uint8), FLOAT_PTR]
    core.har_mpu_decode(raw, sample)
    np.testing.assert_allclose(sample, [1, -1, 0.5, np.pi / 180, -np.pi / 180, 0], atol=1e-7)
