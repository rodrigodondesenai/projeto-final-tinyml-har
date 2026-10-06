#!/usr/bin/env bash
set -euo pipefail
epochs=150
download=true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --epochs) epochs="${2:?Informe o numero de epocas}"; shift 2 ;;
        --skip-download) download=false; shift ;;
        *) echo 'Uso: bash scripts/run_pipeline.sh [--epochs N] [--skip-download]' >&2; exit 2 ;;
    esac
done
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if "$download"; then python scripts/download_dataset.py; fi
for stage in prepare train convert evaluate export; do
    if [[ "$stage" == train ]]; then python -m "ml.src.$stage" --epochs "$epochs"
    else python -m "ml.src.$stage"; fi
done
python -m pytest -q
