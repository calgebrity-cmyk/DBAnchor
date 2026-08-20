"""PostgreSQL live schema reflection and inspection engine."""

from __future__ import annotations

from typing import Optional
from sqlalchemy import Engine, inspect
from sqlalchemy.engine import Inspector

from dbanchor.connection.connector import DatabaseConnector
from dbanchor.schema.models import (
    ColumnSnapshot,
    ForeignKeySnapshot,
    IndexSnapshot,
    SchemaSnapshot,
    TableSnapshot,
)


class SchemaInspector:
    """Inspects live PostgreSQL database schema non-destructively."""

    def __init__(self, connector_or_engine: DatabaseConnector | Engine) -> None:
        if isinstance(connector_or_engine, DatabaseConnector):
            self.engine = connector_or_engine.get_sync_engine()
        else:
            self.engine = connector_or_engine

    def inspect_schema(self, schema_name: Optional[str] = "public") -> SchemaSnapshot:
        """Reflect all tables, columns, indexes, and constraints from the database."""
        inspector: Inspector = inspect(self.engine)

        # SQLite does not support schemas like 'public'
        target_schema = None if self.engine.dialect.name == "sqlite" else schema_name

        table_names = inspector.get_table_names(schema=target_schema)
        view_names = inspector.get_view_names(schema=target_schema)

        tables: dict[str, TableSnapshot] = {}

        for tname in table_names:
            # Columns
            raw_cols = inspector.get_columns(tname, schema=target_schema)
            cols: dict[str, ColumnSnapshot] = {}
            for col in raw_cols:
                cname = col["name"]
                ctype = str(col["type"])
                nullable = col.get("nullable", True)
                default = str(col.get("default")) if col.get("default") is not None else None
                primary_key = bool(col.get("primary_key", False))
                cols[cname] = ColumnSnapshot(
                    name=cname,
                    type_str=ctype,
                    nullable=nullable,
                    default=default,
                    primary_key=primary_key,
                )

            # Primary Key
            pk_dict = inspector.get_pk_constraint(tname, schema=target_schema)
            pks = pk_dict.get("constrained_columns", []) if pk_dict else []

            # Indexes
            raw_indexes = inspector.get_indexes(tname, schema=target_schema)
            indexes: list[IndexSnapshot] = []
            for idx in raw_indexes:
                indexes.append(
                    IndexSnapshot(
                        name=idx["name"] or "",
                        columns=idx.get("column_names", []),
                        unique=bool(idx.get("unique", False)),
                    )
                )

            # Foreign Keys
            raw_fks = inspector.get_foreign_keys(tname, schema=target_schema)
            fks: list[ForeignKeySnapshot] = []
            for fk in raw_fks:
                fks.append(
                    ForeignKeySnapshot(
                        name=fk.get("name"),
                        constrained_columns=fk.get("constrained_columns", []),
                        referred_table=fk.get("referred_table", ""),
                        referred_columns=fk.get("referred_columns", []),
                    )
                )

            tables[tname] = TableSnapshot(
                name=tname,
                columns=cols,
                primary_key=pks,
                indexes=indexes,
                foreign_keys=fks,
            )

        return SchemaSnapshot(
            tables=tables,
            views=view_names,
        )
