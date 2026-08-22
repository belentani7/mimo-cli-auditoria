import subprocess
import os
from pathlib import Path
from typing import Dict, Any

class TestRunner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def detect_framework(self) -> str:
        """Detecta el framework de pruebas basado en archivos del proyecto."""
        if (self.project_root / "pytest.ini").exists() or any(self.project_root.rglob("test_*.py")):
            return "pytest"
        if (self.project_root / "package.json").exists():
            content = (self.project_root / "package.json").read_text()
            if "jest" in content:
                return "jest"
            if "mocha" in content:
                return "mocha"
        return "generic"

    def run_tests(self) -> Dict[str, Any]:
        """Ejecuta las pruebas y devuelve el resultado estructurado."""
        framework = self.detect_framework()
        cmd = []

        if framework == "pytest":
            cmd = ["pytest", "--json-report", "--json-report-file=report.json"]
        elif framework == "jest":
            cmd = ["npm", "test", "--", "--json"]
        else:
            # Intento genérico
            cmd = ["python3", "-m", "unittest", "discover"]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return {
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": str(e)
            }

if __name__ == "__main__":
    tr = TestRunner(".")
    print(f"Framework detectado: {tr.detect_framework()}")
