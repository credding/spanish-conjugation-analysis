import csv
import logging
import sqlite3
from contextlib import closing

from resources import obj_path, resources_path

_logger = logging.getLogger(__name__)

_corpes_db_path = obj_path / "corpes.db"
_corpes_schema_path = resources_path / "corpes_schema.sql"
_corpes_data_path = resources_path / "corpes"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(f"{_corpes_db_path.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    if _corpes_db_path.is_file():
        with (
            connect() as conn,
            closing(conn.cursor()) as cur,
        ):
            cur.execute("SELECT EXISTS(SELECT 1 FROM sqlite_master);")
            if cur.fetchone()[0]:
                return

    _logger.info("initializing CORPES database")

    _corpes_db_path.parent.mkdir(parents=True, exist_ok=True)

    with (
        sqlite3.connect(_corpes_db_path, autocommit=False) as conn,
        closing(conn.cursor()) as cur,
    ):
        cur.executescript(_corpes_schema_path.read_text())

        _load_table_tsv(
            cur,
            table_name="freq_elements",
            tsv_name="frecuencia_elementos_corpes_1_4.txt",
            fieldnames=[
                "form",
                "lemma",
                "tag",
                "freq",
                "freq_norm_with_punc",
                "freq_norm_without_punc",
            ],
            skip_lines=2,
        )

        _load_table_tsv(
            cur,
            table_name="freq_lemmas",
            tsv_name="frecuencia_lemas_corpes_1_4.txt",
            fieldnames=[
                "lemma",
                "class",
                "freq",
                "freq_norm_with_punc",
                "freq_norm_without_punc",
            ],
            skip_lines=2,
        )

        _load_table_tsv(
            cur,
            table_name="freq_forms",
            tsv_name="frecuencia_formas_ortograficas_1_4.txt",
            fieldnames=[
                "form",
                "freq",
                "freq_norm",
            ],
            skip_lines=2,
        )

        _load_table_tsv(
            cur,
            table_name="dp_lemmas",
            tsv_name="listas_dp_lemas.tsv",
            fieldnames=[
                None,
                None,
                "lemma",
                "class",
                "freq",
                "freq_norm",
                "dp",
                "num_countries",
            ],
            skip_lines=6,
        )

        conn.commit()


class _corpes_tsv_dialect(csv.Dialect):
    delimiter = "\t"
    skipinitialspace = True
    lineterminator = "\r\n"
    quoting = csv.QUOTE_NONE


def _load_table_tsv(
    cur: sqlite3.Cursor,
    table_name: str,
    tsv_name: str,
    fieldnames: list[str] | list[str | None],
    skip_lines: int,
) -> None:
    column_names = [x for x in fieldnames if x is not None]

    column_names_clause = ", ".join(column_names)
    values_clause = ", ".join(f":{x}" for x in column_names)
    insert_statement = f"INSERT INTO {table_name} (id, {column_names_clause}) VALUES (:id, {values_clause});"

    tsv_path = _corpes_data_path / tsv_name
    with tsv_path.open("r", newline="") as f:
        for _ in range(skip_lines):
            next(f)
        reader = csv.DictReader(
            f,
            fieldnames=fieldnames,
            dialect=_corpes_tsv_dialect,
        )
        for row in reader:
            try:
                cur.execute(insert_statement, {"id": reader.line_num, **row})
            except sqlite3.IntegrityError as e:
                _logger.warning(
                    "error inserting row %d into %s: %s; data: %s",
                    reader.line_num,
                    table_name,
                    e,
                    row,
                )


if __name__ == "__main__":
    initialize()
