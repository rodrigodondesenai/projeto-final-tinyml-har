# Reconhecimento de atividades humanas com TinyML

> **Projeto final — Unidade Curricular: IA Embarcada e Modelos Compactos**

## Integrantes do grupo

- Gabriel Monteiro de Souza
- Renan Cardoso dos Santos
- Rodrigo Teles Dondé

## Objetivo e justificativa

O objetivo é reconhecer seis atividades humanas a partir de sinais de
acelerômetro e giroscópio: `WALKING`, `WALKING_UPSTAIRS`,
`WALKING_DOWNSTAIRS`, `SITTING`, `STANDING` e `LAYING`. A classificação exige
analisar conjuntamente padrões temporais de movimento e postura em seis canais;
por isso foi utilizado aprendizado de máquina em vez de regras isoladas por
limiar. O protótipo demonstra processamento local e não é um dispositivo médico.

## Como o projeto atende aos requisitos da atividade

| Requisito informado para a atividade | Implementação e motivo | Evidência |
|---|---|---|
| Dados coerentes com o sensor e treinamento de modelo | Utiliza o UCI HAR, com aceleração total e giroscópio, para treinar uma MLP de 1.814 parâmetros sem misturar voluntários de treino e teste. | [Metodologia](docs/metodologia.md), [treinamento](ml/reports/training.json) |
| Conversão e compactação para embarcados | O modelo foi convertido para TFLite INT8 para reduzir memória e permitir inferência no microcontrolador. | [Conversão e métricas](ml/reports/results.md) |
| Deploy real ou simulado | Firmware ESP-IDF executa no ESP32-S3 simulado com MPU6050 no Wokwi. | [Arquitetura](docs/arquitetura.md), `diagram.json` |
| Pipeline de ponta a ponta | As amostras são transformadas em 36 features, normalizadas, quantizadas e classificadas pelo TensorFlow Lite Micro. | [Arquitetura](docs/arquitetura.md) |
| Avaliação e evidências | Foram medidos accuracy, macro F1, tamanho e equivalência entre desktop e firmware; os testes automatizados também verificam os artefatos. | [Validação](docs/validacao.md), [evidências](evidencias/README.md) |
| Repositório público e organização do código | Código, modelos, documentação, testes e evidências estão versionados; `main` e `develop` iniciam o fluxo de trabalho definido para o grupo. | [Git Flow](docs/git_flow.md) |

## Resultados e estado da demonstração

[Conferência final dos requisitos](docs/conferencia_final.md) reúne as
evidências técnicas e os limites da demonstração.

**REPLAY validado no Wokwi: 6/6 comparações PASS com kernels ANSI C.**
A execução inicial com kernels otimizados apresentou divergência de saída;
a troca para ANSI C resolveu a divergência nas seis janelas, mantendo o
modelo e as tolerâncias. [Serial real](evidencias/replay-serial.txt) e
[registro da investigação](docs/validacao.md).

**LIVE validado funcionalmente no Wokwi:** o MPU6050 simulado forneceu
amostras por I2C, a janela foi formada e a inferência ocorreu a cada 1,28 s.
Com o sensor parado, a saída foi `LAYING`; isso não mede accuracy de atividade
humana. Consulte [a evidência LIVE](evidencias/live-wokwi.txt).

Os modelos e relatórios medidos estão em [ml/reports/results.md](ml/reports/results.md). O registro de build, testes e pendências está em [docs/validacao.md](docs/validacao.md). **Resultados UCI/REPLAY não comprovam accuracy com um MPU6050 real.**

| Modelo | Arquivo | Accuracy no teste | Macro F1 |
|---|---:|---:|---:|
| Keras FP32 | 42.119 bytes | 81,27% | 0,8082 |
| TFLite FP32 | 9.072 bytes | 81,27% | 0,8082 |
| TFLite INT8 | 4.240 bytes | 81,13% | 0,8070 |

Comparação na mesma base de 2.947 janelas. O FlatBuffer INT8 é 53,26% menor; a queda de accuracy é 0,136 ponto percentual. O arquivo Keras inclui estado de treinamento, portanto não é a base adequada para medir a compressão dos pesos. Não se alteraram hiperparâmetros após observar o teste.

