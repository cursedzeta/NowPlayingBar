# spotify_client.py
# -------------------------------------
# Cliente autenticado de Spotify (Spotipy)
# -------------------------------------

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import CLIENT_ID, CLIENT_SEC, REDIRECT, SCOPE, CACHE_PATH


def get_spotify_client():
    """Devuelve un cliente autenticado de Spotify listo para usar."""
    auth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SEC,
        redirect_uri=REDIRECT,
        scope=SCOPE,
        cache_path=CACHE_PATH,
    )
    return spotipy.Spotify(auth_manager=auth)
