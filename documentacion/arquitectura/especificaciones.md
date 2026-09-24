# Muévete CB — Plan de Batalla v2
## Hackathon Ciudad Bolívar | POC UD Ciudad Bolívar

> **Objetivo:** construir en ~10–12 horas efectivas un prototipo PWA móvil, desplegable y demostrable que integre movilidad formal + comunitaria, recomendación explicable, reporte ciudadano offline-first y actualización de rutas a partir de reportes.

---

# 1. Resumen ejecutivo

## Producto

**Muévete CB — Corredor Comunitario Inteligente**

Una PWA mobile-first que permite:

1. Seleccionar origen y destino dentro de un microterritorio.
2. Consultar rutas formales y comunitarias/informales.
3. Obtener una recomendación explicable.
4. Visualizar la alternativa en mapa.
5. Reportar bloqueos, retrasos, cambios o riesgos.
6. Guardar reportes sin internet.
7. Sincronizarlos al recuperar conectividad.
8. Hacer que los reportes afecten la confianza/ranking de rutas.
9. Usar LangGraph como orquestador y un proveedor LLM intercambiable.
10. Funcionar en demo incluso sin pagar APIs.

## Idea central

No vender el proyecto como “otro chatbot con mapas”.

Venderlo como:

> **Una red de inteligencia comunitaria de movilidad, offline-first, que convierte conocimiento local de movilidad en datos utilizables para tomar mejores decisiones de viaje.**

### Cadena de valor

**Territorio/GIS → datos de movilidad → conocimiento comunitario → motor determinístico → LangGraph → LLM explicativo → PWA → reportes ciudadanos → actualización de confianza → nuevas recomendaciones**

---

# 2. Qué pide el reto

El reto plantea una plataforma inteligente de rutas/movilidad para Ciudad Bolívar que integre información formal e informal, permita recomendar alternativas según origen/destino/tiempo, visualice la información geográficamente y habilite reportes ciudadanos de bloqueos, retrasos y cambios.

La propuesta debe demostrar un prototipo funcional o modelo conceptual/proceso de integración y un pitch de 5 minutos.

## Rubrica de referencia

- Relevancia territorial: 25%
- Innovación/creatividad: 20%
- Viabilidad técnica: 20%
- Impacto potencial: 20%
- Presentación: 15%

### Implicación para el equipo

No necesitamos construir “mucho software”.

Necesitamos demostrar muy bien:

1. **Entendimiento territorial.**
2. **Integración de datos formales + comunitarios.**
3. **Funcionamiento técnico real.**
4. **Offline-first de verdad.**
5. **IA con función concreta y explicable.**
6. **Retroalimentación ciudadana que modifica el sistema.**
7. **Viabilidad de implementación.**

---

# 3. Alcance definitivo del MVP

## INCLUIR

### A. Consulta de rutas
- Origen.
- Destino.
- Prioridad:
  - más rápido;
  - más económico;
  - más confiable.
- Resultado con:
  - ruta;
  - tiempo estimado;
  - costo;
  - confianza;
  - explicación.

### B. Mapa
- Microterritorio.
- Vías relevantes.
- Paraderos/puntos.
- Rutas formales.
- Rutas comunitarias.
- Incidentes.
- Ruta recomendada.

### C. Reportes ciudadanos
Categorías mínimas:

- Bloqueo.
- Retraso.
- Cambio de ruta.
- Riesgo.
- Otro.

Cada reporte debe tener:
- ubicación;
- categoría;
- descripción opcional;
- fecha/hora;
- identificador anónimo;
- estado de sincronización.

### D. Offline-first
Sin conexión:
- abrir la PWA si ya fue cargada;
- consultar datos locales precargados;
- capturar reportes;
- almacenarlos localmente;
- mostrar estado “pendiente de sincronizar”.

Con conexión:
- sincronizar;
- procesar reportes;
- recalcular recomendaciones.

### E. IA
LangGraph con máximo 4 nodos:

1. Parsear solicitud.
2. Recuperar datos.
3. Evaluar/rankear alternativas.
4. Explicar recomendación.

El LLM NO calcula matemáticamente la ruta.

### F. Proveedor LLM intercambiable

Interfaz conceptual:

```python
class LLMProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
```

Implementaciones posibles:

```text
MockProvider
GeminiProvider
GroqProvider
LocalProvider
```

Para la demo:

**MockProvider debe ser suficiente para que el producto funcione.**

---

# 4. Lo que NO vamos a construir

Si alguien propone cualquiera de estos elementos, debe considerarse fuera de alcance salvo que todo lo esencial ya esté terminado:

