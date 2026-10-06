#!/usr/bin/env bash
set -eo pipefail
# export.sh escolhe o venv do SDK pelo Python encontrado no PATH.
# A imagem IDF usa o Python do sistema (3.12), e o ML usa 3.11.
export PATH="/usr/bin:$PATH"
unset VIRTUAL_ENV
source /opt/esp/idf/export.sh >/dev/null
exec "$IDF_PYTHON_ENV_PATH/bin/python" "$IDF_PATH/tools/idf.py" "$@"
