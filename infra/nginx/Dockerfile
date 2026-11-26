# Proxy de Movil Buscador (DESPLIEGUE-01 v2 §1 y §2, ADR-0018): la imagen oficial de NGINX, con la
# version estable fijada, mas openssl (la imagen alpine no lo trae) para la CA local, el
# certificado provisional del VPS y el htpasswd de la descarga del APK.
FROM nginx:1.30.8-alpine

RUN apk add --no-cache openssl

# Plantilla de la configuracion: el entrypoint oficial la pasa por envsubst al arrancar
# (DOMINIO y MOVIL_PUERTO_HTTPS_SUFIJO); las variables de NGINX ($host, $uri...) no se tocan.
COPY templates/default.conf.template /etc/nginx/templates/default.conf.template
# Se ejecuta antes de 20-envsubst-on-templates.sh: certificados, htpasswd y el sufijo del puerto.
COPY 18-movil.envsh /docker-entrypoint.d/18-movil.envsh
COPY movil-certificado-activo.sh /usr/local/bin/movil-certificado-activo.sh
# Por si la copia de trabajo quedo con CRLF (git en Windows): se normaliza a LF.
RUN sed -i 's/\r$//' /docker-entrypoint.d/18-movil.envsh /usr/local/bin/movil-certificado-activo.sh \
        /etc/nginx/templates/default.conf.template \
    && chmod 0755 /docker-entrypoint.d/18-movil.envsh /usr/local/bin/movil-certificado-activo.sh \
    && mkdir -p /var/www/certbot /srv/descargas
