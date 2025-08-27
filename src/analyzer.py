
def analyze_features(features, track_info):
    # Take Spotify audio features + track info and return a basic analysis dict.
    if not features:
        return {"error": "No features found"}

    tempos = [f["tempo"] for f in features if f]
    energies = [f["energy"] for f in features if f]
    popularities = [t["popularity"] for t in track_info]

    analysis = {
        "avg_tempo": round(sum(tempos) / len(tempos), 2) if tempos else None,
        "avg_energy": round(sum(energies) / len(energies), 2) if energies else None,
        "avg_popularity": round(sum(popularities) / len(popularities), 2) if popularities else None,
    }

    # Mainstream vs niche logic: threshold popularity
    if analysis["avg_popularity"] is not None:
        if analysis["avg_popularity"] > 65:
            analysis["taste_label"] = "Mainstream"
        elif analysis["avg_popularity"] > 40:
            analysis["taste_label"] = "Mixed"
        else:
            analysis["taste_label"] = "Niche"

    return analysis
