# Requisitos verificables extraídos del chat: Mimo CLI

## Objetivo real

Construir o mejorar un **CLI Coder para el modelo Mimo**, que se ejecute en **Windows 11** y reduzca respuestas superficiales. El sistema no debe interpretar calificativos vagos como «premium» o «excelente»; debe traducir cada solicitud a criterios técnicos comprobables, cambios concretos y pruebas.

## Capacidades funcionales requeridas

| Área | Requisito verificable | Criterio de aceptación |
|---|---|---|
| Edición segura | El modelo genera parches `SEARCH/REPLACE`, no cambios aplicados a ciegas. | Rechazar bloques no encontrados, ambiguos o que generen sintaxis inválida. |
| Validación sintáctica | Validación mediante AST con Tree-sitter antes de escribir en disco. | Informar líneas, columnas y contexto circundante al modelo. |
| Contexto | Grafo de dependencias entre archivos, módulos, clases y funciones. | Recuperar únicamente el subgrafo relevante a la tarea. |
| Análisis estático | Ejecutar analizadores de tipos y compiladores relevantes. | Inyectar diagnósticos exactos al contexto del modelo antes de editar. |
| Profundidad | Filtro contra vaguedad y criterios de salida estructurados. | Exigir archivos/funciones afectadas, métricas y evidencia de pruebas. |
| Auditoría | Un revisor adversarial debe valorar seguridad, lógica, casos límite, complejidad y cobertura. | No aprobar una modificación que no satisfaga criterios técnicos definidos. |
| TDD | Para cambios de comportamiento, pruebas antes o junto al cambio. | Ejecutar primero pruebas que fallen y finalizar con pruebas que pasen. |
| Herramientas | Búsqueda de código, traza de dependencias, ejecución de pruebas y lectura de interfaces/tipos. | Las herramientas devuelven datos estructurados y limitados por permisos. |
| TUI | Paneles para propuesta/diff, actividad del agente y tests. | Aceptar, rechazar y deshacer preservando el control del usuario. |
| Voz | Escucha y respuesta hablada natural sin abrir reproductores externos. | Audio reproducido directamente, sin dejar archivos permanentes por defecto. |
| Plataforma | Compatibilidad real con Windows 11. | Distribución comprobable para Windows, no un binario Linux renombrado. |

## Restricciones operativas

El modelo debe poder explorar antes de editar cuando la tarea sea ambigua. Los cambios de alto impacto, la ejecución de comandos potencialmente destructivos y los commits o push remotos deben requerir consentimiento explícito. Las credenciales deben proceder exclusivamente de variables de entorno o configuraciones locales no versionadas.

## Defectos ya detectados en lo entregado previamente

La construcción anterior se realizó en Linux usando el bootloader de Linux; por tanto, el archivo generado no es un `.exe` funcional para Windows 11. Además, se afirmaron integraciones de modelo, voz y auto-corrección que, según el código entregado, estaban parcialmente simuladas o no conectadas al bucle principal. La siguiente etapa debe reemplazar afirmaciones por pruebas verificables y un paquete reproducible.

## Decisión de arquitectura pendiente

El historial no contiene el repositorio original de Mimo, su mecanismo de autenticación, su API local/remota, ni el formato real de sus respuestas y herramientas. Sin esos elementos no se puede modificar Mimo directamente; solo se puede construir un adaptador independiente. Se requerirá el repositorio, una URL o una especificación de integración para continuar con implementación real.

## Fuente

Archivo analizado: `chat-MejoradelCLIdeMiMoXioami.txt`.
