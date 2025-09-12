import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from .scatter_helpers import gam_smoother
from .vnc_helpers import (
    _linkage_matrix,
    _vnc_calculate_info,
    _plot_dendrogram
)


class TimeSeries:

    def __init__(self,
                 time_series: pl.DataFrame,
                 time_col: str,
                 values_col: str):

        time = time_series.get_column(time_col, default=None)
        values = time_series.get_column(values_col, default=None)

        if time is None:
            raise ValueError("""
                Invalid column.
                Check name. Couldn't find column in DataFrame.
                    """)
        if values is None:
            raise ValueError("""
                Invalid column.
                Check name. Couldn't find column in DataFrame.
                """)
        if not isinstance(values.dtype, (pl.Float64, pl.Float32)):
            raise ValueError("""
                Invalid DataFrame.
                Expected a column of normalized frequencies.
                """)
        if len(time) != len(values):
            raise ValueError("""
                Your time and values vectors must be the same length.
                """)

        time_series = time_series.sort(time)
        self.time_intervals = time_series.get_column(time_col).to_numpy()
        self.frequencies = time_series.get_column(values_col).to_numpy()
        self.Z_sd = _linkage_matrix(time_series=self.time_intervals,
                                    frequency=self.frequencies)
        self.Z_cv = _linkage_matrix(time_series=self.time_intervals,
                                    frequency=self.frequencies,
                                    distance_measure='cv')
        self.distances_sd = np.array([self.Z_sd[i][2].item()
                                      for i in range(len(self.Z_sd))])
        self.distances_cv = np.array([self.Z_cv[i][2].item()
                                      for i in range(len(self.Z_cv))])

        self.clusters = None
        self.distance_threshold = None

    def timeviz_barplot(
            self,
            width=8,
            height=4,
            dpi=150,
            barwidth=4,
            fill_color='#440154',
            tick_interval=None,
            label_rotation=None
    ) -> Figure:
        """
        Generate a bar plot of token frequenices over time.

        Parameters
        ----------
        width:
            The width of the plot.
        height:
            The height of the plot.
        dpi:
            The resolution of the plot.
        barwidth:
            The width of the bars.
        fill_color:
            The color of the bars.
        tick_interval:
            Interval spacing for the tick labels.
        label_rotation:
            Angle used to rotate tick labels.

        Returns
        -------
        Figure
            A matplotlib figure.

        """
        xx = self.time_intervals
        yy = self.frequencies

        if label_rotation is None:
            rotation = 90
        else:
            rotation = label_rotation

        if tick_interval is None:
            interval = np.diff(xx)[0]
        else:
            interval = tick_interval

        start_value = np.min(xx)

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        ax.bar(xx, yy, color=fill_color, edgecolor='black',
               linewidth=.5, width=barwidth)

        ax.set_ylabel('Frequency (per mil. words)')

        # Despine
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=.5)

        ax.tick_params(axis="x", which="both", labelrotation=rotation)
        ax.grid(axis='y', color='w', linestyle='--', linewidth=.5)
        # Attempt to use newer matplotlib MultipleLocator with offset.
        # Older versions (<3.8) don't support the 'offset' kwarg, so we
        # gracefully fall back and manually align ticks.
        try:
            ax.xaxis.set_major_locator(
                plt.MultipleLocator(base=interval, offset=start_value)
            )
        except TypeError:
            # Fallback: no offset support. Use basic locator and, if needed,
            # force tick positions to start at the first time value.
            ax.xaxis.set_major_locator(plt.MultipleLocator(interval))
            # If the first tick that would be drawn by the locator would not
            # coincide with the first bar (start_value), set explicit ticks.
            if start_value % interval != 0:
                ticks = np.arange(start_value, xx.max() + interval, interval)
                ax.set_xticks(ticks)
        except Exception:
            # Last-resort: just set ticks to the observed time points.
            ax.set_xticks(xx)

        return fig

    def timeviz_scatterplot(
            self,
            width=8,
            height=4,
            dpi=150,
            point_color='black',
            point_size=0.5,
            smoothing=7,
            confidence_interval=True
    ) -> Figure:
        """
        Generate a scatter plot of token frequenices over time
        with a smoothed fit line and a confidence interval.

        Parameters
        ----------
        width:
            The width of the plot.
        height:
            The height of the plot.
        dpi:
            The resolution of the plot.
        point_color:
            The color of the points.
        point_size:
            The size of the points.
        smoothing:
            A value between 1 and 9 specifying magnitude of smoothing.
        confidence_interval:
            Whether to plot a confidence interval.

        Returns
        -------
        Figure
            A matplotlib figure.

        """
        if 0 < smoothing and smoothing < 10:
            smoothing = smoothing
        else:
            smoothing = 7

        xx = self.time_intervals
        yy = self.frequencies

        # Lightweight spline-based smoother with optional bootstrap CI
        sm = gam_smoother(xx, yy, smoothing=smoothing, ci=confidence_interval)
        fit_line = sm.y_fit
        upper = sm.y_upper if confidence_interval else None
        lower = sm.y_lower if confidence_interval else None

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # plot fit line
        ax.plot(xx, fit_line, color='tomato', linewidth=.5)

        # add confidence interval
        if (
            confidence_interval is True and
            lower is not None and upper is not None
        ):
            ax.fill_between(xx, lower, upper, color='grey', alpha=0.2)

        ax.scatter(xx, yy, s=point_size, color=point_color, alpha=0.75)
        ax.set_ylabel('Frequency (per mil. words)')

        # Despine
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        ticks = [tick for tick in plt.gca().get_yticks() if tick >= 0]
        plt.gca().set_yticks(ticks)

        return fig

    def timeviz_screeplot(self,
                          width=6,
                          height=3,
                          dpi=150,
                          point_size=0.75,
                          distance="sd") -> Figure:
        """
        Generate a scree plot for determining clusters.

        Parameters
        ----------
        width:
            The width of the plot.
        height:
            The height of the plot.
        dpi:
            The resolution of the plot.
        point_size:
            The size of the points.
        distance:
            One of 'sd' (standard deviation)
            or 'cv' (coefficient of variation).

        Returns
        -------
        Figure
            A matplotlib figure.

        """
        dist_types = ['sd', 'cv']
        if distance not in dist_types:
            distance = "sd"

        if distance == "cv":
            dist = self.distances_cv
        else:
            dist = self.distances_sd

        # SCREEPLOT
        yy = dist[::-1]
        xx = np.array([i for i in range(1, len(yy) + 1)])
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        ax.scatter(x=xx,
                   y=yy,
                   marker='o',
                   s=point_size,
                   facecolors='none',
                   edgecolors='black')
        ax.set_xlabel('Clusters')
        ax.set_ylabel(f'Distance (in summed {distance})')

        # Despine
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        return fig

    def timeviz_vnc(self,
                    width=6,
                    height=4,
                    dpi=150,
                    font_size=10,
                    n_periods=1,
                    distance="sd",
                    orientation="horizontal",
                    cut_line=False,
                    periodize=False,
                    hide_labels=False) -> Figure:
        """
        Generate a dendrogram  using the clustering method,
        "Variability-based Neighbor Clustering"(VNC),
        to identify periods in the historical development
        of P that accounts for the temporal ordering of the data.

        Parameters
        ----------
        width:
            The width of the plot.
        height:
            The height of the plot.
        dpi:
            The resolution of the plot.
        font_size:
            The font size for the labels.
        n_periods:
            The number of periods (or clusters).
        distance:
            One of 'sd' (standard deviation)
            or 'cv' (coefficient of variation).
        orientation:
            The orientation of the plot,
            either 'horizontal' or 'vertical'.
        cut_line:
            Whether or not to include a cut line;
            applies only to non-periodized plots.
        periodize:
            The dendrogram can be hard to read when the original
            observation matrix from which the linkage is derived is
            large. Periodization is used to condense the dendrogram.
        hide_labels:
            Whether or not to hide leaf labels.

        Returns
        -------
        Figure
            A matplotlib figure.

        """
        dist_types = ['sd', 'cv']
        if distance not in dist_types:
            distance = "sd"
        orientation_types = ['horizontal', 'vertical']
        if orientation not in orientation_types:
            orientation = "horizontal"

        if distance == "cv":
            Z = self.Z_cv
        else:
            Z = self.Z_sd

        if n_periods > len(Z):
            n_periods = 1
            periodize = False

        if n_periods > 1 and n_periods <= len(Z) and periodize is not True:
            cut_line = True

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Plot the corresponding dendrogram
        if orientation == "horizontal" and periodize is not True:
            X = _vnc_calculate_info(Z,
                                    p=n_periods,
                                    labels=self.time_intervals)

            self.clusters = X['clusters']

            _plot_dendrogram(icoords=X['icoord'],
                             dcoords=X['dcoord'],
                             ivl=X['ivl'],
                             color_list=X['color_list'],
                             mh=X['mh'],
                             orientation='top',
                             p=X['p'],
                             n=X['n'],
                             no_labels=False)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.set_ylabel(f'Distance (in summed {distance})')

            if hide_labels is not True:
                ax.set_xticklabels(X['labels'],
                                   fontsize=font_size,
                                   rotation=90)
            else:
                ax.set_xticklabels([])

            plt.setp(ax.collections, linewidth=.5)

            if cut_line and X['dist_threshold'] is not None:
                ax.axhline(y=X['dist_threshold'],
                           color='r',
                           alpha=0.7,
                           linestyle='--',
                           linewidth=.5)

        if orientation == "horizontal" and periodize is True:
            X = _vnc_calculate_info(Z,
                                    truncate=True,
                                    p=n_periods,
                                    contraction_marks=True,
                                    labels=self.time_intervals)

            self.clusters = X['clusters']

            _plot_dendrogram(
                icoords=X['icoord'],
                dcoords=X['dcoord'],
                ivl=X['ivl'],
                color_list=X['color_list'],
                mh=X['mh'],
                orientation='top',
                p=X['p'],
                n=X['n'],
                no_labels=False,
                contraction_marks=X['contraction_marks'])

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.set_ylabel(f'Distance (in summed {distance})')

            if hide_labels is not True:
                ax.set_xticklabels(X['cluster_labels'],
                                   fontsize=font_size,
                                   rotation=90)
            else:
                ax.set_xticklabels([])

            plt.setp(ax.collections, linewidth=.5)

        if orientation == "vertical" and periodize is not True:
            X = _vnc_calculate_info(Z,
                                    p=n_periods,
                                    labels=self.time_intervals)

            self.clusters = X['clusters']

            _plot_dendrogram(
                icoords=X['icoord'],
                dcoords=X['dcoord'],
                ivl=X['ivl'],
                color_list=X['color_list'],
                mh=X['mh'],
                orientation='right',
                p=X['p'],
                n=X['n'],
                no_labels=False)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_xlabel(f'Distance (in summed {distance})')

            if hide_labels is not True:
                ax.set_yticklabels(X['labels'],
                                   fontsize=font_size,
                                   rotation=0)
            else:
                ax.set_yticklabels([])

            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymax, ymin)
            plt.setp(ax.collections, linewidth=.5)

            if cut_line and X['dist_threshold'] is not None:
                ax.axvline(x=X['dist_threshold'],
                           color='r',
                           alpha=0.7,
                           linestyle='--',
                           linewidth=.5)

        if orientation == "vertical" and periodize is True:
            X = _vnc_calculate_info(Z,
                                    truncate=True,
                                    p=n_periods,
                                    contraction_marks=True,
                                    labels=self.time_intervals)

            self.clusters = X['clusters']

            _plot_dendrogram(
                icoords=X['icoord'],
                dcoords=X['dcoord'],
                ivl=X['ivl'],
                color_list=X['color_list'],
                mh=X['mh'],
                orientation='right',
                p=X['p'],
                n=X['n'],
                no_labels=False,
                contraction_marks=X['contraction_marks'])

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_xlabel(f'Distance (in summed {distance})')

            if hide_labels is not True:
                ax.set_yticklabels(X['cluster_labels'],
                                   fontsize=font_size,
                                   rotation=0)
            else:
                ax.set_yticklabels([])

            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymax, ymin)
            plt.setp(ax.collections, linewidth=.5)

        return fig

    def cluster_summary(self):
        """
        Print a summary of cluster membership.

        Returns
        -------
            Prints to the console.

        """
        cluster_list = self.clusters
        if cluster_list is not None:
            for i, cluster in enumerate(cluster_list, start=1):
                for key, value in cluster.items():
                    print(f"Cluster {i} (n={len(value)}): {[str(v) for v in value]}")  # noqa: E501
        else:
            print("No clusters to summarize.")
