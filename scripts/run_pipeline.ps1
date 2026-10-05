param([int]$Epochs = 150, [switch]$SkipDownload)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Crie a .venv e instale requirements-dev.txt conforme README.' }
if (-not $SkipDownload) {
    & $python scripts/download_dataset.py
    if ($LASTEXITCODE -ne 0) { throw 'Download falhou' }
}
foreach ($stage in @('prepare', 'train', 'convert', 'evaluate', 'export')) {
    if ($stage -eq 'train') { & $python -m "ml.src.$stage" --epochs $Epochs }
    else { & $python -m "ml.src.$stage" }
    if ($LASTEXITCODE -ne 0) { throw "Etapa $stage falhou" }
}
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Testes falharam' }
