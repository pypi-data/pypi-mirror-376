import logging
from sqlite3 import Connection as SQLiteConnection

from tiny_migrations.migration_base import MigrationBase


class TinyMigrations:
    """
    A tiny database migration tool for tracking and applying database schema changes.

    Attributes:
        db_connection (DBAPIConnection): The database connection implementing DBAPI protocol.
    """

    def __init__(self, db_connection: SQLiteConnection):
        """
        Initialize the TinyMigrations tool and ensure the migrations table exists.

        Args:
            db_connection (DBAPIConnection): A database connection implementing the DBAPI protocol.
        """
        self.db_connection = db_connection
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """
        Ensure the migrations tracking table exists in the database.
        Creates the table if it does not exist.
        """
        try:
            cur = self.db_connection.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    unique_id VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.db_connection.commit()
        finally:
            cur.close()

    def get_applied_migrations(self) -> list[str]:
        """
        Read the list of applied migration unique IDs from the database.

        Returns:
            List[str]: A list of unique IDs for applied migrations.
        """
        try:
            cur = self.db_connection.cursor()
            cur.execute("SELECT unique_id FROM migrations ORDER BY applied_at;")
            rows = cur.fetchall()
        finally:
            cur.close()
        return [row[0] for row in rows]

    def _record_migration(self, migration: MigrationBase):
        """
        Record a migration as applied in the database.

        Args:
            migration (MigrationBase): The migration to record.
        """
        try:
            cur = self.db_connection.cursor()
            cur.execute(
                "INSERT INTO migrations (unique_id, description) VALUES (?, ?);",
                (migration.unique_id, migration.description),
            )
            self.db_connection.commit()
        finally:
            cur.close()

    def migrate(self, migrations: list[MigrationBase], target_migration: str | None = "latest"):
        """
        Apply migrations up to the target migration.

        Args:
            migrations (List[MigrationBase]): List of migration objects in dependency order.
            target_migration (str | None): Unique ID of the target migration, or "latest" for all.
        """
        applied_migrations = self.get_applied_migrations()
        start = len(applied_migrations) == 0
        for i, m in enumerate(migrations):
            if i == 0:
                if m.depends_on is not None:
                    raise ValueError(
                        f"Migration {m.unique_id} has a dependency, but it is the first migration in the list."
                    )

            if i > 0 and m.depends_on != migrations[i - 1]:
                raise ValueError(
                    f"Migration {m.unique_id} depends on {m.depends_on.unique_id if m.depends_on else None}, but the previous migration is {migrations[i - 1].unique_id}. Migrations must be in dependency order."
                )

        for m in migrations:
            if not start and applied_migrations[-1] == m.unique_id:
                start = True
                continue

            if start:
                logging.debug(f"Applying migration {m.unique_id}: {m.description}")
                m.up(self.db_connection)
                self._record_migration(m)

            if m.unique_id == target_migration:
                logging.debug(f"Reached target migration {target_migration}. Stopping.")
                break

    def stamp(self, unique_id: str, description: str = "Stamped without applying."):
        """
        Stamp the database with a migration unique_id without applying it.

        Args:
            unique_id (str): The unique ID of the migration to stamp as applied.
            description (str): Description for the stamped migration.
        """
        applied_migrations = self.get_applied_migrations()
        if unique_id in applied_migrations:
            logging.error(f"Migration {unique_id} already stamped. Skipping.")
            return

        logging.debug(f"Stamping migration {unique_id}: {description}")
        try:
            cur = self.db_connection.cursor()
            cur.execute(
                "INSERT INTO migrations (unique_id, description) VALUES (?, ?);",
                (unique_id, description),
            )
            self.db_connection.commit()
        finally:
            cur.close()