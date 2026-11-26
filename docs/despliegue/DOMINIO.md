# Comprar el dominio y apuntarlo al VPS

Lo hace el humano, **después de contratar el VPS** (hace falta su IP pública). Toma unos 15
minutos, más la espera del DNS.

## 1. Elegir y comprar el dominio

1. Elija un registrador de dominios, por ejemplo **Cloudflare Registrar**, **Namecheap** o **Porkbun**. Muchos proveedores de VPS (Hetzner, DigitalOcean, Vultr…) no venden dominios: está bien comprarlo aparte.
2. Busque un nombre **neutro**, que no use marcas ni nombres de instituciones reales. Por ejemplo `movil-prototipo.com` o `prueba-movil.dev`. Un `.com` cuesta unos US$ 10–15 al año.
3. Cómprelo con la **renovación automática desactivada**: el dominio solo se necesita durante el proyecto.
4. Active la **protección de privacidad del WHOIS** si el registrador la ofrece (casi siempre es gratis).

## 2. Elegir el subdominio

La app usa un **subdominio**, por ejemplo `api.movil-prototipo.com`. A esto el resto de los
documentos lo llama `<DOMINIO>`.

## 3. Crear el registro DNS `A`

1. Entre al panel del registrador (o de Cloudflare, si el DNS está ahí) y abra la sección **DNS** del dominio.
2. Agregue un registro nuevo:

   | Campo | Valor |
   |---|---|
   | Tipo | `A` |
   | Nombre (host) | `api` (la parte de la izquierda del subdominio) |
   | Valor (IPv4) | la IP pública del VPS |
   | TTL | automático, o 300 segundos |
   | Proxy (solo en Cloudflare) | **Desactivado** ("Solo DNS", la nube gris) |

3. Guarde. **No** cree un registro `AAAA` (IPv6), salvo que el VPS tenga IPv6 y el firewall la permita.

El proxy de Cloudflare tiene que estar **apagado**: `certbot`, en el VPS, pide el certificado
directamente a Let's Encrypt, y Let's Encrypt necesita llegar al puerto 80 del VPS para validarlo.

## 4. Comprobar

Espere unos minutos y, en la PC, abra PowerShell:

```
Resolve-DnsName api.movil-prototipo.com
```

Tiene que mostrar la IP del VPS. Si no aparece, espere un poco más (puede tardar hasta una hora).

Después, en el `.env` del VPS va `DOMINIO=api.movil-prototipo.com` (ver `MANUAL-DESPLIEGUE.md`).

## 5. Al cierre del proyecto

1. Borre el registro `A` del subdominio.
2. Deje vencer el dominio (con la renovación automática desactivada) o elimínelo desde el registrador.

Ambos pasos van en el acta de eliminación (`docs/contratos/PENDIENTES.md`).
