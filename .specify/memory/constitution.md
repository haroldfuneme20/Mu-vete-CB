<!--
Sync Impact Report
==================
Version change: 2.2.2 → 2.3.0
Motivo del bump (MINOR): revisión de los datos reales. Se precisa el principio VII: el GTFS de
toda Bogotá sigue sin recorte, pero las capas GeoJSON auxiliares pueden venir recortadas a Ciudad
Bolívar y vecinos. Se añaden reglas: cables proyectados del POT excluidos, rutas provisionales
solo en mapa, GTFS vía asset de Release (sin Git LFS). No se elimina ningún principio.

Cambio anterior, 2.2.1 → 2.2.2
Motivo del bump (PATCH): se alinean las rutas y nombres de los datos derivados y semilla con el
diseño del plan (data/seed, data/build/muevete.db, paquete offline por niveles; POI → landmarks).
No cambia ningún principio. Origen: /speckit-analyze hallazgos D3 e I6.

Cambio anterior, 2.2.0 → 2.2.1
Motivo del bump (PATCH): se resuelve TODO(HOSTING) confirmando Render, que ya era la opción
recomendada, y se precisan sus condiciones operativas (RAM, disco efímero, suspensión por
inactividad) y el respaldo en Hugging Face Spaces. No cambia ningún principio.

Cambio anterior, 2.1.0 → 2.2.0
Motivo del bump (MINOR): se añade la política de CI/CD con GitHub Actions + GHCR, el manejo de
secretos y la recomendación de hosting de contenedores. Sin redefiniciones incompatibles.

Cambio anterior, 2.0.0 → 2.1.0
Motivo del bump (MINOR): se define formalmente el motor de rutas (principio II), se fija
SQLite como persistencia y el despliegue en un único servicio desde el monorepo. Escenarios de
demo y rutas comunitarias se delegan a la especificación. Sin redefiniciones incompatibles.

Cambio anterior, 1.2.0 → 2.0.0
Motivo del bump (MAJOR): se redefine el principio VII. Se elimina "un solo microterritorio
recortado" y se reemplaza por "Ciudad Bolívar conectada con toda Bogotá": data completa sin
recorte y al menos un extremo del viaje en Ciudad Bolívar. Se ajustan en consecuencia III
(paquete offline por niveles), I (fuera de alcance), II (dominio de la entrada libre) y la
sección de Fuentes de Datos (sin recorte, persistencia espacial).

Historial:
  - 1.0.0 (2026-09-24): ratificación inicial; se reemplazan todos los placeholders.
  - 1.1.0 (2026-09-24): + VIII Accesibilidad; II ampliado (NL in/out); gates y pruebas con
    verificación de accesibilidad.
  - 1.2.0 (2026-09-24): + sección Fuentes de Datos Territoriales; VI foto opcional; VII
    microterritorio desde BarriosCatastrales; I sin login en MVP1.
  - 2.0.0 (2026-09-24): VII redefinido (toda Bogotá, al menos un extremo en Ciudad Bolívar);
    III offline por niveles; datos sin recorte; §5 y §12 de la especificación reemplazados.
  - 2.1.0 (2026-09-24): definición del motor de rutas; SQLite + R*Tree; despliegue en un solo
    servicio desde el monorepo.
  - 2.2.0 (2026-09-24): CI/CD con GitHub Actions → GHCR → hosting de contenedores; secretos
    en GitHub Secrets.
  - 2.2.1 (2026-09-24): hosting confirmado en Render; respaldo en Hugging Face Spaces.
  - 2.2.2 (2026-09-24): rutas de datos derivados/semilla alineadas con el plan.
  - 2.3.0 (2026-09-24): datos reales — recorte de capas auxiliares aceptado, cables POT
    excluidos, provisionales solo mapa, GTFS por Release.

