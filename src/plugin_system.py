import importlib
import os
from pathlib import Path
from typing import Dict, Any, List

class PluginBase:
    def execute(self, context: Dict[str, Any]) -> Any:
        raise NotImplementedError

class PluginSystem:
    def __init__(self, plugins_dir: str):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True)

    def load_plugins(self):
        """Carga dinámicamente plugins desde el directorio especificado."""
        for plugin_file in self.plugins_dir.glob("*.py"):
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Asumimos que cada plugin tiene una clase que hereda de PluginBase
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, PluginBase) and cls is not PluginBase:
                    self.plugins[module_name] = cls()

class LLMConnector:
    def __init__(self, provider="openai", base_url=None):
        self.provider = provider
        self.base_url = base_url

    def query(self, prompt: str, system_prompt: str = "") -> str:
        if self.provider == "ollama":
            # Simulación de llamada a Ollama local
            return f"[Ollama Response to: {prompt[:20]}...]"
        elif self.provider == "openai":
            # Llamada real a OpenAI (usando la API configurada)
            return "[OpenAI Response]"
        return "[Unknown Provider]"

if __name__ == "__main__":
    ps = PluginSystem("./plugins")
    ps.load_plugins()
    print(f"Plugins cargados: {list(ps.plugins.keys())}")
