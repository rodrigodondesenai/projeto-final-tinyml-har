# Preparação para a banca — perguntas e respostas

> **Rascunho para revisão** — branch `feature/demonstracao-renan`.
> Formato da avaliação (PDF do Projeto Final): até **10 min** de apresentação + até **5 min** de perguntas do professor, **individuais**, para verificar o entendimento de cada integrante.
>
> **Regra do ensaio:** cada pergunta é respondida por quem **não** trabalhou naquela parte. As respostas têm no máximo 3 frases; o que está em *Se aprofundar* é para usar só se o professor insistir.
> A fundamentação segue o formato **[A3, p. 29]** = Aula 3, página 29 do PDF. A lista dos arquivos está no fim do documento.
> Os números saem de `ml/reports/`, `evidencias/` e `firmware/main/generated/`. Não arredonde de cabeça: os valores exatos estão aqui.

## Números que todo integrante precisa saber de cor

| Item | Valor |
|---|---|
| Classes | 6: WALKING, WALKING_UPSTAIRS, WALKING_DOWNSTAIRS, SITTING, STANDING, LAYING |
| Entrada do sensor | 6 canais: aceleração total x/y/z (g) + giroscópio x/y/z (rad/s) |
| Janela | 128 amostras a 50 Hz = 2,56 s; passo de 64 = 1,28 s (overlap 50%) |
| Features | 36 = 6 canais × (média, desvio, RMS, mín., máx., energia) |
| Modelo | MLP 36 → 32 ReLU → 16 ReLU → 6 Softmax = **1.814 parâmetros** |
| Tamanhos | TFLite FP32 **9.072 B** → INT8 **4.240 B** (−53,26%) |
| Qualidade (teste oficial, 2.947 janelas) | FP32 81,27% / F1 0,8082 → INT8 **81,13% / F1 0,8070** (−0,14 p.p.) |
| Memória no device | arena reservada 32 KB, **usada 860 B** |
| Latência no Wokwi | `invoke_us ≈ 3.100` (simulada, não é benchmark) |
| REPLAY | `passed=6 total=6 status=PASS` (equivalência com o desktop; 3/6 acertam o rótulo) |

---

## 1. Visão geral e motivação

**1.1 Por que usar IA e não regras com limiar?**
Seis atividades dependem de padrões combinados em seis canais: postura (direção da gravidade) e movimento (variação e energia). Um limiar isolado separa “parado × em movimento”, mas não distingue subir de descer escada nem sentado de em pé. O modelo aprende essas fronteiras dos dados.

**1.2 Por que TinyML e não mandar os dados para a nuvem?**
Processar no dispositivo reduz latência, preserva privacidade, funciona sem conexão e gasta menos energia, porque transmitir pelo rádio custa mais que inferir **[A1, p. 7–8]**. Um modelo de 4,2 KB cabe com folga no ESP32-S3 (512 KB de SRAM, 8 MB de flash no Wokwi) **[A2, p. 12]**.

**1.3 Quais são as quatro etapas exigidas e onde está cada uma?**
- Coleta: `mpu6050.c`, leitura por I2C a 50 Hz.
- Treino: `ml/src/train.py`.
- Conversão e compressão: `ml/src/convert.py`, PTQ INT8.
- Pipeline no device: `inference.cpp` + `app_main.cpp`, modos REPLAY e LIVE.

Esse é o ciclo “do dado ao dispositivo” **[A3, p. 9–11]**.

---

## 2. Dados (UCI HAR)

**2.1 Por que o UCI HAR e não um dataset próprio?**
O PDF do projeto aceita dataset público e cita o UCI HAR como exemplo. O UCI tem 30 voluntários com rótulos confiáveis, coisa que não conseguiríamos coletar no prazo com boa diversidade **[A6, p. 18]**. O dataset próprio é o trabalho futuro para medir a accuracy real com o MPU6050.

**2.2 Por que `total_acc` e não `body_acc`?**
O MPU6050 mede a aceleração **total**, com a gravidade incluída. O `body_acc` do UCI tem a gravidade removida por um filtro que o firmware não reproduz. Usar `total_acc` mantém o sinal do treino igual ao que o sensor entrega. Além disso, a gravidade é justamente o que distingue LAYING das outras posturas.

**2.3 Por que separar treino e teste por voluntário e não por janela?**
Janelas da mesma pessoa são muito parecidas. Misturá-las entre treino e teste inflaria a accuracy, porque o modelo “reconheceria a pessoa”. Usamos o teste oficial (9 voluntários) e uma validação de 5 voluntários separados do treino. O código verifica isso com um `assert`.

