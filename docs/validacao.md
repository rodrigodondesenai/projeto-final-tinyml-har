# Validação da implementação

Execução realizada em 05/10/2026, Windows, dentro de `projeto-final-tinyml-har`. Python 3.11 local para ML; Python 3.13.1 já existente no ambiente do ESP-IDF para compilação. ESP-IDF 5.4.2 preservado; nenhum SDK global foi atualizado e nenhum `managed_components` foi editado manualmente.

## Investigação da execução Wokwi

Depois dos builds iniciais, o usuário executou o REPLAY no Wokwi e enviou
`REPLAY_SUMMARY passed=0 total=6 status=FAIL`. O log real está em
`evidencias/replay-wokwi-inicial.txt`. As seis janelas apresentaram erro de
features igual a zero na precisão impressa, mas erro máximo de probabilidades
entre 0,10156250 e 0,60156250. Arena usada: 2.876 bytes; Invoke no simulador:
5.354–5.356 us (não é benchmark de placa).

O firmware inicial selecionava `CONFIG_NN_OPTIMIZED=y`. A versão de diagnóstico
passa a usar a opção suportada `CONFIG_NN_ANSI_C=y`, sem mudar modelo, scaler,
dados, tolerâncias ou bibliotecas gerenciadas. Também informa quantas features
e entradas INT8 divergem, a primeira entrada divergente e cada probabilidade
esperada/obtida. Na nova execução enviada pelo usuário, **as seis janelas
passaram**, com erro de features e probabilidades igual a zero na precisão
impressa; a entrada INT8 também passou na comparação exata. O serial real
está em `evidencias/replay-serial.txt` e foi aceito por `check_replay_log.py`.
Invoke medido no simulador: 3.105–3.130 us. Isso confirma a solução ANSI C
nessa configuração; não determina qual instrução/kernel otimizado causou
o desvio nem demonstra defeito no ESP32-S3 físico.

Os tamanhos e hashes em `evidencias/builds.json` referem-se aos builds iniciais.
O build LIVE inicial era otimizado. Na auditoria foi reconfigurado e
recompilado com ANSI C; o build atual está em `evidencias/live-ansi-build.json`,
ainda sem execução LIVE comprovada. Alterações em `sdkconfig.defaults` não
substituem escolhas de um sdkconfig existente: para outros builds, selecione
`ESP-NN → Optimization for nn functions → ANSI C` no `idf.py menuconfig`
daquele build e recompile.

## Evidências dos builds iniciais

| Etapa | Resultado |
|---|---|
| Download oficial UCI | Concluído; SHA256 em `data/provenance.json` |
| Preparação | 5.551 ajuste / 1.801 validação / 2.947 teste, pessoas disjuntas |
| Treinamento | 33 épocas; melhores pesos da época 13; 1.814 parâmetros |
| Conversão | Keras FP32, TFLite FP32 e TFLite INT8 gerados e avaliados |
| Contrato INT8 | Entrada/saída INT8, sem tensores FP32, operadores FullyConnected/Softmax |
| Golden vectors | 6 janelas reais + zero, constante, rampa e ruído |
| Testes automatizados | 21 passed em 28,71 s, incluindo C compilado e carregado no host |
| ESP-IDF REPLAY | Build concluído; `firmware/build/tinyml_har.bin`, 272.464 bytes |
| ESP-IDF LIVE | Build concluído; `firmware/build-live/tinyml_har.bin`, 272.496 bytes |
| Wokwi | Execução inicial otimizada 0/6; nova execução ANSI C **6/6 PASS** |
| Wokwi LIVE | Executado com ANSI C: I2C, janela e inferência contínua; `evidencias/live-wokwi.txt` |
| Placa física | Não executada nem medida |
| GitHub Actions | Workflow preparado; não executado no GitHub |

A primeira tentativa de testes encontrou uma restrição de acesso à pasta temporária do pytest; a repetição autorizada passou. A primeira tentativa de build encontrou bloqueio de subprocessos do ambiente restrito; repetição autorizada gerou o firmware. Isso não foi erro de inferência ou motivo para omitir testes.

## Métricas

| Modelo | Bytes | Accuracy | Macro F1 |
|---|---:|---:|---:|
| Keras FP32 | 42.119 | 81,27% | 0,8082 |
| TFLite FP32 | 9.072 | 81,27% | 0,8082 |
| TFLite INT8 | 4.240 | 81,13% | 0,8070 |

