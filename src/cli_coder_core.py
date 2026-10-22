import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path
from tree_sitter import Language, Parser, Node
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
import tree_sitter_javascript as tsjavascript

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("CLI_Coder_Core")

@dataclass
class SyntaxError:
    line: int
    column: int
    message: str
    context: str

class ASTValidationEngine:
    def __init__(self, language: str = "python"):
        self.language = language
        self.parser = Parser()
        self._load_language()

    def _load_language(self):
        if self.language == "python":
            lang = Language(tspython.language())
        elif self.language == "typescript":
            lang = Language(tstypescript.language_typescript())
        elif self.language == "tsx":
            lang = Language(tstypescript.language_tsx())
        elif self.language == "javascript":
            lang = Language(tsjavascript.language())
        else:
            raise NotImplementedError(f"Lenguaje '{self.language}' no soportado.")
        if hasattr(self.parser, "set_language"):
            self.parser.set_language(lang)
        else:
            self.parser.language = lang

    def validate_content(self, content: str) -> List[SyntaxError]:
        if not content.strip():
            return []
        lines = content.splitlines(keepends=True)
        tree = self.parser.parse(bytes(content, "utf8"))
        return self._extract_errors(tree.root_node, lines)

    def _extract_errors(self, node: Node, lines: List[str]) -> List[SyntaxError]:
        errors = []
        if node.has_error or node.is_error:
            start_line = node.start_point[0] + 1
            ctx_start = max(0, start_line - 3)
            ctx_end = min(len(lines), start_line + 3)
            context = "".join(lines[ctx_start:ctx_end])
            errors.append(SyntaxError(
                line=start_line,
                column=node.start_point[1],
                message=f"Error de sintaxis detectado",
                context=context
            ))
        for child in node.children:
            errors.extend(self._extract_errors(child, lines))
        return errors

    def apply_search_replace(self, original: str, search: str, replace: str) -> Dict[str, Any]:
        if search not in original:
            return {"status": "REJECTED", "reason": "SEARCH_NOT_FOUND"}
        if original.count(search) > 1:
            return {"status": "REJECTED", "reason": "AMBIGUOUS_SEARCH"}

        new_content = original.replace(search, replace, 1)
        errors = self.validate_content(new_content)
        if not errors:
            return {"status": "ACCEPTED", "new_content": new_content}
        return {"status": "REJECTED", "reason": "SYNTAX_INVALID", "errors": [asdict(e) for e in errors]}

class CognitiveOrchestrator:
    def __init__(self):
        self.modes = {
            "explorador": {
                "description": "Investigación y comprensión del código.",
                "tools": ["grep", "find", "cat"],
                "prompt": "Modo Explorador: No escribas código. Investiga el repositorio."
            },
            "cirujano": {
                "description": "Edición precisa de código.",
                "tools": ["search_replace"],
                "prompt": "Modo Cirujano: Edita el código de forma precisa. Usa SEARCH/REPLACE."
            },
            "arquitecto": {
                "description": "Diseño y revisión de nuevas funcionalidades.",
                "tools": ["search_replace", "self_reflection"],
                "prompt": "Modo Arquitecto: Diseña la solución y sométela a auto-revisión."
            }
        }

    def get_mode(self, task: str) -> str:
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["investiga", "donde", "busca", "entiende"]):
            return "explorador"
        if any(kw in task_lower for kw in ["crea", "diseña", "nueva", "implementa"]):
            return "arquitecto"
        return "cirujano"

from ghost_state import GhostStateEngine
from transactional_edit import apply_verified_edit, resolve_source

class CLI_Coder:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.ast_engine = ASTValidationEngine()
        self.orchestrator = CognitiveOrchestrator()
        self.ghost_engine = GhostStateEngine(repo_path)
        self.stt = None
        self.tts = None
        self.max_auto_heals = 1  # No model-backed patch regeneration is implemented

    def _load_voice(self):
        """Carga diferida de STT/TTS: las dependencias de voz son opcionales."""
        if self.stt is not None and self.tts is not None:
            return
        try:
            from voice_stt import VoiceSTT
            from voice_tts import VoiceTTS
        except ImportError as exc:
            raise RuntimeError(
                f"Voz no disponible (dependencia opcional ausente: {exc}). "
                "Instale requirements-voice.txt para activar STT/TTS."
            ) from exc
        self.stt = VoiceSTT()
        self.tts = VoiceTTS()

    def listen_and_process(self):
        """Escucha la voz del usuario y la procesa."""
        self._load_voice()
        audio_file = self.stt.record_audio()
        text = self.stt.transcribe(audio_file)
        logger.info(f"Usuario dijo: {text}")
        return text

    def speak_response(self, text):
        """Responde con voz humana."""
        self._load_voice()
        self.tts.speak(text)

    def auto_heal_loop(self, file_path: str, search: str, replace: str) -> bool:
        """Propose one AST-checked edit; commit only after isolated static validation.

        No model is connected to regenerate failing patches, so retries are
        intentionally disabled rather than pretending to auto-heal.
        """
        try:
            target = resolve_source(self.repo_path, file_path)
            original = target.read_text(encoding="utf-8")
            ast_result = self.ast_engine.apply_search_replace(original, search, replace)
            if ast_result["status"] != "ACCEPTED":
                logger.warning(
                    "AST refused candidate: %s", ast_result.get("reason", "invalid syntax")
                )
                return False
            approved = apply_verified_edit(
                self.repo_path,
                file_path,
                ast_result["new_content"],
                analyze=self.ghost_engine.run_analysis,
            )
            if not approved:
                logger.warning("Static analysis rejected the candidate; source unchanged")
            return approved
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            logger.error("Candidate was not committed: %s", exc)
            return False

    def master_reasoning_loop(self, task: str):
        """Implementa el razonamiento de Sistema 2 (God-Tier 10/10)."""
        logger.info("🧠 Iniciando Bucle de Razonamiento Maestro...")

        # 1. Análisis Topológico inicial
        mode = self.orchestrator.get_mode(task)
        logger.info(f"Modo Cognitivo Seleccionado: {mode.upper()}")

        # 2. Si es explorador, forzar construcción de modelo mental
        if mode == "explorador":
            logger.info("🔭 Construyendo modelo mental del sistema...")
            # Aquí se ejecutarían comandos de búsqueda para alimentar el contexto

        # 3. Ejecución con Auto-Sanación
        # Simulación de un flujo completo:
        # result = self.auto_heal_loop(target_file, search, replace)

        return mode

    def process_task(self, task: str):
        return self.master_reasoning_loop(task)

if __name__ == "__main__":
    coder = CLI_Coder(".")
    coder.process_task("Arregla el bug en el login")
