# Mimo CLI — Auditoría y Base de Reconstrucción

> **Estado:** auditoría técnica y prototipo de referencia. Este repositorio no declara ser una versión funcional, terminada o empaquetada para Windows de Mimo.

Este repositorio conserva el análisis, los requisitos y los módulos de prototipo relacionados con un CLI Coder para **Mimo**. Su propósito es servir como punto de partida verificable para reconstruir una integración real: edición transaccional mediante `SEARCH/REPLACE`, validación de sintaxis con AST, análisis estático, selección de contexto basada en dependencias, ejecución de pruebas y revisión adversarial.

## Qué incluye

| Ruta | Contenido |
|---|---|
| `src/` | Módulos de prototipo examinados durante la auditoría. |
| `docs/` | Requisitos extraídos del historial y auditoría técnica. |
| `tests/` | Prueba funcional de auditoría que expone dependencias y acoplamientos actuales. |
| `assets/` | Reservado para recursos no ejecutables. |
| `scripts/` | Automatización reproducible para crear una copia ZIP local. |

## Hallazgos principales

El prototipo actual contiene ideas útiles, pero no dispone de una integración real con la API o el CLI de Mimo. El grafo de dependencias no resuelve símbolos ni rutas, el bucle de auto-sanación no regenera parches usando un modelo, la TUI no está conectada con el núcleo y el empaquetado previo se hizo en Linux; por tanto, no produce un ejecutable válido para Windows 11.

Consulta [`docs/auditoria_mimo_actual.md`](docs/auditoria_mimo_actual.md) para las pruebas, hallazgos y prioridades, y [`docs/mimo_requisitos_extraidos.md`](docs/mimo_requisitos_extraidos.md) para la especificación funcional recuperada del chat.

## Requisitos para inspeccionar el prototipo

Se recomienda Python 3.11 o superior. El prototipo tiene dependencias opcionales que aún deben desacoplarse para ser instalable de manera fiable:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-prototype.txt
python -m compileall -q src
```

> No se incluyen claves de API. Las configuraciones futuras deben usar variables de entorno y un archivo `.env.example`, nunca secretos versionados.

## Pruebas disponibles

```bash
python tests/audit_functional.py
python tests/test_core_sin_voz.py
```

`audit_functional.py` valida la edición transaccional con AST y la selección de modo
cognitivo. `test_core_sin_voz.py` comprueba que el núcleo se importa e instancia sin
las dependencias opcionales de voz (carga diferida): si STT/TTS no están instalados,
`listen_and_process`/`speak_response` fallan con un `RuntimeError` explicativo en lugar
de romper la importación del módulo. Las dependencias de voz siguen siendo necesarias
para usar esas dos funciones.

## Ruta de reconstrucción recomendada

Primero, integrar el repositorio o API real de Mimo. Después, implementar adaptadores de modelo y herramientas tipadas, edición transaccional, validaciones, pruebas TDD y revisión adversarial. Solo tras pruebas de integración y un pipeline de CI de Windows debe generarse una distribución de Windows.

## Copia de seguridad local

```bash
python scripts/create_backup.py
```

El script genera un ZIP con fecha en el directorio superior, excluyendo entornos virtuales, cachés, registros, archivos temporales y secretos.

## Licencia

No se ha seleccionado una licencia. Antes de distribuir o reutilizar el código, el propietario debe decidir la licencia aplicable y comprobar la compatibilidad de las dependencias.
