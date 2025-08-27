from typing import Dict, List, Literal, Tuple
import numpy as np
from sklearn.cluster import KMeans

FeatureMode = Literal["popularity", "kmeans", "auto"]

# Features used for clustering
CLUSTER_FEATURES = ["danceability", "energy", "valence", "tempo", "acousticness"]

def summarize_basic(features: List[Dict], tracks: List[Dict]) -> Dict:
    """
    Compute simple aggregates for reporting.
    """
    if not features:
        return {"count": 0}

    def safe_avg(vals):
        arr = [v for v in vals if v is not None]
        return float(np.mean(arr)) if arr else None

    tempos = [f.get("tempo") for f in features]
    energies = [f.get("energy") for f in features]
    valences = [f.get("valence") for f in features]
    dance = [f.get("danceability") for f in features]
    pops = [t.get("popularity") for t in tracks]

    return {
        "count": len(features),
        "avg_tempo": round(safe_avg(tempos), 2) if safe_avg(tempos) is not None else None,
        "avg_energy": round(safe_avg(energies), 3) if safe_avg(energies) is not None else None,
        "avg_valence": round(safe_avg(valences), 3) if safe_avg(valences) is not None else None,
        "avg_danceability": round(safe_avg(dance), 3) if safe_avg(dance) is not None else None,
        "avg_popularity": round(safe_avg(pops), 1) if safe_avg(pops) is not None else None,
    }

def label_by_popularity(tracks: List[Dict]) -> Tuple[str, List[int]]:
    """
    Use average popularity to decide vibe.
    Return (label, ranked_indices) where ranked_indices are sorted
    from most representative for that vibe.
    """
    pops = np.array([t["popularity"] for t in tracks], dtype=float)
    avg_pop = pops.mean() if len(pops) else 0.0

    if avg_pop > 65:
        label = "Mainstream"
        # Most popular first
        ranked = list(np.argsort(-pops))
    elif avg_pop > 40:
        label = "Mixed"
        # Middle popularity first (closest to median)
        median = np.median(pops)
        ranked = list(np.argsort(np.abs(pops - median)))
    else:
        label = "Niche"
        # Least popular first
        ranked = list(np.argsort(pops))
    return label, ranked

def label_by_kmeans(features: List[Dict], tracks: List[Dict]) -> Tuple[str, List[int]]:
    """
    Cluster by selected audio features, then assign the cluster with higher
    mean popularity as 'Mainstream' and the other as 'Niche'. 'Mixed' if close.
    Returns (label, ranked_indices) where indices are ordered by how strongly
    they fit the vibe.
    """
    # Build matrix
    X = []
    for f in features:
        row = []
        for k in CLUSTER_FEATURES:
            val = f.get(k)
            if val is None:
                # if missing tempo etc., skip that row entirely
                row = None
                break
            row.append(float(val))
        if row is not None:
            X.append(row)

    if len(X) < 2:
        # Fallback to popularity if clustering is not meaningful
        return label_by_popularity(tracks)

    X = np.array(X, dtype=float)

    # Standardize simple (z-score) for stability
    X_std = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-6)

    kmeans = KMeans(n_clusters=2, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X_std)

    pops = np.array([t["popularity"] for t in tracks[:len(labels)]], dtype=float)
    c0_mean = pops[labels == 0].mean() if np.any(labels == 0) else -1
    c1_mean = pops[labels == 1].mean() if np.any(labels == 1) else -1

    diff = abs(c0_mean - c1_mean)
    if diff < 5:  # clusters are similar in popularity → Mixed
        vibe = "Mixed"
        # Rank by closeness to cluster centers (less distance = more on-vibe)
        dists = kmeans.transform(X_std).min(axis=1)
        ranked = list(np.argsort(dists))
    else:
        main_label = 0 if c0_mean > c1_mean else 1
        niche_label = 1 - main_label
        vibe = "Mainstream" if main_label == 0 else "Mainstream"
        # If majority of tracks fall in niche cluster, call it Niche
        if np.sum(labels == niche_label) > np.sum(labels == main_label):
            vibe = "Niche"
        # Rank: put tracks of the chosen vibe first, sorted by confidence (distance)
        dists = kmeans.transform(X_std)
        conf = -dists[np.arange(len(labels)), labels]  # higher = closer
        # Select indices that belong to the vibe cluster
        chosen = main_label if vibe == "Mainstream" else niche_label
        idxs = [i for i, lab in enumerate(labels) if lab == chosen]
        idxs_sorted = sorted(idxs, key=lambda i: conf[i], reverse=True)
        # Then the rest
        rest = [i for i in range(len(labels)) if i not in idxs_sorted]
        ranked = idxs_sorted + rest

    return vibe, ranked

def decide_vibe(
    features: List[Dict],
    tracks: List[Dict],
    mode: "FeatureMode" = "auto"
) -> Tuple[str, List[int]]:
    """
    Decide playlist vibe and return (label, ranked_indices).
    mode:
      - "popularity": average popularity heuristic
      - "kmeans": 2-cluster KMeans on audio features
      - "auto": try kmeans if enough tracks, else popularity
    """
    if mode == "popularity":
        return label_by_popularity(tracks)
    if mode == "kmeans":
        return label_by_kmeans(features, tracks)
    # auto
    if len(tracks) >= 20:
        return label_by_kmeans(features, tracks)
    return label_by_popularity(tracks)
