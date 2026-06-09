"""Detect how Docker startup should bootstrap Alembic.

Fresh databases should run migrations from base. Older Docker volumes may have
tables created by SQLAlchemy `create_all` but no `alembic_version` table; those
volumes must be stamped before `alembic upgrade head` to avoid duplicate-table
errors.
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import engine


def main() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    table_names = set(inspect(engine).get_table_names())
    app_tables = table_names - {"alembic_version"}

    if "alembic_version" not in table_names and app_tables:
        print("stamp")
        return

    print("upgrade")


if __name__ == "__main__":
    main()
