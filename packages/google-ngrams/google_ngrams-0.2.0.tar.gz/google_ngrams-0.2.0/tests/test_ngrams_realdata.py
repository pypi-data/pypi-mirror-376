from pathlib import Path

import polars as pl
import pytest

from google_ngrams import google_ngram
from google_ngrams.data import sources


@pytest.fixture
def patch_scan_to_local(monkeypatch):
    """
    Patch polars.scan_csv to read the small local gz test file instead of
    fetching from the remote Google repository.
    """
    local = (
        Path(__file__).parent
        / "test_data"
        / "googlebooks-eng-all-2gram-20120701-zz.gz"
    )
    original_scan = pl.scan_csv

    def fake_scan_csv(
        url, separator="\t", has_header=False, schema=None, **kwargs
    ):
        # Delegate to original scan_csv but point to local gz file
        # and preserve any additional keyword args used by the code
        return original_scan(
            str(local),
            separator=separator,
            has_header=has_header,
            schema=schema,
            **kwargs,
        )

    monkeypatch.setattr(pl, "scan_csv", fake_scan_csv)
    return True


def test_google_ngram_realdata_years_and_rf(patch_scan_to_local):
    # Token present in the sample file
    token = "ZZ Z_NOUN"
    df = google_ngram([token], variety="eng", by="year")

    # Expect at least one known year from the sample
    years = df["Year"].to_list()
    assert 1913 in years

    # AF for 1913 from the sample file is 9
    row = df.filter(pl.col("Year") == 1913).select(["AF", "RF"]).row(0)
    af, rf = row
    assert af == 9

    # Compute expected RF using the real totals parquet shipped in package
    totals = pl.read_parquet(sources["eng_all"])
    total_1913 = (
        totals.filter(pl.col("Year") == 1913)
        .select("Total")
        .item()
    )
    expected_rf = af / total_1913 * 1_000_000
    assert pytest.approx(rf, rel=1e-9) == expected_rf
