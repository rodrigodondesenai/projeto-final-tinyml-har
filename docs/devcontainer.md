# Ambiente de desenvolvimento em contêiner

## Abrir e executar

Pré-requisitos: Docker com engine Linux e VS Code com a extensão
`ms-vscode-remote.remote-containers`. No Windows, o Docker Desktop pode usar WSL 2.
Abra a raiz deste repositório e execute **Dev Containers: Reopen in Container**.
A primeira criação baixa as imagens, o SDK e os wheels Python, exigindo internet
e espaço em disco. Alterações no Dockerfile ou no lock exigem
**Dev Containers: Rebuild Container**.

O repositório é montado em `/workspaces/tinyml-har`, evitando espaços e acentos
nos caminhos usados pelo CMake. A arquitetura é Linux amd64, inclusive em hosts
ARM (que precisam de emulação). O ambiente Python fica em `/opt/har-venv`, sem
reutilizar ou sobrescrever uma `.venv` Windows. O Python do ESP-IDF permanece
separado em `/opt/esp/python_env`; o comando `idf.py` ativa esse SDK em um
processo próprio. Terminais e tarefas usam Python do ML por padrão.

Ao criar o ambiente, `pip check` e a suíte `pytest` verificam dependências,
equivalência Python/C e o modelo INT8 já versionado. A criação não baixa o
dataset, não treina e não reexporta os artefatos.

```bash
python --version
idf.py --version
python -m pip check
python -m pytest -q
python scripts/check_replay_log.py evidencias/replay-serial.txt
```

## Versões preservadas

- Python 3.11 (imagem Python 3.11.9) e ESP-IDF 5.4.2.
- `requirements.txt` e `requirements-dev.txt` permanecem como estavam.
- `requirements-lock-linux.txt` preserva todas as versões aplicáveis do
  `requirements-lock-windows.txt`, incluindo as dependências transitivas.
  Apenas `tensorflow-intel` e `colorama` são omitidos: no Windows, o primeiro
  fornece o runtime de TensorFlow; no Linux, ele está no wheel
  `tensorflow==2.16.1`. `colorama` é uma dependência condicional do pytest no
  Windows. O lock Windows continua disponível e inalterado.
- `firmware/dependencies.lock` continua definindo TFLite Micro 1.3.1 e
  ESP-NN 1.4.1. Os defaults mantêm os kernels ANSI C e o alvo ESP32-S3.

Modelos, scaler, vetores, firmware e algoritmos existentes não são modificados
pela configuração. Retreinar em outro sistema operacional/CPU pode produzir
diferenças numéricas; as mesmas versões não garantem pesos ou binários idênticos
entre plataformas. Para repetir a demonstração, use os artefatos versionados.

## Pipeline Python

Os módulos existentes funcionam diretamente com `python`:

```bash
python scripts/download_dataset.py
python -m ml.src.prepare
python -m ml.src.train
python -m ml.src.convert
python -m ml.src.evaluate
python -m ml.src.export
python -m pytest -q
```

O equivalente ao helper PowerShell é `bash scripts/run_pipeline.sh`, com 150
épocas por padrão e as mesmas etapas e interrupção em caso de erro. Aceita
`--epochs N` e `--skip-download`. Esse comando sobrescreve os modelos e
relatórios, assim como o pipeline original. O download offline continua
disponível com `python scripts/download_dataset.py --archive /caminho/arquivo.zip`.

## Firmware, Wokwi e placa

```bash
bash scripts/build_firmware.sh REPLAY
bash scripts/build_firmware.sh LIVE
python scripts/select_wokwi_mode.py REPLAY
# Ou: python scripts/select_wokwi_mode.py LIVE
```

Os helpers mantêm `firmware/build` e `firmware/build-live`, com `sdkconfig` e
`sdkconfig.live` separados, exatamente como os scripts Windows. Não reutilize
esses diretórios ao alternar entre build Windows e Linux: CMake guarda caminhos
absolutos e toolchains. Para manter os dois ambientes simultaneamente, use
checkouts separados; para alternar no mesmo checkout, remova somente os builds
gerados e os sdkconfigs gerados antes de compilar. Os defaults versionados
permanecem como fonte de configuração.

Abra `diagram.json` e use **Wokwi: Start Simulator**. A extensão Wokwi é
instalada no contêiner; sua licença/ativação continua necessária. O seletor só
altera `wokwi.toml` depois de verificar a presença do build. O script
`select_wokwi_mode.ps1` continua disponível no Windows.

Para placa física, a porta serial precisa estar disponível dentro do contêiner.
Em Linux, adicione o dispositivo real a `runArgs` no `devcontainer.json`, por
exemplo `"--device=/dev/ttyUSB0"`, e reconstrua o contêiner. No Windows/WSL,
configure primeiro o encaminhamento USB da placa para o Linux. A porta `COM5`
do host não aparece automaticamente no contêiner. Com a porta disponível:

```bash
cd firmware
idf.py -B build -p /dev/ttyUSB0 flash monitor
# LIVE: idf.py -B build-live -D SDKCONFIG=sdkconfig.live -p /dev/ttyUSB0 flash monitor
```

## Validar sem VS Code

Na raiz, em PowerShell:

```powershell
docker build --platform linux/amd64 -f .devcontainer/Dockerfile -t tinyml-har-devcontainer:local .
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/workspaces/tinyml-har" tinyml-har-devcontainer:local python -m pytest -q
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/workspaces/tinyml-har" tinyml-har-devcontainer:local bash scripts/build_firmware.sh REPLAY
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/workspaces/tinyml-har" tinyml-har-devcontainer:local bash scripts/build_firmware.sh LIVE
```

Para erros de conexão ao Docker, confira `docker context ls` e
`docker version`: o contexto selecionado precisa alcançar o engine Linux.

## Validação realizada

Em 06/10/2026, no Docker Desktop com engine Linux amd64:

- A criação e reconstrução com `@devcontainers/cli` 0.89.0 passaram, incluindo
  o `postCreateCommand`: `pip check` sem conflitos e 21 testes aprovados.
- Todas as versões listadas no lock Linux foram conferidas contra os pacotes
  instalados. `python --version` retornou 3.11.9 e `idf.py --version`, 5.4.2.
- O pipeline completo com os argumentos padrão passou em uma cópia temporária,
  incluindo download UCI, preparação, treino, conversão, avaliação, exportação
  e 21 testes. As accuracies coincidiram com as registradas: 81,27% para FP32
  e 81,13% para INT8, com o modelo INT8 de 4.240 bytes.
- Os helpers foram verificados quanto à passagem de argumentos, interrupção
  em caso de erro e seleção de builds Wokwi presentes/ausentes.
- Os builds REPLAY e LIVE passaram com ESP-IDF 5.4.2 e GCC 14.2.0.
  Todos os defaults foram conferidos nos sdkconfigs gerados, incluindo alvo
  ESP32-S3 e kernels ANSI C. O lock de componentes permaneceu inalterado.

Os modelos, relatórios, vetores e evidências originais não foram substituídos.
A simulação Wokwi e o flash em placa física não foram reexecutados nesta
validação do ambiente.

Referências: [Dev Containers com Dockerfile](https://containers.dev/guide/dockerfile)
e [imagem oficial ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32/api-guides/tools/idf-docker-image.html).
