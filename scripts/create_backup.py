"""Crea un ZIP de respaldo del proyecto excluyendo secretos y artefactos locales."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT.parent
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
ARCHIVE_PATH = OUTPUT_DIR / f"Proyecto_Mimo_CLI_Auditoria_Backup_{TIMESTAMP}.zip"

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".pyright", "build", "dist", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".wav", ".mp3", ".ogg", ".exe", ".msi"}
EXCLUDED_FILENAMES = {".env", "mimo_debug.log"}


def should_include(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in EXCLUDED_FILENAMES:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def main() -> None:
    with ZipFile(ARCHIVE_PATH, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(PROJECT_ROOT.rglob("*")):
            if should_include(path):
                archive.write(path, arcname=Path(PROJECT_ROOT.name) / path.relative_to(PROJECT_ROOT))
    print(ARCHIVE_PATH)


if __name__ == "__main__":
    main()
