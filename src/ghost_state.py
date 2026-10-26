"""Fail-closed Pyright adapter for a locally authorized repository."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from transactional_edit import resolve_source


class GhostStateEngine:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def run_analysis(self, target_file: str) -> list[dict[str, Any]]:
        target = resolve_source(self.project_root, target_file)
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
        if result.returncode != 0 and not data["generalDiagnostics"]:
            raise RuntimeError("Pyright exited with errors but provided no diagnostics; cannot approve edit")
        summary = data.get("summary")
        if isinstance(summary, dict):
            if summary.get("errorCount", 0) and not data["generalDiagnostics"]:
                raise RuntimeError("Pyright reported errors without diagnostics; cannot approve edit")
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
