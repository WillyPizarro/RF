<#
.SYNOPSIS
  Compila el APK de release de Movil Buscador y lo publica en la ruta de descarga del VPS
  (DESPLIEGUE-01 v2 §5 y §6, decision 6; ADR-0017, ADR-0018 §5).

.DESCRIPTION
  En esta maquina (la del proyecto):
    1. flutter build apk --release --dart-define=API_URL=https://<DOMINIO>, firmado con la llave
       que vive FUERA del repositorio (apps/movil/android/key.properties, ignorado por git);
    2. comprueba que el APK NO sea depurable (aapt dump badging, sin application-debuggable) y que
       el applicationId sea pe.prototipo.movilbuscador;
    3. calcula su SHA-256.
  En el VPS, por SSH con la llave dedicada:
    4. lo copia a la carpeta de descargas (DESCARGA_APK_DIR del .env del VPS, montada de solo
       lectura en el proxy) como movil-buscador.apk, sin cortar una descarga en curso (copia a un
       archivo temporal y despues lo renombra);
    5. comprueba alla el mismo SHA-256.
  Al final muestra el SHA-256, para compararlo con el que descargan los probadores.

  NO copia la llave de firma ni la credencial de la descarga: esas no salen de donde estan.
  Se puede correr dos veces seguidas: el segundo APK reemplaza al primero.

.EXAMPLE
  .\scripts\publicar-apk.ps1 -Dominio buscador.ejemplo.pe
  .\scripts\publicar-apk.ps1 -Dominio buscador.ejemplo.pe -Servidor deploy@203.0.113.10 -SinCompilar
#>
param(
    # Subdominio del VPS (el mismo DOMINIO del .env del VPS). Por defecto, MOVIL_DOMINIO.
    [string]$Dominio = $env:MOVIL_DOMINIO,
    # usuario@ip del VPS. Por defecto, la variable de entorno MOVIL_VPS (como desplegar.ps1).
    [string]$Servidor = $env:MOVIL_VPS,
    # Llave SSH dedicada. Por defecto, MOVIL_VPS_LLAVE o ~/.ssh/movil_vps.
    [string]$Llave = $(if ($env:MOVIL_VPS_LLAVE) { $env:MOVIL_VPS_LLAVE } else { Join-Path $HOME '.ssh\movil_vps' }),
    # Carpeta del repositorio en el VPS (para leer DESCARGA_APK_DIR de su infra/.env).
    [string]$Carpeta = '/opt/movil-buscador',
    # Publica el APK ya compilado (apps/movil/build/app/outputs/flutter-apk/app-release.apk).
    [switch]$SinCompilar
)

$ErrorActionPreference = 'Stop'

if (-not $Dominio) { throw 'Falta el dominio: use -Dominio <subdominio> o defina MOVIL_DOMINIO.' }
if ($Dominio -notmatch '^[A-Za-z0-9.-]+$' -or $Dominio -eq 'localhost') { throw "Dominio no valido para el APK de release: $Dominio" }
if (-not $Servidor) { throw 'Falta el servidor: use -Servidor usuario@ip o defina MOVIL_VPS.' }
if (-not (Test-Path $Llave)) { throw "No existe la llave SSH: $Llave" }
if ($Carpeta -notmatch '^/[A-Za-z0-9._/-]+$') { throw "Carpeta no valida: $Carpeta" }

$raiz = Split-Path $PSScriptRoot -Parent
$app = Join-Path $raiz 'apps\movil'
$apk = Join-Path $app 'build\app\outputs\flutter-apk\app-release.apk'

# 1. Compilar
if (-not $SinCompilar) {
    if (-not (Test-Path (Join-Path $app 'android\key.properties'))) {
        throw 'Falta apps/movil/android/key.properties (la llave de firma, fuera del repositorio; ver MANUAL-DESPLIEGUE).'
    }
    Write-Host "== 1. Compilando el APK de release con API_URL=https://$Dominio"
    Push-Location $app
    try {
        & flutter build apk --release "--dart-define=API_URL=https://$Dominio"
        if ($LASTEXITCODE -ne 0) { throw "flutter build fallo (codigo $LASTEXITCODE)." }
    } finally { Pop-Location }
}
if (-not (Test-Path $apk)) { throw "No existe el APK: $apk" }

# 2. No depurable y applicationId correcto
$aapt = Get-ChildItem -Path (Join-Path $(if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { 'C:\Android' }) 'build-tools\*\aapt.exe') -ErrorAction SilentlyContinue |
    Sort-Object FullName | Select-Object -Last 1
if (-not $aapt) { throw 'No se encontro aapt.exe (Android build-tools). Defina ANDROID_HOME.' }
$badging = & $aapt.FullName dump badging $apk
if ($LASTEXITCODE -ne 0) { throw 'aapt dump badging fallo.' }
if ($badging -match 'application-debuggable') { throw 'El APK es depurable: no se publica (DESPLIEGUE-01 §5).' }
if (-not ($badging -match "package: name='pe\.prototipo\.movilbuscador'")) { throw 'El applicationId no es pe.prototipo.movilbuscador.' }
Write-Host '== 2. APK de release, no depurable, pe.prototipo.movilbuscador'

# 3. SHA-256
$sha = (Get-FileHash -Algorithm SHA256 $apk).Hash.ToLower()
Write-Host "== 3. SHA-256 local: $sha"

# 4 y 5. Copiar al VPS y comprobar
$opciones = @('-i', $Llave, '-o', 'IdentitiesOnly=yes')
$remotoTmp = "/tmp/movil-buscador-$sha.apk"
Write-Host "== 4. Copiando a $Servidor"
& scp @opciones $apk "${Servidor}:$remotoTmp"
if ($LASTEXITCODE -ne 0) { throw "scp fallo (codigo $LASTEXITCODE)." }

$remoto = @'
set -euo pipefail
CARPETA="$1"; TMP="$2"; SHA="$3"
cd "$CARPETA"
DIR="$(grep -E '^DESCARGA_APK_DIR=' infra/.env | tail -1 | cut -d= -f2- | tr -d "'\"")"
test -n "$DIR" || { echo "Falta DESCARGA_APK_DIR en $CARPETA/infra/.env"; rm -f "$TMP"; exit 1; }
case "$DIR" in /*) ;; *) DIR="$CARPETA/infra/$DIR" ;; esac
mkdir -p "$DIR"
test "$(sha256sum "$TMP" | cut -d' ' -f1)" = "$SHA" || { echo "El SHA-256 no coincide tras la copia"; rm -f "$TMP"; exit 1; }
install -m 0644 "$TMP" "$DIR/.movil-buscador.apk.nuevo"
mv -f "$DIR/.movil-buscador.apk.nuevo" "$DIR/movil-buscador.apk"
rm -f "$TMP"
echo "SHA-256 en el VPS: $(sha256sum "$DIR/movil-buscador.apk" | cut -d' ' -f1)  ($DIR/movil-buscador.apk)"
'@ -replace "`r`n", "`n"
$remoto | & ssh @opciones $Servidor "bash -s -- '$Carpeta' '$remotoTmp' '$sha'"
if ($LASTEXITCODE -ne 0) { throw "La publicacion en el VPS fallo (codigo $LASTEXITCODE)." }

Write-Host ''
Write-Host "APK publicado en https://$Dominio/descargas/movil-buscador.apk"
Write-Host "SHA-256: $sha"
Write-Host 'La credencial de la descarga se reparte por otro canal (nunca junto con el enlace).'
