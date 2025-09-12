import polars as pl
import pytest

from google_ngrams import google_ngram


def test_google_ngram_invalid_variety():
    with pytest.raises(ValueError):
        google_ngram(["walk"], variety="xx")


def test_google_ngram_invalid_by():
    with pytest.raises(ValueError):
        google_ngram(["walk"], by="century")


def test_google_ngram_mixed_ngram_lengths():
    with pytest.raises(ValueError):
        google_ngram(["teenager", "high school"])  # 1-gram vs 2-gram


def test_google_ngram_too_many_tokens():
    tokens = "a b c d e f"  # 6 tokens
    with pytest.raises(ValueError):
        google_ngram([tokens])


def test_google_ngram_happy_path_year(patch_polars_io):
    df = google_ngram(["walk", "walked", "walks"], variety="eng", by="year")
    # Expected columns
    expect_cols = {"Year", "Token", "AF", "RF"}
    assert expect_cols.issubset(set(df.columns))

    # Should span years from our fixture
    years = df["Year"].to_list()
    assert min(years) == 1900 and max(years) == 1903

    # RF should be AF / Total * 1_000_000
    # In 1900, AF = 100 + 50 + 30 = 180; Total=1_000_000 => 180 per mil
    row_1900 = df.filter(pl.col("Year") == 1900).select(["AF", "RF"]).row(0)
    assert row_1900[0] == 180  # AF
    assert pytest.approx(row_1900[1], rel=1e-6) == 180.0


def test_google_ngram_happy_path_decade(patch_polars_io):
    df = google_ngram(["walk", "walked", "walks"], by="decade")
    # For our tiny fixture 1900-1903, one decade bucket
    assert set(df.columns) == {"Decade", "Token", "AF", "RF"}
    assert df.height == 1
    row = df.select(["AF", "RF"]).row(0)
    # AF sums across years
    assert row[0] == (180 + 200)  # year 1900 AF=180, 1901 AF=200
    # totals: per-year 1_000_000 for 1900-1903 => 4_000_000 in the decade bin
    # (AF for 1902/1903 are zero in our fixture, but totals still sum)
    expected_rf = (180 + 200) / 4_000_000 * 1_000_000
    assert pytest.approx(row[1], rel=1e-6) == expected_rf