- App nativa Android/iOS.
- Integración real con WhatsApp.
- Login/registro de usuarios.
- Panel administrativo completo.
- GPS/turn-by-turn.
- Machine Learning entrenado.
- Optimización matemática compleja.
- Toda Ciudad Bolívar.
- Muchas APIs externas.
- Voz.
- Pagos.
- Chatbot genérico.
- Múltiples agentes.
- Sistema sofisticado de analítica.
- Sistema de seguridad empresarial.
- Integración con todos los operadores.
- Automatización completa de datos institucionales.
- Mapas offline de toda Bogotá.

**Regla:** si una funcionalidad no mejora directamente la demostración principal, se elimina.

---

# 5. Microterritorio

## Decisión crítica

Trabajar con **un solo microterritorio/corredor**.

No intentar representar toda Ciudad Bolívar.

El microterritorio debe permitir demostrar:

- al menos 1 ruta formal;
- varias rutas comunitarias/informales;
- puntos/paraderos;
- un origen y destino representativos;
- al menos 1 contingencia;
- posibilidad de mostrar un cambio de recomendación.

## Criterio de selección

El área debe tener:

1. suficiente información territorial;
2. una situación de movilidad entendible;
3. contraste entre formal e informal/comunitario;
4. posibilidad de obtener o construir datos de demostración trazables;
5. tamaño pequeño para que el mapa funcione offline.

---

# 6. Modelo de datos

## 6.1 Ruta

```json
{
  "id": "route_001",
  "name": "Ruta Comunitaria A",
  "type": "community",
  "origin": "Punto A",
  "destination": "Punto B",
  "stops": ["stop_01", "stop_02"],
  "estimated_time_min": 35,
  "cost": 2500,
  "frequency_min": 15,
  "schedule": "05:00-21:00",
  "reliability": 0.75,
  "source": "community",
  "confidence": 0.78,
  "last_updated": "2026-09-24T10:00:00",
  "geometry": "..."
}
```

## 6.2 Reporte

```json
{
  "id": "report_001",
  "category": "blockage",
  "location": {
    "lat": 4.5,
    "lng": -74.1
  },
  "description": "Bloqueo en la vía",
  "created_at": "2026-09-24T10:30:00",
  "source": "citizen",
  "status": "pending_sync",
  "anonymous_id": "anon_x"
}
```

## 6.3 Campos indispensables

Toda ruta debe tener:

- tipo;
- origen;
- destino;
- tiempo;
- costo;
- disponibilidad/frecuencia;
- fuente;
- confianza;
- última actualización.

Esto permite responder la pregunta crítica:

> “¿De dónde salió esta información?”

---

# 7. Fuente y confianza de datos

Nunca presentar rutas comunitarias como si fueran datos oficiales si no lo son.

Valores de `source`:

```text
institutional
community
territorial
demo_simulated
```

Valores de confianza:

```text
0.0 - 1.0
```

La aplicación puede explicar:

> “Esta alternativa tiene menor confianza porque su información proviene de reporte comunitario reciente.”

Esto convierte la incertidumbre en una característica explícita del producto.

---

# 8. Motor determinístico de rutas

## Regla fundamental

El LLM no decide cuál ruta es matemáticamente mejor.

El motor Python:

1. recibe origen/destino;
2. filtra rutas aplicables;
3. considera incidentes;
4. calcula métricas;
5. calcula score;
6. devuelve alternativas ordenadas.

## Score inicial

Propuesta:

```text
Tiempo:       40%
Disponibilidad: 25%
Confiabilidad: 20%
Costo:        15%
```

El usuario puede cambiar la prioridad.

### Prioridad “rápido”

Aumentar peso de tiempo.

### Prioridad “económico”

Aumentar peso de costo.

### Prioridad “confiable”

Aumentar peso de confianza/reliabilidad.

No buscar una fórmula perfecta. Buscar una fórmula **simple, transparente y explicable**.

---

# 9. Efecto de los reportes

Esta es una de las demostraciones más importantes.

## Flujo

```text
Ciudadano reporta bloqueo
        ↓
Reporte almacenado
        ↓
Reporte asociado a ruta/segmento
        ↓
Confianza/disponibilidad afectada
        ↓
Motor recalcula
        ↓
Nueva recomendación
```

Ejemplo de demo:

### Antes

Ruta A:
- 30 min
- confianza 0.90
- recomendada

Ruta B:
- 38 min
- confianza 0.80

### Reporte

> “Bloqueo en segmento de Ruta A.”

