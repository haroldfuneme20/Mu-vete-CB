# Feature Specification: Muévete CB — MVP de movilidad comunitaria para Ciudad Bolívar

**Feature Branch**: `001-muevete-cb-mvp`

**Created**: 2026-09-24

**Status**: Draft

**Input**: User description: "toma el archivo de constitución y dame las especificaciones junto con los puntos pendientes por resolver"

**Base normativa**: `.specify/memory/constitution.md` v2.2.2 y
`documentacion/arquitectura/especificaciones.md` (Plan de Batalla v2; sus §5 y §12 quedan
reemplazados por la constitución).

## Clarifications

### Session 2026-09-24

- Q: ¿Pares origen/destino de los escenarios de demo? → A: A = Mirador del Paraíso
  (TransMiCable) → Av. Jiménez (centro), prioridad "más rápido"; F = Barrio Paraíso → Portal
  Tunal, prioridad "más confiable".
- Q: ¿Origen de las rutas comunitarias? → A: todas simuladas (`demo_simulated`), declaradas
  como tales en la interfaz y en el pitch.
- Q: ¿Regla de efecto de los reportes? → A: un reporte penaliza parcialmente; 2 o más reportes
  coincidentes (mismo tramo, misma categoría, vigentes, de dispositivos distintos) invalidan el
  tramo.

## User Scenarios & Testing *(mandatory)*

> Todas las historias forman parte de la demo principal y son obligatorias (P0 del plan de
> batalla). La prioridad P1–P6 indica el orden de construcción: cada historia, una vez
> terminada, se puede demostrar por sí sola.

### User Story 1 - Obtener una recomendación de ruta explicada (Priority: P1)

Una persona que vive en un barrio de Ciudad Bolívar indica origen, destino (en cualquier
localidad de Bogotá) y su prioridad (más rápido, más económico o más confiable). Recibe hasta
3 alternativas ordenadas que combinan tramos a pie, rutas comunitarias, SITP, TransMilenio y
TransMiCable. La recomendada muestra tiempo estimado, costo, confianza, fuente de los datos,
tipos de transporte, paradas en orden y una explicación en lenguaje sencillo de por qué se
recomienda.

**Why this priority**: es el núcleo del producto; sin recomendación no hay demo.

**Independent Test**: seleccionar el par origen/destino del Escenario A con prioridad "más
rápido" y verificar que aparece una recomendación con todas sus métricas, la evidencia y la
explicación.

**Acceptance Scenarios**:

1. **Given** un origen en Ciudad Bolívar y un destino en otra localidad, **When** la persona
   busca con prioridad "más rápido", **Then** ve hasta 3 alternativas ordenadas con tiempo,
   costo, confianza, fuente, tramos y explicación.
2. **Given** la misma consulta repetida con los mismos datos, **When** se busca de nuevo,
   **Then** el resultado y el orden son idénticos.
3. **Given** una consulta cuyo origen y destino están ambos fuera de Ciudad Bolívar, **When**
   la persona busca, **Then** el sistema le informa que el servicio cubre viajes con al menos un
   extremo en Ciudad Bolívar.
4. **Given** una alternativa que incluye una ruta comunitaria, **When** se muestra,
   **Then** aparece marcada como comunitaria (no oficial), con su nivel de confianza y su
   fecha de última actualización.
5. **Given** que se cambia la prioridad a "más económico", **When** se repite la búsqueda,
   **Then** el orden refleja el mayor peso del costo y la explicación lo menciona.

---

### User Story 2 - Reportar una contingencia y ver cambiar la recomendación (Priority: P2)

Una persona reporta un bloqueo, retraso, cambio de ruta, riesgo u otro evento, indicando
ubicación, categoría, una descripción opcional y una foto opcional. El reporte es anónimo.
Si el reporte afecta un tramo de la ruta recomendada, al consultar de nuevo la recomendación
cambia y la explicación menciona el reporte como evidencia.

**Why this priority**: demuestra el ciclo de inteligencia comunitaria, el diferenciador frente
a un mapa estático.

**Independent Test**: ejecutar el Escenario B: consultar, registrar dos reportes de bloqueo
desde dos teléfonos distintos sobre un tramo de la ruta recomendada y verificar que la
recomendación pasa a otra alternativa.

**Acceptance Scenarios**:

1. **Given** la ruta A recomendada, **When** se registra un primer reporte de bloqueo sobre un
   tramo de la ruta A y se vuelve a consultar, **Then** la ruta A queda penalizada (más tiempo y
   menor confianza) y la explicación cita el reporte, aunque puede seguir recomendada.
2. **Given** un reporte de bloqueo vigente sobre ese tramo, **When** otro dispositivo registra
   un segundo bloqueo coincidente y se vuelve a consultar, **Then** el tramo queda invalidado,
   la ruta A deja de ser la recomendada y la explicación indica que 2 personas reportaron el
   bloqueo.
3. **Given** dos reportes de bloqueo del mismo dispositivo sobre el mismo tramo, **When** se
   consulta, **Then** cuentan como uno solo (penalización parcial).
4. **Given** un reporte con foto, **When** se guarda, **Then** la foto se conserva sin datos de
   ubicación embebidos y reducida de tamaño.
5. **Given** un reporte sin foto ni descripción, **When** se guarda, **Then** el reporte se
   acepta (solo son obligatorias la ubicación y la categoría).
6. **Given** un reporte cuya vigencia ya venció, **When** se consulta una ruta,
   **Then** ese reporte ya no penaliza la ruta.

---

### User Story 3 - Reportar sin conexión y sincronizar después (Priority: P3)

Sin internet, la persona abre la app (ya cargada antes), consulta la información guardada y crea
un reporte. La app muestra "Guardado localmente. Pendiente de sincronización" y un contador de
reportes pendientes. Al recuperar conexión, la persona pulsa "Sincronizar ahora" (o se
sincroniza automáticamente si el dispositivo lo permite); los reportes se envían y la
recomendación se recalcula.

**Why this priority**: la conectividad limitada es una restricción real del territorio y un
criterio de viabilidad técnica (no negociable en la constitución).

**Independent Test**: ejecutar los Escenarios C y D en un teléfono real en modo avión.

**Acceptance Scenarios**:

1. **Given** el teléfono en modo avión y la app ya visitada antes, **When** se abre la app,
   **Then** carga y muestra el mapa de Ciudad Bolívar, la red troncal y las rutas guardadas.
2. **Given** sin conexión, **When** se crea un reporte, **Then** queda guardado con estado
   "pendiente" y el contador de pendientes aumenta.
3. **Given** reportes pendientes, **When** se cierra y se reabre la app sin conexión,
   **Then** los reportes siguen ahí.
4. **Given** reportes pendientes y la conexión recuperada, **When** se sincroniza, **Then**
   cada reporte pasa a "sincronizado", se muestra la hora de la última sincronización y la
   recomendación se actualiza.
5. **Given** una sincronización interrumpida a mitad, **When** se reintenta, **Then** ningún
   reporte se pierde ni se duplica.
6. **Given** sin conexión, **When** la persona intenta una consulta libre en lenguaje natural,
   **Then** la app le informa de forma accesible que esa opción requiere conexión y le ofrece el
   formulario.
7. **Given** sin conexión y una consulta de formulario nunca hecha antes, **When** se busca,
   **Then** la app informa que el cálculo requiere conexión y ofrece repetirla automáticamente al
   reconectar; si la consulta ya se había hecho, muestra el resultado guardado con su fecha.

---

### User Story 4 - Consultar en lenguaje natural con accesibilidad (Priority: P4)

Una persona mayor o una persona ciega escribe (o dicta con el teclado de su teléfono) una
consulta como "Necesito ir de Paraíso al centro, lo más seguro". El sistema identifica origen,
destino, hora y prioridad y responde con un texto breve y claro que el lector de pantalla del
teléfono lee automáticamente. Todo el flujo (consultar, entender la respuesta, reportar) se
puede completar sin ver la pantalla.

**Why this priority**: da a la IA una función concreta y demostrable y amplía el público a
personas mayores y con discapacidad visual.

**Independent Test**: con el lector de pantalla activo y la pantalla sin mirar, completar una
consulta en lenguaje natural y un reporte.

**Acceptance Scenarios**:

1. **Given** la frase "quiero ir de Paraíso al Portal Tunal lo más barato", **When** se envía,
   **Then** el sistema interpreta origen, destino y prioridad "más económico" y responde con la
   recomendación en texto natural.
2. **Given** una frase ambigua (p. ej. destino no reconocido o con varias coincidencias),
   **When** se envía, **Then** el sistema pregunta para aclarar o propone el formulario; nunca
   inventa un lugar.
