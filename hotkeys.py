# hotkeys.py
# Atajos GLOBALS usando RegisterHotKey (Win32) + nativeEventFilter de Qt

from PySide6 import QtCore, QtWidgets
import ctypes
from ctypes import wintypes

# IDs "públicos" que usa overlay_ui.py
HK_TOGGLE   = 1
HK_PREV     = 2
HK_NEXT     = 3
HK_VOL_UP   = 4   # definidos por compatibilidad, no usados ahora
HK_VOL_DOWN = 5

# --- Win32 constants ---
WM_HOTKEY    = 0x0312
MOD_ALT      = 0x0001
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008

VK_SPACE     = 0x20
VK_LEFT      = 0x25
VK_RIGHT     = 0x27
# (Si querés otros, agregá VK_* que necesites)

# Win32 APIs
user32 = ctypes.windll.user32
RegisterHotKey   = user32.RegisterHotKey
UnregisterHotKey = user32.UnregisterHotKey

# MSG struct (para leer el mensaje nativo)
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    wintypes.DWORD),
        ("pt",      wintypes.POINT),
    ]

class _HotkeyEventFilter(QtCore.QAbstractNativeEventFilter):
    """Intercepta mensajes nativos de Windows y captura WM_HOTKEY."""
    def __init__(self, handler):
        super().__init__()
        self._handler = handler

    def nativeEventFilter(self, eventType, message):
        # En PySide6, eventType para Windows es 'windows_generic_MSG'
        if eventType != 'windows_generic_MSG':
            return False, 0

        try:
            # Convertir sip.voidptr -> int (dirección de memoria real)
            msg_addr = int(message)  
            msg = MSG.from_address(msg_addr)
        except Exception:
            return False, 0

        if msg.message == WM_HOTKEY:
            hk_id = int(msg.wParam)
            try:
                self._handler(hk_id)
            except Exception:
                pass
            return True, 0
        return False, 0


class _GlobalHotkeys:
    """Registrar/limpiar hotkeys con Win32 y enrutar a handler(hk_id)."""
    def __init__(self, handler):
        self._handler = handler
        self._filter = _HotkeyEventFilter(handler)
        self._registered = []

    def start(self):
        app = QtWidgets.QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication no inicializada")

        QtWidgets.QApplication.instance().installNativeEventFilter(self._filter)

        MOD_CTRL_ALT = MOD_CONTROL | MOD_ALT

        # Atajos existentes
        self._reg(HK_TOGGLE,  MOD_CTRL_ALT, VK_SPACE)
        self._reg(HK_PREV,    MOD_CTRL_ALT, VK_LEFT)
        self._reg(HK_NEXT,    MOD_CTRL_ALT, VK_RIGHT)

        # 🔊 Nuevos: Ctrl + Up / Ctrl + Down
        VK_UP   = 0x26
        VK_DOWN = 0x28
        self._reg(HK_VOL_UP,   MOD_CTRL_ALT, VK_UP)
        self._reg(HK_VOL_DOWN, MOD_CTRL_ALT, VK_DOWN)


    def stop(self):
        # Desregistrar hotkeys
        for (hk_id, _mod, _vk) in self._registered:
            try:
                UnregisterHotKey(None, hk_id)
            except Exception:
                pass
        self._registered.clear()

        # Quitar filtro nativo
        app = QtWidgets.QApplication.instance()
        if app and self._filter:
            try:
                app.removeNativeEventFilter(self._filter)
            except Exception:
                pass
        self._filter = None

    def _reg(self, hk_id, modifiers, vk):
        # Si ya existía, desregistra primero por seguridad
        try:
            UnregisterHotKey(None, hk_id)
        except Exception:
            pass
        ok = RegisterHotKey(None, hk_id, modifiers, vk)
        if not ok:
            # Si falla (p.ej. conflicto con otro programa), probá otra combinación
            # o agregá MOD_ALT: modifiers |= MOD_ALT
            # No levantamos excepción para no romper la app, pero podrías loguear.
            pass
        self._registered.append((hk_id, modifiers, vk))

def register_hotkeys(widget, handler):
    """Mantiene la misma interfaz que usabas: devuelve un objeto para cleanup."""
    gh = _GlobalHotkeys(handler)
    gh.start()
    widget._global_hotkeys = gh
    return gh

def unregister_hotkeys(widget):
    gh = getattr(widget, '_global_hotkeys', None)
    if gh:
        gh.stop()
        widget._global_hotkeys = None
