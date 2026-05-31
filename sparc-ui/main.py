import sys
import os
import importlib.util

_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_BASE, "..", "sparc-core", "core"))
sys.path.insert(0, os.path.join(_BASE, "..", "sparc-core"))

# Carrega gui_adapter diretamente pelo caminho para evitar colisão
# de nomes entre sparc-ui/adapters/ e sparc-core/adapters/
_spec = importlib.util.spec_from_file_location(
    "gui_adapter",
    os.path.join(_BASE, "adapters", "gui_adapter.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MainWindow = _mod.MainWindow

from PyQt6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