### Después

Ruta A:
- 30 min base
- penalización por incidente
- confianza reducida
- deja de ser recomendada

Ruta B:
- pasa a ser recomendada.

Esto demuestra que el sistema es un ciclo de inteligencia, no una pantalla estática.

---

# 10. Arquitectura

```text
┌─────────────────────────────┐
│       PWA Mobile             │
│ React/Vite + Leaflet         │
└──────────────┬──────────────┘
               │ REST/JSON
               ▼
┌─────────────────────────────┐
│          FastAPI             │
├─────────────────────────────┤
│ /routes                      │
│ /reports                     │
│ /recommendations             │
│ /sync                        │
└──────────────┬──────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ Mobility DB │   │ Reports DB  │
└──────┬──────┘   └──────┬──────┘
       └────────┬─────────┘
                ▼
       ┌─────────────────┐
       │ Route Engine    │
       │ Python          │
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ LangGraph       │
       ├─────────────────┤
       │ Parse           │
       │ Retrieve        │
       │ Evaluate        │
       │ Explain         │
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ LLM Provider    │
       │ Mock / Free /   │
       │ Local / Cloud   │
       └─────────────────┘
```

## Estructura del repositorio

muevete-cb/
├── frontend/
├── backend/
├── agent/
├── data/
├── README.md
├── package.json
├── requirements.txt
└── ...

## Capa offline

```text
PWA
 │
 ├── Service Worker
 ├── IndexedDB
 ├── Datos precargados
 └── Outbox de reportes
             │
             ▼
       Reconexión
             │
             ▼
          /sync
```

---

# 11. Offline-first: definición correcta

No decir:

> “La IA funciona offline.”

Decir:

> “El núcleo de consulta local y captura ciudadana funciona con conectividad intermitente; la sincronización y las capacidades de IA conectadas se activan cuando existe conectividad.”

## Debe funcionar offline

- PWA ya cargada.
- Datos del microterritorio.
- Consulta de datos locales.
- Captura de reportes.
- Visualización de estado.
- Persistencia local.

## Puede requerir internet

- Sincronización.
- LLM cloud.
- Datos externos.
- Actualización remota.

---

# 12. Mapa offline

Cuidado:

**Leaflet no significa automáticamente mapa offline.**

Para la demo:

- precargar GeoJSON;
- limitar el microterritorio;
- usar geometrías simples;
- evitar depender de tiles externos para la funcionalidad central;
- si hay tiles, asegurar cache/preload y tener fallback visual.

La demostración no debe morir cuando se desconecte internet.

---

# 13. Pantallas

## Pantalla 1 — Inicio

Elementos:

- Origen.
- Destino.
- Prioridad.
- Botón “Buscar ruta”.

## Pantalla 2 — Resultados

Mostrar:

- recomendada;
- tiempo;
- costo;
- confianza;
- tipo de transporte;
- explicación.

## Pantalla 3 — Mapa

Mostrar:

- ruta;
- puntos;
- rutas alternativas;
- incidentes.

## Pantalla 4 — Reportar

Formulario:

```text
¿Qué ocurrió?
[ Bloqueo ]
[ Retraso ]
[ Cambio de ruta ]
[ Riesgo ]
[ Otro ]

¿Dónde?
[ ubicación ]

Descripción:
[ opcional ]

[ Guardar reporte ]
```

## Pantalla 5 — Estado

```text
✓ Conectado
✓ Última sincronización: 10:42

o

⚠ Sin conexión
1 reporte pendiente de sincronización
```

---

# 14. API mínima

## GET

```text
GET /routes
GET /routes/{id}
GET /stops
GET /reports
GET /health
```

## POST

```text
POST /recommendations
POST /reports
POST /sync
```

## Ejemplo

```json
POST /recommendations

{
  "origin": "Punto A",
  "destination": "Punto B",
  "priority": "fast"
}
```

Respuesta:

```json
{
  "recommended_route": "route_001",
  "alternatives": ["route_002", "route_003"],
  "estimated_time_min": 32,
  "cost": 2500,
  "confidence": 0.86,
  "reason": "Menor tiempo estimado y disponibilidad alta."
}
```

---

# 15. LangGraph

## Grafo mínimo

```text
START
  ↓
parse_request
  ↓
retrieve_mobility_data
  ↓
evaluate_routes
  ↓
explain_result
  ↓
END
```

## Responsabilidad por nodo

### parse_request
Convierte lenguaje del usuario a:

```text
origin
destination
time
priority
```

### retrieve_mobility_data