3. **Given** una frase fuera del tema de movilidad, **When** se envía, **Then** el sistema
   indica amablemente que solo responde consultas de viajes.
4. **Given** el lector de pantalla activo, **When** llega la respuesta, **Then** se anuncia
   automáticamente sin que la persona tenga que buscarla.
5. **Given** cualquier ruta mostrada en el mapa, **When** se usa el lector de pantalla,
   **Then** existe una descripción textual equivalente (paradas en orden, tiempos, costo,
   confianza, incidentes).
6. **Given** la respuesta en texto natural, **When** se compara con los datos de la
   alternativa, **Then** no contiene datos que no provengan del cálculo de la recomendación.

---

### User Story 5 - Ver el territorio en el mapa (Priority: P5)

La persona ve en el mapa la ruta recomendada, las alternativas, paraderos y estaciones, rutas
formales y comunitarias diferenciadas e incidentes activos, y puede activar o desactivar
capas.

**Why this priority**: refuerza la pertinencia territorial en el pitch, pero la
recomendación ya es útil sin mapa gracias a la descripción textual.

**Independent Test**: tras una consulta, abrir el mapa y verificar que se dibujan la ruta, las
alternativas, los paraderos y los incidentes, con leyenda que distingue formal y comunitario.

**Acceptance Scenarios**:

1. **Given** una recomendación, **When** se abre el mapa, **Then** la ruta recomendada se
   resalta y las alternativas se distinguen visualmente.
2. **Given** un reporte activo, **When** se ve el mapa, **Then** el incidente aparece en su
   ubicación con su categoría.
3. **Given** sin conexión, **When** se abre el mapa, **Then** se muestra al menos Ciudad
   Bolívar y la red troncal, aunque no haya fondo de mapa descargado.

---

### User Story 6 - Seguir funcionando si falla el servicio de IA (Priority: P6)

Si el proveedor de IA externo no responde, no está configurado o se quedó sin cupo, la app
sigue entregando recomendaciones y explicaciones con el proveedor simulado incluido, sin que la
persona note una interrupción.

**Why this priority**: asegura que la demo no dependa de una API gratuita.

**Independent Test**: ejecutar el Escenario E: desactivar el proveedor externo y repetir el
Escenario A.

**Acceptance Scenarios**:

1. **Given** el proveedor externo caído, **When** se hace una consulta, **Then** se entrega la
   recomendación con una explicación generada por el proveedor simulado.
2. **Given** ningún proveedor externo configurado, **When** se despliega la app, **Then** todo
   el flujo funciona.

---

### Edge Cases

- Origen igual al destino → se informa que no hay viaje que calcular.
- Ninguna alternativa disponible (fuera de horario de servicio o todas **invalidadas** por
  bloqueos confirmados) → se informa con claridad y se sugiere otra hora o prioridad; no se
  muestra una ruta inválida.
