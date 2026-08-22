import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("GitManager")

class GitManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def _run_git(self, args: list) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando git {' '.join(args)}: {e.stderr}")
            raise

    def is_repo(self) -> bool:
        try:
            self._run_git(["rev-parse", "--is-inside-work-tree"])
            return True
        except Exception:
            return False

    def create_branch(self, branch_name: str):
        logger.info(f"Creando rama: {branch_name}")
        self._run_git(["checkout", "-b", branch_name])

    def commit(self, message: str):
        logger.info(f"Haciendo commit: {message}")
        self._run_git(["add", "."])
        self._run_git(["commit", "-m", message])

    def rollback(self):
        logger.warning("Revirtiendo cambios...")
        self._run_git(["reset", "--hard", "HEAD~1"])

    def get_diff(self) -> str:
        return self._run_git(["diff", "HEAD"])

if __name__ == "__main__":
    gm = GitManager(".")
    if gm.is_repo():
        print("Es un repositorio Git.")
    else:
        print("No es un repositorio Git.")
