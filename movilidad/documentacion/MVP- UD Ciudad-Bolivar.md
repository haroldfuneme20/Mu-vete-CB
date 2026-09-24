Para maximizar el puntaje en el reto "Muévete CB" y desarrollar un prototipo funcional en 16 horas efectivas sin sobredimensionar el alcance, la estrategia debe centrarse en construir una **Progressive Web App (PWA)** enfocada en un micro-territorio específico.

A continuación, se detalla el plan de trabajo estructurado según los requerimientos técnicos y la rúbrica de evaluación del documento "POC Ciudad Bolivar UD".

## **1\. Definición del Producto Mínimo Viable (MVP)**

Para cumplir con el requerimiento de accesibilidad y "bajo umbral de adopción", la solución será una PWA. Esto permite que los jurados escaneen un código QR y "descarguen" la app directamente en su navegador móvil sin pasar por tiendas de aplicaciones, cumpliendo con la necesidad de viabilidad técnica.

MD+ 1

* **Mapa Base Delimitado:** Visualización geográfica de paraderos y rutas formales (TransMiCable, SITP) e informales. Para no perder tiempo, **no mapeen toda la localidad**. Elijan una sola zona crítica (ej. la conexión entre una estación de TransMiCable y un barrio periférico como Paraíso o Sierra Morena).  
  MD+ 1  
* **Agente Orquestador (LangGraph \+ Python):** Un asistente de recomendación que cruce origen, destino y tiempo. Para evitar costos de licencias, el agente usará un modelo gratuito (ej. Llama 3 vía Groq o Gemini Free) y la arquitectura de LangGraph se diseñará de forma modular para demostrar al jurado que el nodo del LLM se puede conectar/desconectar o cambiar por un modelo local con una sola línea de código.  
  MD  
* **Reportes Comunitarios Offline:** Un componente de reporte ciudadano para afectaciones en tiempo real (bloqueos, demoras). Si el usuario no tiene internet, la PWA guardará el reporte localmente (usando Service Workers) y lo sincronizará con el backend automáticamente en cuanto detecte conexión.  
  MD

## **2\. Estrategia para la Rúbrica de Evaluación**

El desarrollo y el pitch de 5 minutos deben apuntar directamente a los criterios con los que serán calificados:

MD

* **Pertinencia Territorial (25%):** Sustenten el problema con datos reales. Mencionen cómo su app aborda específicamente la reducción de los trayectos actuales de dos a tres horas y la desconexión del transporte informal.  
  MD+ 1  
* **Innovación y Creatividad (20%):** Destaquen el uso de LangGraph no solo como un chatbot, sino como un agente capaz de tomar decisiones de enrutamiento basadas en los reportes comunitarios.  
  MD  
* **Viabilidad Técnica (20%):** Aquí ganan con la PWA. Demuestren que la aplicación considera la conectividad limitada del territorio al permitir el funcionamiento y la carga de reportes sin internet.  
  MD  
* **Impacto Potencial (20%):** Definan indicadores claros (ej. cantidad de personas beneficiadas en el micro-territorio elegido) y expliquen cómo el modelo offline es escalable a otras zonas rurales.  
  MD  
* **Presentación (15%):** Los cuatro miembros deben participar en el pitch de 5 minutos. El jurado debe poder interactuar con el prototipo durante la presentación.  
  MD+ 1

## **3\. Asignación de Roles y Tareas (Equipo de 4\)**

**Analista de Data y Catastral**

* *Tarea ArcGIS:* Filtrar y exportar únicamente las capas del micro-territorio seleccionado en formato ligero (GeoJSON) para no sobrecargar el frontend.  
* *Contexto:* Mapear los puntos críticos donde coexisten las rutas formales e informales.  
  MD  
* *Pitch:* Encargado de exponer la problemática territorial, citar los datos reales y explicar el impacto esperado.  
  MD

**Arquitecto de Software y Seguridad**

* *Arquitectura PWA:* Configurar el `manifest.json` y los Service Workers para habilitar la caché del mapa y el almacenamiento de reportes sin conexión.  
* *Agente IA:* Estructurar el grafo en LangGraph asegurando que la integración del LLM sea agnóstica y de bajo costo.  
* *Pitch:* Encargado de defender la viabilidad técnica, explicar el funcionamiento offline y la escalabilidad tecnológica.  
  MD

**Desarrollador Senior 1 (Backend \- Python)**

* Crear una API ligera (FastAPI/Flask) para servir los datos GeoJSON y recibir los reportes ciudadanos.  
* Integrar el flujo de LangGraph dentro de los endpoints de Python para procesar las solicitudes de rutas de los usuarios.

**Desarrollador Senior 2 (Frontend \- Mobile First)**

* Construir la interfaz móvil centrada en un mapa interactivo (usando librerías como Leaflet o Mapbox).  
* Implementar la lógica de sincronización (Background Sync) para los reportes de bloqueos o demoras.  
  MD  
* *Pitch:* Junto con el Dev 1, liderar la demostración en vivo del prototipo funcional.  
  MD

## **4\. Cronograma de Ejecución (16 Horas)**

El evento exige el uso de equipos propios y la instalación previa de entornos de desarrollo.

MD

**Día 1: Datos, Backend y Prototipo UI (8 horas)**

* **09:00 \- 11:00:** Asistencia obligatoria al taller introductorio de agentes de Inteligencia Artificial.  
  MD  
* **11:00 \- 13:00:** El Analista exporta el GeoJSON. El Arquitecto levanta el esqueleto de la PWA. Los Devs inician los repositorios (Frontend y Backend).  
* **13:00 \- 17:00:** Integración del mapa base en el frontend. Desarrollo de los endpoints en Python para la ingesta de reportes y la conexión inicial del grafo de LangGraph.

**Día 2: Offline, Integración y Pitch (8 horas)**

* **08:00 \- 12:00:** Implementación de la lógica offline (Service Workers). Conexión del frontend con el agente LangGraph. Creación de datos simulados (mock data) de reportes ciudadanos para probar las respuestas del agente.  
* **12:00 \- 14:00:** Congelamiento de código. Despliegue en un servicio gratuito (Render, Vercel) y generación del código QR. Pruebas apagando los datos móviles para validar la caché.  
* **14:00 \- 16:00:** Preparación de los Entregables 1 (Prototipo/Flujo) y 2 (Pitch de 5 minutos). Ensayo cronometrado del pitch asegurando que los cuatro integrantes hablen.  
  MD+ 1

