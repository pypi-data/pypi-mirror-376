"""Helper functions for DuckDB."""

import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from math import ceil
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any, Optional, Union

import duckdb
import psutil
from packaging import version
from rich import print as rprint

from rq_geo_toolkit.constants import MEMORY_1GB
from rq_geo_toolkit.multiprocessing_utils import WorkerProcess, run_process_with_memory_monitoring

if TYPE_CHECKING:  # pragma: no cover
    from rq_geo_toolkit.rich_utils import VERBOSITY_MODE


DUCKDB_ABOVE_130 = version.parse(duckdb.__version__) >= version.parse("1.3.0")


def sql_escape(value: str) -> str:
    """Escape value for SQL query."""
    return value.replace("'", "''")


def set_up_duckdb_connection(
    tmp_dir_path: Union[str, Path], preserve_insertion_order: bool = False
) -> "duckdb.DuckDBPyConnection":
    """Create DuckDB connection in a given directory."""
    local_db_file = "db.duckdb"
    connection = duckdb.connect(
        database=str(Path(tmp_dir_path) / local_db_file),
        config=dict(preserve_insertion_order=preserve_insertion_order),
    )
    connection.sql("SET enable_progress_bar = false;")
    connection.sql("SET enable_progress_bar_print = false;")

    connection.install_extension("spatial")
    connection.load_extension("spatial")

    return connection


def run_duckdb_query_function_with_memory_limit(
    tmp_dir_path: Path,
    function: Callable[..., None],
    args: Any,
    verbosity_mode: "VERBOSITY_MODE" = "verbose",
    current_threads_limit: Optional[int] = None,
    current_memory_gb_limit: Optional[float] = None,
    limit_memory: bool = True,
) -> tuple[float, int]:
    """Run function with duckdb query and limit threads automatically."""
    current_memory_gb_limit = current_memory_gb_limit or ceil(
        psutil.virtual_memory().total / MEMORY_1GB
    )
    current_threads_limit = (
        current_threads_limit
        or duckdb.sql("SELECT current_setting('threads') AS threads").fetchone()[0]
    )

    while True:
        try:
            with tempfile.TemporaryDirectory(dir=Path(tmp_dir_path).resolve()) as tmp_dir_name:
                nested_tmp_dir_path = Path(tmp_dir_name)
                f = partial(
                    function,
                    current_memory_gb_limit=current_memory_gb_limit,
                    current_threads_limit=current_threads_limit,
                    tmp_dir_path=nested_tmp_dir_path,
                )
                process = WorkerProcess(
                    target=f,
                    args=args,
                )
                run_process_with_memory_monitoring(process)

            return current_memory_gb_limit, current_threads_limit
        except (duckdb.OutOfMemoryException, MemoryError) as ex:
            if current_threads_limit == 1 and (current_memory_gb_limit < 1 or not limit_memory):
                raise MemoryError("Not enough memory to run the query.") from ex
            elif current_threads_limit > 1:
                # First limit number of CPUs
                current_threads_limit = ceil(current_threads_limit / 2)
            elif limit_memory and current_memory_gb_limit > 1:
                # Next limit memory
                current_memory_gb_limit = ceil(current_memory_gb_limit / 2)
            elif limit_memory and current_memory_gb_limit == 1:
                # Reduce memory below 1 GB
                current_memory_gb_limit /= 2
            else:
                raise RuntimeError(
                    "Not expected error during resources checking "
                    f"({current_memory_gb_limit:.2f}GB, {current_threads_limit} threads)."
                ) from ex

            if not verbosity_mode == "silent":
                rprint(
                    f"Encountered {ex.__class__.__name__} during operation."
                    " Retrying with lower number of resources"
                    f" ({current_memory_gb_limit:.2f}GB, {current_threads_limit} threads)."
                )


