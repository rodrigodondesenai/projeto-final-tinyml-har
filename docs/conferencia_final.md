# Conferência final antes da entrega

Data da conferência: 05/10/2026. Esta revisão separa o que foi exigido pelo
PDF do que foi detalhado no texto inicial do projeto. O PDF pede um protótipo
funcional de IA embarcada e permite Wokwi como alternativa ao kit físico. A
lista detalhada de requisitos está no texto inicial fornecido pelo aluno.

## Resultado

O protótipo está tecnicamente pronto para apresentação. Todos os requisitos
técnicos detalhados foram atendidos com dados, treinamento, conversão INT8,
firmware ESP-IDF, deploy simulado, REPLAY, LIVE, testes e documentação.

O repositório está público no GitHub, com o commit inicial e as branches
`main` e `develop` publicados. O fluxo de trabalho para as próximas alterações
está documentado em `docs/git_flow.md`.

## Verificação executada nesta conferência

| Verificação | Resultado |
|---|---|
| `python -m pytest -q --basetemp tests/.build/conferencia-final` | **21 passed em 3,45 s** |
| `python -m pip check` | Nenhuma dependência quebrada |
| Build ESP-IDF REPLAY | Concluído; binário 0x41c80 bytes, 82% livres na partição |
| Build ESP-IDF LIVE | Concluído; binário 0x41a50 bytes, 82% livres na partição |
| Configuração REPLAY | ESP32-S3, modo REPLAY e ANSI C |
| Configuração LIVE | ESP32-S3, modo LIVE e ANSI C |
| Modelo/relatórios/evidências | Hashes e métricas conferidos pela auditoria |
| `git diff --check` | Sem erros de whitespace |
| Wokwi padrão | Devolvido ao build REPLAY determinístico |

## Checklist do professor

| Requisito informado | Resultado | Evidência |
|---|---|---|
| Dados coerentes com sensores | Atendido | UCI HAR oficial, aceleração total em g e giroscópio em rad/s; `data/provenance.json` |
| Treinamento/fine-tuning | Atendido | MLP treinada, 33 épocas, melhor época 13; `ml/reports/training.json` |
| Conversão e compressão | Atendido | TFLite FP32: 9.072 bytes; INT8: 4.240 bytes; redução 53,26% |
| Avaliação | Atendido | Teste oficial com 2.947 janelas; accuracy, macro F1 e matrizes por modelo |
| Deploy real ou simulado | Atendido | Wokwi com ESP32-S3 + MPU6050 |
| Pipeline de entrada à inferência | Atendido | REPLAY e LIVE executados no Wokwi |
| Problema que exige IA | Atendido | Classificação de seis atividades a partir de seis canais inerciais; justificativa no README |
| Código organizado/legível | Atendido | Separação ML, núcleo C, driver, inferência, firmware, scripts e testes |
| GitHub público e Git Flow | Parcialmente atendido | Repositório público, branches `main` e `develop`, `.gitignore`, CI e guia Git Flow. Ainda faltam commits reais de Gabriel e Renan. |
| Publicação | Concluída com autorização do aluno | Commits e push realizados após a revisão dos arquivos |

## Métricas finais

| Artefato | Tamanho | Accuracy | Macro F1 |
|---|---:|---:|---:|
| Keras FP32 | 42.119 bytes | 81,27% | 0,8082 |
| TFLite FP32 | 9.072 bytes | 81,27% | 0,8082 |
| TFLite INT8 | 4.240 bytes | 81,13% | 0,8070 |

A quantização reduziu o FlatBuffer em 53,26% e reduziu a accuracy em 0,135731
ponto percentual. A matriz de confusão e métricas por classe estão em
`ml/reports/results.md` e `ml/reports/metrics.json`.

## Evidência embarcada

- **REPLAY:** seis janelas reais UCI HAR, pipeline completa e probabilidades
  idênticas à referência desktop: `passed=6 total=6 status=PASS`.
  Consulte `evidencias/replay-serial.txt` e `evidencias/wokwi-replay-pass.png`.
- **LIVE:** MPU6050 simulado por I2C, primeira janela em 2,56 s e inferência
  contínua a cada 1,28 s. O sensor parado gerou `LAYING` com confiança 0,996094;
  isso valida o funcionamento, não a accuracy de atividade humana. Consulte
  `evidencias/live-wokwi.txt`.

## Limites que devem ser apresentados com transparência

O UCI HAR foi capturado com smartphone fixo à cintura e já possui filtros e
segmentação. O MPU6050 não reproduz automaticamente posição, orientação,
calibração ou filtros do smartphone. Logo, a accuracy de 81,13% é válida para
o teste oficial UCI HAR, não para pessoas medidas pelo MPU6050 físico. A
próxima evolução correta é coletar dados rotulados com a montagem final e
avaliar pessoas independentes.

O Wokwi confirma o funcionamento simulado permitido pelo PDF. Tempos de
`Invoke()` no simulador não são benchmark da placa física. A biblioteca
ESP-NN otimizada divergiu no Wokwi; a configuração ANSI C reproduziu o modelo
desktop e foi mantida para a demonstração.

## Antes de entregar

1. Transformar `docs/guia_apresentacao.md` em slides, exportar o PDF e ensaiar
   até 10 minutos.
2. Gravar o vídeo de demonstração usando o REPLAY no Wokwi.
3. Convidar Gabriel e Renan no GitHub para que façam contribuições reais e
   commits próprios, integrados por Pull Request para `develop`.
4. Enviar o PDF, o vídeo e `entrega/link-repositorio.txt` na plataforma da
   disciplina.
