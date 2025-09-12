import polars as pl
import pytest

from google_ngrams import TimeSeries


def make_ts(n: int = 20):
    # Years 1900..(1900+n-1) and a bit of signal with noise
    years = list(range(1900, 1900 + n))
    # two regimes with noise to avoid perfect fit
    rf = [10.0 + (i % 3) * 0.5 for i in range(n // 2)] + [
        40.0 + (i % 4) * 0.5 for i in range(n - n // 2)
    ]
    return pl.DataFrame({"Year": years, "RF": rf})


def test_timeseries_validation_errors():
    df_missing_year = pl.DataFrame({
        "Y": [1900, 1901, 1902],
        "RF": [1.0, 2.0, 3.0],
    })
    with pytest.raises(ValueError):
        TimeSeries(df_missing_year, time_col="Year", values_col="RF")

    df_missing_rf = pl.DataFrame({
        "Year": [1900, 1901, 1902],
        "value": [1.0, 2.0, 3.0],
    })
    with pytest.raises(ValueError):
        TimeSeries(df_missing_rf, time_col="Year", values_col="RF")

    # Non-float RF should error
    df_int_rf = pl.DataFrame({"Year": [1900, 1901, 1902], "RF": [1, 2, 3]})
    with pytest.raises(ValueError):
        TimeSeries(df_int_rf, time_col="Year", values_col="RF")


def test_timeseries_init_and_distances():
    ts = TimeSeries(make_ts(), time_col="Year", values_col="RF")
    # linkage matrices should be (n-1) x 4
    assert ts.Z_sd.shape == (len(ts.time_intervals) - 1, 4)
    assert ts.Z_cv.shape == (len(ts.time_intervals) - 1, 4)
    # distances arrays length n-1
    assert len(ts.distances_sd) == len(ts.time_intervals) - 1
    assert len(ts.distances_cv) == len(ts.time_intervals) - 1


def test_timeseries_plots_smoke():
    ts = TimeSeries(make_ts(), time_col="Year", values_col="RF")
    # Barplot
    fig = ts.timeviz_barplot()
    assert fig is not None
    # Scatter with smoothing; choose high smoothing value to reduce df
    fig = ts.timeviz_scatterplot(smoothing=9, confidence_interval=False)
    assert fig is not None
    # Scree
    fig = ts.timeviz_screeplot(distance="sd")
    assert fig is not None


def test_timeseries_vnc_and_cluster_summary(capsys):
    ts = TimeSeries(make_ts(), time_col="Year", values_col="RF")
    # Horizontal, non-periodized with cut line
    fig = ts.timeviz_vnc(n_periods=2, distance="sd", orientation="horizontal")
    assert fig is not None

    # After plotting, clusters should be available
    assert ts.clusters is not None
    assert isinstance(ts.clusters, list)
    assert len(ts.clusters) == 2  # 2 clusters requested

    # Print summary and capture output
    ts.cluster_summary()
    out = capsys.readouterr().out
    assert "Cluster 1" in out and "Cluster 2" in out

    # Periodized vertical plot
    fig = ts.timeviz_vnc(
        n_periods=2,
        distance="cv",
        orientation="vertical",
        periodize=True,
        hide_labels=True,
    )
    assert fig is not None
