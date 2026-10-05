"""Compila o mesmo modulo C usado no ESP-IDF; falha, nao simula equivalencia."""
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
FLOAT_PTR = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
INT8_PTR = np.ctypeslib.ndpointer(dtype=np.int8, flags="C_CONTIGUOUS")


@pytest.fixture(scope="session")
def golden():
    return json.loads((ROOT / "tests/golden_vectors.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def core():
    build = ROOT / "tests/.build"
    build.mkdir(exist_ok=True)
    library = build / ("har_core.dll" if os.name == "nt" else "libhar_core.so")
    import importlib.util
    if importlib.util.find_spec("ziglang"):
        compiler = [sys.executable, "-m", "ziglang", "cc"]
    elif shutil.which("gcc"):
        compiler = ["gcc"]
    else:
        pytest.fail("Instale requirements-dev.txt: compilador necessario para equivalencia real Python/C")
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(build / "zig-cache"), ZIG_LOCAL_CACHE_DIR=str(build / "zig-local"))
    cmd = compiler + ["-shared", "-O2", "-std=c11", "-ffp-contract=off", "-fno-fast-math",
          "-I", str(ROOT / "firmware/components/har_core/include"),
          str(ROOT / "firmware/components/har_core/har_features.c"), "-o", str(library)]
    if os.name != "nt":
        cmd += ["-fPIC", "-lm"]
    subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    dll = ctypes.CDLL(str(library))
    dll.har_extract.argtypes = [FLOAT_PTR, FLOAT_PTR]
    dll.har_extract.restype = ctypes.c_bool
    dll.har_normalize.argtypes = [FLOAT_PTR] * 4
    dll.har_normalize.restype = ctypes.c_bool
    dll.har_quantize.argtypes = [FLOAT_PTR, ctypes.c_float, ctypes.c_int, INT8_PTR, ctypes.c_size_t]
    dll.har_quantize.restype = ctypes.c_bool
    return dll
