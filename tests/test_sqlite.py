"""Integration tests for SQLite database operations."""

from __future__ import annotations

import json

import pytest


class TestSQLiteIntegration:
    """Integration tests for SQLite database operations via CLI."""

    def test_create_sqlite_connection(self, sqlite_db, cli_runner):
        """Test creating a SQLite connection via CLI."""
        connection_name = "test_create_sqlite"

        try:
            # Create connection
            result = cli_runner(
                "connection", "create",
                "--name", connection_name,
                "--db-type", "sqlite",
                "--file-path", str(sqlite_db),
            )
            assert result.returncode == 0
            assert "created successfully" in result.stdout

            # Verify it appears in list
            result = cli_runner("connection", "list")
            assert connection_name in result.stdout
            assert "SQLite" in result.stdout

        finally:
            # Cleanup
            cli_runner("connection", "delete", connection_name, check=False)

    def test_list_connections_shows_sqlite(self, sqlite_connection, cli_runner):
        """Test that connection list shows SQLite connections correctly."""
        result = cli_runner("connection", "list")
        assert result.returncode == 0
        assert sqlite_connection in result.stdout
        assert "SQLite" in result.stdout

    def test_query_sqlite_select(self, sqlite_connection, cli_runner):
        """Test executing SELECT query on SQLite."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT * FROM test_users ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "Charlie" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_sqlite_with_where(self, sqlite_connection, cli_runner):
        """Test executing SELECT with WHERE clause on SQLite."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT name, email FROM test_users WHERE id = 1",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "alice@example.com" in result.stdout
        assert "1 row(s) returned" in result.stdout

    def test_query_sqlite_json_format(self, sqlite_connection, cli_runner):
        """Test query output in JSON format."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "json",
        )
        assert result.returncode == 0

        # Parse JSON output (exclude the row count message)
        lines = result.stdout.strip().split("\n")
        json_output = "\n".join(lines[:-1])  # Remove "(X row(s) returned)"
        data = json.loads(json_output)

        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_query_sqlite_csv_format(self, sqlite_connection, cli_runner):
        """Test query output in CSV format."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "csv",
        )
        assert result.returncode == 0
        assert "id,name" in result.stdout
        assert "1,Alice" in result.stdout
        assert "2,Bob" in result.stdout

    def test_query_sqlite_view(self, sqlite_connection, cli_runner):
        """Test querying a view."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT * FROM test_user_emails ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_sqlite_aggregate(self, sqlite_connection, cli_runner):
        """Test aggregate query on SQLite."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT COUNT(*) as user_count FROM test_users",
        )
        assert result.returncode == 0
        assert "3" in result.stdout

    def test_query_sqlite_join(self, sqlite_connection, cli_runner):
        """Test JOIN query on SQLite."""
        # This test verifies that complex queries work
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", """
                SELECT u.name, p.name as product, p.price
                FROM test_users u
                CROSS JOIN test_products p
                WHERE u.id = 1 AND p.id = 1
            """,
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Widget" in result.stdout

    def test_query_sqlite_insert(self, sqlite_connection, cli_runner):
        """Test INSERT statement on SQLite."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "INSERT INTO test_users (id, name, email) VALUES (4, 'David', 'david@example.com')",
        )
        assert result.returncode == 0
        assert "row(s) affected" in result.stdout.lower() or "executed successfully" in result.stdout.lower()

        # Verify the insert
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT * FROM test_users WHERE id = 4",
        )
        assert "David" in result.stdout

    def test_query_sqlite_update(self, sqlite_connection, cli_runner):
        """Test UPDATE statement on SQLite."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "UPDATE test_products SET stock = 200 WHERE id = 1",
        )
        assert result.returncode == 0

        # Verify the update
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT stock FROM test_products WHERE id = 1",
        )
        assert "200" in result.stdout

    def test_delete_sqlite_connection(self, sqlite_db, cli_runner):
        """Test deleting a SQLite connection."""
        connection_name = "test_delete_sqlite"

        # Create connection first
        cli_runner(
            "connection", "create",
            "--name", connection_name,
            "--db-type", "sqlite",
            "--file-path", str(sqlite_db),
        )

        # Delete it
        result = cli_runner("connection", "delete", connection_name)
        assert result.returncode == 0
        assert "deleted successfully" in result.stdout

        # Verify it's gone
        result = cli_runner("connection", "list")
        assert connection_name not in result.stdout

    def test_query_sqlite_invalid_query(self, sqlite_connection, cli_runner):
        """Test handling of invalid SQL query."""
        result = cli_runner(
            "query",
            "-c", sqlite_connection,
            "-q", "SELECT * FROM nonexistent_table",
            check=False,
        )
        assert result.returncode != 0
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()
