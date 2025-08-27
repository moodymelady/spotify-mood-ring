from typing import Dict, List, Tuple
import time
import spotipy

MAX_TRACKS_ALLOWED = 300  # manageable size cap; tweak as needed
PAGE_LIMIT = 100

def validate_playlist_size(sp: spotipy.Spotify, playlist_id: str) -> Tuple[bool, int]:
    """
    Returns (is_valid, total_tracks). Enforces a cap so analysis stays snappy.
    """
    meta = sp.playlist(playlist_id, fields="tracks.total,name,owner.display_name")
    total = meta["tracks"]["total"]
    return (total <= MAX_TRACKS_ALLOWED, total)

def fetch_all_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[Dict]:
    """
    Fetch all track objects (track dicts) from a playlist, paginated.
    Filters out local/None tracks.
    """
    items: List[Dict] = []
    offset = 0
    while True:
        chunk = sp.playlist_items(
            playlist_id,
            additional_types=["track"],
            offset=offset,
            limit=PAGE_LIMIT,
            fields="items(track(id,name,artists(name,id),popularity,uri)),next"
        )
        for it in chunk["items"]:
            tr = it.get("track")
            if tr and tr.get("id"):
                items.append(tr)
        if not chunk.get("next"):
            break
        offset += PAGE_LIMIT
        # polite pacing to avoid rate limits
        time.sleep(0.05)
    return items

def fetch_audio_features(sp: spotipy.Spotify, track_ids: List[str]) -> List[Dict]:
    """
    Fetch audio features for a list of track IDs in batches of 100.
    """
    feats: List[Dict] = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        feats.extend(sp.audio_features(batch))
        time.sleep(0.05)
    # Align features with track_ids order by trimming None entries
    return [f for f in feats if f]

def create_playlist(sp: spotipy.Spotify, user_id: str, name: str, description: str) -> str:
    """
    Create a playlist and return its ID.
    """
    pl = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description[:300]  # Spotify desc limit
    )
    return pl["id"]

def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, uris: List[str]) -> None:
    """
    Add tracks to playlist in chunks of 100.
    """
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i:i+100])
        time.sleep(0.05)