def run_query_with_memory_monitoring(
    sql_query: str,
    tmp_dir_path: Optional[Path] = None,
    connection: Optional[duckdb.DuckDBPyConnection] = None,
    verbosity_mode: "VERBOSITY_MODE" = "verbose",
    preserve_insertion_order: bool = False,
    limit_memory: bool = True,
) -> None:
    """
    Run SQL query and raise exception if memory threshold is exceeded.

    Will run in external process or use existing DuckDB connection.

    Args:
        sql_query (str): Query to be executed.
        tmp_dir_path (Path, optional): Directory where to create a new DuckDB connection.
            Defaults to None.
        connection (duckdb.DuckDBPyConnection, optional): Existing connection to reuse.
            Defaults to None.
        verbosity_mode (VERBOSITY_MODE, optional): Log level. Defaults to "verbose".
        preserve_insertion_order (bool, optional): Whether to keep operations in order.
            Used only with external process. Defaults to False.
        limit_memory (bool, optional): Whether to automatically limit memory for DuckDB.
            Defaults to True.
    """
    if tmp_dir_path is connection is None:
        raise ValueError("Must pass tmp_dir_path or connection.")

    if tmp_dir_path is not None and connection is not None:
        raise ValueError("Cannot pass both tmp_dir_path and connection at the same time.")

    if tmp_dir_path is not None:
        run_duckdb_query_function_with_memory_limit(
            tmp_dir_path=tmp_dir_path,
            verbosity_mode=verbosity_mode,
            current_memory_gb_limit=None,
            current_threads_limit=None,
            limit_memory=limit_memory,
            function=_run_query,
            args=(sql_query, preserve_insertion_order),
        )
    elif connection is not None:
        current_memory_gb_limit = ceil(psutil.virtual_memory().total / MEMORY_1GB)
        current_threads_limit = connection.sql(
            "SELECT current_setting('threads') AS threads"
        ).fetchone()[0]

        while True:
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    connection.execute(f"SET memory_limit = '{current_memory_gb_limit}GB';")
                    connection.execute(f"SET threads = {current_threads_limit};")

                    actual_memory = psutil.virtual_memory()
                    percentage_threshold = 95
                    if (actual_memory.total * 0.05) > MEMORY_1GB:  # pragma: no cover
                        percentage_threshold = (
                            100 * (actual_memory.total - MEMORY_1GB) / actual_memory.total
                        )

                    query_execution_future = executor.submit(
                        _run_query_with_existing_connection, sql_query, connection
                    )

                    sleep_time = 0.1
                    while query_execution_future.running():
                        actual_memory = psutil.virtual_memory()
                        if actual_memory.percent > percentage_threshold:  # pragma: no cover
                            connection.interrupt()
                            query_execution_future.cancel()
                            raise MemoryError()

                        sleep(sleep_time)
                        sleep_time = min(sleep_time + 0.1, 1.0)

                    query_execution_future.exception()

                    if query_execution_future.cancelled():
                        raise MemoryError()

                return

            except (duckdb.OutOfMemoryException, MemoryError) as ex:
                if current_threads_limit == 2 and (current_memory_gb_limit < 1 or not limit_memory):
                    raise MemoryError("Not enough memory to run the query.") from ex
                elif current_threads_limit > 2:
                    # First limit number of CPUs
                    current_threads_limit = max(2, ceil(current_threads_limit / 2))
                elif limit_memory and current_memory_gb_limit > 1:
                    # Next limit memory
                    current_memory_gb_limit = ceil(current_memory_gb_limit / 2)
                elif limit_memory and current_memory_gb_limit == 1:
                    # Reduce memory below 1 GB
                    current_memory_gb_limit /= 2
                else:
                    raise RuntimeError(
                        "Not expected error during resources checking "
                        f"({current_memory_gb_limit:.2f}GB, {current_threads_limit} threads)."
                    ) from ex

                if not verbosity_mode == "silent":
                    rprint(
                        f"Encountered {ex.__class__.__name__} during operation."
                        " Retrying with lower number of resources"
                        f" ({current_memory_gb_limit:.2f}GB, {current_threads_limit} threads)."
                    )


def _run_query(
    sql_query: str,
    preserve_insertion_order: bool,
    current_memory_gb_limit: float,
    current_threads_limit: int,
    tmp_dir_path: Path,
) -> None:  # pragma: no cover
    with (
        tempfile.TemporaryDirectory(dir=tmp_dir_path) as tmp_dir_name,
        set_up_duckdb_connection(
            tmp_dir_path=Path(tmp_dir_name), preserve_insertion_order=preserve_insertion_order
        ) as conn,
    ):
        conn.execute(f"SET memory_limit = '{current_memory_gb_limit}GB';")
        conn.execute(f"SET threads = {current_threads_limit};")
        conn.sql(sql_query)


def _run_query_with_existing_connection(
    sql_query: str, connection: duckdb.DuckDBPyConnection
) -> None:
    connection.execute(sql_query)
