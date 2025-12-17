# config.py
# -------------------------------------
# Configuración global del NowPlayingOverlay
# -------------------------------------

from pathlib import Path

# --- Credenciales Spotify ---
CLIENT_ID  = "08e638372b3d4dfd91759e9a2fd5dc59"
CLIENT_SEC = "12bc8bd5b998465fbdca85c3030cf961"
REDIRECT   = "http://127.0.0.1:8888/callback"

# --- Permisos requeridos ---
SCOPE = "user-read-currently-playing user-read-playback-state user-modify-playback-state"

# --- Archivos y rutas ---
CACHE_PATH = str(Path.home() / ".cache-spotipy-nowplaying")

# --- Actualización / tiempos ---
POLL_SECONDS = 4           # cada cuántos segundos consulta Spotify
MARQUEE_SPEED_MS = 35      # velocidad del texto desplazable

# Poll adaptativo (segundos)
FAST_POLL_SECONDS   = 0.8   # cuando está reproduciendo
PAUSED_POLL_SECONDS = 2.0   # cuando está en pausa
IDLE_POLL_SECONDS   = 4.0   # cuando no hay reproducción / error

# Si querés ir aún más rápido, probá 0.5. Menos de ~0.5s te puede rate-limitar.

# --- Layout de la barra ---
PADDING_X = 6
PADDING_Y = 4
WIDTH  = 300
HEIGHT = 34
TASKBAR_GAP_PX = 2
MARGIN_RIGHT = 12

# --- Apariencia ---
STYLE_BG = "QFrame { background: rgba(0,0,0,255); border-radius: 9px; }"
STYLE_LABEL = "color: white; font-size: 11px;"
STYLE_PROGRESS = (
    "QProgressBar { background: rgba(255,255,255,28); border: none; }"
    "QProgressBar::chunk { background: #1DB954; }"
)

# --- Posicionamiento “abajo-derecha” por defecto ---
MARGIN_RIGHT   = 8
TASKBAR_GAP_PX = 1

# --- Drag / persistencia ---
REMEMBER_POS = True                 # recordar posición
LOCK_POSITION_DEFAULT = False       # arrancar bloqueado o no
DRAG_SNAP_PX = 12                   # magnetismo a bordes (px)

# --- Volumen ---
VOLUME_STEP = 5                    # incremento/decremento por hotkey
VOL_POPUP_WIDTH = 120
VOL_POPUP_HEIGHT = 38 
