# Contrato del agente (LangGraph) y del proveedor LLM

## Estado del grafo

```python
class AgentState(TypedDict, total=False):
    # entrada
    query: str | None                 # texto libre (lenguaje natural)
    origin: PlaceRef | None           # {ref_id} | {lat, lng}
    destination: PlaceRef | None
    priority: Literal["balanced", "fast", "cheap", "reliable"]
    depart_at: str | None
    # parse_request
    parsed: dict                      # {origin_text, destination_text, priority, time}
    resolved_origin: Place
    resolved_destination: Place
    clarification: dict | None        # {code: AMBIGUOUS_PLACE|OFF_TOPIC, candidates:[...]}
    # retrieve_mobility_data
    active_reports: list[Report]
    data_version: str
    # evaluate_routes
    ranking: list[Alternative]        # salida del motor determinístico
    # explain_result
    explanation: str
    explanation_provider: str
    evidence: list[Evidence]
```

## Nodos (máximo 4, un solo agente)

| Nodo | Responsabilidad | Usa LLM | Falla → |
|---|---|---|---|
| `parse_request` | Si hay `query`, extraer textos de origen/destino, prioridad y hora; resolver lugares con el gazetteer. Si la entrada es de formulario, solo resolver. | Sí (solo texto libre) | `MockProvider` (reglas) |
| `retrieve_mobility_data` | Cargar reportes vigentes y versión de datos. | No | error 500 |
| `evaluate_routes` | Llamar al motor determinístico; devolver ranking con evidencia. | **Nunca** | `NO_ROUTE` |
| `explain_result` | Redactar la explicación en español sencillo con los hechos del ranking; validar cifras. | Sí | Plantilla de `MockProvider` |

Aristas: `START → parse_request → (clarification ? END : retrieve_mobility_data) →
evaluate_routes → explain_result → END`.

## Salida del agente

```python
{
  "recommended_route": Alternative,
  "alternatives": list[Alternative],
  "explanation": str,
  "confidence": float,
  "evidence": list[Evidence],
}
```

## Interfaz del proveedor

```python
class LLMProvider(Protocol):
    name: str
    def generate(self, prompt: str) -> str: ...
```

- Implementaciones: `MockProvider` (defecto, determinístico, sin red), `GeminiProvider`,
  `GroqProvider` (HTTP directo), `LocalProvider` (stub).
- Selección: `LLM_PROVIDER=mock|gemini|groq`; claves `GEMINI_API_KEY`, `GROQ_API_KEY`
  (GitHub Secrets / variables de Render).
- `FallbackProvider(primary, MockProvider)`: timeout 6 s, cualquier excepción o salida
  inválida → Mock. El nombre del proveedor efectivo se devuelve en `explanation_provider`.

## Reglas de prompts

- `parse_request`: salida JSON estricta
  `{"origin_text": str|null, "destination_text": str|null, "priority": str|null, "time": str|null, "on_topic": bool}`.
  Nunca coordenadas ni ids.
- `explain_result`: el prompt incluye solo hechos (nombres de tramos, minutos, costo,
  confianza, fuente, reportes). Instrucción: máximo 3 frases, lenguaje sencillo, sin cifras que
  no estén en los hechos, mencionar "simulada para la demo" si algún tramo es
  `demo_simulated`. Validador: toda cifra del texto debe existir en los hechos.