Principios definidos:
  - [PRINCIPLE_1_NAME] → I. La Demo Manda (alcance mínimo y disciplinado)
  - [PRINCIPLE_2_NAME] → II. El Motor Decide, la IA Explica (NO NEGOCIABLE)
  - [PRINCIPLE_3_NAME] → III. Offline-First Real (NO NEGOCIABLE)
  - [PRINCIPLE_4_NAME] → IV. Trazabilidad y Confianza de los Datos
  - [PRINCIPLE_5_NAME] → V. Proveedor LLM Intercambiable con MockProvider
  - (nuevo)            → VI. Retroalimentación Ciudadana que Modifica el Sistema
  - (nuevo)            → VII. Un Solo Microterritorio, Mobile-First
  - (nuevo, v1.1.0)    → VIII. Accesibilidad por Lenguaje Natural
  - (ampliado, v1.1.0) → II. El Motor Decide, la IA Explica
  - (redefinido, v2.0.0) VII. Un Solo Microterritorio, Mobile-First
                       → VII. Ciudad Bolívar Conectada con Toda Bogotá, Mobile-First

Secciones añadidas:
  - Restricciones Técnicas y Stack (antes [SECTION_2_NAME])
  - Flujo de Trabajo y Gates de Calidad (antes [SECTION_3_NAME])
  - Fuentes de Datos Territoriales (v1.2.0)

Secciones eliminadas: ninguna.

Plantillas dependientes (leen la constitución en runtime, no modificadas aquí):
  - .specify/templates/plan-template.md      ✅ compatible (Constitution Check genérico)
  - .specify/templates/spec-template.md      ✅ compatible
  - .specify/templates/tasks-template.md     ✅ compatible

TODOs diferidos:
  - Escenarios de demo, rutas comunitarias y parámetros numéricos del motor → se definen en la
    especificación (/speckit-specify), no en la constitución.
  - TODO(DATOS_REPO): los GeoJSON y el GTFS aún no están en el repositorio; ubicarlos en data/raw/.
  - TODO(RUTAS_COMUNITARIAS): ninguna fuente entregada contiene rutas informales; se definen
    en la especificación (source = community o demo_simulated).

Fuentes: documentacion/arquitectura/especificaciones.md (Plan de Batalla v2),
01_arquitectura.drawio, img_arquitectura.jpg, mock.jpg, documentacion/MVP- UD Ciudad-Bolivar.md.
-->

# Muévete CB Constitution

## Core Principles

### I. La Demo Manda (alcance mínimo y disciplinado)

- Toda funcionalidad MUST mejorar directamente la demo principal (§44 de la especificación);
  si no lo hace, se elimina.
- MVP1 MUST NOT incluir login, registro ni perfil de usuario con cuenta; la pestaña "Perfil"
  del mock se elimina (o, si se conserva, solo guarda preferencias locales de accesibilidad
  sin cuenta).
- Queda fuera de alcance, salvo que todo P0 esté terminado: app nativa, WhatsApp,
  panel admin, GPS turn-by-turn, ML entrenado, optimización compleja o planificador
  multimodal completo, múltiples agentes, voz, pagos, chatbot genérico, analítica sofisticada,
  mapas/tiles offline detallados de toda Bogotá.
- El trabajo se prioriza en P0 / P1 / P2. Ninguna tarea P1/P2 se inicia mientras exista un P0
  abierto o un gate fallido.
- Nunca se elimina (kill list): recomendación, reportes, offline, sincronización, dataset
  territorial, deploy y demo.

**Rationale**: se ganan puntos por claridad, territorio, trazabilidad y una demo que
funcione, no por cantidad de funcionalidades, en un presupuesto de ~10–12 horas efectivas.

### II. El Motor Decide, la IA Explica (NO NEGOCIABLE)

- El ranking de rutas MUST calcularlo un motor determinístico en Python: filtra rutas
  aplicables, aplica incidentes, calcula métricas y score, y devuelve alternativas ordenadas.
