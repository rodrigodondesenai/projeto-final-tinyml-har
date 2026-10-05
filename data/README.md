# Dados

`raw/`: arquivos oficiais extraídos, não versionados. `processed/`: matrizes de features, índices e seis janelas REPLAY, regeneráveis, não versionados. `provenance.json`: URL, DOI e SHA256 do arquivo efetivamente baixado, versionado.

Origem: Reyes-Ortiz, J.; Anguita, D.; Ghio, A.; Oneto, L.; Parra, X. (2013), *Human Activity Recognition Using Smartphones*, UCI Machine Learning Repository, DOI [10.24432/C54S4K](https://doi.org/10.24432/C54S4K). Artigo: Anguita et al., ESANN 2013, *A Public Domain Dataset for Human Activity Recognition using Smartphones*.

A [página atual da UCI](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones) indica CC BY 4.0. O README histórico distribuído dentro do ZIP traz também texto que proíbe uso comercial. Registramos as duas informações sem alterar os documentos originais. Este projeto é acadêmico; uma licença do código não deve ser presumida como substituta dos termos dos dados.

As seis janelas em `firmware/main/generated/replay_data.h` e em `tests/golden_vectors.json` são derivadas do teste oficial e mantêm esta atribuição. Índices (base zero), pessoas e rótulos estão em `ml/reports/replay_reference.json`.
