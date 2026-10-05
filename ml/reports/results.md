# Resultados medidos no split oficial

Janelas: 2947. Classes na ordem: WALKING, WALKING_UPSTAIRS, WALKING_DOWNSTAIRS, SITTING, STANDING, LAYING.

| Modelo | Bytes do arquivo | Accuracy | Macro F1 |
|---|---:|---:|---:|
| keras_fp32 | 42119 | 0.8127 | 0.8082 |
| tflite_fp32 | 9072 | 0.8127 | 0.8082 |
| tflite_int8 | 4240 | 0.8113 | 0.8070 |

O arquivo Keras inclui metadados/estado de treinamento; a comparacao de compressao usa os dois FlatBuffers.

Queda FP32 TFLite -> INT8: 0.1357 pontos percentuais.

## Matriz de confusao INT8

Linhas = verdadeiro; colunas = previsto; ordem de classes acima.

```text
 423   52   21    0    0    0
 152  308   10    1    0    0
  82   39  299    0    0    0
   0    2    0  342  146    1
   1    4    0   45  482    0
   0    0    0    0    0  537
```

Metricas do interpretador desktop. Nao equivalem a validacao LIVE ou medicao no ESP32.