- Todas las alternativas viables **penalizadas** por reportes (sin invalidar) → se muestra la
  mejor según el score con una advertencia explícita ("todas las opciones tienen reportes
  recientes").
- Reportes contradictorios o duplicados sobre el mismo tramo → se consolidan; no se multiplica
  la penalización sin límite.
- Reporte con ubicación lejos de cualquier ruta → se guarda y se muestra en el mapa, pero no
  afecta el ranking.
- Foto muy pesada o en formato no admitido → se reduce o se rechaza con un mensaje, y el
  reporte se puede enviar sin foto.
- Almacenamiento del teléfono lleno al guardar un reporte offline → se avisa y no se pierde en
  silencio.
- Reloj del teléfono desfasado → la vigencia del reporte se calcula con la hora de recepción en
  el servidor al sincronizar.
- Primera visita sin conexión (app nunca cargada) → no es posible; se documenta que la app
  debe abrirse una vez con conexión.
- Servidor dormido por inactividad (primer acceso tarda) → la app muestra un estado de carga
  claro en vez de un error.
- Nombre de barrio que existe en varias localidades o que se escribe de varias formas → se
  pide confirmar entre las coincidencias.

## Requirements *(mandatory)*

### Functional Requirements

**Consulta y recomendación**

- **FR-001**: El sistema MUST permitir indicar origen, destino, prioridad (más rápido, más
  económico, más confiable; por defecto balanceado) y, opcionalmente, la hora de salida (por
  defecto, ahora).
- **FR-002**: El sistema MUST aceptar como origen o destino un barrio, una parada/estación o un
  punto en el mapa, y MUST exigir que al menos uno de los dos esté en Ciudad Bolívar.
- **FR-003**: El sistema MUST calcular las alternativas con un procedimiento determinístico y
  reproducible (mismas entradas y datos → mismo resultado), sin que la IA elija ni invente
  rutas.
- **FR-004**: El sistema MUST combinar tramos a pie, rutas comunitarias, SITP, TransMilenio y
  TransMiCable, con un máximo de 2 transbordos por alternativa.
- **FR-005**: El sistema MUST devolver hasta 3 alternativas ordenadas; cada una con tiempo
  estimado, costo, disponibilidad, confianza, fuente de cada tramo, paradas en orden, número de
  transbordos y evidencia (fuentes, reportes que la afectaron, fecha de actualización de los
  datos).
- **FR-006**: El ordenamiento MUST usar los perfiles de ponderación de la sección de
  Supuestos (balanceado 40/25/20/15 tiempo/disponibilidad/confiabilidad/costo) y un desempate
  fijo (menor tiempo y luego identificador).
- **FR-007**: Toda recomendación MUST incluir una explicación en lenguaje sencillo construida
  únicamente con los datos calculados de la alternativa.

**Lenguaje natural y accesibilidad**

- **FR-008**: Con conexión, el sistema MUST aceptar una consulta en texto libre en español y
  extraer origen, destino, hora y prioridad.
- **FR-009**: Ante una consulta ambigua o fuera del tema de movilidad, el sistema MUST pedir
  aclaración o redirigir al formulario, sin inventar datos.
- **FR-010**: El formulario estructurado MUST estar siempre disponible. Sin conexión, sugiere
  lugares desde el índice local y, al buscar, muestra el resultado guardado de esa misma consulta
  o del escenario de demo equivalente, indicando la fecha del cálculo; si no existe, informa de
  forma accesible que el cálculo requiere conexión y ofrece guardar la consulta para ejecutarla
  al reconectar.
- **FR-011**: Todas las pantallas MUST poder usarse con los lectores de pantalla nativos de
  Android e iPhone, con controles etiquetados, orden de foco lógico y anuncio automático de la
  respuesta.
- **FR-012**: Toda ruta mostrada en el mapa MUST tener una descripción textual equivalente.
- **FR-013**: La interfaz MUST cumplir contraste WCAG 2.1 AA, texto base mínimo de 16 px con
  zoom del sistema y zonas táctiles de al menos 44×44 px, con lenguaje sencillo.

**Reportes ciudadanos**

- **FR-014**: El sistema MUST permitir crear reportes con ubicación (actual del teléfono o
  punto en el mapa) y categoría (bloqueo, retraso, cambio de ruta, riesgo, otro) como campos
  obligatorios, y descripción y una foto como campos opcionales.
- **FR-015**: Los reportes MUST ser anónimos: solo llevan un identificador anónimo generado en
  el dispositivo, sin cuenta ni datos personales.
- **FR-016**: Las fotos MUST reducirse de tamaño y quedar sin metadatos de ubicación antes de
  guardarse; su ausencia nunca bloquea el envío. La pantalla de reporte MUST pedir no incluir
  rostros ni placas en la foto.
- **FR-017**: Un reporte vigente MUST aplicar una penalización parcial a los tramos cercanos
  según su categoría: bloqueo suma tiempo y reduce confiabilidad; retraso suma tiempo; riesgo
  reduce confiabilidad; cambio de ruta reduce disponibilidad; otro solo informa.
- **FR-018**: Dos o más reportes coincidentes (mismo tramo, misma categoría, vigentes y de
  identificadores anónimos distintos) MUST escalar el efecto: en bloqueo, el tramo queda
  invalidado; en las demás categorías, la penalización se duplica hasta un tope. Varios reportes
  del mismo identificador anónimo sobre el mismo tramo cuentan como uno.
- **FR-018a**: La explicación MUST indicar cuántos reportes coincidentes afectaron cada tramo.
- **FR-019**: Cada reporte MUST mostrar su estado: pendiente, sincronizado o con error.

**Offline y sincronización**

- **FR-020**: Tras una primera visita con conexión, la app MUST abrir sin conexión y mostrar el
  detalle de Ciudad Bolívar, la red troncal y estaciones de toda la ciudad (simplificadas), las
  rutas de los escenarios de demo y las últimas consultas de la persona.
- **FR-021**: Sin conexión, la app MUST guardar los reportes (con foto si la hay) en el
  teléfono, conservarlos al cerrar y reabrir, y mostrar el número de pendientes.
- **FR-022**: Al recuperar conexión, la app MUST permitir sincronizar con un botón visible
  y, donde el dispositivo lo soporte, hacerlo automáticamente; la sincronización MUST ser
  idempotente (sin duplicados ni pérdidas en reintentos).
- **FR-023**: Tras sincronizar, el sistema MUST recalcular las recomendaciones afectadas y
  mostrar la hora de la última sincronización.
- **FR-024**: La app MUST mostrar en todo momento el estado de conexión (conectado / sin
  conexión).

**Mapa**

- **FR-025**: El mapa MUST mostrar la ruta recomendada, alternativas, paraderos, estaciones,
  rutas formales y comunitarias diferenciadas e incidentes activos, con capas activables y
  leyenda.
- **FR-026**: El mapa MUST seguir mostrando los datos esenciales sin conexión aunque no haya
  fondo de mapa disponible.

**Datos y trazabilidad**

- **FR-027**: Cada ruta y tramo MUST registrar tipo, origen, destino, tiempo, costo,
  disponibilidad/frecuencia, fuente (institucional, comunitaria, territorial o simulada para
  demo), confianza de 0 a 1 y fecha de última actualización.
- **FR-028**: La información comunitaria o simulada MUST distinguirse visualmente de la
  institucional y nunca presentarse como oficial.
- **FR-029**: Los datos formales MUST cubrir toda Bogotá, sin recorte geográfico, a partir de
  las fuentes institucionales entregadas (barrios catastrales, troncales y rutas provisionales
  de TransMilenio, paraderos zonales SITP, estaciones de TransMilenio, malla vial y GTFS).
- **FR-030**: Los datos que usa la app MUST poder regenerarse de forma reproducible a partir de
  los archivos originales y los datos semilla; cada registro conserva la referencia a su fuente
  original.

**Continuidad y operación**

- **FR-031**: Si el proveedor de IA externo falla o no está configurado, el sistema MUST
  continuar con el proveedor simulado incluido, sin interrumpir el flujo.
- **FR-032**: El sistema MUST ofrecer una verificación de salud que confirme que el servicio y
  los datos están disponibles.
- **FR-033**: Al reiniciarse, el sistema MUST restaurar el estado inicial de la demo (datos y
  reportes semilla).
- **FR-034**: El sistema MUST NOT requerir registro, inicio de sesión ni cuenta de usuario.

### Key Entities *(include if feature involves data)*

- **Barrio**: unidad territorial catastral; nombre, localidad, geometría. Sirve para nombrar
  origen/destino y validar que un extremo esté en Ciudad Bolívar.
- **Parada / Estación**: punto de acceso (paradero zonal SITP, estación TransMilenio o
  TransMiCable, punto comunitario); nombre, tipo, ubicación, fuente.
- **Ruta**: servicio de transporte (troncal, provisional, zonal, TransMiCable o comunitaria);
  tipo, paradas, frecuencia, horario, costo, fuente, confianza, última actualización.
- **Tramo**: segmento entre dos paradas (o caminata) que compone una alternativa; tiempo,
  costo, fuente y penalizaciones vigentes.
- **Alternativa / Recomendación**: resultado de una consulta; tramos, métricas, score,
  confianza, evidencia y explicación.
- **Reporte**: aporte ciudadano; categoría, ubicación, descripción y foto opcionales, fecha y
  hora, identificador anónimo, estado de sincronización, tramos afectados y vigencia.
- **Fuente de datos**: origen de la información (archivo institucional, levantamiento
  comunitario, simulación de demo) con fecha; toda Ruta, Parada y Tramo apunta a una.
- **Escenario de demo**: par origen/destino con prioridad y contingencia preparados y
  verificados para el pitch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona que no participó en el desarrollo completa los 14 pasos del recorrido
  de demo (escanear QR → sincronizar y ver la actualización) sin ayuda en menos de 3 minutos.
- **SC-002**: Con conexión, la recomendación aparece en menos de 5 segundos en el 95% de las
  consultas de los escenarios de demo (sin contar el primer acceso con el servidor dormido).
- **SC-003**: El 100% de las repeticiones de una misma consulta con los mismos datos producen
  el mismo orden de alternativas.
- **SC-004**: En el Escenario B, el 100% de las veces el segundo reporte de bloqueo
  coincidente cambia la ruta recomendada, y el primero siempre produce una penalización visible
  en tiempo o confianza.
- **SC-005**: El 100% de las recomendaciones muestran fuente, confianza y evidencia, y el 100%
  de los tramos comunitarios aparecen marcados como no oficiales.
- **SC-006**: En modo avión, el 100% de los reportes creados persisten tras cerrar y reabrir la
  app y se sincronizan sin duplicados en menos de 30 segundos después de reconectar y pulsar
  "Sincronizar ahora".
- **SC-007**: Una persona usando solo el lector de pantalla completa una consulta en lenguaje
  natural y un reporte sin asistencia visual; la auditoría automática de accesibilidad
  puntúa ≥ 90/100 en todas las pantallas.
- **SC-008**: Al menos 18 de 20 frases de prueba en lenguaje natural (preparadas por el equipo)
  se interpretan con el origen, destino y prioridad correctos; en las 2 restantes el sistema
  pide aclaración en lugar de equivocarse.
- **SC-009**: Con el proveedor de IA externo desactivado, el 100% de las consultas siguen
  recibiendo recomendación y explicación.
- **SC-010**: El flujo completo funciona en al menos 2 teléfonos Android y 1 iPhone.

## Assumptions

- **Usuarios**: residentes de Ciudad Bolívar, incluidas personas mayores y personas ciegas o
  con baja visión; el idioma de la interfaz y de las consultas es español.
- **Parámetros iniciales del motor** (ajustables en configuración, validables en
  `/speckit-clarify`):
  - distancia caminable máxima 600 m; velocidad a pie 4,5 km/h;
  - espera estimada = mitad de la frecuencia de la ruta; penalización por transbordo +5 min;
  - vigencia de un reporte 2 horas; radio de efecto 100 m alrededor del tramo;
  - un reporte (parcial): bloqueo +15 min y −0,3 de confiabilidad; retraso +10 min; riesgo
    −0,3 de confiabilidad; cambio de ruta −0,3 de disponibilidad;
  - 2 o más reportes coincidentes: bloqueo invalida el tramo; demás categorías duplican la
    penalización, con tope (máximo +30 min; confiabilidad y disponibilidad no bajan de 0,1).
- **Perfiles de ponderación** (tiempo / disponibilidad / confiabilidad / costo):
  balanceado 40/25/20/15; rápido 55/20/15/10; económico 25/20/15/40; confiable 25/25/40/10.
- **Tarifas**: se usan las tarifas vigentes de TransMilenio/SITP y una tarifa declarada para
  cada ruta comunitaria; los transbordos siguen la regla tarifaria vigente del sistema integrado.
- **Confirmación comunitaria**: un reporte penaliza parcialmente y 2 o más de dispositivos
  distintos confirman el evento. Un identificador anónimo por dispositivo es suficiente como
  control para la demo; la moderación humana queda fuera del MVP.
- **Primera carga con conexión**: la app debe abrirse una vez con internet para quedar
  disponible sin conexión.
- **Estado de la demo**: al reiniciar el servicio se vuelve a los datos y reportes semilla; los
  reportes de la sesión no se conservan entre reinicios.
- **Fuera de alcance del MVP**: registro/login/perfil con cuenta, app nativa, WhatsApp, voz
  propia (se usa el dictado y lector del teléfono), navegación paso a paso con GPS, panel
  administrativo, pagos, planificador multimodal completo, fondo de mapa detallado offline de
  toda Bogotá, moderación de reportes.
- **Dependencias**: disponibilidad de los archivos institucionales (barrios catastrales,
  troncales, rutas provisionales, paraderos SITP, estaciones, malla vial y GTFS de Bogotá) y del
  diseño de las rutas comunitarias simuladas.

## Escenarios de Demo

| ID | Escenario | Descripción | Resultado esperado |
|---|---|---|---|
| A | Ruta normal | Mirador del Paraíso (TransMiCable) → Av. Jiménez (centro), prioridad "más rápido" | Recomendación con explicación y evidencia |
| B | Reporte comunitario | Sobre un tramo de la ruta recomendada en A: primer bloqueo desde el teléfono del presentador, segundo bloqueo desde otro teléfono (idealmente del jurado) | El primero penaliza; con el segundo la recomendación cambia y la explicación cita "2 reportes" |
| C | Offline | Modo avión → crear reporte con foto | "Guardado localmente. Pendiente de sincronización" |
| D | Reconexión | Reactivar internet → sincronizar | Reporte sincronizado y recomendación recalculada |
| E | Fallback IA | Proveedor externo desactivado → repetir A | Recomendación y explicación con el proveedor simulado |
| F | Accesibilidad | Lector de pantalla activo → "Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable" | Respuesta anunciada y comprensible sin mirar la pantalla |

Respaldo del Escenario B: si no hay un segundo teléfono disponible, se usa un primer reporte de
bloqueo precargado en los datos semilla de la demo (marcado `demo_simulated`) y el presentador
envía el segundo en vivo.

Los escenarios A y F deben verificarse con los datos reales: las estaciones, paraderos y
barrios usados existen en las fuentes institucionales, y en A hay al menos 2 alternativas
viables para que el Escenario B pueda mostrar el cambio.

## Rutas Comunitarias

Las rutas comunitarias/informales no vienen en ninguna fuente institucional. En el MVP
**todas son simuladas** y se cargan como datos semilla con fuente `demo_simulated`.

- Se requieren al menos 3 rutas comunitarias simuladas, cada una con paradas, costo,
  frecuencia, horario, confianza y fecha.
- Para mantener la pertinencia territorial, se trazan sobre la malla vial real y conectan
  barrios reales de Ciudad Bolívar con estaciones de TransMiCable, TransMilenio o paraderos SITP
  reales.
- Al menos una debe alimentar el Escenario A (p. ej. barrio alto → Mirador del Paraíso o
  Juan Pablo II), de modo que el cambio de recomendación del Escenario B la involucre.
- Su confianza inicial es menor que la de las rutas institucionales (por defecto 0,5–0,6).
- La interfaz y la explicación MUST indicar "ruta comunitaria simulada para la demo", y el
  pitch lo declara explícitamente: el sistema está listo para recibir levantamientos reales
  (`community`) sin cambios de diseño.

## Puntos Pendientes por Resolver

| # | Punto | Responsable sugerido | Bloquea |
|---|---|---|---|
| ~~P-01~~ | ~~Pares origen/destino~~ — resuelto (ver Clarifications) | — | — |
| ~~P-02~~ | ~~Origen de rutas comunitarias~~ — resuelto: todas simuladas | — | — |
| P-02a | Diseñar las 3+ rutas comunitarias simuladas sobre la malla vial y paradas reales | Analista territorial | Escenarios A y B |
| P-03 | Ubicar los archivos originales (barrios catastrales, troncales, rutas provisionales, paraderos SITP, estaciones, malla vial, GTFS) en el repositorio de datos crudos | Analista territorial | Preprocesamiento |
| P-04 | Confirmar nombres de atributos reales de cada archivo (p. ej. el campo exacto de localidad en barrios catastrales) y su sistema de coordenadas | Analista territorial | Preprocesamiento |
| P-05 | Validar que el servicio completo cabe en la memoria del plan gratuito del hosting con los datos de toda Bogotá; si no, activar el respaldo | Arquitectura | Deploy |
| P-06 | Tarifas vigentes de TransMilenio/SITP y regla de transbordos a aplicar | Backend + Territorial | Métrica de costo |
| P-07 | Validar o ajustar los parámetros iniciales del motor y los perfiles de ponderación | Backend | Scoring |
| P-08 | Preparar las 20 frases de prueba en lenguaje natural (SC-008) | Arquitectura / IA | Validación de US4 |
| P-09 | Decidir si se usa un proveedor de IA externo gratuito además del simulado y conseguir su clave | Arquitectura | Solo US4 con IA real |
| P-10 | Definir indicadores de impacto para el pitch sin inventar resultados | Territorial + Arquitectura | Pitch |
| ~~P-11~~ | ~~Regla de efecto de reportes~~ — resuelto: parcial con 1, invalida con 2+ | — | — |
| P-12 | Verificar con los datos reales que el Escenario A tiene ≥ 2 alternativas viables y calibrar la penalización parcial para que el primer reporte no cambie por sí solo la recomendación y el efecto de la confirmación (segundo reporte) se vea con claridad en el Escenario B | Backend + Territorial | Escenario B |
| P-13 | Conseguir un segundo teléfono para el Escenario B (o activar el reporte precargado de respaldo) | Frontend | Ensayo |
