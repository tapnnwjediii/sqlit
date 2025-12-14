# Contributing

Thank you for considering a contribution to sqlit! This guide walks you through setting up your environment, running the test suite, and understanding the CI expectations.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Maxteabag/sqlit.git
   cd sqlit
   ```

2. Install in development mode with test dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

### SQLite Tests (No Docker Required)

SQLite tests can run without any external dependencies:

```bash
pytest tests/ -v -k sqlite
```

### Full Test Suite (Requires Docker)

To run the complete test suite including SQL Server, PostgreSQL, MySQL, MariaDB, Oracle, DuckDB, and CockroachDB tests:

1. Start the test database containers:
   ```bash
   docker compose -f docker-compose.test.yml up -d
   ```

2. Wait for the databases to be ready (about 30-45 seconds), then run tests:
   ```bash
   pytest tests/ -v
   ```

You can leave the containers running between test runs - the test fixtures handle database setup/teardown automatically. Stop them when you're done developing:

```bash
docker compose -f docker-compose.test.yml down
```

### Running Tests for Specific Databases

```bash
pytest tests/ -v -k sqlite      # SQLite only
pytest tests/ -v -k mssql       # SQL Server only
pytest tests/ -v -k PostgreSQL  # PostgreSQL only
pytest tests/ -v -k MySQL       # MySQL only
pytest tests/ -v -k cockroach   # CockroachDB only
```

### Environment Variables

The database tests can be configured with these environment variables:

**SQL Server:**
| Variable | Default | Description |
|----------|---------|-------------|
| `MSSQL_HOST` | `localhost` | SQL Server hostname |
| `MSSQL_PORT` | `1434` | SQL Server port |
| `MSSQL_USER` | `sa` | SQL Server username |
| `MSSQL_PASSWORD` | `TestPassword123!` | SQL Server password |

**PostgreSQL:**
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `testuser` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `TestPassword123!` | PostgreSQL password |
| `POSTGRES_DATABASE` | `test_sqlit` | PostgreSQL database |

**MySQL:**
| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `localhost` | MySQL hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | `TestPassword123!` | MySQL password |
| `MYSQL_DATABASE` | `test_sqlit` | MySQL database |

**CockroachDB:**
| Variable | Default | Description |
|----------|---------|-------------|
| `COCKROACHDB_HOST` | `localhost` | CockroachDB hostname |
| `COCKROACHDB_PORT` | `26257` | CockroachDB port |
| `COCKROACHDB_USER` | `root` | CockroachDB username |
| `COCKROACHDB_PASSWORD` | `` | CockroachDB password (empty for the included Docker container) |
| `COCKROACHDB_DATABASE` | `test_sqlit` | CockroachDB database |

### CockroachDB Quickstart (Docker)

1. Start the included CockroachDB container:
   ```bash
   docker compose -f docker-compose.test.yml up -d cockroachdb
   ```
2. Create a connection (default container runs insecure mode on port `26257` with `root` user):
   ```bash
   sqlit connection create \
     --name "LocalCockroach" \
     --db-type cockroachdb \
     --server "localhost" \
     --port "26257" \
     --database "defaultdb" \
     --username "root"
   ```
3. Launch sqlit and connect:
   ```bash
   sqlit
   ```

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Build**: Verifies the package builds on Python 3.10-3.13
- **SQLite Tests**: Runs SQLite integration tests (no external dependencies)
- **SQL Server Tests**: Runs SQL Server integration tests with Docker service
- **PostgreSQL Tests**: Runs PostgreSQL integration tests with Docker service
- **MySQL Tests**: Runs MySQL integration tests with Docker service
- **MariaDB/Oracle/DuckDB/CockroachDB Tests**: Runs the remaining database integration tests with Docker service where applicable
- **Full Test Suite**: Runs all tests across every supported database

Pull requests must pass all CI checks before merging.
