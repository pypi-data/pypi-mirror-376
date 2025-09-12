import copy
import numpy as np
import polars as pl
from textwrap import dedent

__all__ = [
    "_linkage_matrix",
    "_vnc_calculate_info",
    "_plot_dendrogram",
    "_cut_tree_simple"
]


def _cut_tree_simple(Z, n_clusters=None, height=None):
    if height is not None:
        raise NotImplementedError(
            """
            height-based cuts not supported in simplified implementation
            """
        )
    n = Z.shape[0] + 1
    if n_clusters is None or n_clusters >= n:
        return np.arange(n, dtype=int)
    if n_clusters <= 1:
        return np.zeros(n, dtype=int)
    merges_to_apply = n - int(n_clusters)
    labels = np.arange(n, dtype=int)
    node_leaves = [None] * (2 * n - 1)
    for i in range(n):
        node_leaves[i] = [i]
    for i in range(Z.shape[0]):
        left = int(Z[i, 0])
        right = int(Z[i, 1])
        leaves = node_leaves[left] + node_leaves[right]
        leaves.sort()
        node_leaves[n + i] = leaves
        if i < merges_to_apply:
            block = leaves
            block_labels = labels[block]
            new_label = block_labels.min()
            max_label = block_labels.max()
            labels[block] = new_label
            # compress labels above max_label downward
            mask = labels > max_label
            labels[mask] -= (max_label - new_label)
        else:
            break
    return labels


def _remove_dups(L):
    """
    Remove duplicates AND preserve the original order of the elements.

    The set class is not guaranteed to do this.
    """
    seen_before = set()
    L2 = []
    for i in L:
        if i not in seen_before:
            seen_before.add(i)
            L2.append(i)
    return L2


_dtextsizes = {20: 12, 30: 10, 50: 8, 85: 6, np.inf: 5}
_drotation = {20: 0, 40: 45, np.inf: 90}
_dtextsortedkeys = list(_dtextsizes.keys())
_dtextsortedkeys.sort()
_drotationsortedkeys = list(_drotation.keys())
_drotationsortedkeys.sort()


def _get_tick_text_size(p):
    for k in _dtextsortedkeys:
        if p <= k:
            return _dtextsizes[k]


def _get_tick_rotation(p):
    for k in _drotationsortedkeys:
        if p <= k:
            return _drotation[k]


def _contract_linkage_matrix(
        Z: np.ndarray,
        p=4
) -> np.ndarray:
    """
    Contracts the linkage matrix by reducing the number of clusters
    to a specified number.

    Parameters
    ----------
    Z : np.ndarray
        The linkage matrix.
    p : int
        The number of clusters to retain.

    Returns
    -------
    np.ndarray
        The contracted linkage matrix with updated cluster IDs
        and member counts.
    """
    Z = Z.copy()
    truncated_Z = Z[-(p - 1):]

    n_points = Z.shape[0] + 1
    clusters = [
        dict(node_id=i, left=i, right=i, members=[i], distance=0, n_members=1)
        for i in range(n_points)
    ]
    for z_i in range(Z.shape[0]):
        row = Z[z_i]
        left = int(row[0])
        right = int(row[1])
        cluster = dict(
            node_id=z_i + n_points,
            left=left,
            right=right,
            members=[],
            distance=row[2],
            n_members=int(row[3])
        )
        cluster["members"].extend(copy.deepcopy(clusters[left]["members"]))
        cluster["members"].extend(copy.deepcopy(clusters[right]["members"]))
        cluster["members"].sort()
        clusters.append(cluster)

    node_map = []
    for i in range(truncated_Z.shape[0]):
        node_ids = [int(truncated_Z[i, 0]), int(truncated_Z[i, 1])]
        for cluster in clusters:
            if cluster['node_id'] in node_ids:
                node_map.append(cluster)

    filtered_node_map = []
    superset_node_map = []

    for node in node_map:
        is_superset = False
        for other_node in node_map:
            if (
                node != other_node
                    and set(
                        node['members']
                        ).issuperset(set(other_node['members']))
                    ):
                is_superset = True
                break
        if is_superset:
            superset_node_map.append(node)
        else:
            filtered_node_map.append(node)

    # Add 'truncated_id' to each dictionary in filtered_node_map
    for idx, node in enumerate(
        sorted(filtered_node_map, key=lambda x: x['members'][0])
            ):
        node['truncated_id'] = idx
        node['n_members'] = 1

    for idx, node in enumerate(
        sorted(superset_node_map, key=lambda x: x['node_id'])
            ):
        node['truncated_id'] = idx + len(filtered_node_map)

    # Adjust 'n_members' in superset_node_map to reflect
    # the number of filtered_node_map['members'] sets they contain
    for superset_node in superset_node_map:
        count = 0
        for filtered_node in filtered_node_map:
            if set(
                filtered_node['members']
                    ).issubset(set(superset_node['members'])):
                count += 1
        superset_node['n_members'] = count

    # Create a mapping from node_id to truncated_id and n_members
    node_id_to_truncated_id = {
        node['node_id']: node['truncated_id']
        for node in filtered_node_map + superset_node_map
    }
    node_id_to_n_members = {
        node['node_id']: node['n_members']
        for node in filtered_node_map + superset_node_map
    }

    # Replace values in truncated_Z
    for i in range(truncated_Z.shape[0]):
        truncated_Z[i, 3] = (
            node_id_to_n_members[int(truncated_Z[i, 0])] +
            node_id_to_n_members[int(truncated_Z[i, 1])]
        )
        truncated_Z[i, 0] = node_id_to_truncated_id[int(truncated_Z[i, 0])]
        truncated_Z[i, 1] = node_id_to_truncated_id[int(truncated_Z[i, 1])]

    return truncated_Z


