import pandas as pd
import duckdb
from pathlib import Path
from .base import Warehouse


def quote_ident(name):
    return '"' + name.replace('"', '""') + '"'


class DuckDBWarehouse(Warehouse):
    def __init__(self, path):
        super().__init__()
        self.path = Path(path)

    def _query(self, sql, params):
        if not self.path.exists():
            return pd.DataFrame()
        con = duckdb.connect(str(self.path), read_only=True)
        try:
            return con.execute(sql, params or []).df()
        finally:
            con.close()

    def schema_exists(self, schema):
        df = self._query(
            "SELECT 1 FROM information_schema.schemata WHERE lower(schema_name)=lower(?)",
            [schema],
        )
        return len(df) > 0

    def list_tables(self, schema):
        df = self._query(
            "SELECT table_name FROM information_schema.tables WHERE lower(table_schema) = lower(?) AND table_type='BASE TABLE'",
            [schema],
        )
        return [] if df.empty else [str(x) for x in df.iloc[:, 0]]

    def columns(self, schema, table):
        df = self._query(
            "SELECT column_name FROM information_schema.columns WHERE lower(table_schema)=lower(?) AND lower(table_name)=lower(?)",
            [schema, table],
        )
        return [] if df.empty else [str(x) for x in df.iloc[:, 0]]

    def table_size(self, schema, table):
        df = self._query(
            f"select count(*) from {quote_ident(schema)}.{quote_ident(table)}", []
        )
        return int(df.iloc[0, 0])

    def fetch_table(self, schema: str, table: str) -> pd.DataFrame:
        return self._query(
            f"SELECT * FROM {quote_ident(schema)}.{quote_ident(table)}", []
        )
