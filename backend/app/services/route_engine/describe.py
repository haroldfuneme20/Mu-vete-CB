"""Descripción textual de cada alternativa en español sencillo (T049, FR-012)."""

from __future__ import annotations

MODE_LABEL = {
    "troncal": "TransMilenio",
    "provisional": "la ruta provisional",
    "zonal": "el SITP zonal",
    "alimentador": "el alimentador",
    "transmicable": "el TransMiCable",
    "community": "la ruta comunitaria",
    "walk": "a pie",
}


def money(v: int | float) -> str:
    return "$" + f"{int(round(v)):,}".replace(",", ".")


def minutes(seconds: float) -> int:
    return max(1, int(round(seconds / 60))) if seconds > 0 else 0


def pct(x: float) -> str:
    return f"{int(round(x * 100))}%"


def describe(alt: dict) -> str:
    parts = []
    for leg in alt["legs"]:
        if leg["mode"] == "walk":
            if leg["duration_min"] > 0:
                parts.append(f"Camina {leg['duration_min']} min hasta {leg['to_stop']}.")
            continue
        n_stops = max(1, len(leg["stops"]) - 1)
        name = leg["route_name"]
        label = MODE_LABEL.get(leg["mode"], leg["mode"])
        core = label.split()[-1].lower()
        service = f"el {name}" if core in name.lower() and leg["mode"] == "transmicable" else (
            f"{label} «{name}»")
        sim = " (simulada para la demo)" if leg["source_kind"] == "demo_simulated" else ""
        parts.append(
            f"Toma {service}{sim} en {leg['from_stop']} hasta {leg['to_stop']} "
            f"({n_stops} paradas, {leg['duration_min']} min)."
        )
        for r in leg["reports"]:
            parts.append(
                f"Atención: {r['n_confirm']} reporte(s) de {r['label']} en este tramo."
            )
    parts.append(
        f"En total {alt['total_time_min']} min, {money(alt['cost'])}, "
        f"confianza {pct(alt['confidence'])}."
    )
    return " ".join(parts)
