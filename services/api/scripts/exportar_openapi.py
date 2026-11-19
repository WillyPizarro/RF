"""Imprime el OpenAPI de la API en stdout (ADR-0007).

Uso (desde la raiz del repo):
  docker compose -f infra/docker-compose.yml run --rm --no-deps -T api \
    python scripts/exportar_openapi.py > contratos/api/openapi.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

json.dump(app.openapi(), sys.stdout, ensure_ascii=False, indent=2)
sys.stdout.write("\n")