def _contraction_mark_coordinates(
        Z: np.ndarray,
        p=4
 ) -> list:
    """
    Generates contraction marks for a given linkage matrix.

    Parameters
    ----------
    Z : np.ndarray
        The linkage matrix.
    p : int
        The number of clusters to retain.

    Returns
    -------
    list
        A sorted list of tuples where each tuple contains
        a calculated value based on truncated_id and a distance value.
    """
    Z = Z.copy()
    truncated_Z = Z[-(p-1):]

    n_points = Z.shape[0] + 1
    clusters = [dict(node_id=i,
                     left=i,
                     right=i,
                     members=[i],
                     distance=0,
                     n_members=1) for i in range(n_points)]
    for z_i in range(Z.shape[0]):
        row = Z[z_i]
        left = int(row[0])
        right = int(row[1])
        cluster = dict(
            node_id=z_i + n_points,
            left=left, right=right,
            members=[],
            distance=row[2],
            n_members=int(row[3])
            )
        cluster["members"].extend(copy.deepcopy(clusters[left]["members"]))
        cluster["members"].extend(copy.deepcopy(clusters[right]["members"]))
        cluster["members"].sort()
        clusters.append(cluster)

    node_map = []
    for i in range(truncated_Z.shape[0]):
        node_ids = [int(truncated_Z[i, 0]), int(truncated_Z[i, 1])]
        for cluster in clusters:
            if cluster['node_id'] in node_ids:
                node_map.append(cluster)

    filtered_node_map = []
    superset_node_map = []

    for node in node_map:
        is_superset = False
        for other_node in node_map:
            if (node != other_node
                    and set(node['members']
                            ).issuperset(set(other_node['members']))):
                is_superset = True
                break
        if is_superset:
            superset_node_map.append(node)
        else:
            filtered_node_map.append(node)

    # Create a set of node_ids from filtered_node_map and superset_node_map
    excluded_node_ids = set(
        node['node_id'] for node in filtered_node_map
            ).union(node['node_id'] for node in superset_node_map)

    # Filter clusters that are not in excluded_node_ids
    non_excluded_clusters = [
        cluster for cluster in clusters
        if cluster['node_id'] not in excluded_node_ids
        ]

    # Create a list to store the result
    subset_clusters = []

    # Iterate over filtered_node_map
    for filtered_cluster in filtered_node_map:
        distances = []
        for cluster in non_excluded_clusters:
            if (
                cluster['n_members'] > 1
                    and set(cluster['members']
                            ).issubset(set(filtered_cluster['members']))):
                distances.append(cluster['distance'])
        if distances:
            subset_clusters.append(
                {'node_id': filtered_cluster['node_id'], 'distance': distances}
                )

    # Add 'truncated_id' to each dictionary in filtered_node_map
    for idx, node in enumerate(
        sorted(filtered_node_map, key=lambda x: x['members'][0])
            ):
        node['truncated_id'] = idx

    # Create a mapping from node_id to truncated_id
    node_id_to_truncated_id = {
        node['node_id']: node['truncated_id'] for node in filtered_node_map
        }

    # Add 'truncated_id' to each dictionary in subset_clusters
    for cluster in subset_clusters:
        cluster['truncated_id'] = node_id_to_truncated_id[cluster['node_id']]

    # Create a list of tuples
    contraction_marks = []

    # Iterate over subset_clusters
    for cluster in subset_clusters:
        truncated_id = cluster['truncated_id']
        for distance in cluster['distance']:
            contraction_marks.append((10.0 * truncated_id + 5.0, distance))

    # Sort the list of tuples
    contraction_marks = sorted(contraction_marks, key=lambda x: (x[0], x[1]))

    return contraction_marks


