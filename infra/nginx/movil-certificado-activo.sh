#!/bin/sh
# Elige el certificado activo del proxy (DESPLIEGUE-01 v2 §2, ADR-0018 §2) y deja
# /etc/nginx/certs/activo/{fullchain,privkey}.pem apuntando a el.
#
#   CERT_MODO=local        (compose de desarrollo) CA local propia, generada aqui la primera vez y
#                          guardada en el volumen del proxy, fuera del repositorio. El certificado
#                          del servidor se rehace solo si vence en menos de 30 dias.
#   CERT_MODO=letsencrypt  (VPS) el de Let's Encrypt que emite certbot en /etc/letsencrypt. Mientras
#                          no exista, uno provisional autofirmado para que NGINX arranque y certbot
#                          pueda validar por el puerto 80.
#
# Uso: movil-certificado-activo.sh [--recargar]   (--recargar: nginx -s reload si algo cambio)
set -eu

DOMINIO="${DOMINIO:-localhost}"
MODO="${CERT_MODO:-local}"
BASE=/etc/nginx/certs
ACTIVO="$BASE/activo"
umask 077

enlazar() {  # $1 = carpeta con fullchain.pem y privkey.pem
    if [ "$(readlink "$ACTIVO" 2>/dev/null || true)" != "$1" ]; then
        ln -sfn "$1" "$ACTIVO"
        echo "movil: certificado activo -> $1"
        return 0
    fi
    return 1
}

ca_local() {
    D="$BASE/local"
    mkdir -p "$D"
    if [ ! -s "$D/ca.crt" ] || [ ! -s "$D/ca.key" ]; then
        echo "movil: generando la CA local del proxy (fuera del repositorio, volumen proxy-certs)"
        openssl ecparam -name prime256v1 -genkey -noout -out "$D/ca.key"
        openssl req -x509 -new -key "$D/ca.key" -sha256 -days 3650 \
            -subj "/O=Movil Buscador (prototipo)/CN=Movil Buscador CA local de desarrollo" \
            -addext "basicConstraints=critical,CA:TRUE" \
            -addext "keyUsage=critical,keyCertSign,cRLSign" \
            -out "$D/ca.crt"
        rm -f "$D/fullchain.pem" "$D/privkey.pem"
    fi
    if [ ! -s "$D/fullchain.pem" ] || ! openssl x509 -checkend 2592000 -noout -in "$D/servidor.crt" >/dev/null 2>&1; then
        echo "movil: certificado del servidor para $DOMINIO, firmado por la CA local"
        openssl ecparam -name prime256v1 -genkey -noout -out "$D/privkey.pem"
        openssl req -new -key "$D/privkey.pem" -subj "/CN=$DOMINIO" -out "$D/servidor.csr"
        printf 'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:%s,DNS:localhost,IP:127.0.0.1\n' "$DOMINIO" > "$D/servidor.ext"
        openssl x509 -req -in "$D/servidor.csr" -CA "$D/ca.crt" -CAkey "$D/ca.key" -CAcreateserial \
            -days 397 -sha256 -extfile "$D/servidor.ext" -out "$D/servidor.crt"
        cat "$D/servidor.crt" "$D/ca.crt" > "$D/fullchain.pem"
        rm -f "$D/servidor.csr" "$D/servidor.ext"
    fi
    chmod 0644 "$D/ca.crt" "$D/servidor.crt" "$D/fullchain.pem"
    chmod 0600 "$D/ca.key" "$D/privkey.pem"
    enlazar "$D" || true
}

lets_encrypt() {
    LE="/etc/letsencrypt/live/$DOMINIO"
    if [ -s "$LE/fullchain.pem" ] && [ -s "$LE/privkey.pem" ]; then
        enlazar "$LE"
        return $?
    fi
    P="$BASE/provisional"
    mkdir -p "$P"
    if [ ! -s "$P/fullchain.pem" ]; then
        echo "movil: sin certificado de Let's Encrypt para $DOMINIO todavia; uno provisional autofirmado"
        openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes -days 30 \
            -subj "/CN=$DOMINIO" -addext "subjectAltName=DNS:$DOMINIO" \
            -keyout "$P/privkey.pem" -out "$P/fullchain.pem"
    fi
    enlazar "$P"
}

case "$MODO" in
    local)        ca_local; CAMBIO=1 ;;
    letsencrypt)  if lets_encrypt; then CAMBIO=1; else CAMBIO=0; fi ;;
    *)            echo "movil: CERT_MODO desconocido: $MODO (use local o letsencrypt)" >&2; exit 1 ;;
esac

if [ "${1:-}" = "--recargar" ] && [ "$CAMBIO" = 1 ]; then
    nginx -s reload && echo "movil: nginx recargado"
fi
