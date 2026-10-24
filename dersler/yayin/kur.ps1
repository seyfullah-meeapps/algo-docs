$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$toolsPath = Join-Path $repoRoot '.tools'
$zipPath = Join-Path $toolsPath 'quarto-1.10.18-win.zip'
$installPath = Join-Path $toolsPath 'quarto-1.10.18'
New-Item -ItemType Directory -Force $toolsPath | Out-Null
if (Test-Path -LiteralPath (Join-Path $installPath 'bin/quarto.exe')) {
    Write-Host 'Quarto zaten proje klasorunde kurulu.'
    exit 0
}
Invoke-WebRequest -Uri 'https://github.com/quarto-dev/quarto-cli/releases/download/v1.10.18/quarto-1.10.18-win.zip' -OutFile $zipPath
$packageHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash
if ($packageHash -ne '4e824652ff0da3f646868277582ed59c0872d1456e35350b7d7cdc4243ee18c2') {
    throw 'SHA-256 uyusmuyor. Paket acilmadi.'
}
Expand-Archive -LiteralPath $zipPath -DestinationPath $installPath -Force
Write-Host 'Quarto proje klasorune kuruldu. Sistem PATH ayari degistirilmedi.'
