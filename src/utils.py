import os
from typing import Optional
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_spotify_client() -> spotipy.Spotify:
    """
    Authenticate with Spotify and return a Spotipy client.
    Uses token caching via SpotifyOAuth (creates a .cache file locally).
    """
    load_dotenv()

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        raise RuntimeError("Missing Spotify credentials. Set them in .env")

    scope = (
        "playlist-read-private "
        "playlist-read-collaborative "
        "playlist-modify-public "
        "playlist-modify-private "
        "user-read-private"
    )

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=True,
        cache_path=".cache"  # token cache
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def extract_playlist_id(url_or_id: str) -> str:
    """
    Accepts a playlist URL or ID and returns the playlist ID.
    Handles open.spotify and spotify:playlist formats.
    """
    s = url_or_id.strip()
    if "playlist/" in s:
        return s.split("playlist/")[1].split("?")[0]
    if s.startswith("spotify:playlist:"):
        return s.split(":")[-1]
    return s

def get_user_id(sp: spotipy.Spotify) -> str:
    """
    Returns current user's Spotify ID, or SPOTIFY_USER_ID if set in .env.
    """
    env_id: Optional[str] = os.getenv("SPOTIFY_USER_ID")
    if env_id:
        return env_id
    me = sp.current_user()
    return me["id"]
