"""Genera app/datos/semilla.json de forma determinista (HU-08, ADR-0006 §5).

Solo datos sinteticos: placas con el prefijo reservado ZZ y documentos SIM-########.
Uso (desde services/simuladores): python scripts/generar_semilla.py
El archivo generado se versiona; correr el script de nuevo produce el mismo archivo.
"""

import json
import random
import string
from datetime import date, timedelta
from pathlib import Path

SEMILLA_ALEATORIA = 20261119
TOTAL_VEHICULOS = 220
TOTAL_PERSONAS = 24
DESTINO = Path(__file__).resolve().parent.parent / "app" / "datos" / "semilla.json"

MARCAS = {
    "Toyota": ["Yaris", "Corolla", "Hilux", "RAV4"],
    "Hyundai": ["Accent", "Tucson", "Elantra"],
    "Kia": ["Rio", "Sportage", "Picanto"],
    "Nissan": ["Sentra", "Frontier", "Versa"],
    "Chevrolet": ["Sail", "Spark", "Onix"],
    "Suzuki": ["Swift", "Vitara"],
    "Volkswagen": ["Gol", "Amarok"],
    "Honda": ["Wave 110", "CB 190R"],
}
MOTOS = {"Wave 110", "CB 190R"}
CAMIONETAS = {"Hilux", "Frontier", "Amarok"}
SUV = {"RAV4", "Tucson", "Sportage", "Vitara"}
COLORES = ["Blanco", "Negro", "Plata", "Gris", "Rojo", "Azul", "Verde", "Beige"]
MOTIVOS_VEHICULO = [
    "Robo de vehículo (simulado)",
    "Hurto de vehículo (simulado)",
    "Vehículo vinculado a investigación (simulado)",
    "Orden de captura del vehículo (simulada)",
]
MOTIVOS_PERSONA = [
    "Orden de captura por robo agravado (simulada)",
    "Orden de captura por hurto (simulada)",
    "Orden de captura por estafa (simulada)",
    "Orden de captura por lesiones graves (simulada)",
    "Orden de captura por receptación (simulada)",
]
AUTORIDADES = [
    "Juzgado Penal Simulado N.º 1",
    "Juzgado Penal Simulado N.º 2",
    "Juzgado de Investigación Preparatoria Simulado N.º 3",
    "Sala Penal Simulada N.º 4",
]
NOMBRES = [
    "Ana", "Bruno", "Carla", "Diego", "Elena", "Fabio", "Gloria", "Hugo", "Irene", "Jorge",
    "Karina", "Luis", "Marta", "Nicolás", "Olga", "Pablo", "Rosa", "Sergio", "Teresa", "Víctor",
]
APELLIDOS = [
    "Prueba", "Ficticio", "Ejemplo", "Simulado", "Muestra", "Demo", "Ensayo", "Sintético",
]


def _fecha(rng: random.Random) -> str:
    inicio = date(2023, 1, 1)
    return (inicio + timedelta(days=rng.randrange(0, 1000))).isoformat()


def _vehiculos(rng: random.Random) -> list[dict]:
    placas: set[str] = {"ZZA-101", "ZZB-201"}
    letras = string.ascii_uppercase + string.digits
    while len(placas) < TOTAL_VEHICULOS:
        tercera = rng.choice(letras)
        numero = rng.randrange(0, 1000)
        placa = f"ZZ{tercera}-{numero:03d}"
        if placa != "ZZZ-999":
            placas.add(placa)

    vehiculos = []
    contador_req = 0
    for i, placa in enumerate(sorted(placas)):
        marca = rng.choice(sorted(MARCAS))
        modelo = rng.choice(MARCAS[marca])
        if modelo in MOTOS:
            tipo = "Motocicleta"
        elif modelo in CAMIONETAS:
            tipo = "Camioneta"
        elif modelo in SUV:
            tipo = "SUV"
        else:
            tipo = "Automóvil"
        if placa == "ZZA-101":
            con_req = True
        elif placa == "ZZB-201":
            con_req = False
        else:
            con_req = i % 7 == 3
        requisitoria = None
        if con_req:
            contador_req += 1
            requisitoria = {
                "codigo": f"SIM-RQV-{contador_req:04d}",
                "motivo": rng.choice(MOTIVOS_VEHICULO),
                "autoridad": rng.choice(AUTORIDADES),
                "fecha_emision": _fecha(rng),
            }
        vehiculos.append(
            {
                "placa": placa,
                "marca": marca,
                "modelo": modelo,
                "color": rng.choice(COLORES),
                "tipo": tipo,
                "requisitoria_vigente": con_req,
                "requisitoria": requisitoria,
            }
        )
    return vehiculos


def _personas(rng: random.Random) -> list[dict]:
    personas = []
    for n in range(1, TOTAL_PERSONAS + 1):
        personas.append(
            {
                "persona_id": f"SIM-P-{n:04d}",
                "nombres": NOMBRES[(n - 1) % len(NOMBRES)],
                "apellidos": " ".join(rng.sample(APELLIDOS, 2)),
                "documento": f"SIM-{n:08d}",
                "requisitoria": {
                    "codigo": f"SIM-RQP-{n:04d}",
                    "motivo": rng.choice(MOTIVOS_PERSONA),
                    "autoridad": rng.choice(AUTORIDADES),
                    "fecha_emision": _fecha(rng),
                },
            }
        )
    return personas


def main() -> None:
    rng = random.Random(SEMILLA_ALEATORIA)
    semilla = {
        "nota": "Datos 100 % sinteticos generados por scripts/generar_semilla.py. No editar a mano.",
        "vehiculos": _vehiculos(rng),
        "personas": _personas(rng),
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(semilla, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    con_req = sum(v["requisitoria_vigente"] for v in semilla["vehiculos"])
    print(f"{DESTINO}: {len(semilla['vehiculos'])} vehiculos ({con_req} con requisitoria), "
          f"{len(semilla['personas'])} personas")


if __name__ == "__main__":
    main()