- El score MUST ser simple, transparente y reproducible (mismo input → mismo output).
  Pesos base: tiempo 40%, disponibilidad 25%, confiabilidad 20%, costo 15%; la prioridad del
  usuario (rápido / económico / confiable) solo ajusta pesos.
- El LLM MUST NOT decidir, calcular ni inventar rutas. Su rol se limita a interpretar la
  solicitud en lenguaje natural (`parse_request` → `origin`, `destination`, `time`,
  `priority`) y redactar la respuesta en lenguaje natural (`explain_result`).
- La entrada libre MUST estar acotada a viajes en Bogotá con origen o destino en Ciudad
  Bolívar: no es un
  chatbot genérico. Si la solicitud es ambigua o está fuera de dominio, el sistema MUST pedir
  aclaración o redirigir al formulario, nunca improvisar una respuesta.
- La respuesta en lenguaje natural MUST construirse solo con datos devueltos por el motor
  (ruta, tiempo, costo, confianza, fuente, incidentes); no puede añadir hechos.
- **Definición del motor de rutas**: módulo Python puro dentro del backend, sin LLM ni llamadas
  de red, que recibe `origin`, `destination`, `priority`, `time` y los reportes activos, y
  ejecuta siempre este pipeline:
  1. *Resolver ubicaciones*: barrio, parada o coordenada → punto; buscar paradas/estaciones
     cercanas a distancia caminable.
  2. *Generar candidatos*: combinar tramos (caminata, ruta comunitaria, SITP, TransMilenio,
     TransMiCable) sobre un grafo precalculado desde el GTFS y las rutas comunitarias, con un
     máximo de 2 transbordos.
  3. *Estimar métricas* por candidato: tiempo (caminata + espera por frecuencia + viaje +
     transbordos), costo (tarifas), disponibilidad (horario/frecuencia) y confiabilidad
     (`confidence` de la fuente).
  4. *Aplicar incidentes*: los reportes activos cercanos a un tramo lo penalizan según su
     categoría (p. ej. `blockage` lo invalida o penaliza fuertemente; `delay` suma tiempo;
     `risk` reduce confiabilidad).
  5. *Calcular score* normalizado con los pesos de la prioridad elegida y ordenar, con desempate
     determinístico (menor tiempo, luego identificador).
  6. *Devolver* las 3 mejores alternativas con sus métricas y la evidencia usada: fuentes,
     reportes que afectaron cada tramo y fecha de actualización de los datos.
  Los parámetros numéricos (distancia caminable, ventana de vigencia de reportes, penalizaciones
  y perfiles de pesos) se fijan en la especificación y MUST vivir en configuración, no
  dispersos en el código. El motor MUST tener tests unitarios propios.
- LangGraph MUST tener como máximo 4 nodos: `parse_request → retrieve_mobility_data →
  evaluate_routes → explain_result`. Un solo agente.
- Toda recomendación MUST devolver: ruta recomendada, alternativas, explicación, confianza y
  evidencia.

**Rationale**: evita rutas alucinadas y permite defender ante el jurado por qué se
recomienda cada alternativa.

### III. Offline-First Real (NO NEGOCIABLE)

- Sin conexión, la PWA ya cargada MUST: abrir, mostrar el paquete offline precargado,
  consultar rutas locales, capturar reportes, persistirlos en IndexedDB (outbox) y mostrar el
  estado "pendiente de sincronizar".
- Como la data completa de Bogotá es demasiado pesada para el teléfono, el paquete offline
  MUST ser por niveles: (a) detalle de Ciudad Bolívar (barrios, paraderos, vías principales,
  rutas comunitarias); (b) red troncal y estaciones de TransMilenio de toda la ciudad,
  simplificadas; (c) las rutas de los escenarios de demo y las últimas consultas del usuario.
  La data completa (GTFS, malla vial y paraderos de toda la ciudad) vive en el backend y solo se
  consulta con conexión.
