from utils import get_spotify_client, extract_playlist_id
from analyzer import analyze_features

def main():
    sp = get_spotify_client()

    playlist_url = input("Paste a Spotify playlist link: ").strip()
    playlist_id = extract_playlist_id(playlist_url)

    # Fetch playlist tracks
    results = sp.playlist_items(playlist_id, additional_types=['track'])
    items = results["items"]

    track_ids = []
    track_info = []
    for item in items:
        track = item["track"]
        if track: 
            track_ids.append(track["id"])
            track_info.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "popularity": track["popularity"]
            })

    print(f"\nFetched {len(track_ids)} tracks.")

    # Fetch audio features
    features = sp.audio_features(track_ids)

    # Analyze
    analysis = analyze_features(features, track_info)

    print("\n--- Playlist Analysis ---")
    for key, val in analysis.items():
        print(f"{key}: {val}")

if __name__ == "__main__":
    main()