def _convert_linkage_to_coordinates(
        Z: np.ndarray
) -> dict:
    """
    Converts a linkage matrix to coordinates for plotting a dendrogram.

    Parameters
    ----------
    Z : np.ndarray
        The linkage matrix.

    Returns
    -------
    dict
        A dictionary containing 'icoord', 'dcoord', and 'ivl'
        for plotting the dendrogram.
    """
    ivl = [i for i in range(Z.shape[0] + 1)]
    n = len(ivl)
    icoord = []
    dcoord = []
    clusters = {i: [i] for i in range(n)}
    current_index = n
    positions = {i: (i + 1) * 10 - 5 for i in range(n)}
    heights = {i: 0 for i in range(n)}

    for i in range(len(Z)):
        cluster1 = int(Z[i, 0])
        cluster2 = int(Z[i, 1])
        dist = Z[i, 2].item()
        new_cluster = clusters[cluster1] + clusters[cluster2]
        clusters[current_index] = new_cluster

        x1 = positions[cluster1]
        x2 = positions[cluster2]
        x_new = (x1 + x2) / 2
        positions[current_index] = x_new

        h1 = heights[cluster1]
        h2 = heights[cluster2]
        heights[current_index] = dist

        icoord.append([x1, x1, x2, x2])
        dcoord.append([h1, dist, dist, h2])

        current_index += 1

    # Sort icoord and dcoord by the first element in each icoord list
    sorted_indices = sorted(range(len(icoord)), key=lambda i: icoord[i][0])
    icoord = [icoord[i] for i in sorted_indices]
    dcoord = [dcoord[i] for i in sorted_indices]

    return {"icoord": icoord, "dcoord": dcoord, "ivl": ivl}


