# nowPlayingOverlay.py
# Overlay minimalista "Now Playing" (hotkeys globales + auto-inicio opcional + menú contextual + doble-click)

import sys, os, time, threading, webbrowser, ctypes
from pathlib import Path
from ctypes import wintypes

from PySide6 import QtCore, QtGui, QtWidgets
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Configuración Spotify ---
SCOPE = "user-read-currently-playing user-read-playback-state user-modify-playback-state"
CACHE_PATH = str(Path.home() / ".cache-spotipy-nowplaying")
CLIENT_ID  = "08e638372b3d4dfd91759e9a2fd5dc59"
CLIENT_SEC = "12bc8bd5b998465fbdca85c3030cf961"
REDIRECT   = "http://127.0.0.1:8888/callback"

# --- UI / Layout ---
POLL_SECONDS = 4
MARQUEE_SPEED_MS = 35
PADDING_X = 10
PADDING_Y = 5

WIDTH  = 320
HEIGHT = 34
TASKBAR_GAP_PX = 2
MARGIN_RIGHT = 12

# --- Hotkeys globales ---
WM_HOTKEY   = 0x0312
MOD_ALT     = 0x0001
MOD_CONTROL = 0x0002
VK_SPACE    = 0x20
VK_LEFT     = 0x25
VK_RIGHT    = 0x27
HK_TOGGLE = 1
HK_PREV   = 2
HK_NEXT   = 3
user32 = ctypes.windll.user32

# --- Registro de inicio automático (Windows) ---
def register_startup():
    """Agrega el script al inicio de Windows (HKCU\...\Run)."""
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
    exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    winreg.SetValueEx(key, "NowPlayingOverlay", 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)

def unregister_startup():
    """Quita el script del inicio de Windows."""
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "NowPlayingOverlay")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def is_registered_in_startup():
    """Verifica si el script ya está en el inicio."""
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "NowPlayingOverlay")
        winreg.CloseKey(key)
        # Comparamos por el path del archivo (dentro del valor que incluye python.exe "script")
        return os.path.abspath(__file__) in val
    except FileNotFoundError:
        return False
    except Exception:
        return False

# --------- Íconos dibujados ----------
def _base_icon(size):
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing, True)
    p.setPen(QtCore.Qt.NoPen)
    p.setBrush(QtGui.QColor(255, 255, 255))
    return pm, p

def icon_play(size=16):
    pm, p = _base_icon(size)
    w = h = size
    path = QtGui.QPainterPath()
    path.moveTo(w*0.30, h*0.20)
    path.lineTo(w*0.30, h*0.80)
    path.lineTo(w*0.78, h*0.50)
    path.closeSubpath()
    p.drawPath(path); p.end()
    return QtGui.QIcon(pm)

def icon_pause(size=16):
    pm, p = _base_icon(size)
    w = h = size
    barw = w*0.24
    gap  = w*0.10
    r1 = QtCore.QRectF(w*0.22, h*0.18, barw, h*0.64)
    r2 = QtCore.QRectF(w*0.22+barw+gap, h*0.18, barw, h*0.64)
    p.drawRoundedRect(r1, 1.5, 1.5)
    p.drawRoundedRect(r2, 1.5, 1.5)
    p.end()
    return QtGui.QIcon(pm)

def icon_next(size=16):
    pm, p = _base_icon(size)
    w = h = size
    path = QtGui.QPainterPath()
    path.moveTo(w*0.18, h*0.20)
    path.lineTo(w*0.18, h*0.80)
    path.lineTo(w*0.64, h*0.50)
    path.closeSubpath()
    p.drawPath(path)
    r = QtCore.QRectF(w*0.70, h*0.18, w*0.12, h*0.64)
    p.drawRoundedRect(r, 1.5, 1.5)
    p.end()
    return QtGui.QIcon(pm)

def icon_prev(size=16):
    pm, p = _base_icon(size)
    w = h = size
    path = QtGui.QPainterPath()
    path.moveTo(w*0.82, h*0.20)
    path.lineTo(w*0.82, h*0.80)
    path.lineTo(w*0.36, h*0.50)
    path.closeSubpath()
    p.drawPath(path)
    r = QtCore.QRectF(w*0.18, h*0.18, w*0.12, h*0.64)
    p.drawRoundedRect(r, 1.5, 1.5)
    p.end()
    return QtGui.QIcon(pm)