Obtiene:

- rutas;
- reportes;
- puntos;
- contexto territorial.

### evaluate_routes

Llama al motor determinístico.

### explain_result

Convierte el resultado en una explicación natural.

---

# 16. Contrato del agente

Entrada:

```python
{
    "origin": str,
    "destination": str,
    "priority": str,
    "time": str | None
}
```

Salida:

```python
{
    "recommended_route": dict,
    "alternatives": list,
    "explanation": str,
    "confidence": float,
    "evidence": list
}
```

El agente debe ser capaz de responder:

- qué recomienda;
- por qué;
- con qué evidencia;
- qué nivel de confianza tiene.

---

# 17. Proveedor LLM

Arquitectura:

```text
LangGraph
   ↓
LLMProvider
   ├── MockProvider
   ├── GeminiProvider
   ├── GroqProvider
   └── LocalProvider
```

## Regla

El código del agente NO debe depender directamente de:

```python
gemini.generate(...)
```

Debe depender de:

```python
llm.generate(...)
```

Así se puede cambiar proveedor sin modificar el grafo.

## MockProvider

Debe existir desde el principio.

Su propósito:

- demo sin internet;
- demo sin API;
- cero costo;
- comportamiento determinístico;
- fallback si falla el proveedor.

---

# 18. Datos que debe entregar el equipo GIS

## Paquete territorial mínimo

### Capas

- vías;
- barrios/sectores relevantes;
- paraderos/puntos;
- estaciones;
- rutas formales;
- rutas comunitarias;
- puntos críticos;
- POI necesarios para el escenario.

### Para cada elemento relevante

- nombre;
- geometría;
- tipo;
- identificador;
- fuente.

### Entregable técnico

Idealmente:

```text
/data
  /geojson
    roads.geojson
    stops.geojson
    formal_routes.geojson
    community_routes.geojson
    incidents.geojson
    pois.geojson
  routes.json
  stops.json
  seed_reports.json
```

---

# 19. Responsabilidades del analista territorial

No limitar el rol a “exportar GeoJSON”.

Debe funcionar como **Product Owner territorial**.

Debe entregar:

### 1 microterritorio

### 3 datos territoriales concretos

### 3 lugares concretos

### 3 actores locales relevantes

### 1 problema de movilidad claramente delimitado

### Evidencia de origen de cada dato

### Contexto para el pitch

Debe poder responder:

> ¿Por qué este territorio?

> ¿Por qué este problema?

> ¿Quién conoce esta movilidad?

> ¿Qué parte es oficial y qué parte es comunitaria?

---

# 20. Dataset de demo

No necesitamos miles de registros.

Objetivo:

- 5–10 rutas;
- 10–20 puntos;
- 10 POI;
- 5–10 reportes;
- 3–5 escenarios de contingencia.

Lo importante es:

**trazabilidad + coherencia + demo controlada.**

---

# 21. Escenarios de demo

Preparar al menos:

### Escenario A — Ruta normal

Origen → destino → recomendación.

### Escenario B — Reporte

Usuario reporta bloqueo → ruta cambia.

### Escenario C — Offline

Desactivar conexión → crear reporte → guardar localmente.

### Escenario D — Reconexion

Activar conexión → sincronizar → recalcular.

### Escenario E — Fallback IA

Simular fallo de proveedor → MockProvider → aplicación continúa.

---

# 22. Demo principal

## Duración

Máximo 3 minutos de demo dentro del pitch.

### Paso 1

Abrir QR/PWA.

### Paso 2

Seleccionar origen y destino.

### Paso 3

Mostrar recomendación.

### Paso 4

Mostrar explicación:

> “Se recomienda esta alternativa por menor tiempo estimado y alta disponibilidad.”

### Paso 5

Simular reporte:

> “Bloqueo en Ruta A.”

### Paso 6

Enviar reporte.

### Paso 7

Actualizar recomendación.

### Paso 8

Desactivar internet.

### Paso 9

Crear segundo reporte.

### Paso 10

Mostrar:

> “Guardado localmente. Pendiente de sincronización.”

### Paso 11

Reactivar internet.

### Paso 12

Sincronizar.

### Paso 13

Mostrar actualización.

---

# 23. Pitch de 5 minutos

## 0:00–0:35 — Problema

Presentar el problema de movilidad en el territorio:

- tiempos largos;
- incertidumbre;
- coexistencia formal/informal;
- conocimiento comunitario disperso;
- conectividad como restricción.

## 0:35–1:10 — Insight