def _vnc_calculate_info(
        Z: np.ndarray,
        p=None,
        truncate=False,
        contraction_marks=False,
        labels=None
) -> dict:
    Z = Z.copy()
    Zs = Z.shape
    n = Zs[0] + 1

    if labels is not None:
        if Zs[0] + 1 != len(labels):
            labels = None
            print(dedent(
                """
                Dimensions of Z and labels are not consistent.
                Using defalut labels.
                """))
    if labels is None:
        labels = [str(i) for i in range(Zs[0] + 1)]
    else:
        labels = labels

    if p is not None and p > n or p < 2:
        p = None
        truncate = False
        contraction_marks = False

    if p is not None:
        cluster_assignment = [i.item() for i in _cut_tree_simple(Z, p)]

        # Create a dictionary to hold the clusters
        cluster_dict = {}

        # Iterate over the labels and clusters to populate the dictionary
        for label, cluster in zip(labels, cluster_assignment):
            cluster_key = f'cluster_{cluster + 1}'
            if cluster_key not in cluster_dict:
                cluster_dict[cluster_key] = []
            cluster_dict[cluster_key].append(label)

        # Convert the dictionary to a list of dictionaries
        cluster_list = [{key: value} for key, value in cluster_dict.items()]

        # Create a new list to hold the cluster labels
        cluster_labels = []

        # Iterate over the cluster_list to create the labels
        for cluster in cluster_list:
            for key, value in cluster.items():
                if len(value) == 1:
                    cluster_labels.append(str(value[0]))
                else:
                    cluster_labels.append(f"{value[0]}-{value[-1]}")

        # get distance for plotting cut line
        dist = [x[2].item() for x in Z]
        dist_threshold = np.mean(
            [dist[len(dist)-p+1], dist[len(dist)-p]]
        )
    else:
        dist_threshold = None
        cluster_list = None
        cluster_labels = None

    if truncate is True:
        truncated_Z = _contract_linkage_matrix(Z, p=p)

        if contraction_marks is True:
            contraction_marks = _contraction_mark_coordinates(Z, p=p)
        else:
            contraction_marks = None

        Z = truncated_Z
    else:
        Z = Z
        contraction_marks = None

    R = _convert_linkage_to_coordinates(Z)

    mh = np.max(Z[:, 2])
    Zn = Z.shape[0] + 1
    color_list = ['k'] * (Zn - 1)
    leaves_color_list = ['k'] * Zn
    R['n'] = Zn
    R['mh'] = mh
    R['p'] = p
    R['labels'] = labels
    R['color_list'] = color_list
    R['leaves_color_list'] = leaves_color_list
    R['clusters'] = cluster_list
    R['cluster_labels'] = cluster_labels
    R['dist_threshold'] = dist_threshold
    R["contraction_marks"] = contraction_marks

    return R