## Execução Python (PowerShell, na raiz)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/download_dataset.py
.\.venv\Scripts\python.exe -m ml.src.prepare
.\.venv\Scripts\python.exe -m ml.src.train
.\.venv\Scripts\python.exe -m ml.src.convert
.\.venv\Scripts\python.exe -m ml.src.evaluate
.\.venv\Scripts\python.exe -m ml.src.export
.\.venv\Scripts\python.exe -m pytest -q
```

Ou execute `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1` após instalar as dependências. Para repetir exatamente o ambiente Windows registrado, instale `requirements-lock-windows.txt`. O download usa exclusivamente a UCI; sem conexão, obtenha o ZIP oficial e use `scripts/download_dataset.py --archive 'C:\caminho\arquivo.zip'`.

Os artefatos já gerados permitem executar os testes e compilar sem treinar novamente. Nunca substitua o modelo sem reexportar scaler, referências e vetores. O exportador não contém modelo fictício de fallback.

## Firmware e Wokwi

Reutilize o ESP-IDF **5.4.2** instalado. No ambiente Windows encontrado neste computador:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_firmware.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_firmware.ps1 -Mode LIVE
```

O script aceita `-IdfPath` e `-ToolsPath` em outro computador. Não instala nem altera o SDK. No terminal ESP-IDF já ativado, a alternativa é:

```powershell
cd firmware
idf.py set-target esp32s3
idf.py build
idf.py -p COM5 flash monitor
```

Substitua `COM5` pela porta da placa. Para LIVE em um terminal ESP-IDF, use `idf.py menuconfig`, menu **TinyML HAR**, escolha LIVE e recompile. No Windows, o script mantém builds e sdkconfigs separados; o caminho dos pais com espaços pode exigir os nomes curtos que ele fornece.

Abra `diagram.json` no VS Code, instale/ative a extensão Wokwi e execute **Wokwi: Start Simulator**. `wokwi.toml` aponta ao build REPLAY completo (`flasher_args.json`, bootloader + partições + aplicação). A configuração já contém ESP32-S3, MPU6050, SDA GPIO 8 e SCL GPIO 9. Para simular LIVE, altere os dois caminhos de `firmware/build/` para `firmware/build-live/`.

REPLAY executa seis janelas reais, compara features, entrada INT8 e probabilidades com a referência desktop e imprime `REPLAY_SUMMARY ... status=PASS` apenas se a equivalência passar. PASS indica equivalência numérica, não que todas as seis previsões acertaram o rótulo verdadeiro. No conjunto escolhido sem seleção por acerto, a referência desktop acerta três de seis; todas são do voluntário 2. A accuracy publicada usa as 2.947 janelas, não essa demonstração. Salve a saída real e confira com `.\.venv\Scripts\python.exe scripts/check_replay_log.py evidencias/replay-serial.txt`.

LIVE usa I2C a 400 kHz, aquisição nominal de 50 Hz em tarefa separada, janela de 128 amostras e passo de 64. Saída serial: `class=... confidence=... invoke_us=...`. A confiança é o maior softmax quantizado; não é probabilidade calibrada de acerto.

## Organização

```text
docs/                  arquitetura, metodologia, validação, apresentação, Git Flow
data/                  procedência; raw/ e processed/ ficam fora do Git
ml/src/                features, preparação, treino, conversão, avaliação, exportação
ml/models/             Keras, TFLite FP32, TFLite INT8 e scaler
ml/reports/            métricas, matrizes, split, treino, conversão e REPLAY
ml/notebooks/          exploração dos relatórios, sem duplicar o treinamento
firmware/components/   núcleo C testado no host e usado no ESP32
firmware/main/         MPU6050, TFLM, LIVE/REPLAY e artefatos gerados
tests/                 equivalência real Python/C, golden vectors e contratos
evidencias/            registros de execução e roteiro de evidências
scripts/               download, pipeline e build
```

Repositório público: [rodrigodondesenai/projeto-final-tinyml-har](https://github.com/rodrigodondesenai/projeto-final-tinyml-har).

Leia [arquitetura](docs/arquitetura.md), [metodologia](docs/metodologia.md), [apresentação de 10 minutos](docs/guia_apresentacao.md) e [Git Flow](docs/git_flow.md).

## Fontes e atribuição

Dataset: Reyes-Ortiz et al., *Human Activity Recognition Using Smartphones*, [UCI, DOI 10.24432/C54S4K](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones). Artigo: Anguita et al., *A Public Domain Dataset for Human Activity Recognition using Smartphones*, ESANN 2013. A página atual indica CC BY 4.0; o README histórico do ZIP contém uma restrição comercial diferente. Preservamos essa distinção em [data/README.md](data/README.md) e a autoria dos dados.

Referências de implementação: [TFLM Espressif](https://github.com/espressif/esp-tflite-micro), [quantização inteira TensorFlow](https://www.tensorflow.org/lite/performance/post_training_integer_quant), [Wokwi ESP-IDF](https://docs.wokwi.com/vscode/project-config), [MPU6050](https://docs.wokwi.com/parts/wokwi-mpu6050).