- Los reportes MUST sobrevivir a cerrar y reabrir la app.
- Al reconectar, el outbox MUST sincronizarse vía `/sync` (con botón "Sincronizar ahora" como
  mecanismo garantizado; Background Sync solo como mejora progresiva) y disparar recálculo.
- El mapa MUST funcionar con GeoJSON precargado; la funcionalidad central no depende de tiles
  externos (si se usan, con caché y fallback visual).
- Se comunica con precisión: "el núcleo de consulta y captura funciona con conectividad
  intermitente; sincronización e IA conectada requieren internet". Nunca "la IA funciona
  offline".
- El offline MUST validarse físicamente en modo avión en teléfono real.

**Rationale**: la conectividad limitada es una restricción real del territorio y un
criterio de viabilidad técnica.

### IV. Trazabilidad y Confianza de los Datos

- Toda ruta MUST tener: tipo, origen, destino, tiempo, costo, disponibilidad/frecuencia,
  `source`, `confidence` (0.0–1.0) y `last_updated`.
- `source` MUST ser uno de: `institutional`, `community`, `territorial`, `demo_simulated`.
- Los datos comunitarios o simulados MUST NOT presentarse como oficiales; la UI diferencia
  visualmente rutas formales y comunitarias y muestra fuente y confianza.
- No se inventan resultados de impacto: solo indicadores de proceso/producto medibles.

**Rationale**: la pregunta crítica "¿de dónde salió esta información?" debe tener respuesta
para cada dato; la incertidumbre es una característica explícita del producto.

### V. Proveedor LLM Intercambiable con MockProvider

- El agente MUST depender únicamente de la interfaz `LLMProvider.generate(prompt) -> str`,
  nunca de un SDK concreto (p. ej. `gemini.generate(...)`).
- `MockProvider` MUST existir desde el inicio, ser determinístico, costo cero, operar sin
  internet y actuar como fallback automático ante fallo del proveedor real.
- El producto completo MUST funcionar sin ninguna API paga. Gemini/Groq/Local son opcionales.

**Rationale**: la demo no puede morir por una API gratuita caída o sin cupo.

### VI. Retroalimentación Ciudadana que Modifica el Sistema

- Un reporte MUST incluir: ubicación, categoría (`blockage`, `delay`, `route_change`, `risk`,
  `other`), descripción opcional, fecha/hora, identificador anónimo y estado de sincronización.
- Un reporte MAY incluir **una foto opcional**. Si se adjunta: se comprime en el cliente
  (lado mayor ≤ 1280 px, ≤ 1 MB), se eliminan los metadatos EXIF (incluida la ubicación GPS)
  antes de guardarla, se almacena como Blob en IndexedDB junto al reporte en el outbox y se
  sube al sincronizar. La foto nunca es obligatoria ni bloquea el envío del reporte, y el botón
  para adjuntarla tiene etiqueta accesible.
- Un reporte MUST asociarse a ruta/segmento y afectar confianza/disponibilidad, de modo que el
  motor recalcule y la recomendación pueda cambiar (escenario Ruta A → Ruta B).
- Los reportes son anónimos; no se recolectan datos personales.

**Rationale**: demuestra un ciclo de inteligencia comunitaria, no una pantalla estática.

### VII. Ciudad Bolívar Conectada con Toda Bogotá, Mobile-First

- El motor MUST usar el GTFS completo de Bogotá (sin recorte), porque los viajes reales salen
  de Ciudad Bolívar hacia otras localidades. Las capas GeoJSON auxiliares (sectores, paraderos,
  estaciones, troncales, provisionales, malla vial) MAY venir recortadas a Ciudad Bolívar y sus
  localidades vecinas; los destinos fuera de ese recorte se resuelven con las estaciones y
  paraderos del GTFS y con hitos (`landmarks.json`).
- Todo viaje MUST tener al menos un extremo (origen o destino) en Ciudad Bolívar, identificado
  en `BarriosCatastrales` con `Localidad = Ciudad Bolívar`; el otro extremo puede estar en
  cualquier localidad de Bogotá. Así se cubren tanto la ida como el regreso a casa.
