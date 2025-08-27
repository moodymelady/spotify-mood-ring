import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

def get_spotify_client():
    """Authenticate with Spotify and return a client instance."""
    load_dotenv()

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    scope = "playlist-read-private user-read-private"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    ))

    return sp

def extract_playlist_id(url: str) -> str:
    """Pull playlist ID from a Spotify playlist URL."""
    if "playlist/" in url:
        return url.split("playlist/")[1].split("?")[0]
    return url
