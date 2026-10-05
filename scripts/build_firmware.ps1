param(
    [ValidateSet('REPLAY', 'LIVE')][string]$Mode = 'REPLAY',
    [string]$IdfPath = $env:IDF_PATH,
    [string]$ToolsPath = 'C:\Espressif\tools'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $IdfPath) {
    $registry = Join-Path $ToolsPath 'idf-env.json'
    if (-not (Test-Path $registry)) { throw 'Abra o terminal ESP-IDF ou informe -IdfPath e -ToolsPath.' }
    $installed = (Get-Content -Raw $registry | ConvertFrom-Json).idfInstalled.PSObject.Properties
    $IdfPath = ($installed | Select-Object -First 1).Value.path
}
if (-not (Test-Path (Join-Path $IdfPath 'tools\idf.py'))) { throw 'ESP-IDF nao encontrado.' }
# Caminhos curtos do Windows evitam espacos em CMake/Ninja, sem copiar nem mudar o SDK.
$fso = New-Object -ComObject Scripting.FileSystemObject
$shortRoot = $fso.GetFolder($projectRoot).ShortPath
$env:IDF_PATH = $fso.GetFolder($IdfPath).ShortPath
$env:IDF_TOOLS_PATH = $ToolsPath
$romDirectory = Get-ChildItem -LiteralPath (Join-Path $ToolsPath 'esp-rom-elfs') -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if ($romDirectory) { $env:ESP_ROM_ELF_DIR = $romDirectory.FullName }
$env:IDF_TARGET = 'esp32s3'
$env:IDF_CCACHE_ENABLE = '0'
$env:IDF_COMPONENT_CACHE_PATH = Join-Path $shortRoot '.cache\idf-components'
$env:PYTHONUTF8 = '1'
$idfPython = if ($env:IDF_PYTHON_ENV_PATH) {
    Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts\python.exe'
} else {
    (Get-ChildItem -LiteralPath (Join-Path $ToolsPath 'python') -Recurse -Filter python.exe |
        Where-Object { $_.FullName -match 'venv\\Scripts' } | Select-Object -First 1).FullName
}
if (-not $idfPython) { throw 'Python do ESP-IDF ausente. Ative seu ambiente ESP-IDF existente.' }
$env:IDF_PYTHON_ENV_PATH = Split-Path (Split-Path $idfPython -Parent) -Parent
$bins = @((Split-Path $idfPython -Parent))
foreach ($tool in @('cmake', 'ninja', 'xtensa-esp-elf', 'esp32ulp-elf')) {
    $executables = Get-ChildItem -LiteralPath (Join-Path $ToolsPath $tool) -Recurse -Filter '*.exe' -ErrorAction SilentlyContinue
    $bins += $executables | Select-Object -ExpandProperty DirectoryName -Unique
}
$env:PATH = ($bins -join ';') + ';' + $env:PATH
$firmware = Join-Path $shortRoot 'firmware'
$build = if ($Mode -eq 'LIVE') { 'build-live' } else { 'build' }
$config = if ($Mode -eq 'LIVE') { 'sdkconfig.live' } else { 'sdkconfig' }
$defaults = if ($Mode -eq 'LIVE') { 'sdkconfig.defaults;sdkconfig.live.defaults' } else { 'sdkconfig.defaults' }
Push-Location $firmware
try {
    & $idfPython (Join-Path $env:IDF_PATH 'tools\idf.py') -B $build -D "SDKCONFIG=$firmware\$config" -D "SDKCONFIG_DEFAULTS=$defaults" build
    if ($LASTEXITCODE -ne 0) { throw "Build $Mode falhou com codigo $LASTEXITCODE" }
} finally { Pop-Location }
