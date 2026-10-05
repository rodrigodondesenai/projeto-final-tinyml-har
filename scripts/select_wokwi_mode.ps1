param([Parameter(Mandatory=$true)][ValidateSet('REPLAY', 'LIVE')][string]$Mode)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$buildFolder = if ($Mode -eq 'LIVE') { 'build-live' } else { 'build' }
foreach ($artifact in @('flasher_args.json', 'tinyml_har.elf')) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot "firmware\$buildFolder\$artifact"))) {
        throw "Build ausente. Execute scripts/build_firmware.ps1 -Mode $Mode primeiro."
    }
}
$config = "[wokwi]`nversion = 1`nfirmware = 'firmware/$buildFolder/flasher_args.json'`nelf = 'firmware/$buildFolder/tinyml_har.elf'`n"
[System.IO.File]::WriteAllText((Join-Path $projectRoot 'wokwi.toml'), $config, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Wokwi configurado para $Mode. Pare a simulacao e execute Wokwi: Start Simulator."