- Las rutas comunitarias/informales y los reportes ciudadanos se concentran en Ciudad Bolívar
  y actúan como "primer y último tramo" que conecta con TransMiCable, TransMilenio y SITP.
- El motor MUST mantenerse simple: combina tramos (comunitario/caminata + SITP/TransMilenio)
  con un máximo de 2 transbordos; no se implementa un planificador multimodal completo.
- La demo MUST apoyarse en 3–5 escenarios preparados y trazables (p. ej. barrio de Ciudad
  Bolívar → centro/trabajo en otra localidad), con al menos 1 contingencia que cambie la
  recomendación.
- La UI MUST ser PWA mobile-first, accesible desde QR/URL, sin instalación desde tiendas y sin
  registro obligatorio; usable en Chrome Android y Safari iPhone.

**Rationale**: la movilidad de Ciudad Bolívar es, en su mayoría, hacia fuera de la localidad;
recortar la ciudad ocultaría el problema real (trayectos largos con transbordos). La
profundidad comunitaria se mantiene en la localidad y la cobertura formal abarca la ciudad.

### VIII. Accesibilidad por Lenguaje Natural

- El usuario MUST poder consultar escribiendo en lenguaje natural (p. ej. "Necesito ir del
  TransMiCable al barrio Paraíso, lo más seguro") y recibir la recomendación como texto
  natural, claro y breve, además de las tarjetas y el mapa.
- Público objetivo explícito: personas mayores y personas ciegas o con baja visión.
- La PWA MUST ser operable con lectores de pantalla del sistema (TalkBack, VoiceOver): HTML
  semántico, etiquetas/ARIA en todos los controles, orden de foco lógico y la respuesta del
  agente anunciada mediante región `aria-live`.
- El mapa MUST NOT ser el único medio de información: toda ruta tiene equivalente textual
  (paradas en orden, tiempos, costo, confianza, incidentes).
- Legibilidad: texto base ≥ 16 px con soporte de zoom del sistema, contraste WCAG 2.1 AA,
  objetivos táctiles ≥ 44×44 px, lenguaje sencillo sin jerga técnica.
- El dictado por voz se apoya en el teclado/lector del sistema operativo; construir voz propia
  (TTS/STT) sigue fuera de alcance del MVP (P2 opcional con Web Speech API).
- El formulario estructurado (origen/destino/prioridad) MUST mantenerse siempre como
  alternativa y como modo offline: sin conexión la entrada libre puede no estar disponible y la
  app lo comunica de forma accesible.

**Rationale**: la entrada y salida en lenguaje natural reducen la barrera de uso para
población mayor o con discapacidad visual, y le dan a la IA una función concreta y
demostrable más allá de "chatbot con mapa".

## Restricciones Técnicas y Stack

- **Frontend**: PWA React + Vite, Leaflet, Service Worker, IndexedDB (outbox), `manifest.json`.
  Librería de componentes UI (p. ej. Material UI) opcional.
- **Backend**: Python + FastAPI, REST/JSON. API mínima: `GET /routes`, `GET /routes/{id}`,
  `GET /stops`, `GET /reports`, `GET /health`, `POST /recommendations`, `POST /reports`,
  `POST /sync`.
- **Agente**: LangGraph (≤4 nodos) + `LLMProvider` con `MockProvider`, `GeminiProvider`,
  `GroqProvider`, `LocalProvider`.
- **Datos**: archivos originales en `data/raw/`; datos semilla en `data/seed/` (rutas
  comunitarias simuladas, reportes semilla, escenarios de demo, hitos `landmarks.json`); base
  derivada `data/build/muevete.db` y paquete offline por niveles (`offline/manifest.json` +
  GeoJSON simplificados).
- **Repositorio**: monorepo con `frontend/`, `backend/`, `agent/`, `data/`, `docs/`,
  `README.md`.
- **Persistencia backend**: SQLite (un solo archivo). Un script de preprocesamiento reproducible
  genera la base desde `data/raw/` (GTFS, GeoJSON, rutas comunitarias, reportes semilla).
  Las búsquedas espaciales usan el módulo R*Tree incluido en SQLite (por bounding box) y
  Shapely en Python para el cálculo fino; no se requiere SpatiaLite ni servidor de base de
  datos. La misma base guarda los reportes ciudadanos.
- **Despliegue**: un único servicio desde el monorepo. FastAPI sirve la API y los archivos
  estáticos del build de la PWA (mismo dominio, sin CORS), empaquetado en un Dockerfile.
  El despliegue MUST poder reconstruir la base desde el script y los datos semilla en cada
  arranque, por si el disco del hosting no es persistente.
- **CI/CD con GitHub**: el código vive en un repositorio de GitHub y se despliega con GitHub
  Actions:
  - en cada pull request hacia `dev` o `main`: lint, tests del backend (incluido el motor de
    rutas) y build de la PWA; si fallan, no se hace merge;
  - en cada push a `main`: build de la imagen Docker, publicación en GitHub Container Registry
    (GHCR) y disparo del despliegue en el hosting (deploy hook o CLI);
  - las API keys de proveedores LLM y los tokens de despliegue MUST vivir en GitHub Secrets o en
    las variables del hosting, nunca en el repositorio. Sin ellas, la app arranca con
    `MockProvider`.
- **Hosting**: **Render**, como un único Web Service que ejecuta la imagen Docker publicada en
  GHCR. GitHub Actions dispara el despliegue en cada push a `main` mediante el deploy hook de
  Render, guardado en GitHub Secrets.
  - El contenedor MUST mantenerse dentro de la RAM del plan elegido (512 MB en el plan
    gratuito); el consumo se mide temprano en local con `docker stats` durante consultas de
    ruta reales.
  - El disco de Render no es persistente: la base SQLite se reconstruye al arrancar desde el
    script y los datos semilla.
  - Como el plan gratuito suspende el servicio por inactividad, durante el evento MUST
    mantenerse activo (workflow programado de GitHub Actions que haga ping a `GET /health` o
    plan Starter de pago) y verificarse con `GET /health` antes del pitch.
  - GitHub Pages no se usa porque solo sirve contenido estático y no ejecuta el backend.
- Sin dependencias de pago obligatorias; minimizar APIs externas.

## Fuentes de Datos Territoriales

| Fuente | Uso en el sistema | `source` |
|---|---|---|
| `BarriosCatastrales` (atributo `Localidad`) | Nombrar barrios origen/destino en toda Bogotá y validar que un extremo esté en Ciudad Bolívar | `territorial` |
| Trazado troncal TransMilenio | Geometría de rutas formales troncales | `institutional` |
| Rutas provisionales SITP | Solo mapa (no están en el GTFS); son oficiales, no informales | `institutional` |
| Paraderos zonales SITP | Paraderos (stops) que se articulan con TransMilenio | `institutional` |
| Estaciones TransMilenio | Estaciones y puntos de transbordo | `institutional` |
| Malla vial integrada | Vías y segmentos para asociar reportes e incidentes | `institutional` |
| GTFS Bogotá | Rutas, paradas, frecuencias, horarios y tarifa formales | `institutional` |
| Levantamiento del equipo | Rutas comunitarias/informales | `community` / `demo_simulated` |

- Los cables proyectados del POT (p. ej. `CableAereo_CB.geojson`) MUST NOT usarse en rutas ni
  en el mapa: no son servicios operativos y presentarlos confundiría planeación con oferta real.
- El GTFS (> 100 MB) no se versiona en git: se publica como asset de un Release de GitHub y el
  build lo descarga (`GTFS_URL` / `GTFS_RELEASE_URL`).

- Los archivos originales se guardan sin modificar en `data/raw/` y los datos semilla en
  `data/seed/`. Los derivados (la base `data/build/muevete.db` y el paquete offline) los genera
  un script reproducible (no edición manual).
- El GTFS se carga completo; las capas GeoJSON se usan con la cobertura con que llegan (recorte
  de Ciudad Bolívar y vecinos aceptado en v2.3.0). Para el paquete offline solo se generan
  versiones simplificadas (menos vértices, menos atributos) por niveles del principio III.
- El GTFS completo se carga en el backend; de él salen `frequency_min`, `schedule`, tiempos
  estimados y los puntos de transbordo de las rutas formales.
- Por el volumen de la data (GTFS y malla vial de toda la ciudad), el preprocesamiento MUST
  precalcular en SQLite el grafo de tramos, los índices R*Tree y los transbordos; no se
  recorren los GeoJSON completos en cada consulta.
- Las rutas comunitarias y los escenarios de demo se definen en la especificación
  (`/speckit-specify`) y se cargan como datos semilla trazables.
- Todas las capas MUST llevarse al mismo sistema de referencia (WGS84, EPSG:4326) para
  Leaflet.
- Cada registro derivado conserva el identificador y el nombre del archivo de origen para
  mantener la trazabilidad (principio IV).

## Flujo de Trabajo y Gates de Calidad

- **Ramas**: `main` = estable, `dev` = integración, `feature/*` = trabajo individual. No se
  hacen cambios grandes directamente en `main`.
- **Gates secuenciales**: (1) PWA abre → (2) mapa y datos cargan → (3) origen/destino produce
  ruta → (4) reporte funciona → (5) reporte modifica recomendación → (6) reporte funciona
  offline → (7) sincronización funciona → (8) deploy funciona → (9) demo completa sin
  intervención del desarrollador. Si un gate falla, MUST NOT agregarse funcionalidades nuevas.
- **Pruebas mínimas**: tests básicos del backend que verifiquen scoring reproducible y que un
  reporte altere el ranking; checklists funcional, offline, móvil y de demo (§32); checklist de
  accesibilidad: flujo completo (consulta en lenguaje natural → respuesta → reporte) ejecutado
  con TalkBack o VoiceOver y auditoría Lighthouse de accesibilidad ≥ 90.
- **Congelamiento**: antes del pitch se congela el código; solo se corrigen errores críticos,
  de deploy o de demo.
- **Contingencia**: deploy alternativo (la misma imagen Docker en Hugging Face Spaces, también
  si el contenedor supera la RAM de Render) → ejecución local → red local → video de respaldo.
- Decisiones acordadas (alcance, cobertura territorial, stack, modelo de datos, scoring,
  arquitectura del agente, estrategia offline) MUST NOT reabrirse sin un bloqueo técnico real.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica, documento previo o sugerencia
  durante el hackathon. `documentacion/arquitectura/especificaciones.md` (v2) es la referencia
  de detalle; ante conflicto con documentos anteriores (p. ej. `MVP- UD Ciudad-Bolivar.md`),
  prevalece la v2 y esta constitución. Desde la v2.0.0, esta constitución reemplaza las
  secciones §5 (microterritorio) y §12 (mapa offline) de la especificación.
- Toda spec, plan y lista de tareas (`/speckit-*`) MUST pasar el "Constitution Check" contra
  estos principios; cualquier violación se justifica explícitamente en el plan.
- **Enmiendas**: se proponen en el checkpoint del equipo, se aprueban por consenso del equipo
  (o del Arquitecto ante empate) y se registran en el Sync Impact Report.
- **Versionado semántico**: MAJOR = eliminación o redefinición incompatible de un principio;
  MINOR = principio o sección nuevos o ampliados; PATCH = aclaraciones y redacción.
- **Revisión de cumplimiento**: en cada gate y en cada checkpoint de 10 minutos.

**Version**: 2.3.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
