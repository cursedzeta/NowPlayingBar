# main.py
# -------------------------------------
# Punto de entrada del programa (con auto-inicio opcional en Windows)
# -------------------------------------

import sys
import platform
from PySide6 import QtWidgets

from spotify_client import get_spotify_client
from overlay_ui import Overlay

# Autostart opcional (solo Windows)
try:
    from autostart import is_registered_in_startup, register_startup
except Exception:
    # En otros SO o si faltan dependencias, simplemente no se usa auto-start
    is_registered_in_startup = lambda: False  # type: ignore
    def register_startup():  # type: ignore
        raise NotImplementedError("Auto-start no disponible en este sistema.")

def _maybe_prompt_autostart(parent=None):
    """Pregunta 1 sola vez si querés agregar al inicio (solo Windows)."""
    if platform.system().lower() != "windows":
        return
    try:
        if not is_registered_in_startup():
            resp = QtWidgets.QMessageBox.question(
                parent,
                "Inicio automático",
                "¿Querés que NowPlayingOverlay se inicie automáticamente al prender tu PC?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if resp == QtWidgets.QMessageBox.Yes:
                register_startup()
                QtWidgets.QMessageBox.information(parent, "Inicio automático", "Listo: se iniciará con Windows.")
    except Exception as e:
        # No rompemos el flujo por un fallo del registro
        QtWidgets.QMessageBox.warning(parent, "Inicio automático", f"No se pudo configurar el inicio:\n{e}")

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Pregunta de auto-inicio (Windows)
    _maybe_prompt_autostart()

    sp = get_spotify_client()
    w = Overlay(sp)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
