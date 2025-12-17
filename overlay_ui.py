# overlay_ui.py
# Barra con controles (prev/play/next), sin volumen, atajos GLOBALS.

import time, threading, webbrowser
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from config import (
    FAST_POLL_SECONDS,
    IDLE_POLL_SECONDS,
    PADDING_X,
    PADDING_Y,
    PAUSED_POLL_SECONDS,
    WIDTH,
    HEIGHT,
    STYLE_BG,
    STYLE_LABEL,
    STYLE_PROGRESS,
    MARQUEE_SPEED_MS,
    MARGIN_RIGHT,
    TASKBAR_GAP_PX,
    REMEMBER_POS,
    LOCK_POSITION_DEFAULT,
    DRAG_SNAP_PX,
)
from icons import icon_play, icon_pause, icon_next, icon_prev, icon_share
from hotkeys import (
    HK_VOL_DOWN,
    HK_VOL_UP,
    register_hotkeys,
    unregister_hotkeys,
    HK_TOGGLE,
    HK_PREV,
    HK_NEXT,
)
from settings_store import load_settings, save_settings


# ---------- Label con marquesina ----------
class MarqueeLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.setStyleSheet(STYLE_LABEL)
        self.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

    def start(self):
        self.timer.start(MARQUEE_SPEED_MS)

    def reset_scroll(self):
        self.offset = 0
        self.update()

    def tick(self):
        self.offset += 1
        if self.offset > self.fontMetrics().horizontalAdvance(self.text()) + 40:
            self.offset = 0
        self.update()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        txt = self.text()
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(txt)
        h = self.height()
        x = -self.offset
        while x < self.width():
            p.drawText(
                x,
                0,
                max(text_w + 40, self.width()),
                h,
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                txt,
            )
            x += text_w + 40


# ---------- Grip de arrastre ----------
class DragGrip(QtWidgets.QFrame):
    startDrag = QtCore.Signal(QtCore.QPointF)
    doDrag = QtCore.Signal(QtCore.QPointF)
    endDrag = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(12)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.setStyleSheet(
            """
            QFrame {
                background: rgba(15,15,15,100);
                border-top-left-radius: 9px;
                border-bottom-left-radius: 9px;
            }
        """
        )
        self._dragging = False

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self.startDrag.emit(e.globalPosition())
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.doDrag.emit(e.globalPosition())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == QtCore.Qt.LeftButton:
            self._dragging = False
            self.endDrag.emit()
            e.accept()
        else:
            super().mouseReleaseEvent(e)


