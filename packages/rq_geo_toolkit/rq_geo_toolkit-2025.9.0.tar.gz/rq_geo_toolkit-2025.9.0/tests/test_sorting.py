"""Tests for sorting and compressing geoparquet files."""

import tempfile
from pathlib import Path

import pyarrow.parquet as pq
from tqdm import tqdm

from rq_geo_toolkit.duckdb import set_up_duckdb_connection
from rq_geo_toolkit.geoparquet_compression import compress_parquet_with_duckdb
from rq_geo_toolkit.geoparquet_sorting import sort_geoparquet_file_by_geometry


def test_sorting() -> None:
    """Test if sorted file is smaller and metadata in both files is equal."""
    download_file_url = (
        "s3://overturemaps-us-west-2/release/2024-08-20.0/theme=places/type=place/"
        "part-00002-93118862-ebe9-4b31-8277-1a87d792bd5d-c000.zstd.parquet"
    )
    save_path = Path("files/unsorted_example.parquet")
    save_path.parent.mkdir(exist_ok=True, parents=True)

    query = f"""
    COPY (
        SELECT id, geometry
        FROM read_parquet('{download_file_url}')
        USING SAMPLE 100%
    ) TO '{save_path}' (FORMAT parquet);
    """
    with tempfile.TemporaryDirectory(dir=save_path.parent.resolve()) as tmp_dir_name:
        tmp_dir_path = Path(tmp_dir_name)

        if not save_path.exists():
            with set_up_duckdb_connection(
                tmp_dir_path=tmp_dir_path, preserve_insertion_order=True
            ) as connection:
                connection.execute(query)

        unsorted_pq = compress_parquet_with_duckdb(
                input_file_path=save_path,
                output_file_path=tmp_dir_path / "unsorted.parquet",
                working_directory=tmp_dir_path,
            )

        total_rows = pq.read_metadata(save_path).num_rows
        last_rows = 0

        with tqdm(total=total_rows) as pbar:
            def report_progress(n: int) -> None:
                nonlocal last_rows, pbar
                diff = n - last_rows
                pbar.update(diff)
                last_rows = n

            sorted_pq = sort_geoparquet_file_by_geometry(
                input_file_path=save_path,
                output_file_path=tmp_dir_path / "sorted.parquet",
                working_directory=tmp_dir_path,
                remove_input_file=False,
                progress_callback=report_progress,
            )

        assert pq.read_schema(unsorted_pq).equals(pq.read_schema(sorted_pq))
        assert pq.read_metadata(unsorted_pq).num_rows == pq.read_metadata(sorted_pq).num_rows

        assert unsorted_pq.stat().st_size > sorted_pq.stat().st_size
