import os
from pathlib import Path
from typing import Dict, List, Set
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
import tree_sitter_javascript as tsjavascript

class RepoGraph:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.graph: Dict[str, Set[str]] = {}
        self.parser = Parser()
        self.languages = {
            ".py": Language(tspython.language()),
            ".ts": Language(tstypescript.language_typescript()),
            ".tsx": Language(tstypescript.language_tsx()),
            ".js": Language(tsjavascript.language()),
            ".jsx": Language(tsjavascript.language())
        }

    def index(self):
        """Indexa el repositorio usando tree-sitter para múltiples lenguajes."""
        for ext in self.languages.keys():
            for file_path in self.root_dir.rglob(f"*{ext}"):
                relative_path = str(file_path.relative_to(self.root_dir))
                lang = self.languages[ext]
                self.parser.set_language(lang)
                self.graph[relative_path] = self._extract_entities(file_path, lang)

    def _extract_entities(self, file_path: Path, lang: Language) -> Set[str]:
        entities = set()
        try:
            content = file_path.read_bytes()
            tree = self.parser.parse(content)

            # Query para encontrar funciones, clases e importaciones
            # Nota: Esto es una simplificación, en producción se usarían queries SCM más complejas
            root = tree.root_node
            self._traverse_node(root, entities)
        except Exception:
            pass
        return entities

    def _traverse_node(self, node, entities):
        # Captura básica de nombres de funciones y clases basada en tipos de nodos comunes
        node_type = node.type
        if "function" in node_type or "class" in node_type:
            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf-8")
                    prefix = "func:" if "function" in node_type else "class:"
                    entities.add(f"{prefix}{name}")

        # Captura de importaciones (simplificado)
        if "import" in node_type:
            entities.add(f"import:{node.text.decode('utf-8')[:50]}")

        for child in node.children:
            self._traverse_node(child, entities)

    def get_dependencies(self, file_path: str) -> List[str]:
        return list(self.graph.get(file_path, set()))

if __name__ == "__main__":
    rg = RepoGraph(".")
    rg.index()
    print(f"Archivos indexados: {list(rg.graph.keys())}")
