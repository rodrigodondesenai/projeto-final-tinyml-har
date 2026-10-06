# Demonstração em vídeo

> **Rascunho para revisão** — branch `feature/demonstracao-renan`.
> Este documento registra o que o vídeo gravado mostra, confere esse conteúdo contra os requisitos do Projeto Final
> e traz o roteiro da tomada complementar e da narração.

**Link do vídeo:** `<colar aqui o link do YouTube não listado / Google Drive>`

> O arquivo `.mp4` **não é versionado**: são 18,7 MB de binário, que pesam no clone e não diferenciam no git.
> O repositório guarda o link e esta descrição.

---

## 1. O vídeo gravado (v1) — conferência

Arquivo local: `evidencias/video-demonstracao-tinyml-har.mp4`. Resolução 1636×948, 30 fps, **23 s**.
Conferido quadro a quadro em 05/10/26.

| Tempo | O que aparece na tela | Evidência |
|---|---|---|
| 0:00–0:02 | VS Code com o Wokwi Simulator aberto; circuito ESP32-S3-DevKitC-1 + MPU6050; terminal já no fim do REPLAY | Circuito montado no Wokwi |
| 0:02–0:06 | Simulação reiniciada; log de boot da ROM do ESP32-S3 | Firmware carregado no simulador |
| 0:06–0:12 | `ESP-IDF v5.4.2 2nd stage bootloader`, `SPI Flash Size: 8MB`, tabela de partições | Build feito com ESP-IDF, alvo ESP32-S3 |
| 0:12–0:20 | Linhas `replay=0..5` com `truth`, `class`, `confidence`, `invoke_us`, `feature_error=0.00000000`, `probability_error=0.00000000`, `parity=PASS` | Inferência TFLM no device, paridade com o desktop |
| 0:20–0:23 | `REPLAY_SUMMARY passed=6 total=6 status=PASS` e simulação parada | Resultado final do pipeline |

### O que o v1 cobre e o que falta

| Requisito (PDF do Projeto Final / escopo) | No v1? | Observação |
|---|---|---|
| Deploy em dispositivo simulado (Wokwi) | ✅ | ESP32-S3 + MPU6050 visíveis |
| Inferência do modelo no device | ✅ | 6 inferências com `invoke_us ≈ 3.130` |
| Pipeline “desde a leitura dos dados até a inferência” | 🟡 Parcial | O REPLAY lê janelas embutidas; **a leitura do sensor (LIVE) não aparece** |
| Coleta de dados de sensores | ❌ | Sem cena do MPU6050 sendo lido por I2C |
| Treino, conversão e compressão | ❌ | Não aparecem no vídeo, só nos slides e em `ml/reports/` |
| Narração/explicação | ⚠️ Não verificado | Conferir se há áudio; sem ele, o vídeo depende dos slides para ter contexto |

**Conclusão:** o v1 prova o REPLAY, mas não mostra o **sensor**, que é justamente a primeira etapa exigida.
Recomendação: **não regravar o v1.** Gravar uma tomada complementar curta, só do LIVE (seção 2), e juntar as duas.
Como só a configuração do Wokwi muda (sem tocar no código), o firmware congelado continua valendo.

---

## 2. Tomada complementar — LIVE (≈ 40 s)

**Quem grava:** Rodrigo, que tem o ESP-IDF 5.4.2 instalado.
**Pré-requisito:** build LIVE já existente (`scripts/build_firmware.ps1 -Mode LIVE`, saída em `firmware/build-live/`).

Preparação:
1. No `wokwi.toml`, trocar `firmware/build/` por `firmware/build-live/` nos dois caminhos. **Não commitar essa troca**: o padrão do repositório é o REPLAY.
2. **Ensaiar antes de gravar:** clicar no MPU6050 no Wokwi e testar se mudar a aceleração do eixo Z para o X altera a classe.
   - Se alterar, use a cena 2b.
   - Se não alterar, pule a 2b e grave só a 2a. A narração explica o porquê.