> “El problema no es únicamente encontrar una ruta. Es que parte del conocimiento real de movilidad vive fuera de los sistemas formales y puede desaparecer cuando cambia la situación en la calle.”

## 1:10–2:20 — Demo

Ruta → recomendación → explicación.

## 2:20–3:00 — Inteligencia comunitaria

Reporte → ruta cambia.

## 3:00–3:40 — Offline

Desconectar → reportar → guardar → reconectar → sincronizar.

## 3:40–4:20 — Arquitectura

GIS + datos + motor + LangGraph + proveedor LLM + PWA.

## 4:20–5:00 — Impacto

Indicadores:

- rutas comunitarias digitalizadas;
- porcentaje de rutas con información actualizada;
- reportes capturados;
- tiempo de sincronización;
- porcentaje de reportes offline;
- porcentaje de recomendaciones con evidencia.

Cerrar con:

> “Muévete CB no reemplaza el conocimiento del territorio: lo convierte en una capa de información que puede compartirse, actualizarse y utilizarse para decidir mejor cómo moverse.”

---

# 24. Plan de trabajo: 10–12 horas efectivas

No asumir que las 16 horas nominales son horas completas de desarrollo.

## BLOQUE 0 — Arranque
### 30–45 min

Todos:

- leer alcance;
- confirmar microterritorio;
- confirmar stack;
- crear repo;
- definir branches;
- repartir responsabilidades;
- definir criterio de “terminado”.

**Salida:** backlog inicial + repo.

---

## BLOQUE 1 — Datos y esqueleto
### 1.5 horas

### GIS
- seleccionar microterritorio;
- exportar GeoJSON;
- preparar rutas;
- definir fuentes.

### Backend
- crear FastAPI;
- endpoints;
- modelos.

### Frontend
- crear PWA;
- layout mobile;
- navegación.

### Arquitectura
- estructura LangGraph;
- LLMProvider;
- MockProvider;
- service worker/IndexedDB.

**Gate 1:**
La aplicación abre en móvil y existe el primer mapa/pantalla.

---

## BLOQUE 2 — Ruta funcional
### 2 horas

### Backend
- route engine;
- scoring;
- recomendaciones.

### Frontend
- origen/destino;
- resultados.

### GIS
- validar geometrías;
- validar nombres;
- validar escenarios.

### Arquitectura
- conectar LangGraph al motor.

**Gate 2:**
Origen + destino → recomendación real.

---

## BLOQUE 3 — Reportes
### 1.5 horas

- formulario;
- POST /reports;
- persistencia;
- asociación con ruta;
- penalización.

**Gate 3:**

Reporte → cambia ranking.

---

## BLOQUE 4 — Offline
### 2 horas

- service worker;
- IndexedDB;
- outbox;
- captura offline;
- botón “Sincronizar ahora”;
- endpoint /sync.

**Gate 4:**

Internet apagado → reporte guardado.

---

## BLOQUE 5 — Integración
### 1.5 horas

- LangGraph;
- explicación;
- MockProvider;
- datos finales;
- errores;
- loading;
- estado de conexión.

**Gate 5:**

Demo completa de principio a fin.

---

## BLOQUE 6 — Deploy + ensayo
### 1.5 horas

- deploy;
- QR;
- prueba en 2–3 teléfonos;
- prueba offline;
- fallback local;
- pitch;
- cronómetro.

**Gate 6:**

Una persona que no desarrolló el sistema puede ejecutar la demo siguiendo un guion.

---

# 25. Organización del equipo

## Persona 1 — Senior Backend

Responsable:

- FastAPI;
- modelos;
- route engine;
- scoring;
- endpoints;
- sincronización backend.

### Definition of Done

- endpoints funcionando;
- datos consistentes;
- score reproducible;
- tests básicos;
- demo no depende de intervención manual del backend.

---

## Persona 2 — Senior Frontend

Responsable:

- PWA;
- UX móvil;
- mapa;
- pantallas;
- estados online/offline;
- reportes.

### Definition of Done

- usable en teléfono;
- botones claros;
- estados visibles;
- offline demostrable;
- navegación completa.

---

## Persona 3 — Analista GIS / Territorial

Responsable:

- microterritorio;
- GeoJSON;
- rutas;
- puntos;
- fuentes;
- confianza;
- contexto territorial;
- validación del escenario.

### Definition of Done

- dataset final;
- trazabilidad;
- geometrías válidas;
- explicación territorial lista para pitch.

---

## Persona 4 — Arquitectura / Seguridad / Agente

Responsable:

- LangGraph;
- LLMProvider;
- MockProvider;
- contrato del agente;
- integración;
- PWA/service worker si aplica;
- riesgos técnicos;
- fallback.

### Definition of Done

- LangGraph funcional;
- proveedor intercambiable;
- mock funcional;
- arquitectura explicable;
- demo no depende de API paga.

---

# 26. Gestión del trabajo

## Tablero

Usar columnas:

```text
BACKLOG
READY
DOING
BLOCKED
REVIEW
DONE
```

## Cada tarea debe tener

```text
ID:
Título:
Responsable:
Prioridad:
Dependencias:
Estimación:
Definition of Done:
Estado:
Bloqueo:
```

## Prioridades

### P0 — Obligatorio

Sin esto no existe demo:

- PWA;
- mapa/datos;
- origen/destino;
- recomendación;
- reporte;
- offline;
- sincronización;
- deploy;
- pitch.

### P1 — Importante

- explicación IA;
- confianza;
- ranking configurable;
- escenarios adicionales.

### P2 — Deseable

- mejoras visuales;
- animaciones;
- más filtros;
- métricas.

---

# 27. Backlog inicial

| ID | Tarea | Responsable | Prioridad | Estado |
|---|---|---|---|---|
| T01 | Crear repo y estructura | Arquitectura | P0 | TODO |
| T02 | Seleccionar microterritorio | GIS | P0 | TODO |
| T03 | Exportar GeoJSON | GIS | P0 | TODO |
| T04 | Definir schema de rutas | Backend | P0 | TODO |
| T05 | Crear FastAPI | Backend | P0 | TODO |
| T06 | Crear PWA | Frontend | P0 | TODO |
| T07 | Integrar mapa | Frontend | P0 | TODO |
| T08 | Crear route engine | Backend | P0 | TODO |
| T09 | Crear scoring | Backend | P0 | TODO |
| T10 | Crear LangGraph | Arquitectura | P0 | TODO |
| T11 | Crear MockProvider | Arquitectura | P0 | TODO |
| T12 | Integrar recomendación | Backend + Arquitectura | P0 | TODO |
| T13 | Crear formulario reporte | Frontend | P0 | TODO |
| T14 | Persistir reportes | Backend | P0 | TODO |
| T15 | Implementar IndexedDB | Frontend/Arquitectura | P0 | TODO |
| T16 | Implementar outbox | Frontend | P0 | TODO |
| T17 | Implementar /sync | Backend | P0 | TODO |
| T18 | Hacer que reporte afecte ranking | Backend | P0 | TODO |
| T19 | Estado online/offline | Frontend | P0 | TODO |
| T20 | Deploy | Arquitectura | P0 | TODO |
| T21 | QR | Frontend | P0 | TODO |
| T22 | Ensayo completo | Todos | P0 | TODO |
| T23 | Pitch | Todos | P0 | TODO |
| T24 | Métricas/indicadores | GIS + Arquitectura | P1 | TODO |
| T25 | Mejoras visuales | Frontend | P2 | TODO |

---

# 28. Reunión de sincronización

Hacer checkpoints cortos.

## Cada checkpoint: 10 minutos

Cada persona responde:

1. ¿Qué terminé?
2. ¿Qué haré ahora?
3. ¿Estoy bloqueado?
4. ¿Necesito algo de otra persona?

No hacer reuniones largas.

---

# 29. Gates de calidad

## Gate 1

PWA abre.

## Gate 2

Mapa y datos cargan.

## Gate 3

Origen/destino produce ruta.

## Gate 4

Reporte funciona.

## Gate 5

Reporte modifica recomendación.

## Gate 6

Reporte funciona offline.

## Gate 7

Sincronización funciona.

## Gate 8

Deploy funciona.

## Gate 9

Demo completa sin intervención del desarrollador.

Si se falla un gate:

**NO agregar funcionalidades nuevas.**

---

# 30. Kill list

Si faltan menos de 2 horas y el sistema principal no está estable, eliminar en este orden:

1. Animaciones.
2. Mejoras visuales.
3. Filtros avanzados.
4. Más rutas.
5. Más POI.
6. Funciones secundarias del agente.
7. Proveedor LLM externo.

Nunca eliminar:

- recomendación;
- reportes;
- offline;
- sincronización;
- dataset territorial;
- deploy;
- demo.

---

# 31. Riesgos críticos

## R1 — No saber de dónde vienen las rutas comunitarias

Mitigación:

- fuente;
- fecha;
- confianza;
- diferenciación explícita.

## R2 — LLM decide la ruta

Mitigación:

- motor determinístico.

