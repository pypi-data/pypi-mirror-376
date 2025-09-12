import os
import re
import polars as pl
import warnings
import logging
from textwrap import dedent
from typing import List
from .data import sources


def google_ngram(
        word_forms: List[str],
        variety="eng",
        by="decade"
) -> pl.DataFrame:
    """
    Fetches Google Ngram data for specified word forms.

    This function retrieves ngram data from the Google Books Ngram Viewer
    for the given word forms. It supports different varieties of English
    (e.g., British, American) and allows aggregation by year or decade.

    Parameters
    ----------
    word_forms : List
        List of word forms to search for.
    variety : str
        Variety of English ('eng', 'gb', 'us').
    by : str
        Aggregation level ('year' or 'decade').

    Returns
    -------
    pl.DataFrame
        DataFrame containing the ngram data.
    """
    variety_types = ["eng", "gb", "us"]
    if variety not in variety_types:
        raise ValueError("""variety_types
                         Invalid variety type. Expected one of: %s
                         """ % variety_types)
    by_types = ["year", "decade"]
    if by not in by_types:
        raise ValueError("""variety_types
                         Invalid by type. Expected one of: %s
                         """ % by_types)
    word_forms = [re.sub(r'([a-zA-Z0-9])-([a-zA-Z0-9])',
                         r'\1 - \2', wf) for wf in word_forms]
    word_forms = [wf.strip() for wf in word_forms]
    n = [len(re.findall(r'\S+', wf)) for wf in word_forms]
    n = list(set(n))

    if len(n) > 1:
        raise ValueError("""Check spelling.
                         Word forms should be lemmas of the same word
                         (e.g. 'teenager' and 'teenagers'
                         or 'walk', 'walks' and 'walked'
                         """)
    if n[0] > 5:
        raise ValueError("""Ngrams can be a maximum of 5 tokens.
                         Hyphenated words are split and include the hyphen,
                         so 'x-ray' would count as 3 tokens.
                         """)

    gram = [wf[:2] if n[0] > 1 else wf[:1] for wf in word_forms]
    gram = list(set([g.lower() for g in gram]))

    if len(gram) > 1:
        raise ValueError("""Check spelling.
                         Word forms should be lemmas of the same word
                         (e.g. 'teenager' and 'teenagers'
                         or 'walk', 'walks' and 'walked'
                         """)

    if re.match(r'^[a-z][^a-z]', gram[0]):
        gram[0] = re.sub(r'[^a-z]', '_', gram[0])
    if re.match(r'^[0-9]', gram[0]):
        gram[0] = gram[0][:1]
    if re.match(r'^[\W]', gram[0]):
        gram[0] = "punctuation"

    if any(re.match(r'^[ßæðøłœıƒþȥəħŋªºɣđĳɔȝⅰʊʌʔɛȡɋⅱʃɇɑⅲ]', g) for g in gram):
        gram[0] = "other"

    gram[0] = gram[0].encode('latin-1', 'replace').decode('latin-1')

    # Use HTTPS for integrity (Google Storage supports it) instead of HTTP
    if variety == "eng":
        repo = f"https://storage.googleapis.com/books/ngrams/books/googlebooks-eng-all-{n[0]}gram-20120701-{gram[0]}.gz"  # noqa: E501
    else:
        repo = f"https://storage.googleapis.com/books/ngrams/books/googlebooks-eng-{variety}-all-{n[0]}gram-20120701-{gram[0]}.gz"  # noqa: E501

    logger = logging.getLogger(__name__)
    logger.info(dedent(
        """
        Accessing repository. For larger ones
        (e.g., ngrams containing 2 or more words).
        This may take a few minutes...
        """
    ))

    # Preserve exact tokens for equality filtering in non-regex fallbacks
    tokens_exact = list(word_forms)
    word_forms = [re.sub(
        r'(\.|\?|\$|\^|\)|\(|\}|\{|\]|\[|\*|\+|\|)',
        r'\\\1', wf
        ) for wf in word_forms]

    grep_words = "|".join([f"^{wf}$" for wf in word_forms])

    # Read the data from the google repository and format
    schema = {"column_1": pl.String,
              "column_2": pl.Int64,
              "column_3": pl.Int64,
              "column_4": pl.Int64}
    try:
        df = pl.scan_csv(
            repo,
            separator='\t',
            has_header=False,
            schema=schema,
            truncate_ragged_lines=True,
            low_memory=True,
            quote_char=None,
            ignore_errors=True,
        )
    except TypeError:
        # Fallback for environments/tests that monkeypatch scan_csv with a
        # limited signature. Use minimal, widely-supported args.
        df = pl.scan_csv(repo, separator='\t', has_header=False, schema=schema)
    # Push down filter and projection before collection to minimize memory
    filtered_df = (
        df
        .filter(pl.col("column_1").str.contains(r"(?i)" + grep_words))
        .select([
            pl.col("column_1").alias("Token"),
            pl.col("column_2").alias("Year"),
            pl.col("column_3").alias("AF"),
        ])
    )

    # Optional: allow tuning streaming batch size via env
    try:
        chunk_sz = os.environ.get("POLARS_STREAMING_CHUNK_SIZE")
        if chunk_sz:
            pl.Config.set_streaming_chunk_size(int(chunk_sz))
    except Exception:
        pass

    # Collect with streaming fallback for stability across polars versions
    try:
        logger.debug("Collecting with engine='streaming'.")
        all_grams = filtered_df.collect(engine="streaming")
    except Exception:
        try:
            # Older streaming path (deprecated in newer Polars)
            logger.debug("Collecting with deprecated streaming=True path.")
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    category=DeprecationWarning,
                    message=r"the `streaming` parameter was deprecated.*",
                )
                all_grams = filtered_df.collect(  # type: ignore[arg-type]
                    streaming=True
                )
        except Exception:
            try:
                # Plain in-memory collect
                logger.debug(
                    "Collecting with in-memory engine (no streaming)."
                )
                all_grams = filtered_df.collect()
            except Exception:
                # Final memory-safe fallback: batched CSV reader with
                # per-batch filter
                logger.debug(
                    "Falling back to batched CSV reader + per-batch filter."
                )
                batch_sz = int(
                    os.environ.get("POLARS_CSV_BATCH_SIZE", "200000")
                )
                try:
                    reader = pl.read_csv_batched(
                        repo,
                        separator='\t',
                        has_header=False,
                        ignore_errors=True,
                        low_memory=True,
                        batch_size=batch_sz,
                    )
                    filtered_batches = []
                    # Prefer equality match for speed and stability
                    try:
                        for batch in reader:  # type: ignore[assignment]
                            fb = (
                                batch
                                .filter(pl.col("column_1").is_in(tokens_exact))
                                .select([
                                    pl.col("column_1").alias("Token"),
                                    pl.col("column_2").alias("Year"),
                                    pl.col("column_3").alias("AF"),
                                ])
                            )
                            if fb.height:
                                filtered_batches.append(fb)
                    except TypeError:
                        # Fallback for alternate reader APIs
                        while True:
                            try:
                                batches = reader.next_batches(1)
                            except AttributeError:
                                break
                            if not batches:
                                break
                            batch = batches[0]
                            fb = (
                                batch
                                .filter(pl.col("column_1").is_in(tokens_exact))
                                .select([
                                    pl.col("column_1").alias("Token"),
                                    pl.col("column_2").alias("Year"),
                                    pl.col("column_3").alias("AF"),
                                ])
                            )
                            if fb.height:
                                filtered_batches.append(fb)

                    if filtered_batches:
                        all_grams = pl.concat(filtered_batches)
                    else:
                        all_grams = pl.DataFrame({
                            "Token": pl.Series([], dtype=pl.String),
                            "Year": pl.Series([], dtype=pl.Int64),
                            "AF": pl.Series([], dtype=pl.Int64),
                        })
                except Exception as e:
                    # If batched reader is unavailable, re-raise with guidance
                    raise RuntimeError(
                        "Polars batched CSV reader fallback failed; consider "
                        "upgrading Polars or disabling this code path via "
                        "environment if necessary."
                    ) from e

    # read totals
    if variety == "eng":
        f_path = sources.get("eng_all")
    elif variety == "gb":
        f_path = sources.get("gb_all")
    elif variety == "us":
        f_path = sources.get("us_all")

    total_counts = pl.read_parquet(f_path)
    # format totals, fill missing data, and sum
    total_counts = total_counts.cast({
        "Year": pl.UInt32,
        "Total": pl.UInt64,
        "Pages": pl.UInt64,
        "Volumes": pl.UInt64,
    })

    total_counts = (
        total_counts
        .with_columns(
            pl.col("Year")
            .cast(pl.String).str.to_datetime("%Y")
            )
        .sort("Year")
        .upsample(time_column="Year", every="1y")
        .with_columns(
            pl.col(["Total", "Pages", "Volumes"])
            .fill_null(strategy="zero")
            )
            )
    total_counts = (
        total_counts
        .group_by_dynamic(
            "Year", every="1y"
        ).agg(pl.col("Total").sum())
    )

    # sum token totals, convert to datetime and fill in missing years
    sum_tokens = (
        all_grams
        .group_by("Year", maintain_order=True)
        .agg(pl.col("AF").sum())
    )
    sum_tokens = (
        sum_tokens
        .with_columns(
            pl.col("Year")
            .cast(pl.String).str.to_datetime("%Y")
            )
        .sort("Year")
        .upsample(time_column="Year", every="1y")
        .with_columns(
                pl.col("AF")
                .fill_null(strategy="zero")
                )
        )
    # join with totals
    sum_tokens = sum_tokens.join(total_counts, on="Year", how="right")
    # Fill any missing AF created by the join (years with no token hits)
    sum_tokens = sum_tokens.with_columns(
        pl.col("AF").fill_null(strategy="zero")
    )

    if by == "decade":
        sum_tokens = (
            sum_tokens
            .group_by_dynamic("Year", every="10y")
            .agg(pl.col(["AF", "Total"]).sum())
        )
    # normalize RF per million tokens
    sum_tokens = (
        sum_tokens
        .with_columns(
            RF=pl.col("AF").truediv("Total").mul(1000000)
            )
        .with_columns(
            pl.col("RF").fill_nan(0)
            )
    )
    sum_tokens.insert_column(1, (pl.lit(word_forms)).alias("Token"))
    sum_tokens = (
        sum_tokens
        .with_columns(
            pl.col("Year").dt.year().alias("Year")
            )
        .drop("Total")
        )

    if by == "decade":
        # Avoid .rename to prevent potential segfaults
        sum_tokens = (
            sum_tokens
            .with_columns(pl.col("Year").alias("Decade"))
            .drop("Year")
        )

    return sum_tokens
