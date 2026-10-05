# Evidências

Evidências reais já obtidas: [serial REPLAY](replay-serial.txt) e
[screenshot original enviada pelo usuário](wokwi-replay-pass.png), ambos com
`passed=6 total=6 status=PASS`. A imagem foi copiada sem edição; o SHA256
da origem e da cópia é `27cba34b3a761fff425ad0a18ccbad8cadf088aa3dd47793aab25e4786ad0777`.
A captura precede a correção do pino de alimentação do diagrama; comprova
REPLAY, não aquisição LIVE. A conferência está em `docs/conferencia_requisitos.md`.

O [serial LIVE](live-wokwi.txt) comprova I2C, formação de janela e inferência
contínua no Wokwi. A classe LAYING do sensor parado não é uma medição de
accuracy de atividade humana.

O **vídeo de demonstração** não é versionado (`*.mp4` está no `.gitignore`). O link,
a conferência cena a cena e o roteiro de narração estão em
[`docs/demonstracao.md`](../docs/demonstracao.md).

Salvar aqui resultados reais de execução, sem copiar saídas esperadas como medições:

- Testes Python/C e contratos dos modelos.
- Build REPLAY e LIVE, versão do ESP-IDF, tamanho do binário.
- Serial real de Wokwi/placa com seis linhas REPLAY e resumo.
- Captura do circuito Wokwi e, se disponível, montagem física.
- Medições LIVE e protocolo de coleta própria, se realizados.

Os modelos, métricas completas e históricos estão em `ml/reports/`. O status consolidado está em `docs/validacao.md`. Não incluir tokens do Wokwi, credenciais, caminhos pessoais desnecessários nem o PDF do professor em um repositório público.
