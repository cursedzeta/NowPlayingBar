# autostart.py
# -------------------------------------
# Registro en inicio de Windows (HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
# -------------------------------------

import os
import sys
import platform
from pathlib import Path

APP_NAME = "NowPlayingOverlay"

def _ensure_windows():
    if platform.system().lower() != "windows":
        raise NotImplementedError("Auto-start solo está implementado para Windows.")

def _pythonw_executable() -> str:
    """
    Devuelve pythonw.exe si existe junto a sys.executable (mejor para ocultar consola),
    si no existe, devuelve sys.executable.
    """
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    return str(pyw) if pyw.exists() else str(exe)

def _entry_script_path() -> str:
    """
    Ruta absoluta a main.py (punto de entrada del proyecto).
    Asume estructura propuesta, estando este archivo en el mismo directorio que main.py.
    """
    # Si este archivo está en el mismo directorio que main.py:
    here = Path(__file__).resolve().parent
    candidate = here / "main.py"
    if candidate.exists():
        return str(candidate)

    # Fallback: si está en un paquete/estructura distinta, intentamos relativo a cwd
    candidate = Path.cwd() / "main.py"
    if candidate.exists():
        return str(candidate)

    # Último recurso: usa __file__ (no ideal pero evita romper)
    return str(Path(__file__).resolve())

def build_run_command() -> str:
    """
    Construye el comando que irá al registro:
    "C:\Path\to\pythonw.exe" "C:\path\to\main.py"
    """
    exe = _pythonw_executable()
    entry = _entry_script_path()
    return f"\"{exe}\" \"{entry}\""

def register_startup() -> None:
    """Agrega el programa al inicio de Windows."""
    _ensure_windows()
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    cmd = build_run_command()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)

def unregister_startup() -> bool:
    """Elimina el programa del inicio. Devuelve True si lo quitó, False si no estaba."""
    _ensure_windows()
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False

def is_registered_in_startup() -> bool:
    """Verifica si el programa ya está en el inicio."""
    _ensure_windows()
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
        # Comparamos normalizando (por si cambia python/pythonw o separadores)
        expected = build_run_command()
        return os.path.normcase(val) == os.path.normcase(expected)
    except FileNotFoundError:
        return False
    except OSError:
        return False