**2.4 O que significa janela 128 e passo 64?**
A cada 64 amostras novas (1,28 s), o modelo olha as últimas 128 (2,56 s). O overlap de 50% evita perder um movimento que caia na fronteira entre duas janelas **[A6, p. 24]**. É a mesma segmentação do UCI.

**2.5 Por que 50 Hz?**
É a taxa do UCI HAR. Os movimentos humanos ficam abaixo de cerca de 20 Hz, e pelo critério de Nyquist 50 Hz basta (≥ 2 × 20) **[A6, p. 6]**. O filtro passa-baixa do MPU6050 em ~20 Hz evita aliasing **[A6, p. 23]**.

*Se aprofundar:* o filtro do MPU6050 não é idêntico ao filtro do smartphone usado no UCI. É uma das fontes de domain shift (ver 6.4).

---

## 3. Treinamento

**3.1 Por que 36 features e não a rede no sinal bruto (128×6)?**
É um trade-off consciente:
- Ganho: com features, o modelo é minúsculo (1.814 parâmetros) e só usa 2 operadores (`FULLY_CONNECTED`, `SOFTMAX`).
- Ganho: o mesmo código C de features roda no PC e no ESP32, o que torna a paridade verificável.
- Custo: as estatísticas perdem a ordem temporal e a frequência. É por isso que as três caminhadas se confundem.

**3.2 Como se calcula o número de parâmetros?**
Numa camada Dense: `entradas × neurônios + neurônios` (bias) **[A3, p. 7]**. Fica 36×32+32 = 1.184, mais 32×16+16 = 528, mais 16×6+6 = 102, total **1.814**, conferido pelo `model.summary()` **[A3, p. 18]**.

**3.3 Por que ReLU nas camadas ocultas e Softmax na saída?**
A ReLU dá não linearidade com custo quase zero **[A3, p. 5]**. A Softmax transforma as 6 saídas numa distribuição que soma 1, adequada para classificação multiclasse.

**3.4 Como foi escolhida a quantidade de épocas?**
Por early stopping na **validação** (paciência 20): o treino rodou 33 épocas e restaurou os pesos da melhor, a 13. O conjunto de teste não foi usado para nenhuma escolha.

**3.5 Por que normalizar com Z-score? Onde ficam a média e o desvio?**
O Z-score `(x − μ)/σ` põe as 36 features na mesma escala **[A6, p. 22]**. μ e σ são calculados **só no treino** e gravados como constantes em `model_params.h`. Recalcular no device mudaria a distribuição da entrada.

**3.6 Por que a accuracy é 81% e não 95% como em alguns artigos?**
Esses artigos usam as 561 features prontas do UCI ou redes no sinal bruto. Nós limitamos a entrada a 36 features que o MCU calcula sozinho a partir do sensor. Os erros se concentram em WALKING × UPSTAIRS (152 erros) e SITTING × STANDING (146), classes que diferem por ritmo e detalhe temporal que as estatísticas não capturam.

---

## 4. Conversão e compressão

**4.1 O que é a quantização que vocês fizeram?**
Trocar pesos e ativações de float32 (4 bytes) por int8 (1 byte) **[A3, p. 24]**. Cada valor real vira `q = round(x / scale) + zero_point`, saturado em [−128, 127] **[A3, p. 26–27]**. Foi feita depois do treino, então é **PTQ** (*post-training quantization*) **[A3, p. 29]**, com o conversor do TFLite **[A3, p. 30]**.

**4.2 O que são `scale` e `zero_point`? Quais os valores do modelo?**
`scale` é o tamanho de um “degrau” inteiro em unidades reais, e `zero_point` é o inteiro que representa o zero real. Na entrada: `scale = 0,0585`, `zero_point = −19`. Na saída: `scale = 1/256`, `zero_point = −128`. Por isso a confiança máxima possível é 255/256 = **0,996094**.

**4.3 Para que serve o `representative_dataset`?**
Na quantização full-integer, o conversor precisa saber a faixa real de cada ativação para escolher `scale`/`zero_point`. Passamos 512 janelas **só do treino**: calibrar com o teste seria vazamento de dados.

**4.4 Por que o modelo diminuiu 53% e não 75% (4×)?**
Os 4× valem para os **pesos** **[A3, p. 17]**. O arquivo `.tflite` tem também estrutura do FlatBuffer, metadados e bias em int32, que não encolhem. Em modelos pequenos, essa parte fixa pesa proporcionalmente mais.

