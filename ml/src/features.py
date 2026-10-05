"""Features em float32; acumulacao sequencial, igual a har_features.c."""
import numpy as np
from .common import WINDOW


def extract_features(windows):
    x = np.asarray(windows, dtype=np.float32)
    single = x.ndim == 2
    if single:
        x = x[None, ...]
    if x.ndim != 3 or x.shape[1:] != (WINDOW, 6) or not np.isfinite(x).all():
        raise ValueError("Esperado (N,128,6) ou (128,6), valores finitos")
    total = np.zeros((len(x), 6), np.float32)
    squares = np.zeros_like(total)
    low, high = x[:, 0].copy(), x[:, 0].copy()
    for i in range(WINDOW):
        total += x[:, i]
        squares += x[:, i] * x[:, i]
        low = np.minimum(low, x[:, i])
        high = np.maximum(high, x[:, i])
    mean = total / np.float32(WINDOW)
    variance = np.zeros_like(total)
    for i in range(WINDOW):
        delta = x[:, i] - mean
        variance += delta * delta
    energy = squares / np.float32(WINDOW)
    out = np.stack([mean, np.sqrt(variance / np.float32(WINDOW)),
                    np.sqrt(energy), low, high, energy], axis=-1).reshape(len(x), 36)
    return out[0] if single else out


def fit_scaler(features):
    # Estimacao estavel; exportar os mesmos parametros float32 ao C.
    mean = features.astype(np.float64).mean(axis=0).astype(np.float32)
    scale = features.astype(np.float64).std(axis=0).astype(np.float32)
    scale[scale < 1e-6] = 1.0
    return mean, scale


def normalize(features, mean, scale):
    return (np.asarray(features, np.float32) - mean) / scale


def quantize(values, scale, zero_point):
    """Round half away from zero, identico a roundf do C99."""
    if scale <= 0:
        raise ValueError("Escala de quantizacao deve ser positiva")
    x = np.asarray(values, np.float32) / np.float32(scale)
    rounded = np.copysign(np.floor(np.abs(x) + np.float32(0.5)), x)
    return np.clip(rounded + zero_point, -128, 127).astype(np.int8)