## R3 — Offline falso

Mitigación:

- prueba física con modo avión.

## R4 — Mapa depende de internet

Mitigación:

- datos locales;
- fallback visual.

## R5 — API gratuita falla

Mitigación:

- MockProvider.

## R6 — Demasiado territorio

Mitigación:

- un microterritorio.

## R7 — Demasiadas funcionalidades

Mitigación:

- P0/P1/P2.

## R8 — Demo falla

Mitigación:

- datos seed;
- escenario preparado;
- fallback local;
- ensayo.

## R9 — No hay evidencia de impacto

Mitigación:

- definir indicadores medibles;
- no inventar resultados.

---

# 32. Pruebas mínimas

## Funcionales

- [ ] origen válido;
- [ ] destino válido;
- [ ] ruta encontrada;
- [ ] alternativa encontrada;
- [ ] scoring reproducible;
- [ ] reporte creado;
- [ ] reporte afecta ruta;
- [ ] sincronización funciona.

## Offline

- [ ] abrir app precargada;
- [ ] consultar datos locales;
- [ ] crear reporte;
- [ ] cerrar/reabrir;
- [ ] reporte persiste;
- [ ] reconectar;
- [ ] sincronizar.

## Móvil

- [ ] Chrome Android;
- [ ] Safari iPhone;
- [ ] botones táctiles;
- [ ] mapa usable;
- [ ] texto legible.

## Demo

- [ ] QR;
- [ ] URL;
- [ ] escenario seed;
- [ ] proveedor mock;
- [ ] modo offline;
- [ ] recuperación.

---

# 33. Indicadores de impacto

No prometer impactos que todavía no fueron medidos.

Usar indicadores de proceso/producto:

### Cobertura

- número de rutas comunitarias digitalizadas;
- número de puntos integrados.

### Actualización

- % de rutas con fecha de actualización;
- tiempo entre reporte y actualización.

### Participación

- número de reportes;
- % de reportes capturados offline.

### Calidad

- % de recomendaciones con evidencia;
- nivel de confianza promedio.

### Operación

- tiempo de respuesta;
- porcentaje de sincronizaciones exitosas.

---

# 34. Preguntas difíciles del jurado

## “¿De dónde salen las rutas informales?”

Respuesta:

> “Las tratamos como datos comunitarios, no como datos oficiales. Cada registro tiene fuente, fecha y nivel de confianza. En el prototipo trabajamos con un microterritorio y hacemos explícita la trazabilidad.”

## “¿Por qué usar IA?”

> “La decisión de ruta la realiza un motor determinístico. La IA se usa para interpretar solicitudes y explicar la recomendación con evidencia. Así evitamos que un modelo genere rutas que no existen.”

## “¿Funciona sin internet?”

> “El núcleo offline permite consultar datos precargados y capturar reportes. La sincronización y el proveedor LLM conectado requieren conectividad.”

## “¿Qué pasa si falla el modelo?”

> “El sistema tiene un proveedor desacoplado y un MockProvider. La recomendación determinística continúa funcionando.”

## “¿Por qué no hacer una app nativa?”

> “Para el prototipo buscamos reducir la barrera de adopción: QR, navegador y PWA. La misma arquitectura puede evolucionar posteriormente.”

## “¿Por qué solo un territorio?”

> “Porque queremos demostrar profundidad y trazabilidad antes que una cobertura superficial. La arquitectura está preparada para ampliar el dataset.”

---

# 35. Definition of Done global

El proyecto se considera terminado cuando:

- [ ] La PWA abre desde un QR.
- [ ] Funciona en teléfono.
- [ ] Muestra el microterritorio.
- [ ] Tiene rutas formales y comunitarias diferenciadas.
- [ ] Permite origen/destino.
- [ ] Recomienda una ruta.
- [ ] Explica por qué.
- [ ] Muestra confianza/fuente.
- [ ] Permite reportar.
- [ ] Reporte funciona sin conexión.
- [ ] Reporte persiste.
- [ ] Reporte se sincroniza.
- [ ] Reporte puede cambiar el ranking.
- [ ] LangGraph está integrado.
- [ ] MockProvider funciona.
- [ ] No depende de una API paga.
- [ ] Demo completa ensayada.
- [ ] Pitch cronometrado.
- [ ] Hay plan de contingencia.

---

# 36. Gestión del día del evento

## Antes de comenzar

- [ ] Laptops cargados.
- [ ] Cargadores.
- [ ] Teléfonos.
- [ ] Repo clonado.
- [ ] Dependencias verificadas.
- [ ] URL de deploy disponible.
- [ ] QR preparado.
- [ ] Dataset local.
- [ ] Copia de respaldo.