Redução entre FlatBuffers: 53,26%. Queda de accuracy: 0,135731 ponto percentual. Concordância de classes FP32/INT8: 98,8463%. Maior diferença de probabilidade Keras/TFLite FP32: 6,56e-7. Matrizes completas para os três modelos em `ml/reports/metrics.json`; matriz INT8 legível em `ml/reports/results.md`.

Os erros mais frequentes incluem escadas versus caminhada e sentado versus em pé. A baseline é limitada e não foi ajustada usando esses resultados do teste. As seis janelas REPLAY são todas do voluntário 2, índices base zero `[79, 133, 109, 31, 0, 55]`, e três classificações desktop estão corretas. PASS/FAIL embarcado compara com essas previsões, incluindo seus erros; não cria 100% de accuracy artificial.

## Build e memória

Dependências resolvidas: `espressif/esp-tflite-micro=1.3.1`, `espressif/esp-nn=1.4.1`, IDF 5.4.2, registradas em `firmware/dependencies.lock`. Compilador Xtensa GCC 14.2.0. Modelo, scaler e janelas usados são os gerados pelo treino real.

Os hashes dos dois binários iniciais e a confirmação dos modos compilados estão em `evidencias/builds.json`. Os mapas iniciais foram analisados pelo `esp_idf_size`, registrados em `evidencias/replay-size.json` e `evidencias/live-size.json`. No REPLAY inicial, a região DIRAM ocupa 90.863 bytes estaticamente de 341.760, incluindo código/dados dessa região; isso não representa o pico de heap em execução. A arena reserva 32 KiB; o log inicial mediu 2.876 bytes usados. O trecho ANSI C recebido não inclui a linha da arena, portanto não se atribui automaticamente essa medição ao novo binário. O REPLAY ANSI C tem 269.440 bytes, com hash em `evidencias/replay-diagnostico.json`. Não usar o BSS agregado de `size` como estimativa direta da RAM física ESP32.

Houve avisos não fatais de caminhos longos do CMake e de código de terceiros (`std::is_pod`/shadowing). A primeira configuração REPLAY também avisou sobre `ESP_ROM_ELF_DIR`, utilizado para depuração GDB; o script passou a localizar essa pasta já instalada. Não foi necessária alteração do SDK ou de dependências gerenciadas para concluir o build.

## Pendências para a entrega acadêmica

1. Captura e serial REPLAY já salvos: `evidencias/wokwi-replay-pass.png` e `evidencias/replay-serial.txt`. Checklist completo e próximos passos em `docs/conferencia_requisitos.md`.
2. O LIVE no Wokwi já registrou arena usada (860 bytes) e `Invoke()` de 3.125–3.126 us. Para desempenho de hardware, usar placa física.
3. Para afirmar desempenho LIVE com pessoas, coletar dados MPU6050 rotulados com mesma fixação/eixos/filtros, calibrar e avaliar voluntários independentes. A simulação não valida accuracy do sensor.
4. Revisar a publicação e escolher a licença do código. Efetuar commits, branches Git Flow, remoto e push manualmente.

## Comandos para continuar

Na raiz do workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_firmware.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_firmware.ps1 -Mode LIVE
```

No VS Code: `F1` → `Wokwi: Start Simulator`. O `wokwi.toml` padrão aponta a REPLAY. Após copiar a saída serial real para `evidencias/replay-serial.txt`:

```powershell
.\.venv\Scripts\python.exe scripts/check_replay_log.py evidencias/replay-serial.txt
```

Para placa física, em terminal ESP-IDF ativado, substituindo a porta correta:

```powershell
cd firmware
idf.py -B build -p COM5 flash monitor
```

Para LIVE, ainda dentro de `firmware`, use:

```powershell
idf.py -B build-live -D SDKCONFIG=sdkconfig.live -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.live.defaults" -p COM5 flash monitor
```

Alternativamente escolha LIVE no `menuconfig` e recompile conforme README. A criação de evidência serial não foi simulada neste projeto.

## Git

Repositório local inicializado, branch inicial `main`, nenhum commit, staging ou push. `git diff --stat` vazio é esperado porque todos os arquivos são novos e não rastreados. `git status --short` os exibe com `??`. Inventário completo em `docs/arquivos_criados.md`; snapshot dos comandos em `evidencias/git-status.txt`.
