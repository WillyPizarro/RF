<#
.SYNOPSIS
  Despliega una rama o un commit de Movil Buscador en el VPS (DESPLIEGUE-01 §6, decision 4).

.DESCRIPTION
  Entra al VPS por SSH con la llave dedicada y, alla:
    1. trae el codigo desde origin (git fetch) y deja la carpeta en esa rama o commit;
    2. construye las imagenes;
    3. aplica las migraciones con el servicio "herramientas" (rol dueño de Supabase);
    4. levanta api, simuladores, proxy (NGINX) y certbot (up -d --build);
    5. la primera vez, pide el certificado de Let's Encrypt con certbot (webroot por el puerto 80)
       y recarga NGINX; despues certbot lo renueva solo (DESPLIEGUE-01 v2 §2);
    6. espera a que https://<DOMINIO>/v1/salud responda 200.
  Con -CargarUsuarios, ademas corre app.cargar_usuarios (pide la credencial de administracion de
  Auth en el VPS si no esta en su .env; no queda guardada).

  No copia ningun secreto: usa el infra/.env que ya esta en el VPS. Se puede correr dos veces
  seguidas: git checkout, las migraciones y la carga de usuarios son idempotentes.

.EXAMPLE
  .\scripts\desplegar.ps1 main
  .\scripts\desplegar.ps1 despliegue-01 -CargarUsuarios
  .\scripts\desplegar.ps1 3367787 -Servidor deploy@203.0.113.10 -Llave $HOME\.ssh\movil_vps
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Referencia,
    # usuario@ip del VPS. Por defecto, la variable de entorno MOVIL_VPS.
    [string]$Servidor = $env:MOVIL_VPS,
    # Llave SSH dedicada. Por defecto, MOVIL_VPS_LLAVE o ~/.ssh/movil_vps.
    [string]$Llave = $(if ($env:MOVIL_VPS_LLAVE) { $env:MOVIL_VPS_LLAVE } else { Join-Path $HOME '.ssh\movil_vps' }),
    # Carpeta del repositorio en el VPS.
    [string]$Carpeta = '/opt/movil-buscador',
    [switch]$CargarUsuarios
)

$ErrorActionPreference = 'Stop'

if (-not $Servidor) { throw 'Falta el servidor: use -Servidor usuario@ip o defina MOVIL_VPS.' }
if (-not (Test-Path $Llave)) { throw "No existe la llave SSH: $Llave" }
if ($Referencia -notmatch '^[A-Za-z0-9._/-]+$') { throw "Referencia no valida: $Referencia" }
if ($Carpeta -notmatch '^/[A-Za-z0-9._/-]+$') { throw "Carpeta no valida: $Carpeta" }

# Script que corre en el VPS (bash). Recibe la referencia, la carpeta y si carga usuarios.
$remoto = @'
set -euo pipefail
REF="$1"; CARPETA="$2"; CARGAR="$3"
cd "$CARPETA"
C="docker compose -f infra/docker-compose.yml -f infra/docker-compose.vps.yml --env-file infra/.env"

test -f infra/.env || { echo "Falta $CARPETA/infra/.env (ver docs/despliegue/MANUAL-DESPLIEGUE.md)"; exit 1; }
DOMINIO="$(grep -E '^DOMINIO=' infra/.env | tail -1 | cut -d= -f2- | tr -d "'\"")"
test -n "$DOMINIO" || { echo "Falta DOMINIO en infra/.env"; exit 1; }

echo "== 1. Codigo: $REF"
git fetch --prune origin
if git rev-parse --verify -q "origin/$REF" >/dev/null; then
  git checkout --force --detach "origin/$REF"
else
  git checkout --force --detach "$REF"
fi
git log --oneline -1

echo "== 2. Imagenes"
$C --profile herramientas build api herramientas simuladores proxy

echo "== 3. Migraciones (rol dueño, servicio herramientas)"
$C --profile herramientas run --rm herramientas python -m app.migrar

if [ "$CARGAR" = "si" ]; then
  echo "== 3b. Usuarios de prueba"
  if grep -qE '^AUTH_ADMIN_CLAVE=.+' infra/.env; then
    $C --profile herramientas run --rm herramientas python -m app.cargar_usuarios
  else
    read -r -s -p "Credencial de administracion de Auth (no se muestra ni se guarda): " AUTH_ADMIN_CLAVE; echo
    export AUTH_ADMIN_CLAVE
    $C --profile herramientas run --rm herramientas python -m app.cargar_usuarios
    unset AUTH_ADMIN_CLAVE
  fi
fi

echo "== 4. Servicios"
$C up -d --build --remove-orphans

echo "== 5. Certificado de Let's Encrypt para $DOMINIO"
for i in $(seq 1 30); do $C exec -T proxy true 2>/dev/null && break; sleep 2; done
if $C exec -T proxy test -s "/etc/letsencrypt/live/$DOMINIO/fullchain.pem"; then
  echo "Ya existe; certbot lo renueva solo (servicio certbot)."
else
  CORREO="$(grep -E '^CERTBOT_EMAIL=' infra/.env | tail -1 | cut -d= -f2- | tr -d "'\"")"
  if [ -n "$CORREO" ]; then OPC_CORREO="--email $CORREO --no-eff-email"; else OPC_CORREO="--register-unsafely-without-email"; fi
  # NGINX ya sirve /.well-known/acme-challenge/ por el puerto 80 con un certificado provisional.
  $C run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot     -d "$DOMINIO" $OPC_CORREO --agree-tos --non-interactive
  $C exec -T proxy /usr/local/bin/movil-certificado-activo.sh --recargar
fi

echo "== 6. Salud: https://$DOMINIO/v1/salud"
for i in $(seq 1 60); do
  codigo="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "https://$DOMINIO/v1/salud" || true)"
  if [ "$codigo" = "200" ]; then
    echo "OK: /v1/salud responde 200"
    $C ps
    exit 0
  fi
  sleep 5
done
echo "ERROR: /v1/salud no respondio 200 en 5 minutos (ultimo codigo: $codigo)"
$C ps
$C logs --tail 50 api proxy
exit 1
'@

$cargar = if ($CargarUsuarios) { 'si' } else { 'no' }
# Bash necesita fin de linea LF.
$remoto = $remoto -replace "`r`n", "`n"

Write-Host "Desplegando '$Referencia' en $Servidor ($Carpeta)..."
# -t solo si hay que pedir la credencial por teclado en el VPS.
$opciones = @('-i', $Llave, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=no')
if ($CargarUsuarios) {
    # Con -t no se puede usar stdin para el script: se envia codificado como argumento.
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($remoto))
    & ssh @opciones -t $Servidor "echo $b64 | base64 -d > /tmp/desplegar_movil.sh && bash /tmp/desplegar_movil.sh '$Referencia' '$Carpeta' '$cargar'; r=`$?; rm -f /tmp/desplegar_movil.sh; exit `$r"
} else {
    $remoto | & ssh @opciones $Servidor "bash -s -- '$Referencia' '$Carpeta' '$cargar'"
}
if ($LASTEXITCODE -ne 0) { throw "El despliegue fallo (codigo $LASTEXITCODE)." }
Write-Host 'Despliegue terminado.'
