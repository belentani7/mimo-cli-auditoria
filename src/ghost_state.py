"""Fail-closed Pyright adapter for a locally authorized repository."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class GhostStateEngine:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def run_analysis(self, target_file: str) -> list[dict[str, Any]]:
        target = (self.project_root / target_file).resolve()
        if not target.is_relative_to(self.project_root) or not target.is_file():
            raise ValueError("Target for static analysis must be a file inside the repository")
        try:
            result = subprocess.run(
                ["pyright", "--outputjson", str(target)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("Pyright did not execute; static validation cannot be assumed successful") from exc

        if result.returncode not in (0, 1) or not result.stdout.strip():
            raise RuntimeError("Pyright failed without parseable diagnostics; file must not be committed")
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("Pyright did not return valid JSON diagnostics") from exc
        if not isinstance(data, dict) or not isinstance(data.get("generalDiagnostics"), list):
            raise RuntimeError("Pyright output did not include generalDiagnostics")
        diagnostics = []
        for item in data["generalDiagnostics"]:
            if not isinstance(item, dict):
                raise RuntimeError("Malformed Pyright diagnostic")
            position = item.get("range", {}).get("start", {}).get("line", 0)
            diagnostics.append({
                "line": position + 1,
                "message": str(item.get("message", "Unknown static analysis issue")),
                "severity": str(item.get("severity", "error")),
            })
        return diagnostics

    def format_for_llm(self, errors: list[dict[str, Any]]) -> str:
        if not errors:
            return "ESTADO_FANTASMA: No se detectaron errores de tipo."
        feedback = "ESTADO_FANTASMA (Análisis Estático):\n"
        for error in errors[:5]:
            feedback += f"- Línea {error['line']} [{error['severity'].upper()}]: {error['message']}\n"
        return feedback
