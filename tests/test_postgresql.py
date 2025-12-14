"""Integration tests for PostgreSQL database operations."""

from __future__ import annotations

import json

import pytest


class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL database operations via CLI.

    These tests require a running PostgreSQL instance (via Docker).
    Tests are skipped if PostgreSQL is not available.
    """

    def test_create_postgres_connection(self, postgres_db, cli_runner):
        """Test creating a PostgreSQL connection via CLI."""
        from .conftest import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD

        connection_name = "test_create_postgres"

        try:
            # Create connection
            result = cli_runner(
                "connection", "create",
                "--name", connection_name,
                "--db-type", "postgresql",
                "--server", POSTGRES_HOST,
                "--port", str(POSTGRES_PORT),
                "--database", postgres_db,
                "--username", POSTGRES_USER,
                "--password", POSTGRES_PASSWORD,
            )
            assert result.returncode == 0
            assert "created successfully" in result.stdout

            # Verify it appears in list
            result = cli_runner("connection", "list")
            assert connection_name in result.stdout
            assert "PostgreSQL" in result.stdout

        finally:
            # Cleanup
            cli_runner("connection", "delete", connection_name, check=False)

    def test_list_connections_shows_postgres(self, postgres_connection, cli_runner):
        """Test that connection list shows PostgreSQL connections correctly."""
        result = cli_runner("connection", "list")
        assert result.returncode == 0
        assert postgres_connection in result.stdout
        assert "PostgreSQL" in result.stdout

    def test_query_postgres_select(self, postgres_connection, cli_runner):
        """Test executing SELECT query on PostgreSQL."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT * FROM test_users ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "Charlie" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_postgres_with_where(self, postgres_connection, cli_runner):
        """Test executing SELECT with WHERE clause on PostgreSQL."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT name, email FROM test_users WHERE id = 1",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "alice@example.com" in result.stdout
        assert "1 row(s) returned" in result.stdout

    def test_query_postgres_limit(self, postgres_connection, cli_runner):
        """Test PostgreSQL LIMIT clause."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT * FROM test_users ORDER BY id LIMIT 2",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "2 row(s) returned" in result.stdout

    def test_query_postgres_json_format(self, postgres_connection, cli_runner):
        """Test query output in JSON format."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "json",
        )
        assert result.returncode == 0

        # Parse JSON output (exclude the row count message)
        lines = result.stdout.strip().split("\n")
        json_output = "\n".join(lines[:-1])
        data = json.loads(json_output)

        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_query_postgres_csv_format(self, postgres_connection, cli_runner):
        """Test query output in CSV format."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "csv",
        )
        assert result.returncode == 0
        assert "id,name" in result.stdout
        assert "1,Alice" in result.stdout
        assert "2,Bob" in result.stdout

    def test_query_postgres_view(self, postgres_connection, cli_runner):
        """Test querying a view on PostgreSQL."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT * FROM test_user_emails ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_postgres_aggregate(self, postgres_connection, cli_runner):
        """Test aggregate query on PostgreSQL."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT COUNT(*) as user_count FROM test_users",
        )
        assert result.returncode == 0
        assert "3" in result.stdout

    def test_query_postgres_insert(self, postgres_connection, cli_runner):
        """Test INSERT statement on PostgreSQL."""
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "INSERT INTO test_users (id, name, email) VALUES (4, 'David', 'david@example.com')",
        )
        assert result.returncode == 0

        # Verify the insert
        result = cli_runner(
            "query",
            "-c", postgres_connection,
            "-q", "SELECT * FROM test_users WHERE id = 4",
        )
        assert "David" in result.stdout

    def test_delete_postgres_connection(self, postgres_db, cli_runner):
        """Test deleting a PostgreSQL connection."""
        from .conftest import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD

        connection_name = "test_delete_postgres"

        # Create connection first
        cli_runner(
            "connection", "create",
            "--name", connection_name,
            "--db-type", "postgresql",
            "--server", POSTGRES_HOST,
            "--port", str(POSTGRES_PORT),
            "--database", postgres_db,
            "--username", POSTGRES_USER,
            "--password", POSTGRES_PASSWORD,
        )

        # Delete it
        result = cli_runner("connection", "delete", connection_name)
        assert result.returncode == 0
        assert "deleted successfully" in result.stdout

        # Verify it's gone
        result = cli_runner("connection", "list")
        assert connection_name not in result.stdout
