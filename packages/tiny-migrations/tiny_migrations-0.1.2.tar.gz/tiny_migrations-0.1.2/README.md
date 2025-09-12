# Tiny Migrations

## Introdution

![PyPI version](https://img.shields.io/pypi/v/tiny-migrations.svg)


A tiny, lightweight, package for managing sqlite database migrations. Designed to work without INI files or dynamic module loading, making it ideal for compiled or frozen applications as well as traditional servers.

* PyPI package: https://pypi.org/project/tiny-migrations/
* Free software: MIT License

## Installation

Install via pip:

```sh
pip install tiny-migrations
```

---

## Defining Migrations

Create migration classes by subclassing `MigrationBase`. Each migration must implement the `up(db_connection)` method.

```python
from tiny_migrations import MigrationBase

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
        cursor.close()
```

Each migration requires a unique ID and a description:

```python
migration1 = CreateUsersTable("001", "Create users table")
```

You can specify dependencies using the `depends_on` argument:

```python
migration2 = AddEmailColumn("002", "Add email column", depends_on=migration1)
```

---

## Setting Up the Database Connection

Use a direct `sqlite3.Connection` object:

```python
import sqlite3

db_conn = sqlite3.connect("my_database.db")
```

---

## Running Migrations

Pass your migrations to `TinyMigrations` and run them in order:

```python
from tiny_migrations import TinyMigrations

tm = TinyMigrations(db_conn)
tm.migrate([migration1, migration2])
```

---

## Migration Dependencies

Migrations must depend on a previous migration. Ensure you pass them in dependency order:

```python
migration2 = AddEmailColumn("002", "Add email column", depends_on=migration1)
tm.migrate([migration1, migration2])
```

---

## Targeted Migration

You can migrate up to a specific migration by passing its unique ID:

```python
tm.migrate([migration1, migration2, migration3], target_migration="002")
```

---

## Example: Adding and Modifying Tables

```python
class AddAgeColumn(MigrationBase):
    def up(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER;")
        db_connection.commit()
        cursor.close()

migration3 = AddAgeColumn("003", "Add age column", depends_on=migration2)

tm.migrate([migration1, migration2, migration3])
```

---

## Stamping Migrations

You can mark a migration as applied without actually running its `up` method using the `stamp` feature. This is useful when you want to record that a migration has already been applied manually or outside of Tiny Migrations.

```python
tm.stamp("001", "Stamp test migration")
```

---

## Troubleshooting

- If you get a dependency error, check the order and `depends_on` attributes.
- Make sure your `up` method receives the database connection argument.
