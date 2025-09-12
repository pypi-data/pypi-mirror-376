class MigrationBase:
    def __init__(
        self, unique_id: str, description: str = "No description provided.", depends_on: "MigrationBase | None" = None
    ):
        if not unique_id or not isinstance(unique_id, str) or unique_id == "latest":
            raise ValueError("A valid unique_id must be provided.")

        self.unique_id = unique_id
        self.description = description
        self.depends_on = depends_on

    def up(self, db_connection):
        """
        Apply the migration using the provided database connection.

        Args:
            db_connection: The database connection to use for migration operations.
        """
        raise NotImplementedError("The 'up' method must be implemented by subclasses.")
