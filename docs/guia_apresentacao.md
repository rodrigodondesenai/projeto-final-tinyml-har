# Apresentação: até 10 minutos

| Tempo | Conteúdo | Evidência |
|---|---|---|
| 0:00–1:00 | Problema: reconhecer seis atividades localmente; por que aprender padrões | README e classes |
| 1:00–2:15 | UCI HAR, cintura, 50 Hz, g/rad/s e separação por pessoa | data_split.json |
| 2:15–3:30 | Janela 128/64, 36 features, scaler sem leakage | arquitetura e uma fórmula |
| 3:30–4:30 | MLP 36→32→16→6, 1.814 parâmetros, early stopping | training.json |
| 4:30–5:45 | Comparação FP32/INT8 e matriz de confusão | results.md |
| 5:45–7:30 | Demonstração REPLAY no Wokwi ou placa; ler classe/confiança e PASS/FAIL | serial real salvo |
| 7:30–8:30 | LIVE, ligação MPU6050, aquisição e diferença de domínio | diagram.json |
| 8:30–9:30 | Testes de equivalência, limitações e melhoria com coleta própria | testes e arquitetura |
| 9:30–10:00 | Fechamento e margem para imprevistos | status real da entrega |

Antes da apresentação: ensaie a execução REPLAY ANSI C. Já existem serial real
em `evidencias/replay-serial.txt` e captura em `evidencias/wokwi-replay-pass.png`
para usar como backup. Mostre o resultado 6/6 PASS como equivalência numérica,
separado da accuracy de 81,13% no teste completo. O checklist da entrega está
em `docs/conferencia_final.md`; LIVE já possui evidência funcional em
`evidencias/live-wokwi.txt`.

## Perguntas prováveis

**Por que IA e não if/else?** As classes compartilham amplitudes e posturas; combinamos estatísticas de seis eixos para aprender relações a partir de exemplos. Não provamos que todo método de regras seria inferior; uma baseline simples seria uma comparação útil.

**O MPU6050 mede os mesmos sinais do UCI?** Mede grandezas compatíveis após converter unidades, mas não reproduz o smartphone, orientação, fixação e filtros. A aceleração usada é total, com gravidade. LIVE exige avaliação com coleta própria.

**Por que não usar body_acc?** O sensor não entrega aceleração com gravidade removida. Replicar essa separação exigiria uma cadeia de filtros e estados coerente. `total_acc` evita essa suposição.

**O REPLAY é só uma lista de respostas prontas?** Não. Reproduz 128×6 amostras reais, calcula features e scaler, quantiza e executa TFLM. As respostas desktop são usadas somente na comparação.

**PASS significa 100% de accuracy?** Não. Significa que o embarcado concorda numericamente com o desktop nessas janelas. Um erro de classificação pode ter parity PASS.

**Como evitou data leakage?** Teste oficial por pessoa, validação interna por pessoa, scaler e calibração apenas no ajuste. Não escolhi exemplos por acerto nem fiz ajustes após ver o teste.

**Como funciona a quantização?** Mapeia números reais para inteiros com escala e zero point. Pesos e ativações INT8, bias/acumuladores INT32. Na saída recuperamos uma aproximação da softmax.

**Qual foi a perda?** Consultar `results.md`: FP32 TFLite 81,27% e INT8 81,13%, aproximadamente 0,136 ponto percentual, com redução do FlatBuffer de 9.072 para 4.240 bytes.

**Toda pipeline usa INT8?** Não. Aquisição convertida, features e normalização usam float32. A rede TFLM tem entrada/saída e pesos INT8.

**Por que RMS e energia?** É uma baseline compacta conforme proposta; há redundância matemática. Remover energia e comparar na validação é uma ablação futura.

**Quanto usa de RAM e quanto demora?** O firmware reserva arena de 32 KiB e imprime o uso real. `invoke_us` só mede a rede. Não substituir medição em hardware por tamanho de arquivo ou tempo de simulação.

**Por que a accuracy não passou de 95%?** Usamos 36 estatísticas simples, rede pequena e avaliação em pessoas não vistas. Trabalhos com 561 features ou modelos diferentes não são comparações diretas. Apresentamos a baseline medida sem inflar o resultado.

**Que melhoria priorizaria?** Dados rotulados do MPU6050 com posição e filtros definidos, validação por pessoa, baselines e ablação no treino. Isso trata a diferença de domínio antes de aumentar a rede.
