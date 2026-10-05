# Repositório público e Git Flow

O repositório público do projeto é [rodrigodondesenai/projeto-final-tinyml-har](https://github.com/rodrigodondesenai/projeto-final-tinyml-har). `data/raw`, `data/processed`, ambiente virtual, caches e builds são ignorados. Modelos pequenos, parâmetros, golden vectors, relatórios e `firmware/dependencies.lock` devem ser versionados juntos.

Fluxo sugerido: `main` para entregas; `develop` para integração; `feature/*` para funcionalidades; `release/*` para preparação da entrega; `hotfix/*` para correções da versão publicada. Sem commit inicial, branches ainda não têm histórico real. Não se fabricou uma sequência de commits para representar trabalho passado.

Comandos **manuais**, após revisão:

```powershell
git status --short
git add .
git diff --cached --stat
git commit -m "feat: implementa pipeline TinyML HAR e firmware"
git switch -c develop
git switch -c feature/validacao-live
```

Ao finalizar a funcionalidade, abra PR para `develop`; prepare `release/1.0.0` e integre a entrega em `main` e `develop`. Configure o remoto e envie branches somente quando decidir publicar. `git diff --stat` não lista arquivos ainda não rastreados; use também `git status --short`.
