#!/usr/bin/env python
import pytest

"""Tests for `tiny_migrations` package."""

import sqlite3

from tiny_migrations import MigrationBase, TinyMigrations


class DummyMigration(MigrationBase):
    def __init__(self, unique_id, description, depends_on=None):
        self.unique_id = unique_id
        self.description = description
        self.depends_on = depends_on
        self.applied = False

    def up(self, db_connection):
        self.applied = True


@pytest.fixture
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()


def test_migrations_table_created(db_connection):
    TinyMigrations(db_connection)
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migrations';")
    assert cursor.fetchone() is not None


def test_apply_single_migration(db_connection):
    tm = TinyMigrations(db_connection)
    migration = DummyMigration("001", "Create users table")
    tm.migrate([migration])
    assert migration.applied
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001"]


def test_apply_multiple_migrations_in_order(db_connection):
    tm = TinyMigrations(db_connection)
    m1 = DummyMigration("001", "First migration")
    m2 = DummyMigration("002", "Second migration", depends_on=m1)
    tm.migrate([m1, m2])
    assert m1.applied and m2.applied
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations ORDER BY applied_at;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001", "002"]


def test_dependency_order_enforced(db_connection):
    tm = TinyMigrations(db_connection)
    m1 = DummyMigration("001", "First migration")
    m2 = DummyMigration("002", "Second migration", depends_on=m1)
    with pytest.raises(ValueError):
        tm.migrate([m2, m1])


def test_duplicate_migration_not_applied_twice(db_connection):
    tm = TinyMigrations(db_connection)
    m1 = DummyMigration("001", "First migration")
    tm.migrate([m1])
    m1.applied = False
    tm.migrate([m1])
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM migrations WHERE unique_id='001';")
    count = cursor.fetchone()[0]
    assert count == 1


def test_migrate_to_target_migration(db_connection):
    tm = TinyMigrations(db_connection)
    m1 = DummyMigration("001", "First migration")
    m2 = DummyMigration("002", "Second migration", depends_on=m1)
    m3 = DummyMigration("003", "Third migration", depends_on=m2)
    tm.migrate([m1, m2, m3], target_migration="002")
    assert m1.applied and m2.applied and not m3.applied
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations ORDER BY applied_at;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001", "002"]


def test_migrate_to_target_migration_then_appy_another(db_connection):
    tm = TinyMigrations(db_connection)
    m1 = DummyMigration("001", "First migration")
    m2 = DummyMigration("002", "Second migration", depends_on=m1)
    m3 = DummyMigration("003", "Third migration", depends_on=m2)
    tm.migrate([m1, m2, m3], target_migration="002")
    assert m1.applied and m2.applied and not m3.applied
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations ORDER BY applied_at;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001", "002"]
    tm.migrate([m1, m2, m3], target_migration="latest")
    assert m1.applied and m2.applied and m3.applied
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations ORDER BY applied_at;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001", "002", "003"]


def test_create_table_and_add_column(db_connection):
    """
    Test migrations that create a table, add a column, and depend on previous migrations.
    """

    class CreateUsersTable(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL
                );
            """)
            db_connection.commit()
            self.applied = True

    class AddEmailColumn(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT;")
            db_connection.commit()
            self.applied = True

    class AddAgeColumn(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER;")
            db_connection.commit()
            self.applied = True

    m1 = CreateUsersTable("001", "Create users table")
    m2 = AddEmailColumn("002", "Add email column", depends_on=m1)
    m3 = AddAgeColumn("003", "Add age column", depends_on=m2)
    tm = TinyMigrations(db_connection)
    tm.migrate([m1, m2, m3])

    # Check table and columns
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns = [row[1] for row in cursor.fetchall()]
    assert "id" in columns
    assert "username" in columns
    assert "email" in columns
    assert "age" in columns


def test_insert_and_update_data_with_migrations(db_connection):
    """
    Test migrations that insert and update data, with dependencies.
    """

    class CreateProductsTable(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL
                );
            """)
            db_connection.commit()
            self.applied = True

    class InsertProduct(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("INSERT INTO products (name, price) VALUES (?, ?);", ("Widget", 9.99))
            db_connection.commit()
            self.applied = True

    class UpdateProductPrice(MigrationBase):
        def up(self, db_connection):
            cursor = db_connection.cursor()
            cursor.execute("UPDATE products SET price = ? WHERE name = ?;", (12.49, "Widget"))
            db_connection.commit()
            self.applied = True

    m1 = CreateProductsTable("101", "Create products table")
    m2 = InsertProduct("102", "Insert Widget product", depends_on=m1)
    m3 = UpdateProductPrice("103", "Update Widget price", depends_on=m2)
    tm = TinyMigrations(db_connection)
    tm.migrate([m1, m2, m3])

    # Check data
    cursor = db_connection.cursor()
    cursor.execute("SELECT name, price FROM products;")
    row = cursor.fetchone()
    assert row == ("Widget", 12.49)


def test_stamp_migration(db_connection):
    tm = TinyMigrations(db_connection)
    tm.stamp("001", "Stamp test migration")
    cursor = db_connection.cursor()
    cursor.execute("SELECT unique_id FROM migrations;")
    rows = cursor.fetchall()
    assert [row[0] for row in rows] == ["001"]


def test_stamp_duplicate_migration(db_connection, caplog):
    tm = TinyMigrations(db_connection)
    tm.stamp("001", "Stamp test migration")
    # Try to stamp again
    with caplog.at_level("ERROR"):
        tm.stamp("001", "Stamp test migration")
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM migrations WHERE unique_id='001';")
    count = cursor.fetchone()[0]
    assert count == 1
    # Should log error
    assert any("already stamped" in msg for msg in caplog.messages)
