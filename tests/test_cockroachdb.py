"""Integration tests for CockroachDB database operations."""

from __future__ import annotations

import json

import pytest


class TestCockroachDBIntegration:
    """Integration tests for CockroachDB database operations via CLI.

    These tests require a running CockroachDB instance (via Docker).
    Tests are skipped if CockroachDB is not available.
    """

    def test_create_cockroachdb_connection(self, cockroachdb_db, cli_runner):
        """Test creating a CockroachDB connection via CLI."""
        from .conftest import COCKROACHDB_HOST, COCKROACHDB_PORT, COCKROACHDB_USER, COCKROACHDB_PASSWORD

        connection_name = "test_create_cockroachdb"

        try:
            # Create connection
            args = [
                "connection", "create",
                "--name", connection_name,
                "--db-type", "cockroachdb",
                "--server", COCKROACHDB_HOST,
                "--port", str(COCKROACHDB_PORT),
                "--database", cockroachdb_db,
                "--username", COCKROACHDB_USER,
                "--password", COCKROACHDB_PASSWORD or "",
            ]
            result = cli_runner(*args)
            assert result.returncode == 0
            assert "created successfully" in result.stdout

            # Verify it appears in list
            result = cli_runner("connection", "list")
            assert connection_name in result.stdout
            assert "CockroachDB" in result.stdout

        finally:
            # Cleanup
            cli_runner("connection", "delete", connection_name, check=False)

    def test_list_connections_shows_cockroachdb(self, cockroachdb_connection, cli_runner):
        """Test that connection list shows CockroachDB connections correctly."""
        result = cli_runner("connection", "list")
        assert result.returncode == 0
        assert cockroachdb_connection in result.stdout
        assert "CockroachDB" in result.stdout

    def test_query_cockroachdb_select(self, cockroachdb_connection, cli_runner):
        """Test executing SELECT query on CockroachDB."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT * FROM test_users ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "Charlie" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_cockroachdb_with_where(self, cockroachdb_connection, cli_runner):
        """Test executing SELECT with WHERE clause on CockroachDB."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT name, email FROM test_users WHERE id = 1",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "alice@example.com" in result.stdout
        assert "1 row(s) returned" in result.stdout

    def test_query_cockroachdb_limit(self, cockroachdb_connection, cli_runner):
        """Test CockroachDB LIMIT clause."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT * FROM test_users ORDER BY id LIMIT 2",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "2 row(s) returned" in result.stdout

    def test_query_cockroachdb_json_format(self, cockroachdb_connection, cli_runner):
        """Test query output in JSON format."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
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

    def test_query_cockroachdb_csv_format(self, cockroachdb_connection, cli_runner):
        """Test query output in CSV format."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "csv",
        )
        assert result.returncode == 0
        assert "id,name" in result.stdout
        assert "1,Alice" in result.stdout
        assert "2,Bob" in result.stdout

    def test_query_cockroachdb_view(self, cockroachdb_connection, cli_runner):
        """Test querying a view on CockroachDB."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT * FROM test_user_emails ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_cockroachdb_aggregate(self, cockroachdb_connection, cli_runner):
        """Test aggregate query on CockroachDB."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT COUNT(*) as user_count FROM test_users",
        )
        assert result.returncode == 0
        assert "3" in result.stdout

    def test_query_cockroachdb_insert(self, cockroachdb_connection, cli_runner):
        """Test INSERT statement on CockroachDB."""
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "INSERT INTO test_users (id, name, email) VALUES (4, 'David', 'david@example.com')",
        )
        assert result.returncode == 0

        # Verify the insert
        result = cli_runner(
            "query",
            "-c", cockroachdb_connection,
            "-q", "SELECT * FROM test_users WHERE id = 4",
        )
        assert "David" in result.stdout

    def test_delete_cockroachdb_connection(self, cockroachdb_db, cli_runner):
        """Test deleting a CockroachDB connection."""
        from .conftest import COCKROACHDB_HOST, COCKROACHDB_PORT, COCKROACHDB_USER, COCKROACHDB_PASSWORD

        connection_name = "test_delete_cockroachdb"

        # Create connection first
        args = [
            "connection", "create",
            "--name", connection_name,
            "--db-type", "cockroachdb",
            "--server", COCKROACHDB_HOST,
            "--port", str(COCKROACHDB_PORT),
            "--database", cockroachdb_db,
            "--username", COCKROACHDB_USER,
            "--password", COCKROACHDB_PASSWORD or "",
        ]
        cli_runner(*args)

        # Delete it
        result = cli_runner("connection", "delete", connection_name)
        assert result.returncode == 0
        assert "deleted successfully" in result.stdout

        # Verify it's gone
        result = cli_runner("connection", "list")
        assert connection_name not in result.stdout
