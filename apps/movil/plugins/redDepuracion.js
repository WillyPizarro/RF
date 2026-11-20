/**
 * Config plugin: network_security_config de Android (CONTRATO-HU-04 v3 §8, opcion B del humano).
 *
 * - main (release y debug): el base-config confia solo en los certificados del sistema y no
 *   permite texto plano. Los certificados del usuario (la CA local de Caddy instalada en el
 *   telefono) solo cuentan dentro de <debug-overrides>, que Android ignora si la app no es
 *   depurable (release).
 * - debug: el mismo archivo mas una excepcion de texto plano SOLO para localhost/127.0.0.1, para
 *   que el dev build cargue el JS desde Metro por `adb reverse tcp:8081 tcp:8081`. Va en el
 *   source set `src/debug`, asi que nunca entra en un build de release.
 *
 * Ningun certificado ni llave va en el repositorio: el telefono confia en la CA porque el humano
 * la instala a mano (pasos en informes/DEV-HU-04.md).
 */
const fs = require('fs');
const path = require('path');
const { withAndroidManifest, withDangerousMod } = require('expo/config-plugins');

const NOMBRE = 'network_security_config';

const BASE = `  <base-config cleartextTrafficPermitted="false">
    <trust-anchors>
      <certificates src="system" />
    </trust-anchors>
  </base-config>
  <debug-overrides>
    <trust-anchors>
      <certificates src="user" />
    </trust-anchors>
  </debug-overrides>`;

const SOLO_DEBUG = `  <!-- Solo en debug: Metro por adb reverse (http://localhost:8081). -->
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="false">localhost</domain>
    <domain includeSubdomains="false">127.0.0.1</domain>
  </domain-config>`;

function xml(cuerpo) {
  return `<?xml version="1.0" encoding="utf-8"?>\n<network-security-config>\n${cuerpo}\n</network-security-config>\n`;
}

function escribir(raiz, conjunto, contenido) {
  const carpeta = path.join(raiz, 'app', 'src', conjunto, 'res', 'xml');
  fs.mkdirSync(carpeta, { recursive: true });
  fs.writeFileSync(path.join(carpeta, `${NOMBRE}.xml`), contenido);
}

module.exports = function redDepuracion(config) {
  config = withAndroidManifest(config, (cfg) => {
    const aplicacion = cfg.modResults.manifest.application?.[0];
    if (aplicacion) {
      aplicacion.$['android:networkSecurityConfig'] = `@xml/${NOMBRE}`;
      // Con networkSecurityConfig, usesCleartextTraffic no aplica; se quita para no confundir.
      delete aplicacion.$['android:usesCleartextTraffic'];
    }
    return cfg;
  });
  return withDangerousMod(config, [
    'android',
    (cfg) => {
      const raiz = cfg.modRequest.platformProjectRoot;
      escribir(raiz, 'main', xml(BASE));
      escribir(raiz, 'debug', xml(`${BASE}\n${SOLO_DEBUG}`));
      return cfg;
    },
  ]);
};
