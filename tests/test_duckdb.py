"""Integration tests for DuckDB database operations."""

from __future__ import annotations

import json

import pytest


class TestDuckDBIntegration:
    """Integration tests for DuckDB database operations via CLI.

    These tests use a temporary DuckDB database file.
    Tests are skipped if DuckDB is not installed.
    """

    def test_create_duckdb_connection(self, duckdb_db, cli_runner):
        """Test creating a DuckDB connection via CLI."""
        connection_name = "test_create_duckdb"

        try:
            # Create connection
            result = cli_runner(
                "connection", "create",
                "--name", connection_name,
                "--db-type", "duckdb",
                "--file-path", str(duckdb_db),
            )
            assert result.returncode == 0
            assert "created successfully" in result.stdout

            # Verify it appears in list
            result = cli_runner("connection", "list")
            assert connection_name in result.stdout
            assert "DuckDB" in result.stdout

        finally:
            # Cleanup
            cli_runner("connection", "delete", connection_name, check=False)

    def test_list_connections_shows_duckdb(self, duckdb_connection, cli_runner):
        """Test that connection list shows DuckDB connections correctly."""
        result = cli_runner("connection", "list")
        assert result.returncode == 0
        assert duckdb_connection in result.stdout
        assert "DuckDB" in result.stdout

    def test_query_duckdb_select(self, duckdb_connection, cli_runner):
        """Test executing SELECT query on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT * FROM test_users ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "Charlie" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_duckdb_with_where(self, duckdb_connection, cli_runner):
        """Test executing SELECT with WHERE clause on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT name, email FROM test_users WHERE id = 1",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "alice@example.com" in result.stdout
        assert "1 row(s) returned" in result.stdout

    def test_query_duckdb_limit(self, duckdb_connection, cli_runner):
        """Test DuckDB LIMIT clause."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT * FROM test_users ORDER BY id LIMIT 2",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Bob" in result.stdout
        assert "2 row(s) returned" in result.stdout

    def test_query_duckdb_json_format(self, duckdb_connection, cli_runner):
        """Test query output in JSON format."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
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

    def test_query_duckdb_csv_format(self, duckdb_connection, cli_runner):
        """Test query output in CSV format."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT id, name FROM test_users ORDER BY id LIMIT 2",
            "--format", "csv",
        )
        assert result.returncode == 0
        assert "id,name" in result.stdout
        assert "1,Alice" in result.stdout
        assert "2,Bob" in result.stdout

    def test_query_duckdb_view(self, duckdb_connection, cli_runner):
        """Test querying a view on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT * FROM test_user_emails ORDER BY id",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "3 row(s) returned" in result.stdout

    def test_query_duckdb_aggregate(self, duckdb_connection, cli_runner):
        """Test aggregate query on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT COUNT(*) as user_count FROM test_users",
        )
        assert result.returncode == 0
        assert "3" in result.stdout

    def test_query_duckdb_join(self, duckdb_connection, cli_runner):
        """Test JOIN query on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT u.name, p.name as product FROM test_users u CROSS JOIN test_products p WHERE u.id = 1 AND p.id = 1",
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "Widget" in result.stdout

    def test_query_duckdb_insert(self, duckdb_connection, cli_runner):
        """Test INSERT statement on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "INSERT INTO test_users (id, name, email) VALUES (4, 'David', 'david@example.com')",
        )
        assert result.returncode == 0

        # Verify the insert
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT * FROM test_users WHERE id = 4",
        )
        assert "David" in result.stdout

    def test_query_duckdb_update(self, duckdb_connection, cli_runner):
        """Test UPDATE statement on DuckDB."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "UPDATE test_users SET name = 'Alicia' WHERE id = 1",
        )
        assert result.returncode == 0

        # Verify the update
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT name FROM test_users WHERE id = 1",
        )
        assert "Alicia" in result.stdout

    def test_delete_duckdb_connection(self, duckdb_db, cli_runner):
        """Test deleting a DuckDB connection."""
        connection_name = "test_delete_duckdb"

        # Create connection first
        cli_runner(
            "connection", "create",
            "--name", connection_name,
            "--db-type", "duckdb",
            "--file-path", str(duckdb_db),
        )

        # Delete it
        result = cli_runner("connection", "delete", connection_name)
        assert result.returncode == 0
        assert "deleted successfully" in result.stdout

        # Verify it's gone
        result = cli_runner("connection", "list")
        assert connection_name not in result.stdout

    def test_query_duckdb_invalid_query(self, duckdb_connection, cli_runner):
        """Test handling of invalid SQL query."""
        result = cli_runner(
            "query",
            "-c", duckdb_connection,
            "-q", "SELECT * FROM nonexistent_table",
            check=False,
        )
        # Should fail gracefully
        assert result.returncode != 0 or "error" in result.stdout.lower() or "error" in result.stderr.lower()