| Cena | Tempo | Ação | O que precisa ficar legível |
|---|---|---|---|
| 2a | 0:00–0:20 | Iniciar a simulação | `kernels=ESP_NN_ANSI_C`, `mode=LIVE`, `modelo_bytes=4240 arena_usada=860`, e linhas `class=LAYING confidence=0.996094 invoke_us=...` a cada ~1,28 s |
| 2b | 0:20–0:40 | Abrir o painel do MPU6050 e mover a gravidade de Z para X | A classe mudar no log após 1–2 janelas (até ~2,6 s de atraso, o tempo de encher a janela) |
| — | fim | Parar a simulação; restaurar o `wokwi.toml` | — |

---

## 3. Roteiro de narração

Pode ser narrado ao vivo na apresentação, sobre o vídeo sem áudio, ou gravado.
Duração alvo da versão final (v1 + LIVE): **~1 min 10 s**. Isso cabe nos 10 minutos de apresentação sem consumir o espaço dos slides.

| Trecho | Duração | Fala |
|---|---|---|
| Abertura (v1, 0:00) | 5 s | “Este é o ESP32-S3 simulado no Wokwi, ligado ao MPU6050 por I2C nos GPIOs 8 e 9.” |
| Boot (v1, 0:06) | 5 s | “O firmware foi compilado com o ESP-IDF 5.4.2; o modelo INT8 de 4.240 bytes vai embutido na flash.” |
| REPLAY (v1, 0:12) | 12 s | “No modo REPLAY, seis janelas reais do teste do UCI HAR, uma por atividade, passam pelo mesmo pipeline do sensor: features, normalização, quantização e TensorFlow Lite Micro. Para cada uma, o firmware compara com o resultado do Python.” |
| Resumo (v1, 0:20) | 8 s | “Seis de seis PASS, com erro zero nas features e nas probabilidades. Isso prova que o dispositivo calcula exatamente o que o modelo viu no treino. Não é accuracy: a accuracy de 81% vem das 2.947 janelas do teste.” |
| LIVE (2a) | 15 s | “No modo LIVE, uma task lê o MPU6050 a 50 Hz, monta janelas de 2,56 segundos e classifica a cada 1,28 segundo. Com o sensor parado, a gravidade está no eixo que o modelo associa a estar deitado: LAYING.” |
| LIVE (2b) | 10 s | Se a classe mudou: “Girando a gravidade para o eixo vertical, a classe muda para postura em pé ou sentada.” Se não mudou: “Atividades dinâmicas não podem ser simuladas com valores estáticos do Wokwi; por isso o REPLAY é a prova com dados reais.” |
| Fecho | 5 s | “Coleta, inferência e resultado no monitor serial, tudo no dispositivo.” |

---

## 4. Checklist antes de enviar

```
[ ] Link do vídeo colado no topo deste arquivo e acessível sem login
[ ] Duração total ≤ ~1 min 30 s
[ ] REPLAY_SUMMARY passed=6 total=6 status=PASS legível
[ ] Tomada LIVE com inferências periódicas (class=... confidence=... invoke_us=...)
[ ] Circuito ESP32-S3 + MPU6050 visível
[ ] wokwi.toml restaurado para firmware/build/ (REPLAY) no repositório
[ ] .mp4 fora do git (git status não lista o arquivo como staged)
```

## 5. Evidências relacionadas

| Arquivo | Conteúdo |
|---|---|
| [`evidencias/replay-serial.txt`](../evidencias/replay-serial.txt) | Log serial completo do REPLAY (o mesmo do vídeo) |
| [`evidencias/wokwi-replay-pass.png`](../evidencias/wokwi-replay-pass.png) | Screenshot do REPLAY PASS |
| [`evidencias/live-wokwi.txt`](../evidencias/live-wokwi.txt) | Log serial do LIVE (sensor parado → LAYING) |
| [`docs/validacao.md`](validacao.md) | Investigação ESP-NN × ANSI C e builds |
| [`docs/banca_perguntas.md`](banca_perguntas.md) | Respostas para “o que o PASS prova” e “por que LAYING” (6.1–6.3) |

Fundamentação no material de aula: execução no Wokwi com ESP-IDF **[A2, p. 38–42]**; desabilitar o ESP-NN no Wokwi **[A4, p. 41]**; pipeline sensor → pré-processamento → modelo **[A6, p. 8]**.
As siglas e os arquivos estão em [`guia_do_codigo.md`](guia_do_codigo.md#9-referências-ao-material-de-aula).
