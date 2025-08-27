from typing import List, Dict
from utils import get_spotify_client, extract_playlist_id, get_user_id
from playlist import (
    validate_playlist_size,
    fetch_all_tracks,
    fetch_audio_features,
    create_playlist,
    add_tracks_to_playlist,
    MAX_TRACKS_ALLOWED
)
from analyzer import summarize_basic, decide_vibe

def pick_tracks_by_vibe(vibe: str, ranked_indices: List[int], tracks: List[Dict], count: int) -> List[Dict]:
    """
    Given vibe and ranked indices, pick 'count' tracks from 'tracks' in that ranked order,
    padding with remaining items to preserve playlist length if needed.
    """
    chosen = []
    seen = set()
    for idx in ranked_indices:
        if idx < len(tracks) and tracks[idx]["id"] not in seen:
            chosen.append(tracks[idx])
            seen.add(tracks[idx]["id"])
        if len(chosen) >= count:
            break
    # pad if necessary (shouldn't happen often)
    if len(chosen) < count:
        for t in tracks:
            if t["id"] not in seen:
                chosen.append(t)
            if len(chosen) >= count:
                break
    return chosen[:count]

def main():
    sp = get_spotify_client()
    user_id = get_user_id(sp)

    print("Paste a Spotify playlist URL or ID:")
    playlist_input = input("> ").strip()
    playlist_id = extract_playlist_id(playlist_input)

    ok, total = validate_playlist_size(sp, playlist_id)
    if not ok:
        print(f"Playlist has {total} tracks, which exceeds the cap ({MAX_TRACKS_ALLOWED}).")
        print("Trim it or change MAX_TRACKS_ALLOWED in src/playlist.py.")
        return

    print(f"Fetching tracks... (total={total})")
    tracks = fetch_all_tracks(sp, playlist_id)
    if not tracks:
        print("No tracks found.")
        return

    track_ids = [t["id"] for t in tracks]
    print("Fetching audio features...")
    features = fetch_audio_features(sp, track_ids)

    # Align features and tracks by ID (defensive)
    id_to_feat = {f["id"]: f for f in features if f and f.get("id")}
    aligned_tracks, aligned_features = [], []
    for t in tracks:
        f = id_to_feat.get(t["id"])
        if f:
            aligned_tracks.append(t)
            aligned_features.append(f)

    summary = summarize_basic(aligned_features, aligned_tracks)
    print("\n--- Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v}")

    vibe, ranked_indices = decide_vibe(aligned_features, aligned_tracks, mode="auto")
    print(f"\nDetected vibe: {vibe}")

    # Build new playlist with same number of tracks as original (or aligned length)
    target_count = len(aligned_tracks)
    chosen_tracks = pick_tracks_by_vibe(vibe, ranked_indices, aligned_tracks, target_count)
    chosen_uris = [t["uri"] for t in chosen_tracks]

    source_meta = sp.playlist(playlist_id, fields="name")
    source_name = source_meta["name"]

    new_name = f"{source_name} • {vibe} Mirror"
    desc = f"Generated to reflect the playlist's {vibe.lower()} vibe based on audio features and popularity."
    print(f"\nCreating new playlist: {new_name}")
    new_pl_id = create_playlist(sp, user_id, new_name, desc)

    print("Adding tracks...")
    add_tracks_to_playlist(sp, new_pl_id, chosen_uris)

    url = f"https://open.spotify.com/playlist/{new_pl_id}"
    print("\nDone.")
    print(f"New playlist: {url}")

if __name__ == "__main__":
    main()
