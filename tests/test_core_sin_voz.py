import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_importa_nucleo_sin_dependencias_de_voz():
    import cli_coder_core

    assert hasattr(cli_coder_core, "ASTValidationEngine")
    assert hasattr(cli_coder_core, "CLI_Coder")


def test_instancia_cli_sin_voz_disponible():
    from cli_coder_core import CLI_Coder

    agent = CLI_Coder(".")
    assert agent.stt is None
    assert agent.tts is None


def test_uso_de_voz_sin_dependencias_da_error_claro():
    from cli_coder_core import CLI_Coder

    agent = CLI_Coder(".")
    try:
        agent.listen_and_process()
    except RuntimeError as exc:
        assert "pyaudio" in str(exc).lower() or "voz" in str(exc).lower()
    else:
        raise AssertionError("listen_and_process debio fallar con voz no disponible")


if __name__ == "__main__":
    test_importa_nucleo_sin_dependencias_de_voz()
    test_instancia_cli_sin_voz_disponible()
    test_uso_de_voz_sin_dependencias_da_error_claro()
    print("TEST_LAZY_VOICE=PASS")