def _linkage_matrix(
        time_series,
        frequency,
        distance_measure='sd'
) -> np.ndarray:

    input_values = frequency.copy()
    years = time_series.copy()

    data_collector = {}
    data_collector["0"] = input_values
    position_collector = {}
    position_collector[1] = 0
    overall_distance = 0
    number_of_steps = len(input_values) - 1

    for i in range(1, number_of_steps + 1):
        difference_checker = []
        unique_years = np.unique(years)

        for j in range(len(unique_years) - 1):
            first_name = unique_years[j]
            second_name = unique_years[j + 1]
            pooled_sample = input_values[np.isin(years,
                                                 [first_name,
                                                  second_name])]

            if distance_measure == "sd":
                difference_checker.append(0 if np.sum(pooled_sample) == 0
                                          else np.std(pooled_sample, ddof=1))
            elif distance_measure == "cv":
                difference_checker.append(
                    0 if np.sum(pooled_sample) == 0
                    else np.std(pooled_sample, ddof=1) / np.mean(pooled_sample)
                    )

        pos_to_be_merged = np.argmin(difference_checker)
        distance = np.min(difference_checker)
        overall_distance += distance
        lower_name = unique_years[pos_to_be_merged]
        higher_name = unique_years[pos_to_be_merged + 1]

        matches = np.isin(years, [lower_name, higher_name])
        new_mean_age = round(np.mean(years[matches]), 4)
        position_collector[i + 1] = np.where(matches)[0] + 1
        years[matches] = new_mean_age
        data_collector[f"{i}: {distance}"] = input_values

    hc_build = pl.DataFrame({
        'start': [
            min(pos)
            if isinstance(pos, (list, np.ndarray))
            else pos for pos in position_collector.values()
            ],
        'end': [
            max(pos)
            if isinstance(pos, (list, np.ndarray))
            else pos for pos in position_collector.values()
            ]
    })

    idx = np.arange(len(hc_build))

    y = [np.where(
        hc_build['start'].to_numpy()[:i] == hc_build['start'].to_numpy()[i]
        )[0] for i in idx]
    z = [np.where(
        hc_build['end'].to_numpy()[:i] == hc_build['end'].to_numpy()[i]
        )[0] for i in idx]

    merge1 = [
        y[i].max().item() if len(y[i]) else np.nan for i in range(len(y))
        ]
    merge2 = [
        z[i].max().item() if len(z[i]) else np.nan for i in range(len(z))
        ]

    hc_build = (
        hc_build.with_columns([
            pl.Series('merge1',
                      [
                        min(m1, m2) if not np.isnan(m1) and
                        not np.isnan(m2)
                        else np.nan for m1, m2 in zip(merge1, merge2)
                        ]),
            pl.Series('merge2',
                      [
                        max(m1, m2) for m1, m2 in zip(merge1, merge2)
                        ])
                    ])
    )

    hc_build = (
        hc_build.with_columns([
            pl.Series('merge1', [
                min(m1, m2) if not np.isnan(m1) and
                not np.isnan(m2) else np.nan for m1, m2 in zip(merge1, merge2)
                ]),
            pl.Series('merge2', [
                max(m1, m2) if not np.isnan(m1)
                else m2 for m1, m2 in zip(merge1, merge2)
                ])
        ])
        )

    hc_build = (
        hc_build.with_columns([
            pl.when(
                pl.col('merge1').is_nan() &
                pl.col('merge2').is_nan()
                ).then(-pl.col('start')
                       ).otherwise(pl.col('merge1')).alias('merge1'),
            pl.when(
                pl.col('merge2')
                .is_nan()
                ).then(-pl.col('end')
                       ).otherwise(pl.col('merge2')).alias('merge2')
            ])
            )

    to_merge = [-np.setdiff1d(
        hc_build.select(
            pl.col('start', 'end')
            ).row(i),
        hc_build.select(
            pl.col('start', 'end')
            ).slice(1, i-1).to_numpy().flatten()
        ) for i in idx]

    to_merge = [x[0].item() if len(x) > 0 else np.nan for x in to_merge]

    hc_build = (
        hc_build
        .with_columns([
            pl.when(pl.col('merge1').is_nan()
                    ).then(pl.Series(to_merge, strict=False)
                           ).otherwise(pl.col('merge1')).alias('merge1')
                        ])
                    )

    hc_build = hc_build.with_row_index()
    n = hc_build.height

    hc_build = (hc_build
                .with_columns(
                    pl.when(pl.col("merge1").lt(0))
                    .then(pl.col("merge1").mul(-1).sub(1))
                    .otherwise(pl.col('merge1').add(n-1)).alias('merge1')
                    )
                .with_columns(
                    pl.when(pl.col("merge2").lt(0))
                    .then(pl.col("merge2").mul(-1).sub(1))
                    .otherwise(pl.col('merge2').add(n-1)).alias('merge2')
                    )
                )

    hc_build = (
        hc_build
        .with_columns(distance=np.array(list(data_collector.keys())))
        .with_columns(pl.col("distance").str.replace(r"(\d+: )", ""))
        .with_columns(pl.col("distance").cast(pl.Float64))
        .with_columns(pl.col("distance").cum_sum().alias("distance"))
        )

    size = np.array(
        [
            len(x) if isinstance(x, (list, np.ndarray))
            else 1 for x in position_collector.values()
        ])

    hc_build = (
        hc_build
        .with_columns(size=size)
        .with_columns(pl.col("size").cast(pl.Float64))
        )

    hc_build = hc_build.filter(pl.col("index") != 0)

    hc = hc_build.select("merge1", "merge2", "distance", "size").to_numpy()
    return hc


