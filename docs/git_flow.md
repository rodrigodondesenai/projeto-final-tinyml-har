# Repositório público e Git Flow

O repositório público do projeto é [rodrigodondesenai/projeto-final-tinyml-har](https://github.com/rodrigodondesenai/projeto-final-tinyml-har). `data/raw`, `data/processed`, ambiente virtual, caches e builds são ignorados. Modelos pequenos, parâmetros, golden vectors, relatórios e `firmware/dependencies.lock` devem ser versionados juntos.

O fluxo adotado usa `main` para a versão de entrega e `develop` para integração. As próximas alterações devem ser feitas em `feature/*`; `release/*` prepara uma entrega e `hotfix/*` corrige uma versão publicada. O commit inicial e as branches `main` e `develop` já estão publicados; não foi criada uma sequência artificial de commits para representar trabalho passado.

Para uma nova funcionalidade, após revisão:

```powershell
git status --short
git switch -c feature/validacao-live
```

Ao finalizar a funcionalidade, abra uma Pull Request para `develop`. Antes da entrega, prepare `release/1.0.0` e integre a versão em `main` e `develop`. `git diff --stat` não lista arquivos ainda não rastreados; use também `git status --short`.
