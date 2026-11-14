#!/usr/bin/env python3
"""Informe semanal de nuevas convocatorias (HTML autocontenido), generado desde la línea de comandos.

Uso:
    python scripts/informe_semanal.py                 # últimos 7 días, informes/informe-semanal-AAAA-MM-DD.html
    python scripts/informe_semanal.py --dias 14 --api http://localhost:8000

También está disponible como enlace en el backend: GET /informe-semanal
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.informe_semanal import construir, nuevas_desde  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=7, help="ventana de días hacia atrás (7)")
    ap.add_argument("--api", default="http://localhost:8000", help="URL del backend")
    ap.add_argument("--salida", default=None, help="ruta del HTML (por defecto informes/informe-semanal-AAAA-MM-DD.html)")
    args = ap.parse_args()

    hoy = date.today()
    desde = hoy - timedelta(days=args.dias)
    with urllib.request.urlopen(f"{args.api}/api/convocatorias?estado=ABIERTAS", timeout=30) as r:
        todas = json.load(r)["convocatorias"]
    nuevas = nuevas_desde(todas, desde)

    salida = Path(args.salida) if args.salida else Path(__file__).resolve().parent.parent / "informes" / f"informe-semanal-{hoy.isoformat()}.html"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(construir(nuevas, desde, hoy), encoding="utf-8")
    print(f"{len(nuevas)} convocatorias nuevas → {salida}")


if __name__ == "__main__":
    main()
