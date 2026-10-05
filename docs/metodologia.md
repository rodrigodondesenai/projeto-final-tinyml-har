# Metodologia e reprodutibilidade

## Origem dos requisitos

O texto anexado pelo usuário define o projeto HAR, classes, hardware, modos, documentação, testes e proibição de commits/push. O PDF chamado “Descrição do projeto final.pdf” contém apresentação da UC, ementa, cronograma, avaliação e proposta geral de protótipo funcional; não contém a rubrica detalhada listada no texto. O conteúdo do PDF é referência acadêmica, não autorização para ações externas. Apresentação planejada em até 10 minutos, conforme solicitação do usuário.

## Dados e divisão

Fonte exclusiva: [UCI HAR](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones), DOI 10.24432/C54S4K. Download e SHA256 em `data/provenance.json`. O script valida CRC e bloqueia caminhos que escapem do diretório na extração. Preserva os arquivos originais em `data/raw`, ignorado pelo Git.

Há 7.352 janelas de treino oficial e 2.947 de teste. O split oficial separa voluntários. Dentro do treino, `GroupShuffleSplit(test_size=0.2, random_state=42)` gera 5.551 janelas de ajuste e 1.801 de validação, sem interseção de voluntários. Os IDs estão em `ml/reports/data_split.json`. Não se faz split aleatório por janela: janelas sobrepostas vazariam informação.

Scaler ajustado somente nas 5.551 janelas de ajuste. Early stopping usa somente validação interna. Calibração INT8: 512 janelas do ajuste, sem validação/teste. O teste oficial é reservado para mensuração final e demonstração REPLAY, sem seleção de hiperparâmetros. Não há refit no treino completo após seleção.

## Features

Para cada canal, nesta ordem: média, desvio padrão populacional (ddof=0), RMS, mínimo, máximo e energia média `sum(x²)/128`. São 36 valores, agrupados por canal, e não por estatística. O desvio usa duas passagens: média e depois soma dos desvios quadráticos. Python e C acumulam amostra por amostra em float32.

Energia e RMS são redundantes (`energia = RMS²`), mas mantidos para estabelecer a baseline solicitada. Uma futura ablação feita apenas com validação pode comparar 30 features sem energia, magnitudes, correlações ou conteúdo espectral. Não se alegou que 36 features sejam ótimas.

Normalização: `(feature - média_treino)/desvio_treino`; se desvio <1e-6, usar 1. Os parâmetros finais são armazenados em float32 e exportados para C. Não normalizamos cada janela isoladamente nem usamos a normalização das 561 features do UCI. Não removemos gravidade nem adicionamos filtros aos sinais já processados do dataset.

## Modelo e compressão

MLP 36→32 ReLU→16 ReLU→6 Softmax, 1.814 parâmetros, Adam 0,001, batch 64, seed 42. Até 150 épocas, patience 20 pelo `val_loss`, restaurando melhores pesos. TensorFlow CPU com uma thread intra/inter-op e operações determinísticas no treinamento; versões fixadas e ambiente congelado. Portabilidade bit a bit entre plataformas não é garantida; golden vectors usam tolerância explícita.

Keras FP32 é salvo com scaler. A conversão congela variáveis como constantes e produz um FlatBuffer FP32 e outro com operações inteiras, entrada/saída INT8. O caminho de congelamento usado evita problemas de variáveis na combinação Keras 3/TF 2.16, mas usa uma API interna; versões são fixadas e a conversão é verificada. Não se editam `managed_components` nem bibliotecas para forçar compatibilidade.

Quantização pós-treino com dados representativos somente do ajuste. O exportador verifica dtypes e operadores. Redução do tamanho é comparada entre FlatBuffers, não entre `.keras` e `.tflite`, cujos contêineres diferem.

## Avaliação e limites

Accuracy, macro F1, relatório por classe e matriz de confusão para Keras FP32, TFLite FP32 e INT8. As linhas da matriz são verdadeiros; as colunas, previstos. As classes são WALKING, WALKING_UPSTAIRS, WALKING_DOWNSTAIRS, SITTING, STANDING, LAYING, nessa ordem; rótulos originais 1–6 são convertidos para 0–5.

Os resultados completos estão em `ml/reports/metrics.json`. Queda FP32→INT8 é medida em pontos percentuais; concordância entre previsões e diferença FP32 também são registradas. O dataset contém atividades em condições controladas; postura SITTING/STANDING e movimentos semelhantes podem se confundir. Janelas próximas são correlacionadas; não se apresentam intervalos de confiança ingênuos tratando cada janela como pessoa independente.

Futuras melhorias: validação cruzada por voluntário no treino, ablação de features, baseline árvore rasa e modelo linear, análise de erros e coleta MPU6050. Sempre preservar o teste final para evitar otimização indireta sobre ele. A softmax não oferece detecção confiável de atividades fora das seis classes.

## Repetição

Comandos no README; `scripts/run_pipeline.ps1` executa as etapas em ordem e interrompe em falhas. `ml/reports/training.json` guarda histórico e época escolhida; `conversion.json` guarda hashes, quantização e operadores. `tests/golden_vectors.json` contém seis janelas reais e quatro sintéticas: zero, constante, rampa e ruído com seed. Testes adicionais verificam unidades, sinal, endianess, overlap, reset e arredondamento/saturação INT8.
