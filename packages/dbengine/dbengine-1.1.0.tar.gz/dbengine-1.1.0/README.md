# DBEngine

A unified, production-ready database interface for Python that provides seamless access to SQLite, Parquet, and PostgreSQL databases through a consistent pandas-based API.

## Features

- **Multi-Database Support**: Work with SQLite, Parquet files, and PostgreSQL databases using the same API
- **Production-Ready**: Built-in configuration management and error handling
- **Pandas Integration**: Native pandas DataFrame/Series support for all operations
- **High Performance**: Connection pooling, batching, and optimised data handling
- **PostgreSQL Server Management**: Programmatically start/stop PostgreSQL servers using Docker for development and testing
- **Comprehensive Testing**: Full test suite with validation and integration tests
- **Easy Setup**: Simple installation and configuration with sensible defaults

## Quick Start

### Installation

```bash
pip install dbengine
```

### Basic Usage

```python
from dbengine import create_database
import pandas as pd

# Create a SQLite database
db = create_database('sqlite', database='my_data')

# Create sample data
data = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# Write data
db.write(table_name='users', item=data)

# Read data
users = db.query(table_name='users')
print(users)

# Query data
young_users = db.query(criteria=[('age', '=', 25)], table_name='users')
print(young_users)

```

### PostgreSQL Server Management

```python
import pandas as pd
from dbengine import create_postgres_server, PostgreSQLDatabase, DatabaseConfig

# Start a PostgreSQL server for development/testing
with create_postgres_server(port=5433) as server:
    # Create database configuration from server connection params
    config = DatabaseConfig(
        database_config={
            "db_type": "postgresql",
            "params": server.get_connection_params()
        }
    )

    # Create database connection
    db = PostgreSQLDatabase(config)

    # Use the database normally
    data = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
    db.write(table_name='users', item=data)

    # Database and server automatically cleaned up
```

## Supported Databases

### SQLite

- **Use Case**: Local development, testing, lightweight applications
- **Features**: File-based, serverless, ACID transactions
- **Configuration**: Simple file path specification

### Parquet

- **Use Case**: Data analytics, archival, big data processing
- **Features**: Columnar storage, compression, fast analytics
- **Configuration**: Directory path with compression options

### PostgreSQL

- **Use Case**: Production applications, multi-user systems
- **Features**: Full ACID compliance, connection pooling, advanced SQL
- **Configuration**: Host, port, credentials, SSL support
- **Server Management**: Docker-based server lifecycle management for development/testing

## Configuration

DBEngine supports configuration files for different environments with YAML format.

### Sample Configuration Files

There are sample configuration files in the `sample_configs` folder.

**SQLite Configuration:**

```yaml
database:
  db_type: sqlite
  params:
    path: data/database.db

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers: null
```

**PostgreSQL Configuration:**

```yaml
database:
  db_type: postgresql
  params:
    host: localhost
    port: 5432
    database: dbengine
    user: dbengine
    password: your_password_here

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers: null
```

**Parquet Configuration:**

```yaml
database:
  db_type: parquet
  params:
    path: data/parquet

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers: null
```

**Note**: All configuration values must be set in the YAML configuration files.

### Creating Configuration Files

DBEngine provides a convenient function to generate sample configuration files for any supported database type:

```python
from dbengine import create_config_file

# Create a SQLite configuration file
create_config_file('config/sqlite_config.yaml', 'sqlite', load_config=True)

# Create a PostgreSQL configuration file
create_config_file('config/postgres_config.yaml', 'postgresql', load_config=False)

# Create a Parquet configuration file
create_config_file('config/parquet_config.yaml', 'parquet', load_config=True)
```

#### Function Parameters:

- `path`: Where to create the configuration file
- `db_type`: Database type (`'sqlite'`, `'postgresql'`, or `'parquet'`)
- `load_config`: If `True`, returns a `DatabaseConfig` object; if `False`, only creates the file
- `overwrite`: If `True`, overwrites existing files; if `False`, loads existing files when `load_config=True`

## Advanced Usage

### PostgreSQL Server Management

DBEngine includes utilities to programmatically start and stop PostgreSQL servers using Docker, making it perfect for development workflows and testing:

```python
import pandas as pd
from dbengine import PostgreSQLServerManager, PostgreSQLDatabase, DatabaseConfig

# Manual server lifecycle management
server = PostgreSQLServerManager(port=5433, database='my_test_db')
server.start()

try:
    # Create database configuration from server connection params
    config = DatabaseConfig(
        database_config={
            "db_type": "postgresql",
            "params": server.get_connection_params()
        }
    )

    # Create database connection
    db = PostgreSQLDatabase(config)

    # Perform database operations
    data = pd.DataFrame({'id': [1, 2, 3], 'value': ['a', 'b', 'c']})
    db.write(table_name='test_table', item=data)

    result = db.query(table_name='test_table')
    print(result)

finally:
    server.stop()

# Context manager (recommended)
with PostgreSQLServerManager(port=5434) as server:
    config = DatabaseConfig(
        database_config={
            "db_type": "postgresql",
            "params": server.get_connection_params()
        }
    )
    db = PostgreSQLDatabase(config)
    # Server automatically stopped when exiting context
```

#### Server Management Features:

- **Docker Integration**: Automatic container lifecycle management
- **Port Configuration**: Avoid conflicts with existing PostgreSQL instances
- **Custom Databases**: Create servers with specific database names and credentials
- **Health Checks**: Automatic server readiness detection
- **Multiple Servers**: Run multiple isolated PostgreSQL instances simultaneously

## Examples

See the `notebooks/` directory for comprehensive usage examples.

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

**Note**: PostgreSQL server management tests require Docker to be running. Tests will be automatically skipped if Docker is not available.

## Development

### Setup Development Environment

```bash
git clone https://github.com/tomemgouveia/dbengine.git
cd dbengine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Prerequisites

For PostgreSQL server management features, you'll need:

- **Docker**: Required for PostgreSQL server management utilities

```bash
# Install Docker (macOS)
brew install docker

# Install Docker (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install docker.io

# Start Docker daemon
sudo systemctl start docker  # Linux
# or use Docker Desktop on macOS/Windows
```

### Code Quality

The project uses automated code quality tools:

```bash
# Format code
black src/ tests/

# Check imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
