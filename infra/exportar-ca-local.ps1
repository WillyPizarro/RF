<#
.SYNOPSIS
  Copia la CA local del proxy NGINX fuera del repositorio y muestra su huella (DESPLIEGUE-01 v2 §2).

.DESCRIPTION
  El proxy genera la CA local la primera vez que arranca en modo local (volumen proxy-certs). Este
  script la copia desde el contenedor en marcha a una carpeta FUERA del repositorio, para
  instalarla como CA de usuario en el telefono de pruebas (solo la confia el APK de depuracion).
  Muestra la huella SHA-256 del certificado, la que se compara en el telefono (Ajustes > Seguridad
  > Ver certificados de seguridad > Usuario). La llave privada de la CA no sale del volumen.

.EXAMPLE
  .\infra\exportar-ca-local.ps1
  .\infra\exportar-ca-local.ps1 -Destino C:\Willy\Trabajo\MININTER\ca-local-nginx
#>
param(
    # Carpeta de destino, fuera del repositorio.
    [string]$Destino = (Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'ca-local-nginx'),
    [string]$EnvFile = (Join-Path $PSScriptRoot '.env')
)
$ErrorActionPreference = 'Stop'

$raiz = Split-Path $PSScriptRoot -Parent
$destinoCompleto = [IO.Path]::GetFullPath($Destino)
if ($destinoCompleto.StartsWith([IO.Path]::GetFullPath($raiz), [StringComparison]::OrdinalIgnoreCase)) {
    throw "El destino tiene que estar FUERA del repositorio: $destinoCompleto"
}
New-Item -ItemType Directory -Force $destinoCompleto | Out-Null
$archivo = Join-Path $destinoCompleto 'movil-buscador-ca-local.crt'

$compose = @('compose', '-f', (Join-Path $PSScriptRoot 'docker-compose.yml'), '--env-file', $EnvFile)
& docker @compose cp 'proxy:/etc/nginx/certs/local/ca.crt' $archivo
if ($LASTEXITCODE -ne 0) { throw 'No se pudo copiar la CA (el proxy tiene que estar en marcha en modo local).' }

$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $archivo
$huella = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($cert.RawData))).Replace('-', ':')
Write-Host "CA local exportada: $archivo"
Write-Host "Sujeto:   $($cert.Subject)"
Write-Host "Vigencia: $($cert.NotBefore.ToString('yyyy-MM-dd')) a $($cert.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "SHA-256:  $huella"