**4.5 Por que comparar com o TFLite FP32 (9.072 B) e não com o `.keras` (42.119 B)?**
O `.keras` inclui estado do otimizador e metadados de treino. Compará-lo com o INT8 exageraria o ganho. A comparação justa é FlatBuffer contra FlatBuffer.

**4.6 Por que não usaram pruning nem destilação?**
A ordem de ataque da UC é quantizar primeiro e aplicar pruning e destilação só se o modelo ainda não couber **[A3, p. 21; A4, p. 24]**. Com 4,2 KB de modelo e 860 B de arena, não havia pressão de memória. Pruning **[A3, p. 31–35]** e destilação **[A3, p. 38–39]** ficam como trabalho futuro.

**4.7 A quantização piorou o modelo?**
Quase nada: −0,14 ponto percentual de accuracy (81,27% → 81,13%) e F1 de 0,8082 → 0,8070, nas mesmas 2.947 janelas. É o trade-off tamanho × acurácia que a Aula 3 pede para documentar.

---

## 5. Firmware e deploy

**5.1 Como o modelo entra no ESP32?**
O `.tflite` (FlatBuffer **[A4, p. 7]**) é convertido em array C, o mesmo papel do `xxd -i` da aula **[A4, p. 36–37]**, e gravado em `model_data.cc`. Ele vai para a **Flash** junto com o firmware. As ativações ficam na **SRAM** **[A3, p. 19]**.

**5.2 O que é a tensor arena e por que só 860 B de 32 KB?**
O TFLite Micro não usa alocação dinâmica **[A4, p. 26]**: todos os tensores intermediários vivem num bloco estático reservado no código, a arena. Os maiores tensores de ativação são minúsculos: a entrada de 36 bytes em int8 e a camada de 32 neurônios, com 32 bytes. O pico de RAM é o pior momento, não a soma das camadas **[A3, p. 20]**, então quase toda a arena sobra. Os 32 KB são margem configurável pelo Kconfig.

**5.3 Qual a sequência do TFLite Micro no código?**
`GetModel` → `MicroMutableOpResolver` com os 2 ops → `MicroInterpreter` → `AllocateTensors` → copiar a entrada int8 → `Invoke` → ler a saída int8 e dequantizar. É a mesma estrutura do Hello World da aula **[A4, p. 28–33]**.

**5.4 Por que desligaram o ESP-NN?**
O ESP-NN usa instruções otimizadas do ESP32-S3 que o Wokwi não reproduz fielmente. Com ele, as saídas divergiram do desktop. A própria aula manda desabilitá-lo para o Wokwi **[A4, p. 41]**. Com kernels ANSI C, o REPLAY bateu 6/6.

**5.5 Por que duas tasks e uma fila em vez de um `while(1)`?**
A aquisição precisa de um período exato de 20 ms (50 Hz). Se a inferência rodasse na mesma task, cada `Invoke()` atrasaria a próxima leitura. Com tasks FreeRTOS concorrentes **[A2, p. 59, 62]**, a task de aquisição produz janelas e o loop principal consome pela fila.

**5.6 Por que `vTaskDelayUntil` e não `vTaskDelay`?**
`vTaskDelayUntil` mantém o período absoluto de 20 ms, como um timer **[A1, p. 30–31]**. `vTaskDelay` esperaria 20 ms *depois* de terminar o trabalho, e a taxa real cairia para menos de 50 Hz.

**5.7 Como o firmware sabe que o sensor está ligado certo?**
Lendo o registrador `WHO_AM_I` (`0x75`), que deve responder `0x68`. Se não responder, o init retorna `ESP_ERR_NOT_FOUND`. O exemplo da UC faz a mesma checagem **[A2, p. 81; A6, p. 17]**. O I2C é endereçado e precisa de pull-ups **[A1, p. 40]**.

**5.8 Como os valores brutos do sensor viram g e rad/s?**
O ADC do MPU6050 tem 16 bits **[A1, p. 32; A6, p. 15]**. Com ±2 g há 16.384 contagens por g, e com ±250 °/s há 131 contagens por °/s. O giroscópio ainda é multiplicado por π/180 para chegar a rad/s, a unidade do UCI.

**5.9 O que acontece se uma leitura I2C falhar?**
O firmware registra `ESP_LOGW`, descarta a janela incompleta e continua amostrando. Uma leitura ruim não derruba o dispositivo nem contamina a inferência **[A2, p. 57–58]**.

---

## 6. Validação e limitações

