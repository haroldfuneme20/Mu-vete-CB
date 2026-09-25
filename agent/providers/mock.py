"""MockProvider: determinístico, sin red, costo cero (constitución V).

Reconoce dos tipos de prompt por su encabezado:
- `### TAREA: PARSE` → interpreta la consulta con reglas y devuelve JSON.
- `### TAREA: EXPLAIN` → redacta la explicación con una plantilla a partir de los hechos.
"""

from __future__ import annotations

import json
import re

from backend.app.geo import strip_accents

FACTS_MARK = "### HECHOS"
QUERY_MARK = "### CONSULTA"

PRIORITY_WORDS = [
    ("cheap", r"\b(barat[oa]s?|economic[oa]s?|menos plata|menos dinero|mas barat[oa])\b"),
    ("reliable", r"\b(segur[oa]s?|seguridad|confiable|confiabilidad|tranquil[oa]|sin riesgos?)\b"),
    ("fast", r"\b(rapid[oa]s?|pronto|urgente|lo antes posible|mas rapid[oa]|afan)\b"),
]
MOBILITY_WORDS = r"\b(ir|llegar|voy|vamos|viajar|ruta|ruta[s]?|bus|transmilenio|cable|" \
                 r"desde|hasta|como llego|moverme|salir|regresar|volver|trasladarme)\b"
_ART = ""  # los artículos se conservan: "Las Cruces", "La Candelaria"
_GO = r"(?:ir|llegar|voy|viajar|irme|moverme|ir me|llego|salgo|regresar|volver)"
PATTERNS = [
    # "... ir a Y desde X"
    rf"\b{_GO} (?:a |al |hasta |hacia |para ){_ART}(?P<d>.+?) desde {_ART}(?P<o>.+)",
    # "... desde/de/del X hasta/a/al Y"
    rf"\b(?:desde|del|de) {_ART}(?P<o>.+?) (?:hasta|hacia|para|al|a) {_ART}(?P<d>.+)",
    # "... ir a Y" (sin origen)
    rf"\b{_GO} (?:a |al |hasta |hacia |para ){_ART}(?P<d>.+)",
    # "como llego a Y"
    rf"\bcomo (?:llego|voy) (?:a |al |hasta ){_ART}(?P<d>.+)",
]
TRAILING = re.compile(
    r"\s*(,|\.|;)?\s*(lo |la |el )?(mas |muy )?(rapid[oa]|barat[oa]|economic[oa]|segur[oa]|"
    r"confiable|pronto|urgente|posible|por favor|con seguridad|a las .*|manana.*|hoy.*|ahora.*|"
    r"en la manana.*|en la tarde.*|en la noche.*|que sea .*)$"
)
TIME_RE = re.compile(r"\ba las (\d{1,2})(?::(\d{2}))?\s*(am|pm|de la manana|de la tarde|"
                     r"de la noche)?")


def _clean_place(text: str | None) -> str | None:
    if not text:
        return None
    t = text.strip()
    for _ in range(3):
        t = TRAILING.sub("", t).strip()
    t = re.sub(r"^(el barrio |barrio |la estacion |estacion )", "", t).strip(" ,.")
    return t or None


def parse_rules(query: str) -> dict:
    q = strip_accents(query).lower().strip()
    q = re.sub(r"[¿?¡!]", " ", q)
    q = re.sub(r"\s+", " ", q)
    priority = None
    for prio, rx in PRIORITY_WORDS:
        if re.search(rx, q):
            priority = prio
            break
    time = None
    m = TIME_RE.search(q)
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        suf = m.group(3) or ""
        if ("pm" in suf or "tarde" in suf or "noche" in suf) and h < 12:
            h += 12
        time = f"{h:02d}:{mi:02d}"
    origin = dest = None
    for rx in PATTERNS:
        mm = re.search(rx, q)
        if mm:
            origin = _clean_place(mm.groupdict().get("o"))
            dest = _clean_place(mm.groupdict().get("d"))
            break
    on_topic = bool(origin or dest or re.search(MOBILITY_WORDS, q))
    return {"origin_text": origin, "destination_text": dest, "priority": priority,
            "time": time, "on_topic": on_topic}


def _money(v) -> str:
    return "$" + f"{int(round(v)):,}".replace(",", ".")


def explain_template(f: dict) -> str:
    rec = f["recommended"]
    rides = [leg for leg in rec["legs"] if leg["mode"] != "walk"]
    names = " y luego ".join(leg["route_name"] for leg in rides) or "caminar"
    reason = {
        "fast": "la opción más rápida" if f.get("is_fastest") else "la mejor para llegar pronto",
        "cheap": "la opción más económica" if f.get("is_cheapest") else "la mejor por costo",
        "reliable": "la opción más confiable" if f.get("is_most_reliable")
        else "la mejor por confiabilidad",
    }.get(f.get("priority"), "la que mejor combina tiempo, costo y confiabilidad")
    parts = [
        f"Te recomiendo tomar {names}, porque es {reason}: "
        f"{rec['total_time_min']} minutos y {_money(rec['cost'])}."
    ]
    used = {leg["route_name"] for leg in rides}
    blocked = sorted(f.get("blocked", []), key=lambda b: (b["route_name"] not in used,
                                                          b["route_name"]))
    for b in blocked[:2]:
        where = (f"el tramo {b['from_stop']} – {b['to_stop']} de {b['route_name']}"
                 if b.get("from_stop") else b["route_name"])
        parts.append(f"Evitamos {where} porque {b['n_confirm']} personas reportaron un bloqueo.")
    for leg in rides:
        for r in leg["reports"]:
            who = "1 persona reportó" if r["n_confirm"] == 1 else \
                f"{r['n_confirm']} personas reportaron"
            parts.append(f"Ten en cuenta que {who} {r['label']} en {leg['route_name']}.")
    if any(leg["source_kind"] == "demo_simulated" for leg in rides):
        parts.append("Incluye una ruta comunitaria simulada para la demo.")
    parts.append(f"Confianza de la recomendación: {int(round(rec['confidence'] * 100))}%.")
    return " ".join(parts)


class MockProvider:
    name = "mock"

    def generate(self, prompt: str) -> str:
        if "### TAREA: PARSE" in prompt:
            query = prompt.split(QUERY_MARK, 1)[1].strip() if QUERY_MARK in prompt else prompt
            return json.dumps(parse_rules(query), ensure_ascii=False)
        if "### TAREA: EXPLAIN" in prompt:
            facts = json.loads(prompt.split(FACTS_MARK, 1)[1].strip())
            return explain_template(facts)
        return ""
