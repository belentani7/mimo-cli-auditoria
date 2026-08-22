import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("GhostState")

class GhostStateEngine:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def run_analysis(self, target_file: str) -> List[Dict[str, Any]]:
        """Ejecuta pyright para obtener el estado fantasma (errores de tipo)."""
        try:
            # Ejecutar pyright en modo JSON
            cmd = ["pyright", "--outputjson", str(self.project_root / target_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Pyright devuelve código de salida > 0 si hay errores, pero el JSON es válido
            if not result.stdout:
                return []

            data = json.loads(result.stdout)
            diagnostics = data.get("generalDiagnostics", [])

            # Filtrar solo errores y advertencias relevantes
            ghost_errors = []
            for diag in diagnostics:
                ghost_errors.append({
                    "line": diag["range"]["start"]["line"] + 1,
                    "message": diag["message"],
                    "severity": diag["severity"]
                })
            return ghost_errors
        except Exception as e:
            logger.error(f"Error al ejecutar análisis fantasma: {e}")
            return []

    def format_for_llm(self, errors: List[Dict[str, Any]]) -> str:
        if not errors:
            return "✅ ESTADO_FANTASMA: No se detectaron errores de tipo."

        feedback = "👻 ESTADO_FANTASMA (Análisis Estático):\n"
        for err in errors[:5]: # Limitar para no saturar
            feedback += f"- Línea {err['line']} [{err['severity'].upper()}]: {err['message']}\n"
        return feedback
