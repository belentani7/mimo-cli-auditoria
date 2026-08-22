import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cli_coder_core import ASTValidationEngine, CLI_Coder


def main() -> None:
    validator = ASTValidationEngine("python")
    source = "def f(x):\n    return x + 1\n"
    accepted = validator.apply_search_replace(source, "return x + 1", "return x + 2")
    rejected = validator.apply_search_replace(source, "return x + 1", "return (")

    assert accepted["status"] == "ACCEPTED", accepted
    assert rejected["status"] == "REJECTED", rejected

    agent = CLI_Coder(".")
    mode = agent.process_task("Investiga dónde se utiliza la función f")
    assert mode == "explorador", mode
    print("AUDIT_AST=PASS")
    print("AUDIT_MODE=PASS")


if __name__ == "__main__":
    main()
