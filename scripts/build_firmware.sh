#!/usr/bin/env bash
set -euo pipefail
mode="${1:-REPLAY}"
case "$mode" in
    REPLAY) build=build; config=sdkconfig; defaults=sdkconfig.defaults ;;
    LIVE) build=build-live; config=sdkconfig.live; defaults='sdkconfig.defaults;sdkconfig.live.defaults' ;;
    *) echo 'Uso: bash scripts/build_firmware.sh [REPLAY|LIVE]' >&2; exit 2 ;;
esac
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root/firmware"
export IDF_TARGET=esp32s3 IDF_CCACHE_ENABLE=0 PYTHONUTF8=1
export IDF_COMPONENT_CACHE_PATH="$root/.cache/idf-components"
idf.py -B "$build" -D "SDKCONFIG=$root/firmware/$config" -D "SDKCONFIG_DEFAULTS=$defaults" build
