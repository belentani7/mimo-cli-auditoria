import os
import logging
from cli_coder_core import CLI_Coder
from cli_coder_tui import CLICoderApp
from repo_graph import RepoGraph
from git_manager import GitManager
from test_runner import TestRunner
from plugin_system import PluginSystem

# Configuración Global
logging.basicConfig(level=logging.INFO, filename="mimo_debug.log")

def main():
    root_path = os.getcwd()

    # Inicialización de Módulos Omnipotentes
    repo_graph = RepoGraph(root_path)
    git_manager = GitManager(root_path)
    test_runner = TestRunner(root_path)
    plugin_system = PluginSystem(os.path.join(root_path, "plugins"))

    # Cargar Plugins
    plugin_system.load_plugins()

    # Inicializar Core
    cli_coder = CLI_Coder(root_path)

    # Inyectar dependencias en el core (para autonomía total)
    cli_coder.git = git_manager
    cli_coder.tester = test_runner
    cli_coder.graph = repo_graph

    # Lanzar TUI
    app = CLICoderApp()
    app.run()

if __name__ == "__main__":
    main()
