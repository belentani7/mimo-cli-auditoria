import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("GitManager")


class GitManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as error:
            logger.error("Error ejecutando git %s: %s", " ".join(args), error.stderr)
            raise

    def is_repo(self) -> bool:
        try:
            self._run_git(["rev-parse", "--is-inside-work-tree"])
            return True
        except (OSError, subprocess.CalledProcessError):
            return False

    def create_branch(self, branch_name: str) -> None:
        if not branch_name or branch_name.startswith("-"):
            raise ValueError("El nombre de rama no es válido")
        self._run_git(["check-ref-format", "--branch", branch_name])
        logger.info("Creando rama: %s", branch_name)
        self._run_git(["checkout", "-b", branch_name])

    def _validated_paths(self, paths: list[str] | None) -> list[str]:
        if not paths:
            raise ValueError("Indique explícitamente las rutas que se incluirán en el commit")

        root = self.repo_path.resolve()
        validated: list[str] = []
        for raw_path in paths:
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise ValueError("Cada ruta debe ser una cadena no vacía")
            candidate = Path(raw_path)
            if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts or ".git" in candidate.parts:
                raise ValueError(f"Ruta no permitida: {raw_path}")
            if not (root / candidate).resolve().is_relative_to(root):
                raise ValueError(f"La ruta sale del repositorio: {raw_path}")
            normalized = candidate.as_posix()
            if normalized not in validated:
                validated.append(normalized)
        return validated

    def commit(self, message: str, paths: list[str] | None = None) -> None:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("El mensaje del commit no puede estar vacío")
        selected_paths = self._validated_paths(paths)
        logger.info("Creando commit con %d rutas seleccionadas", len(selected_paths))
        self._run_git(["--literal-pathspecs", "add", "--", *selected_paths])
        # Only selected paths: an unrelated file could already be staged in the index.
        self._run_git(["--literal-pathspecs", "commit", "--only", "-m", message, "--", *selected_paths])

    def rollback(self, *, confirm: bool = False) -> None:
        if not confirm:
            raise PermissionError("La reversión requiere confirm=True y crea un commit git revert")
        if self._run_git(["status", "--porcelain"]):
            raise RuntimeError("Debe guardar o limpiar sus cambios antes de revertir un commit")
        logger.warning("Revirtiendo el último commit mediante git revert")
        self._run_git(["revert", "--no-edit", "HEAD"])

    def get_diff(self) -> str:
        return self._run_git(["diff", "HEAD"])


if __name__ == "__main__":
    gm = GitManager(".")
    if gm.is_repo():
        print("Es un repositorio Git.")
    else:
        print("No es un repositorio Git.")
