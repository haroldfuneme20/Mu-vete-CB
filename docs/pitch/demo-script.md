# Guion de demo (≤ 3 min) — 14 pasos (spec §44)

Preparación: `curl $PUBLIC_URL/api/health` → `ok`; dos teléfonos con la PWA abierta al menos una
vez con conexión; QR impreso; TalkBack/VoiceOver listo en un teléfono.

| # | Acción | Qué decir / qué se ve |
|---|---|---|
| 1 | Escanear el QR | Abre en el navegador, sin tienda ni registro |
| 2 | Abrir Muévete CB | Barra de estado "Conectado" |
| 3 | Formulario: Mirador del Paraíso → Av. Jiménez, "Más rápido" | Escenario A |
| 4 | Ver la recomendación | TransMiCable + troncal, tiempo, costo, confianza y fuente |
| 5 | Leer "¿Por qué esta ruta?" | La IA explica; el motor decidió (cifras verificables) |
| 6 | Ver el territorio | "Ver en mapa": ruta resaltada, rutas comunitarias simuladas punteadas |
| 7 | Teléfono 1: reportar bloqueo en el cable | Primer reporte → penalización parcial ("1 persona reportó") |
| 8 | Teléfono 2 (jurado): mismo bloqueo | Segundo reporte → la recomendación cambia ("2 personas reportaron") |
| 9 | Activar modo avión | Barra "Sin conexión"; la app sigue abierta |
| 10 | Crear otro reporte con foto | "Guardado localmente. Pendiente de sincronización" |
| 11 | Ver Estado | Contador "1 reporte pendiente" |
| 12 | Quitar modo avión | Evento de reconexión |
| 13 | "Sincronizar ahora" | Reporte sincronizado, hora de última sincronización |
| 14 | Ver la actualización | Recomendación recalculada |

Respaldo del paso 8 sin segundo teléfono: desplegar con `DEMO_B_BACKUP=true` (primer bloqueo
precargado, marcado como simulado) y hacer en vivo solo el segundo reporte.

Accesibilidad (Escenario F, 30 s): con el lector de pantalla, pestaña "Pregunta con tus palabras":
"Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable" → la respuesta se anuncia sola.

**Aviso obligatorio en el pitch:** los datos actuales son de prueba (mock) hasta cargar los
archivos oficiales, y las rutas comunitarias son simuladas para la demo.