# ---------- Ventana principal ----------
class Overlay(QtWidgets.QWidget):
    newText = QtCore.Signal(str)
    newProg = QtCore.Signal(int)
    newState = QtCore.Signal(bool)

    def __init__(self, spotify):
        super().__init__()
        self.sp = spotify
        self.playing = False
        self.pos_locked = LOCK_POSITION_DEFAULT
        self._drag_offset = QtCore.QPoint(0, 0)

        # Ventana tipo overlay (sin barra, siempre arriba, sin Alt+Tab)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Fondo + grip
        self.bg = QtWidgets.QFrame()
        self.bg.setStyleSheet(STYLE_BG)
        self.grip = DragGrip(self)
        self.grip.startDrag.connect(self._on_start_drag)
        self.grip.doDrag.connect(self._on_do_drag)
        self.grip.endDrag.connect(self._on_end_drag)

        # Controles
        self.btnPrev = QtWidgets.QToolButton()
        self.btnPlay = QtWidgets.QToolButton()
        self.btnNext = QtWidgets.QToolButton()
        for b in (self.btnPrev, self.btnPlay, self.btnNext):
            b.setAutoRaise(True)
            b.setIconSize(QtCore.QSize(16, 16))
            b.setCursor(QtCore.Qt.PointingHandCursor)
        self.btnPrev.setIcon(icon_prev())
        self.btnPlay.setIcon(icon_play())
        self.btnNext.setIcon(icon_next())

        # Nuevo botón: copiar enlace
        self.btnCopy = QtWidgets.QToolButton()
        self.btnCopy.setAutoRaise(True)
        self.btnCopy.setIconSize(QtCore.QSize(16, 16))
        self.btnCopy.setCursor(QtCore.Qt.PointingHandCursor)
        self.btnCopy.setIcon(icon_share())
        self.btnCopy.setToolTip("Copiar enlace de la canción")
        self.btnCopy.setStyleSheet(
            """
            QToolButton {
                background: transparent;
                padding: 0px;
                border: none;
                color: #d0d0d0;
            }
            QToolButton:hover {
                color: #e5e5e5;
            }
            QToolButton:pressed {
                color: #b0b0b0;
            }
        """
        )

        # Texto
        self.label = MarqueeLabel("Esperando reproducción…")
        self.label.setMinimumWidth(150)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )

        # Progreso
        self.progress = QtWidgets.QProgressBar()
        self.progress.setFixedHeight(2)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1000)
        self.progress.setStyleSheet(STYLE_PROGRESS)

        # Layout superior
        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(PADDING_X, PADDING_Y, PADDING_X, 6)
        top.setSpacing(8)
        top.addWidget(self.grip)
        top.addWidget(self.btnPrev)
        top.addWidget(self.btnPlay)
        top.addWidget(self.btnNext)
        top.addSpacing(4)
        top.addWidget(self.label, 1)   # el texto se expande
        top.addWidget(self.btnCopy)    # botón copiar, pegado a la derecha

        v = QtWidgets.QVBoxLayout(self.bg)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addLayout(top)
        v.addWidget(self.progress)

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.bg)

        self.resize(WIDTH, HEIGHT)
        self._restore_or_default_position()

        # Señales UI
        self.newText.connect(self.set_text)
        self.newProg.connect(self.progress.setValue)
        self.newState.connect(self.set_playing)

        # Worker Spotify
        self.worker = threading.Thread(target=self.loop_spotify, daemon=True)
        self.worker.start()

        self.label.start()

        # Progreso suave
        self.smooth = QtCore.QTimer(self)
        self.smooth.timeout.connect(self._tick_progress_local)
        self._progress_local = 0
        self._progress_real = 0
        self._last_update_time = 0
        self._track_duration_ms = 1
        self.smooth.start(60)  # 60ms para suavidad

        # Interacciones
        self.bg.mouseDoubleClickEvent = self.open_spotify
        self.bg.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.bg.customContextMenuRequested.connect(self.show_menu)
        self.btnPrev.clicked.connect(self.on_prev)
        self.btnPlay.clicked.connect(self.on_toggle)
        self.btnNext.clicked.connect(self.on_next)
        self.btnCopy.clicked.connect(self.copy_link)

        # Atajos GLOBALS
        self._hotkeys = register_hotkeys(self, self.handle_hotkey)

    # ----- Posición / persistencia / magnetismo -----
    def position_bottom_right(self):
        screen = (
            QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos())
            or QtGui.QGuiApplication.primaryScreen()
        )
        avail = screen.availableGeometry()
        x = avail.right() - self.width() - MARGIN_RIGHT
        y = avail.bottom() - self.height() - TASKBAR_GAP_PX
        self.move(x, y)

    def _restore_or_default_position(self):
        if not REMEMBER_POS:
            self.position_bottom_right()
            return
        s = load_settings()
        pos = s.get("window_pos")
        if isinstance(pos, list) and len(pos) == 2:
            self.move(self._snap_and_clamp(QtCore.QPoint(int(pos[0]), int(pos[1]))))
        else:
            self.position_bottom_right()
        self.pos_locked = bool(s.get("pos_locked", LOCK_POSITION_DEFAULT))

    def _save_position(self):
        if not REMEMBER_POS:
            return
        s = load_settings()
        s["window_pos"] = [int(self.x()), int(self.y())]
        s["pos_locked"] = bool(self.pos_locked)
        save_settings(s)

    def _on_start_drag(self, gpos):
        if self.pos_locked:
            return
        tl = self.frameGeometry().topLeft()
        self._drag_offset = QtCore.QPoint(
            int(gpos.x()) - tl.x(), int(gpos.y()) - tl.y()
        )

    def _on_do_drag(self, gpos):
        if self.pos_locked:
            return
        desired = QtCore.QPoint(
            int(gpos.x()) - self._drag_offset.x(), int(gpos.y()) - self._drag_offset.y()
        )
        self.move(self._snap_and_clamp(desired))

    def _on_end_drag(self):
        self._save_position()

    def _snap_and_clamp(self, pt: QtCore.QPoint) -> QtCore.QPoint:
        screen = (
            QtGui.QGuiApplication.screenAt(pt) or QtGui.QGuiApplication.primaryScreen()
        )
        avail = screen.availableGeometry()
        x, y = pt.x(), pt.y()
        w, h = self.width(), self.height()
        if abs(x - avail.left()) <= DRAG_SNAP_PX:
            x = avail.left()
        elif abs((x + w) - avail.right()) <= DRAG_SNAP_PX:
            x = avail.right() - w
        if abs(y - avail.top()) <= DRAG_SNAP_PX:
            y = avail.top()
        elif abs((y + h) - avail.bottom()) <= DRAG_SNAP_PX:
            y = avail.bottom() - h
        margin = 2
        x = max(avail.left() + margin, min(x, avail.right() - w - margin))
        y = max(avail.top() + margin, min(y, avail.bottom() - h - margin))
        return QtCore.QPoint(x, y)

    # ----- Menú -----
    def show_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        a1 = menu.addAction("Abrir Spotify")
        a2 = menu.addAction("Reubicar (abajo-derecha)")
        menu.addSeparator()
        a_lock = menu.addAction("Bloquear posición")
        a_lock.setCheckable(True)
        a_lock.setChecked(self.pos_locked)
        menu.addSeparator()
        a3 = menu.addAction("Salir")

        act = menu.exec_(self.mapToGlobal(pos))
        if act == a1:
            self.open_spotify(None)
        elif act == a2:
            self.position_bottom_right()
            self._save_position()
        elif act == a_lock:
            self.pos_locked = a_lock.isChecked()
            self._save_position()
        elif act == a3:
            QtWidgets.QApplication.quit()

    # ----- UI -----
    def set_text(self, txt):
        if self.label.text() != txt:
            self.label.setText(txt)
            self.label.reset_scroll()

    def set_playing(self, is_playing):
        self.playing = is_playing
        self.btnPlay.setIcon(icon_pause() if is_playing else icon_play())

    # Copiar enlace de la canción actual
    def copy_link(self):
        try:
            pb = self.sp.current_playback()
            item = pb.get("item") if pb else None
            if not item:
                raise RuntimeError("no item")
            url = (item.get("external_urls") or {}).get("spotify")
            if not url:
                tid = item.get("id")
                if tid:
                    url = f"https://open.spotify.com/track/{tid}"
            if not url:
                raise RuntimeError("no url")
            QtGui.QGuiApplication.clipboard().setText(url)
            QtWidgets.QToolTip.showText(
                QtGui.QCursor.pos(), "Enlace copiado ✔", self.btnCopy, 1500
            )
        except Exception:
            QtWidgets.QToolTip.showText(
                QtGui.QCursor.pos(), "No hay canción activa", self.btnCopy, 1500
            )

    def _tick_progress_local(self):
        """Progreso suave local que se sincroniza con el real."""
        if not self.playing:
            return

        current_time = time.time() * 1000  # en milisegundos

        if self._last_update_time == 0:
            self._last_update_time = current_time
            return

        time_diff = current_time - self._last_update_time
        self._last_update_time = current_time

        if self._track_duration_ms > 0:
            ms_progress = time_diff
            progress_increment = (ms_progress / self._track_duration_ms) * 1000

            self._progress_local = min(1000, self._progress_local + progress_increment)

            diff_with_real = abs(self._progress_local - self._progress_real)
            if diff_with_real < 50:
                self.progress.setValue(int(self._progress_local))

    def loop_spotify(self):
        last_txt = None
        is_playing_prev = False

        while True:
            sleep_s = IDLE_POLL_SECONDS
            try:
                pb = self.sp.current_playback()
                is_playing = False
                txt = "Nada reproduciéndose"
                pct = 0
                duration_ms = 1

                if pb:
                    if pb.get("item"):
                        name = pb["item"]["name"]
                        artists = ", ".join(a["name"] for a in pb["item"]["artists"])
                        txt = f"{name} — {artists}"
                        pos = int(pb.get("progress_ms") or 0)
                        duration_ms = int(pb["item"].get("duration_ms") or 1)
                        pct = int(1000 * pos / max(1, duration_ms))

                        self._track_duration_ms = duration_ms

                    is_playing = bool(pb.get("is_playing"))

                if txt != last_txt:
                    self.newText.emit(txt)
                    last_txt = txt

                self.newState.emit(is_playing)

                self._progress_real = pct

                if abs(self._progress_local - pct) > 30 or not is_playing_prev:
                    self._progress_local = pct
                    self.progress.setValue(pct)

                if is_playing != is_playing_prev:
                    self._last_update_time = time.time() * 1000

                if is_playing:
                    sleep_s = FAST_POLL_SECONDS
                else:
                    sleep_s = PAUSED_POLL_SECONDS

                is_playing_prev = is_playing

            except Exception as e:
                retry_after = None
                try:
                    if hasattr(e, "http_status") and e.http_status == 429:
                        retry_after = float(
                            getattr(e, "headers", {}).get("Retry-After", "")
                        )
                except Exception:
                    pass

                if retry_after:
                    sleep_s = max(retry_after, IDLE_POLL_SECONDS)
                else:
                    self.newText.emit("(sin conexión)")
                    self.newState.emit(False)
                    self.newProg.emit(0)
                    sleep_s = IDLE_POLL_SECONDS

            time.sleep(sleep_s)

    # ----- Controles Spotify -----
    def on_prev(self):
        try:
            self.sp.previous_track()
        except Exception:
            pass

    def on_toggle(self):
        try:
            if self.playing:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
        except Exception:
            pass

    def on_next(self):
        try:
            self.sp.next_track()
        except Exception:
            pass

    # ----- Atajos globales -----
    def handle_hotkey(self, hotkey_id):
        """Maneja los atajos globales."""
        if hotkey_id == HK_TOGGLE:
            self.on_toggle()
        elif hotkey_id == HK_PREV:
            self.on_prev()
        elif hotkey_id == HK_NEXT:
            self.on_next()
        elif hotkey_id == HK_VOL_UP:
            self.adjust_volume(5)
        elif hotkey_id == HK_VOL_DOWN:
            self.adjust_volume(-5)

    def adjust_volume(self, delta):
        """Sube o baja el volumen actual en pasos de 5%."""
        try:
            pb = self.sp.current_playback()
            if not pb or "device" not in pb:
                return
            vol = pb["device"].get("volume_percent", 50)
            new_vol = max(0, min(100, vol + delta))
            self.sp.volume(new_vol)
        except Exception:
            pass

    def open_spotify(self, event):
        webbrowser.open("https://open.spotify.com/")

    def closeEvent(self, e):
        self._save_position()
        unregister_hotkeys(self)
        e.accept()
