# niorclconn

A Python package for Oracle database connections with environment variable support and convenient connection management.

## Features

- **Environment Variable Support**: Automatically reads Oracle credentials from environment variables
- **Flexible Configuration**: Support for both direct parameters and environment variables
- **Context Manager Support**: Use with `with` statements for automatic connection cleanup
- **Convenience Functions**: Simple functions for quick connection operations
- **Type Hints**: Full type annotation support for better IDE experience
- **Comprehensive Testing**: Includes both unit tests and integration test examples

## Installation

```bash
pip install niorclconn
```

Or using Poetry:

```bash
poetry add niorclconn
```

## Quick Start

### Using Environment Variables

Set the following environment variables:

```bash
export ORACLE_USER=your_username
export ORACLE_PASSWORD=your_password
export ORACLE_DSN=your_dsn  # e.g., "localhost:1521/XE" or TNS name
```

Then use the package:

```python
from niorclconn import ConnectionManager

# Automatically uses environment variables
manager = ConnectionManager()
connection = manager.open_connection()

# Use the connection
cursor = connection.cursor()
cursor.execute("SELECT 1 FROM DUAL")
result = cursor.fetchone()
print(result)

# Clean up
manager.close_connection()
```

### Using Direct Parameters

```python
from niorclconn import ConnectionManager

manager = ConnectionManager(
    user="your_username",
    password="your_password",
    dsn="localhost:1521/XE"
)

connection = manager.open_connection()
# ... use connection ...
manager.close_connection()
```

### Using Context Manager (Recommended)

```python
from niorclconn import ConnectionManager

with ConnectionManager("user", "password", "dsn") as connection:
    cursor = connection.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    result = cursor.fetchone()
    print(f"Current time: {result[0]}")
# Connection automatically closed
```

### Using Convenience Functions

```python
from niorclconn import open_connection, close_connection

# Quick connection
connection = open_connection("user", "password", "dsn")

# Use connection
cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
table_count = cursor.fetchone()[0]
print(f"Number of tables: {table_count}")

# Close connection
close_connection(connection)
```

## Environment Variables

The package supports the following environment variables:

| Variable | Alternative | Description |
|----------|-------------|-------------|
| `ORACLE_USER` | `ORACLE_USERNAME` | Oracle database username |
| `ORACLE_PASSWORD` | - | Oracle database password |
| `ORACLE_DSN` | `TNS_ADMIN` | Data Source Name (DSN) or TNS name |

**Note**: Direct parameters take precedence over environment variables.

## Configuration Examples

### Easy Connect String
```python
manager = ConnectionManager(dsn="localhost:1521/XE")
```

### TNS Name
```python
manager = ConnectionManager(dsn="ORCL")  # Assuming ORCL is in your tnsnames.ora
```

### Full TNS Descriptor
```python
dsn = """(DESCRIPTION=
    (ADDRESS=(PROTOCOL=TCP)(HOST=localhost)(PORT=1521))
    (CONNECT_DATA=(SID=XE))
)"""
manager = ConnectionManager(dsn=dsn)
```

## Error Handling

The package raises appropriate exceptions for better error handling:

```python
from niorclconn import ConnectionManager
import oracledb

try:
    manager = ConnectionManager()  # May raise ValueError if credentials missing
    connection = manager.open_connection()  # May raise oracledb.Error

    # Your database operations here

except ValueError as e:
    print(f"Configuration error: {e}")
except oracledb.Error as e:
    print(f"Database error: {e}")
finally:
    if 'manager' in locals():
        manager.close_connection()
```

## Testing

Run the test suite:

```bash
# Install development dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=niorclconn
```

### Integration Testing

For integration tests with a real Oracle database, update the test credentials in `tests/test_connector.py` and remove the `@pytest.mark.skip` decorator.

## API Reference

### ConnectionManager

```python
class ConnectionManager:
    def __init__(self, user=None, password=None, dsn=None):
        """Initialize connection manager with credentials."""

    def open_connection(self) -> oracledb.Connection:
        """Open database connection."""

    def close_connection(self) -> None:
        """Close database connection."""

    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
```

### Convenience Functions

```python
def open_connection(user=None, password=None, dsn=None) -> oracledb.Connection:
    """Open an Oracle database connection."""

def close_connection(connection: oracledb.Connection) -> None:
    """Close an Oracle database connection."""
```

## Requirements

- Python 3.9+
- oracledb >= 2.0.0

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Changelog

### 0.1.0
- Initial release
- Environment variable support
- Context manager support
- Comprehensive test suite
- Type hints and documentation