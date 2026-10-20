from abc import ABC, abstractmethod

import pandas as pd


class Warehouse(ABC):
    @abstractmethod
    def schema_exists(self, schema: str) -> bool: ...

    @abstractmethod
    def list_tables(self, schema: str) -> list[str]: ...

    @abstractmethod
    def columns(self, schema: str, table: str) -> list[str]: ...

    @abstractmethod
    def table_size(self, schema: str, table: str) -> int: ...

    @abstractmethod
    def fetch_table(self, schema: str, table: str) -> pd.DataFrame: ...

    def close(self) -> None:
        pass
