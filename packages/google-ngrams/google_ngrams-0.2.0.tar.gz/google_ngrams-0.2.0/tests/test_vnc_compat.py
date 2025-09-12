import numpy as np

from google_ngrams.vnc import _linkage_matrix


def legacy_sd_heights(values, years):
    # Replicate the R legacy algorithm to compute cumulative SD heights
    x = list(values)
    names = [str(y) for y in years]
    heights = []
    overall_distance = 0.0

    n_steps = len(x) - 1
    for _ in range(n_steps):
        # unique(names) preserving order
        uniq_names = []
        for nm in names:
            if nm not in uniq_names:
                uniq_names.append(nm)

        diffs = []
        for j in range(len(uniq_names) - 1):
            first_name = uniq_names[j]
            second_name = uniq_names[j + 1]
            pooled = [
                v for v, nm in zip(x, names)
                if nm in (first_name, second_name)
            ]
            s = 0.0 if sum(pooled) == 0 else np.std(pooled, ddof=1)
            diffs.append(s)

        pos = int(np.argmin(diffs))
        distance = float(diffs[pos])
        overall_distance += distance

        lower_name = uniq_names[pos]
        higher_name = uniq_names[pos + 1]
        mean_age = round(
            np.mean([
                float(nm) for nm in names
                if nm in (lower_name, higher_name)
            ]),
            4,
        )
        new_name = str(mean_age)
        names = [
            new_name if nm in (lower_name, higher_name) else nm
            for nm in names
        ]

        heights.append(overall_distance)

    return np.array(heights, dtype=float)


def to_r_merge(Z):
    # Convert our linkage children indices to R hclust merge format
    # Z shape: (n-1, 4),
    # columns: merge1, merge2, distance, size; indices are 0-based
    n = Z.shape[0] + 1
    children = Z[:, :2].astype(int)
    out = np.empty((n - 1, 2), dtype=int)
    for i in range(n - 1):
        for k in (0, 1):
            v = children[i, k]
            if v < n:
                # leaf -> negative 1-based index
                out[i, k] = -(v + 1)
            else:
                # cluster node id uses offset (n-1) in _linkage_matrix
                # map to the 1-based previous row index expected by R hclust
                out[i, k] = (v - (n - 1)) + 1
    return out


def test_vnc_sd_heights_match_legacy():
    values = np.array([
        29.47368421, 42.20472441, 72.83870968, 76.72619048,
        69.56521739, 62.42647059, 64.9122807, 118.9690722,
        177.34375,
    ])
    years = np.array([1925, 1935, 1945, 1955, 1965, 1975, 1985, 1995, 2005])

    legacy = legacy_sd_heights(values, years)
    Z = _linkage_matrix(
        time_series=years.copy(),
        frequency=values.copy(),
        distance_measure="sd",
    )
    got = Z[:, 2].astype(float)

    assert len(got) == len(legacy)
    # Tight tolerance to match R test
    assert np.allclose(got, legacy, rtol=0, atol=1e-12)


def test_vnc_sd_merge_matches_expected():
    # Compare structural equivalence: reconstruct leaf sets from
    # the legacy algorithm and from our linkage matrix and check
    # each step's merged leaf composition.
    values = np.array([
        29.47368421, 42.20472441, 72.83870968, 76.72619048,
        69.56521739, 62.42647059, 64.9122807, 118.9690722,
        177.34375,
    ])
    years = np.array([1925, 1935, 1945, 1955, 1965, 1975, 1985, 1995, 2005])
    n = len(values)

    def legacy_merge_sets(vals):
        x = list(vals)
        names = list(range(1, n + 1))  # 1-based leaf ids
        sets = []
        for _ in range(n - 1):
            uniq = []
            for nm in names:
                if nm not in uniq:
                    uniq.append(nm)
            diffs = []
            for j in range(len(uniq) - 1):
                a = uniq[j]
                b = uniq[j + 1]
                pooled = [v for v, nm in zip(x, names) if nm in (a, b)]
                s = 0.0 if sum(pooled) == 0 else np.std(pooled, ddof=1)
                diffs.append(s)
            pos = int(np.argmin(diffs))
            a = uniq[pos]
            b = uniq[pos + 1]
            merged = {i for i, nm in enumerate(names, start=1) if nm in (a, b)}
            sets.append(merged)
            # deterministically relabel merged cluster using the min label
            new_id = min(a, b)
            names = [new_id if nm in (a, b) else nm for nm in names]
        return sets

    legacy_sets = legacy_merge_sets(values)

    # Build sets from our Z
    Z = _linkage_matrix(
        time_series=years.copy(),
        frequency=values.copy(),
        distance_measure="sd",
    )
    node_sets = {i: {i + 1} for i in range(n)}
    our_sets = []
    for i in range(Z.shape[0]):
        left = int(Z[i, 0])
        right = int(Z[i, 1])
        parent = n + i
        node_sets[parent] = node_sets[left] | node_sets[right]
        our_sets.append(node_sets[parent])

    assert len(legacy_sets) == len(our_sets)
    for s_exp, s_got in zip(legacy_sets, our_sets):
        assert s_exp == s_got


def test_vnc_cv_heights_match_expected():
    values = np.array([
        29.47368421, 42.20472441, 72.83870968, 76.72619048,
        69.56521739, 62.42647059, 64.9122807, 118.9690722,
        177.34375,
    ])
    years = np.array([1925, 1935, 1945, 1955, 1965, 1975, 1985, 1995, 2005])

    Z_cv = _linkage_matrix(
        time_series=years.copy(),
        frequency=values.copy(),
        distance_measure="cv",
    )
    got = Z_cv[:, 2].astype(float)

    expected_cv = np.array([
        0.02760720, 0.06436534, 0.11344400, 0.19704553,
        0.38557467, 0.66417976, 0.95527116, 1.51295599,
    ])

    assert len(got) == len(expected_cv)
    assert np.allclose(got, expected_cv, rtol=0, atol=1e-8)
