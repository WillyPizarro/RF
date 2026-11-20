"""Verificación de CONTRATO-HU-04 v3 §8 que no necesita el teléfono (ENCARGO-HU-04, M-3).

    python pruebas/datos/verificar_prebuild_hu04.py

1. Copia `apps/movil` a una carpeta temporal FUERA del repositorio (sin `node_modules`, `android`,
   `ios` ni `.expo`). `node_modules` se enlaza con un junction de Windows (o un symlink), no se
   copia.
2. Genera `android/` en la copia. Por defecto con la **forma c**; con `--intentar-completo`,
   antes prueba las formas a y b:
   a. `npx expo prebuild --platform android --no-install --clean` (límite de 4 min).
   b. La plantilla de Expo (`node_modules/expo/template.tgz`) más TODOS los plugins de la app con
      `compileModsAsync` (límite de 4 min).
   c. La plantilla de Expo más los mods base de Expo y SOLO los plugins locales de la app (los de
      `app.json` que empiezan con `./`, como el del `network_security_config`), con
      `withPlugins` + `compileModsAsync`.
   En este equipo, a y b no terminan: se cuelgan en mods de Expo o de terceros (el prebuild, en
   `withPackageRefactor`; aviso del DEV y comprobado por el TESTER el 2026-11-19, con más de 10 min
   sin avanzar). La forma c ejecuta los mismos mods base que el prebuild y el plugin que escribe el
   §8, así que el XML y el manifiesto son los que se generarían. Lo único que no evalúa son los
   plugins de terceros (`expo-dev-client`, `expo-secure-store`, `expo-camera`), y ninguno de ellos
   declara un `network_security_config`.
3. Comprueba sobre lo generado:
   - `network_security_config`: los certificados del usuario aparecen SOLO dentro de
     `<debug-overrides>`; el `<base-config>` confía solo en los del sistema y no permite texto
     plano; el manifiesto apunta a ese archivo.
   - La variante `release` no es depurable: ni el manifiesto principal ni el bloque `release` del
     `build.gradle` ponen `debuggable` en `true`.
4. En el repositorio: `git ls-files` no muestra ningún `.crt`, `.pem`, `.key` ni `.der`, y
   `.gitignore` los excluye (`git check-ignore`).
5. Borra la copia: primero quita el enlace de `node_modules` (sin tocar el real) y después la
   carpeta.

Sale con código 0 si todo cumple y 1 si algo no; imprime cada comprobación con OK o FALLA.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
APP = RAIZ / "apps" / "movil"
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
EXCLUIR = {"node_modules", "android", "ios", ".expo", "__tests__", ".maestro"}
EXTENSIONES = (".crt", ".pem", ".key", ".der")

resultados: list[tuple[bool, str]] = []


def comprobar(ok: bool, texto: str) -> None:
    resultados.append((ok, texto))
    print(("OK     " if ok else "FALLA  ") + texto)


def enlazar(destino: Path, origen: Path) -> None:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(destino), str(origen)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
    else:
        destino.symlink_to(origen, target_is_directory=True)


def quitar_enlace(enlace: Path) -> None:
    """Quita solo el enlace (junction o symlink), nunca el contenido del destino."""
    if os.name == "nt":
        os.rmdir(enlace)  # en un junction, borra el enlace y deja intacto el destino
    else:
        enlace.unlink()


LIMITE_PREBUILD_S = 240

MODS_JS = r"""
const { getPrebuildConfigAsync } = require('@expo/prebuild-config');
const { compileModsAsync } = require('@expo/config-plugins');
(async () => {
  const raiz = process.cwd();
  const { exp } = await getPrebuildConfigAsync(raiz, { platforms: ['android'] });
  await compileModsAsync(exp, { projectRoot: raiz, platforms: ['android'],
                                assertMissingModProviders: false });
  console.log('MODS_OK');
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""


def matar_arbol(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def prebuild(copia: Path) -> tuple[bool, str]:
    """(terminó bien, salida). False si falla o si no termina en LIMITE_PREBUILD_S."""
    entorno = dict(os.environ, CI="1", EXPO_NO_TELEMETRY="1")
    npx = shutil.which("npx") or "npx"
    proc = subprocess.Popen([npx, "expo", "prebuild", "--platform", "android", "--no-install",
                             "--clean"], cwd=copia, env=entorno, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace")
    try:
        salida, _ = proc.communicate(timeout=LIMITE_PREBUILD_S)
        return proc.returncode == 0, salida
    except subprocess.TimeoutExpired:
        matar_arbol(proc)
        salida, _ = proc.communicate()
        return False, f"(no terminó en {LIMITE_PREBUILD_S} s)\n" + (salida or "")


def preparar_plantilla(copia: Path) -> None:
    android = copia / "android"
    shutil.rmtree(android, ignore_errors=True)
    with tarfile.open(APP / "node_modules" / "expo" / "template.tgz") as tgz:
        for m in tgz.getmembers():
            if m.name.startswith("package/android/") and (m.isfile() or m.isdir()):
                m.name = m.name[len("package/"):]
                tgz.extract(m, copia, filter="data")


def correr_node(copia: Path, js: str, limite: int) -> tuple[bool, str]:
    proc = subprocess.Popen(["node", "-e", js], cwd=copia, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace", env=dict(os.environ, EXPO_NO_TELEMETRY="1"))
    try:
        salida, _ = proc.communicate(timeout=limite)
        return proc.returncode == 0 and "MODS_OK" in salida, salida
    except subprocess.TimeoutExpired:
        matar_arbol(proc)
        salida, _ = proc.communicate()
        return False, f"(no terminó en {limite} s)" + chr(10) + (salida or "")


def generar_por_mods(copia: Path) -> tuple[bool, str]:
    """Forma b: plantilla de Expo + todos los plugins de la app."""
    preparar_plantilla(copia)
    return correr_node(copia, MODS_JS, LIMITE_PREBUILD_S)


MODS_LOCALES_JS = r"""
const { withPlugins, compileModsAsync } = require('@expo/config-plugins');
const { getConfig } = require('@expo/config');
(async () => {
  const raiz = process.cwd();
  const { exp } = getConfig(raiz, { skipSDKVersionRequirement: true });
  const locales = (exp.plugins || []).filter((p) => {
    const nombre = Array.isArray(p) ? p[0] : p;
    return typeof nombre === 'string' && nombre.startsWith('./');
  });
  console.log('plugins locales evaluados: ' + JSON.stringify(locales));
  if (!locales.length) throw new Error('app.json no declara ningún plugin local');
  const base = { name: exp.name, slug: exp.slug, android: exp.android || {}, plugins: [],
                 _internal: { projectRoot: raiz } };
  await compileModsAsync(withPlugins(base, locales),
                         { projectRoot: raiz, platforms: ['android'], assertMissingModProviders: false });
  console.log('MODS_OK');
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""


def generar_por_plugins_locales(copia: Path) -> tuple[bool, str]:
    """Forma c: plantilla de Expo + mods base + solo los plugins locales de la app."""
    preparar_plantilla(copia)
    return correr_node(copia, MODS_LOCALES_JS, 300)


def revisar_generado(android: Path) -> None:
    main = android / "app" / "src" / "main"
    manifiesto = main / "AndroidManifest.xml"
    comprobar(manifiesto.is_file(), "prebuild generó AndroidManifest.xml")
    if not manifiesto.is_file():
        return
    app = ET.parse(manifiesto).getroot().find("application")
    nsc_ref = app.get(f"{ANDROID_NS}networkSecurityConfig") if app is not None else None
    comprobar(nsc_ref == "@xml/network_security_config",
              f"el manifiesto apunta a @xml/network_security_config (vino {nsc_ref!r})")
    comprobar(app is not None and app.get(f"{ANDROID_NS}debuggable") != "true",
              "el manifiesto principal no pone android:debuggable=\"true\"")

    nsc = main / "res" / "xml" / "network_security_config.xml"
    comprobar(nsc.is_file(), "existe res/xml/network_security_config.xml")
    if nsc.is_file():
        raiz = ET.parse(nsc).getroot()
        base = raiz.find("base-config")
        debug = raiz.find("debug-overrides")
        comprobar(base is not None, "hay <base-config>")
        comprobar(debug is not None, "hay <debug-overrides>")
        if base is not None:
            fuentes = [c.get("src") for c in base.iter("certificates")]
            comprobar(fuentes == ["system"],
                      f"<base-config> confía solo en certificados del sistema (vino {fuentes})")
            comprobar(base.get("cleartextTrafficPermitted") != "true",
                      "<base-config> no permite texto plano")
        if debug is not None:
            comprobar("user" in [c.get("src") for c in debug.iter("certificates")],
                      "<debug-overrides> confía en los certificados del usuario")
        fuera = [el for el in raiz if el.tag != "debug-overrides"
                 for c in el.iter("certificates") if c.get("src") == "user"]
        comprobar(not fuera, "los certificados del usuario aparecen SOLO dentro de <debug-overrides>")

    gradle = android / "app" / "build.gradle"
    comprobar(gradle.is_file(), "existe app/build.gradle")
    if gradle.is_file():
        texto = gradle.read_text(encoding="utf-8")
        m = re.search(r"\brelease\s*\{", texto[texto.find("buildTypes"):]) if "buildTypes" in texto else None
        bloque = ""
        if m:
            ini = texto.find("buildTypes") + m.end()
            nivel, i = 1, ini
            while i < len(texto) and nivel:
                nivel += {"{": 1, "}": -1}.get(texto[i], 0)
                i += 1
            bloque = texto[ini:i]
        comprobar(bool(m), "build.gradle tiene un bloque buildTypes { release { … } }")
        comprobar(not re.search(r"debuggable\s*(=\s*)?true", bloque),
                  "la variante release no es depurable (debuggable no es true)")


def revisar_repositorio() -> None:
    r = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True)
    versionados = [f for f in r.stdout.splitlines() if f.lower().endswith(EXTENSIONES)]
    comprobar(not versionados, f"git ls-files: ningún certificado ni llave versionado ({versionados})")
    for ext in EXTENSIONES:
        for ruta in (f"apps/movil/caddy-root{ext}", f"caddy-root{ext}", f"infra/local{ext}"):
            ignorado = subprocess.run(["git", "check-ignore", "-q", ruta], cwd=RAIZ).returncode == 0
            comprobar(ignorado, f".gitignore excluye {ruta}")


def main() -> int:
    # La consola de Windows (cp1252) no puede imprimir los símbolos que muestra Expo.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    temporal = Path(tempfile.mkdtemp(prefix="tester-hu04-prebuild-"))
    assert RAIZ.resolve() not in [temporal.resolve(), *temporal.resolve().parents]
    copia = temporal / "movil"
    enlace = copia / "node_modules"
    try:
        shutil.copytree(APP, copia, ignore=lambda d, nombres: [n for n in nombres if n in EXCLUIR])
        enlazar(enlace, APP / "node_modules")
        ok, salida = False, ""
        if "--intentar-completo" in sys.argv:
            for nombre, forma in (("a (prebuild completo)", prebuild),
                                  ("b (plantilla + todos los plugins)", generar_por_mods)):
                ok, salida = forma(copia)
                print(f"forma {nombre}: {'terminó' if ok else 'no terminó o falló'}")
                if ok:
                    break
                print(salida[-1200:])
        if not ok:
            ok, salida = generar_por_plugins_locales(copia)
            print("forma c (plantilla + mods base + plugins locales): "
                  + ("terminó" if ok else "falló"))
            print(salida[-1500:])
        comprobar(ok, "se generó android/ con los mods de la app")
        if ok:
            revisar_generado(copia / "android")
    finally:
        if enlace.exists() or enlace.is_symlink():
            quitar_enlace(enlace)
        assert (APP / "node_modules").is_dir(), "¡el node_modules real desapareció!"
        shutil.rmtree(temporal, ignore_errors=True)
    revisar_repositorio()
    malas = [t for ok, t in resultados if not ok]
    print(f"\n{len(resultados) - len(malas)} OK, {len(malas)} FALLA")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