## Durante el desarrollo

Mantener:

```text
main = estable
dev = integración
feature/* = trabajo individual
```

No hacer cambios grandes directamente en `main`.

## Antes del pitch

Congelar código.

Solo corregir:

- errores críticos;
- problemas de deploy;
- problemas de demo.

No agregar features.

---

# 37. Fallback de emergencia

Si el deploy falla:

### Nivel 1

Deploy alternativo.

### Nivel 2

Ejecutar localmente.

### Nivel 3

Compartir por red local.

### Nivel 4

Video grabado como respaldo visual.

Pero siempre intentar primero la demo real.

---

# 38. Regla de oro del equipo

> **No ganar por cantidad de funcionalidades. Ganar por claridad, territorio, trazabilidad y una demo que funcione.**

El jurado debe entender en menos de 30 segundos:

1. cuál es el problema;
2. qué hace Muévete CB;
3. qué tiene de diferente;
4. por qué la solución es técnicamente viable.

---

# 39. Checklist final del producto

## Producto
- [ ] Problema concreto.
- [ ] Microterritorio.
- [ ] Rutas formales.
- [ ] Rutas comunitarias.
- [ ] Recomendación.
- [ ] Reporte.
- [ ] Offline.
- [ ] Sync.
- [ ] Re-ranking.
- [ ] Mapa.
- [ ] IA explicable.

## Datos
- [ ] Fuentes.
- [ ] Confianza.
- [ ] Timestamp.
- [ ] Geometrías.
- [ ] Escenarios.

## Técnica
- [ ] FastAPI.
- [ ] PWA.
- [ ] IndexedDB.
- [ ] Service Worker.
- [ ] LangGraph.
- [ ] Provider abstraction.
- [ ] MockProvider.
- [ ] Deploy.

## Presentación
- [ ] Pitch 5 min.
- [ ] Demo ≤ 3 min.
- [ ] Todos participan.
- [ ] Preguntas difíciles preparadas.
- [ ] QR.
- [ ] Backup.

---

# 40. Plantilla diaria de seguimiento

## Fecha

`YYYY-MM-DD`

## Objetivo del bloque

`...`

## Hecho

- [ ]

## En progreso

- [ ]

## Bloqueados

- [ ]

## Decisiones tomadas

- [ ]

## Riesgos nuevos

- [ ]

## Próximo bloque

- [ ]

---

# 41. Registro de tareas del equipo

Copiar esta tabla y actualizar durante el hackathon:

| ID | Tarea | Responsable | P0/P1/P2 | Estado | Inicio | Fin | Bloqueo | Evidencia |
|---|---|---|---|---|---|---|---|---|
| T01 | | | | TODO | | | | |
| T02 | | | | TODO | | | | |
| T03 | | | | TODO | | | | |
| T04 | | | | TODO | | | | |
| T05 | | | | TODO | | | | |
| T06 | | | | TODO | | | | |
| T07 | | | | TODO | | | | |
| T08 | | | | TODO | | | | |
| T09 | | | | TODO | | | | |
| T10 | | | | TODO | | | | |

---

# 42. Decisiones técnicas pendientes

Completar al iniciar:

- [ ] Microterritorio definitivo.
- [ ] Stack frontend.
- [ ] Stack backend.
- [ ] Base de datos.
- [ ] Hosting.
- [ ] Librería de mapa.
- [ ] Estrategia de tiles/offline.
- [ ] Proveedor LLM opcional.
- [ ] Estrategia de sincronización.
- [ ] URL final.

---

# 43. Decisiones que NO deben reabrirse sin motivo

Una vez acordadas:

- alcance;
- microterritorio;
- stack;
- modelo de datos;
- scoring;
- arquitectura del agente;
- estrategia offline;

no volver a discutirlas salvo que exista un bloqueo técnico real.

---

# 44. Resultado esperado

Al finalizar, una persona externa debe poder:

1. Escanear QR.
2. Abrir Muévete CB.
3. Elegir origen/destino.
4. Ver una recomendación.
5. Entender por qué fue recomendada.
6. Ver el territorio.
7. Reportar una contingencia.
8. Ver que la recomendación cambia.
9. Activar modo avión.
10. Crear otro reporte.
11. Verlo guardado localmente.
12. Recuperar conexión.
13. Sincronizar.
14. Ver la actualización.

**Si todo eso funciona, el prototipo tiene una historia técnica y territorial completa.**