# --------- Texto deslizante ----------
class MarqueeLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.setStyleSheet("color: white; font-size: 11px;")
        self.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

    def start(self): self.timer.start(MARQUEE_SPEED_MS)
    def reset_scroll(self): self.offset = 0; self.update()

    def tick(self):
        self.offset += 1
        if self.offset > self.fontMetrics().horizontalAdvance(self.text()) + 30:
            self.offset = 0
        self.update()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        txt = self.text()
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(txt)
        h = self.height()
        x = -self.offset
        while x < self.width():
            p.drawText(x, 0, max(w + 30, self.width()), h,
                       QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, txt)
            x += w + 30

# -------------- Overlay principal --------------
class Overlay(QtWidgets.QWidget):
    newText  = QtCore.Signal(str)
    newProg  = QtCore.Signal(int)
    newState = QtCore.Signal(bool)

    def __init__(self, sp: spotipy.Spotify):
        super().__init__()
        self.sp = sp
        self.playing = False
        self._hotkeys_registered = False

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Fondo
        self.bg = QtWidgets.QFrame()
        self.bg.setStyleSheet("QFrame { background: rgba(0,0,0,1); border-radius: 9px; }")

        # Botones
        self.btnPrev = QtWidgets.QToolButton(); self.btnPrev.setIcon(icon_prev())
        self.btnPlay = QtWidgets.QToolButton(); self.btnPlay.setIcon(icon_play())
        self.btnNext = QtWidgets.QToolButton(); self.btnNext.setIcon(icon_next())
        for b in (self.btnPrev, self.btnPlay, self.btnNext):
            b.setAutoRaise(True)
            b.setCursor(QtCore.Qt.PointingHandCursor)
            b.setIconSize(QtCore.QSize(16,16))
            b.setFixedSize(24, 24)
            b.setStyleSheet("QToolButton:hover { background: rgba(255,255,255,0.10); border-radius: 6px; }")

        # Texto
        self.label = MarqueeLabel("…")
        self.label.setMinimumWidth(150)

        # Progreso
        self.progress = QtWidgets.QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1000)
        self.progress.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,25); border: none; }"
            "QProgressBar::chunk { background: #1DB954; }"
        )

        # Layout
        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(PADDING_X, PADDING_Y, PADDING_X, 4)
        top.setSpacing(6)
        top.addWidget(self.btnPrev)
        top.addWidget(self.btnPlay)
        top.addWidget(self.btnNext)
        top.addSpacing(4)
        top.addWidget(self.label, 1)

        v = QtWidgets.QVBoxLayout(self.bg)
        v.setContentsMargins(0, 0, 0, 0)
        v.addLayout(top)
        v.addWidget(self.progress)

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.bg)

        # Tamaño/posición
        self.setFixedSize(WIDTH, HEIGHT)
        self.position_bottom_right()

        # => Doble click: abrir Spotify
        self.bg.mouseDoubleClickEvent = self._on_double_click

        # => Menú contextual (clic derecho)
        self.bg.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.bg.customContextMenuRequested.connect(self.show_menu)

        # Acciones
        self.btnPrev.clicked.connect(self.on_prev)
        self.btnPlay.clicked.connect(self.on_toggle)
        self.btnNext.clicked.connect(self.on_next)

        self.newText.connect(self.set_text)
        self.newProg.connect(self.progress.setValue)
        self.newState.connect(self.set_playing)

        self.worker = threading.Thread(target=self.loop_spotify, daemon=True)
        self.worker.start()
        self.label.start()

        self.smooth = QtCore.QTimer(self)
        self.smooth.setInterval(200)
        self.smooth.timeout.connect(self._tick_progress_local)
        self._progress_local = 0
        self.smooth.start()

        QtCore.QTimer.singleShot(0, self._register_hotkeys)

    # -------- Posicionamiento --------
    def position_bottom_right(self):
        screen = QtGui.QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        x = avail.right() - self.width() - MARGIN_RIGHT
        y = avail.bottom() - self.height() - TASKBAR_GAP_PX
        self.move(x, y)

    # -------- Doble click --------
    def _on_double_click(self, event):
        webbrowser.open("https://open.spotify.com/")

    # -------- Menú contextual --------
    def show_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        a1 = menu.addAction("Abrir Spotify")
        a2 = menu.addAction("Reubicar (abajo-derecha)")

        # Toggle de inicio automático
        auto_menu_text = "Inicio automático: ON" if is_registered_in_startup() else "Inicio automático: OFF"
        a3 = menu.addAction(auto_menu_text)

        a4 = menu.addAction("Salir")
        act = menu.exec_(self.mapToGlobal(pos))

        if act == a1:
            webbrowser.open("https://open.spotify.com/")
        elif act == a2:
            self.position_bottom_right()
        elif act == a3:
            # toggle
            try:
                if is_registered_in_startup():
                    ok = unregister_startup()
                    if ok:
                        QtWidgets.QMessageBox.information(self, "Inicio automático", "Se desactivó el inicio automático.")
                    else:
                        QtWidgets.QMessageBox.information(self, "Inicio automático", "Ya estaba desactivado.")
                else:
                    register_startup()
                    QtWidgets.QMessageBox.information(self, "Inicio automático", "Se activó el inicio automático.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"No se pudo cambiar el inicio automático:\n{e}")
        elif act == a4:
            QtWidgets.QApplication.quit()

    # -------- UI ----------
    def set_text(self, txt):
        if self.label.text() != txt:
            self.label.setText(txt)
            self.label.reset_scroll()

    def set_playing(self, is_playing: bool):
        self.playing = is_playing
        self.btnPlay.setIcon(icon_pause() if self.playing else icon_play())

    def _tick_progress_local(self):
        if self.playing:
            self.progress.setValue(min(1000, self.progress.value() + 3))

    # -------- Spotify ----------
    def on_prev(self):
        try: self.sp.previous_track()
        except: pass

    def on_toggle(self):
        try:
            if self.playing: self.sp.pause_playback()
            else: self.sp.start_playback()
        except: pass

    def on_next(self):
        try: self.sp.next_track()
        except: pass

    def loop_spotify(self):
        last_txt = None
        while True:
            try:
                pb = self.sp.current_playback()
                is_playing = False
                txt = "Nada reproduciéndose"
                pct = 0
                if pb and pb.get("item"):
                    name = pb["item"]["name"]
                    artists = ", ".join(a["name"] for a in pb["item"]["artists"])
                    txt = f"{name} — {artists}"
                    is_playing = bool(pb.get("is_playing"))
                    pos = int(pb.get("progress_ms") or 0)
                    dur = int(pb["item"].get("duration_ms") or 1)
                    pct = int(1000 * pos / max(1, dur))
                if txt != last_txt:
                    self.newText.emit(txt)
                    last_txt = txt
                self.newState.emit(is_playing)
                self.newProg.emit(pct)
                self._progress_local = pct
            except Exception:
                self.newText.emit("(sin conexión)")
                self.newState.emit(False)
                self.newProg.emit(0)
            time.sleep(POLL_SECONDS)

    # --- Hotkeys globales ---
    def _register_hotkeys(self):
        hwnd = int(self.winId())
        user32.RegisterHotKey(hwnd, HK_TOGGLE, MOD_CONTROL | MOD_ALT, VK_SPACE)
        user32.RegisterHotKey(hwnd, HK_PREV,   MOD_CONTROL | MOD_ALT, VK_LEFT)
        user32.RegisterHotKey(hwnd, HK_NEXT,   MOD_CONTROL | MOD_ALT, VK_RIGHT)
        self._nef = _WinHotkeyFilter(self._dispatch_hotkey)
        QtWidgets.QApplication.instance().installNativeEventFilter(self._nef)

    def _dispatch_hotkey(self, hotkey_id):
        if   hotkey_id == HK_TOGGLE: self.on_toggle()
        elif hotkey_id == HK_PREV:   self.on_prev()
        elif hotkey_id == HK_NEXT:   self.on_next()

    def closeEvent(self, e):
        hwnd = int(self.winId())
        for hk in (HK_TOGGLE, HK_PREV, HK_NEXT):
            user32.UnregisterHotKey(hwnd, hk)
        e.accept()

class _WinHotkeyFilter(QtCore.QAbstractNativeEventFilter):
    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd",   wintypes.HWND),
            ("message",wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time",   wintypes.DWORD),
            ("pt_x",   wintypes.LONG),
            ("pt_y",   wintypes.LONG),
        ]
    def __init__(self, cb):
        super().__init__()
        self.cb = cb
    def nativeEventFilter(self, eventType, message):
        if eventType != "windows_generic_MSG":
            return False, 0
        msg = _WinHotkeyFilter.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.cb(int(msg.wParam))
            return True, 0
        return False, 0

# ---- main ----
def main():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SEC,
        redirect_uri=REDIRECT,
        scope=SCOPE,
        cache_path=CACHE_PATH))

    app = QtWidgets.QApplication(sys.argv)

    # Preguntar solo una vez si no está registrado (opcional)
    try:
        if sys.platform.startswith("win") and not is_registered_in_startup():
            resp = QtWidgets.QMessageBox.question(
                None, "Inicio automático",
                "¿Querés que NowPlayingOverlay se inicie automáticamente al prender tu PC?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if resp == QtWidgets.QMessageBox.Yes:
                register_startup()
    except Exception:
        pass

    w = Overlay(sp)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