**6.1 O que o `REPLAY ... status=PASS` prova?**
Prova que o firmware calcula **exatamente** o mesmo que o Python nas mesmas 6 janelas reais:
- 36 features com tolerância de 1e-5;
- 36 bytes de entrada INT8 idênticos;
- probabilidades com diferença ≤ 2/256.

Ou seja, o pré-processamento em C não diverge do treino **[A3, p. 10–11]**.

**6.2 Mas só 3 das 6 janelas acertaram. Isso não é ruim?**
Não, porque o PASS mede equivalência, não acerto. O desktop também erra essas 3, e o firmware reproduz os mesmos erros, que é o que queríamos provar. A accuracy oficial (81,13%) vem das 2.947 janelas; 6 janelas não medem qualidade. Elas foram escolhidas antes de qualquer inferência: a primeira de cada classe, sem *cherry-picking*.

**6.3 Por que o modo LIVE parado mostra sempre LAYING com 0,996?**
No Wokwi o MPU6050 entrega valores estáticos, e a gravidade padrão cai num eixo que, no referencial do UCI, corresponde a estar deitado. O 0,996 é o teto da saída INT8 (255/256), não “certeza absoluta”. O LIVE prova que o caminho sensor → janela → inferência funciona, e não mede accuracy.

**6.4 O que é domain shift neste projeto?**
O modelo foi treinado com um smartphone preso à cintura, com orientação, filtros e calibração próprios. O MPU6050 tem outro referencial de eixos, outro filtro e outro ruído. A accuracy de 81% vale para o UCI, não para o MPU6050. A solução correta é coletar dados rotulados com a montagem final e fazer fine-tuning **[A6, p. 18]**.

**6.5 Como garantem que ninguém troca o modelo e esquece as constantes?**
Por três mecanismos:
- O `inference_init` compara `scale`/`zero_point` do modelo com os de `model_params.h` e falha se forem diferentes.
- Os testes automáticos compilam o mesmo `har_features.c` no PC e comparam com golden vectors.
- O CI roda testes e builds em todo PR.

**6.6 A latência de 3,1 ms é real?**
Não: é tempo simulado no Wokwi, com kernels ANSI C (sem ESP-NN). Medir na placa física com ESP-NN ligado é trabalho futuro.

---

## 7. Processo e organização

**7.1 Como foi organizado o repositório e o git flow?**
`main` guarda a versão entregue e `develop` integra as mudanças. Cada contribuição veio de uma `feature/*` com Pull Request revisado. A entrega saiu de uma `release/1.0.0` com a tag `v1.0.0`.

**7.2 Como o código está organizado?**
- `ml/src`: pipeline Python.
- `firmware/components/har_core`: núcleo C portátil, testado no PC.
- `firmware/main`: sensor, inferência e aplicação.
- `generated`: artefatos exportados, nunca editados à mão.
- `tests` e `evidencias`.

O guia de leitura está em [`docs/guia_do_codigo.md`](guia_do_codigo.md).

---

## 8. Trabalho futuro — para fechar a apresentação

| Melhoria | Motivo |
|---|---|
| CNN 1D sobre o sinal bruto | Recuperar ordem temporal e frequência e reduzir as confusões entre caminhadas |
| Dataset próprio com o MPU6050 + fine-tuning | Eliminar o domain shift e medir a accuracy real |
| Pruning / destilação **[A3, p. 31–39]** | Só se um modelo maior deixar de caber |
| Medir latência e energia na placa com ESP-NN | Trocar o número simulado por um real |
| Modo de coleta CSV no firmware | Base para o dataset próprio **[A6, p. 18]** |

---

## Referências ao material de aula

Material da UC *IA Embarcada e Modelos Compactos* (prof. MSc. Rodrigo Kobashikawa Rosa, UniSENAI). A paginação é a do PDF.

| Sigla | Arquivo |
|---|---|
| A1 | `Aula 1-Fundamentos de Microcontroladores e IA Embarcada.pdf` |
| A2 | `Aula 2-C _ MicroPython para Sistemas Embarcados com ESP32.pdf` |
| A3 | `Aula 3 - Treinamento de modelos para IA Embarcada.pdf` |
| A4 | `Aula 4 - Introdução ao Tensorflow Lite.pdf` |
| A6 | `Aula 6 - TinyML para Áudio e Sensores de Vibração.pdf` |

Também citado: o PDF `Descrição do projeto final.pdf` (formato da avaliação: 10 + 5 min, perguntas individuais, organização do código).