def _plot_dendrogram(
        icoords,
        dcoords,
        ivl,
        p,
        n,
        mh,
        orientation,
        no_labels,
        color_list,
        leaf_font_size=None,
        leaf_rotation=None,
        contraction_marks=None,
        ax=None,
        above_threshold_color='C0'
):
    # Import matplotlib here so that it's not imported unless dendrograms
    # are plotted. Raise an informative error if importing fails.
    try:
        # if an axis is provided, don't use pylab at all
        if ax is None:
            import matplotlib.pylab
        import matplotlib.patches
        import matplotlib.collections
    except ImportError as e:
        raise ImportError("You must install the matplotlib library to plot "
                          "the dendrogram. Use no_plot=True to calculate the "
                          "dendrogram without plotting.") from e

    if ax is None:
        ax = matplotlib.pylab.gca()
        # if we're using pylab, we want to trigger a draw at the end
        trigger_redraw = True
    else:
        trigger_redraw = False

    # Independent variable plot width
    ivw = len(ivl) * 10
    # Dependent variable plot height
    dvw = mh + mh * 0.05

    iv_ticks = np.arange(5, len(ivl) * 10 + 5, 10)
    if orientation in ('top', 'bottom'):
        if orientation == 'top':
            ax.set_ylim([0, dvw])
            ax.set_xlim([0, ivw])
        else:
            ax.set_ylim([dvw, 0])
            ax.set_xlim([0, ivw])

        xlines = icoords
        ylines = dcoords
        if no_labels:
            ax.set_xticks([])
            ax.set_xticklabels([])
        else:
            ax.set_xticks(iv_ticks)

            if orientation == 'top':
                ax.xaxis.set_ticks_position('bottom')
            else:
                ax.xaxis.set_ticks_position('top')

            # Make the tick marks invisible because they cover up the links
            for line in ax.get_xticklines():
                line.set_visible(False)

            leaf_rot = (float(_get_tick_rotation(len(ivl)))
                        if (leaf_rotation is None) else leaf_rotation)
            leaf_font = (float(_get_tick_text_size(len(ivl)))
                         if (leaf_font_size is None) else leaf_font_size)
            ax.set_xticklabels(ivl, rotation=leaf_rot, size=leaf_font)

    elif orientation in ('left', 'right'):
        if orientation == 'left':
            ax.set_xlim([dvw, 0])
            ax.set_ylim([0, ivw])
        else:
            ax.set_xlim([0, dvw])
            ax.set_ylim([0, ivw])

        xlines = dcoords
        ylines = icoords
        if no_labels:
            ax.set_yticks([])
            ax.set_yticklabels([])
        else:
            ax.set_yticks(iv_ticks)

            if orientation == 'left':
                ax.yaxis.set_ticks_position('right')
            else:
                ax.yaxis.set_ticks_position('left')

            # Make the tick marks invisible because they cover up the links
            for line in ax.get_yticklines():
                line.set_visible(False)

            leaf_font = (float(_get_tick_text_size(len(ivl)))
                         if (leaf_font_size is None) else leaf_font_size)

            if leaf_rotation is not None:
                ax.set_yticklabels(ivl, rotation=leaf_rotation, size=leaf_font)
            else:
                ax.set_yticklabels(ivl, size=leaf_font)

    # Let's use collections instead. This way there is a separate legend item
    # for each tree grouping, rather than stupidly one for each line segment.
    colors_used = _remove_dups(color_list)
    color_to_lines = {}
    for color in colors_used:
        color_to_lines[color] = []
    for (xline, yline, color) in zip(xlines, ylines, color_list):
        color_to_lines[color].append(list(zip(xline, yline)))

    colors_to_collections = {}
    # Construct the collections.
    for color in colors_used:
        coll = matplotlib.collections.LineCollection(color_to_lines[color],
                                                     colors=(color,))
        colors_to_collections[color] = coll

    # Add all the groupings below the color threshold.
    for color in colors_used:
        if color != above_threshold_color:
            ax.add_collection(colors_to_collections[color])
    # If there's a grouping of links above the color threshold, it goes last.
    if above_threshold_color in colors_to_collections:
        ax.add_collection(colors_to_collections[above_threshold_color])

    if contraction_marks is not None:
        Ellipse = matplotlib.patches.Ellipse
        for (x, y) in contraction_marks:
            if orientation in ('left', 'right'):
                e = Ellipse((y, x), width=dvw / 100, height=1.0)
            else:
                e = Ellipse((x, y), width=1.0, height=dvw / 100)
            ax.add_artist(e)
            e.set_clip_box(ax.bbox)
            e.set_alpha(0.5)
            e.set_facecolor('k')

    if trigger_redraw:
        matplotlib.pylab.draw_if_interactive()
