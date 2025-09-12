
# Pyagenity API

A Python API framework with GraphQL support, task management, and CLI tools for building scalable web applications.

## Installation

### From PyPI (Recommended)
```bash
pip install pyagenity-api
```

### From Source
```bash
git clone https://github.com/Iamsdt/pyagenity-api.git
cd pyagenity-api
pip install -e .
```

## Quick Start

1. **Initialize a new project:**
```bash
pag init
```

2. **Start the API server with default configuration:**
```bash
pag api
```

3. **Start the API server with custom configuration:**
```bash
pag api --config custom-config.json
```

4. **Start the API server on different host/port:**
```bash
pag api --host 127.0.0.1 --port 9000
```

## CLI Commands

The `pag` command provides the following subcommands:

### `pag api`
Start the Pyagenity API server.

**Options:**
- `--config TEXT`: Path to config file (default: pyagenity.json)
- `--host TEXT`: Host to run the API on (default: 0.0.0.0)
- `--port INTEGER`: Port to run the API on (default: 8000)
- `--reload/--no-reload`: Enable auto-reload (default: enabled)

**Examples:**
```bash
# Start with default configuration
pag api

# Start with custom config file
pag api --config my-config.json

# Start on localhost only, port 9000
pag api --host 127.0.0.1 --port 9000

# Start without auto-reload
pag api --no-reload
```

### `pag init`
Initialize a new config file with default settings.

**Options:**
- `--output TEXT`: Output config file path (default: pyagenity.json)
- `--force`: Overwrite existing config file

**Examples:**
```bash
# Create default config
pag init

# Create config with custom name
pag init --output custom-config.json

# Overwrite existing config
pag init --force
```

### `pag version`
Show the CLI version information.

```bash
pag version
```

## Configuration

The configuration file (`pyagenity.json`) supports the following structure:

```json
{
  "app": {
    "name": "Pyagenity API",
    "version": "1.0.0",
    "debug": true
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1
  },
  "database": {
    "url": "sqlite://./pyagenity.db"
  },
  "redis": {
    "url": "redis://localhost:6379"
  }
}
```

## File Resolution

The CLI automatically finds your config file in this order:
1. Absolute path (if provided with `--config`)
2. Current working directory
3. Relative to script location (for development)
4. Package installation directory (fallback)

## Project Structure

```
pyagenity-api/
├── pyagenity_api/           # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # CLI module
│   └── src/                # Source code
│       └── app/            # FastAPI application
│           ├── main.py     # FastAPI app entry point
│           ├── core/       # Core functionality
│           ├── routers/    # API routes
│           └── tasks/      # Background tasks
├── graph/                  # Graph implementation
├── migrations/             # Database migrations
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
├── Makefile              # Development commands
├── MANIFEST.in           # Package manifest
└── README.md             # This file
```

## Features

- **FastAPI Backend**: High-performance async web framework
- **GraphQL Support**: Built-in GraphQL API with Strawberry
- **Task Management**: Background task processing with Taskiq
- **CLI Tools**: Command-line interface for easy management
- **Database Integration**: Support for multiple databases via Tortoise ORM
- **Redis Integration**: Caching and session management
- **Authentication**: Firebase authentication support
- **Development Tools**: Pre-commit hooks, linting, testing
- **Docker Support**: Container deployment ready

## Setup

### Prerequisites
- Python 3.x
- pip
- [Any other prerequisites]

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/10XScale-in/backend-base.git
    ```

2. Create a virtual environment and activate:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Database

### Database Configuration
The database configuration is located in `src/app/db/setup_database.py`.

### Database Migration
We use Aerich for database migrations. Follow these steps to manage your database:

1. Initialize the database initially:
    ```bash
    aerich init -t src.app.db.setup_database.TORTOISE_ORM
    ```

2. Create initial database schema:
    ```bash
    aerich init-db
    ```

3. Generate migration files:
    ```bash
    aerich migrate
    ```

4. Apply migrations:
    ```bash
    aerich upgrade
    ```

5. Revert migrations (if needed):
    ```bash
    aerich downgrade
    ```

## Running the Application

### Command Line
To run the FastAPI application using Uvicorn:
1. Start the application:
    ```bash
    uvicorn src.app.main:app --reload
    ```

2. You can also run the debugger.

### VS Code
Add the following configuration to your `.vscode/launch.json` file:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.app.main:app",
                "--host",
                "localhost",
                "--port",
                "8880"
            ],
            "jinja": true,
            "justMyCode": true
        }
    ]
}
```
Then you can run and debug the application using the VS Code debugger.
### Run the Broker
1. Run the taskiq worker
```taskiq worker src.app.worker:broker -fsd -tp 'src/**/*_tasks.py' --reload
```
## Development

### Using the Makefile

The project includes a comprehensive Makefile for development tasks:

```bash
# Show all available commands
make help

# Install package in development mode
make dev-install

# Run tests
make test

# Test CLI installation
make test-cli

# Format code
make format

# Run linting
make lint

# Run all checks (lint + test)
make check

# Clean build artifacts
make clean

# Build package
make build

# Publish to TestPyPI
make publish-test

# Publish to PyPI
make publish

# Complete release workflow
make release
```

### Manual Development Setup

If you prefer manual setup:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Iamsdt/pyagenity-api.git
    cd pyagenity-api
    ```

2. **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. **Install in development mode:**
    ```bash
    pip install -e .
    ```

4. **Install development dependencies:**
    ```bash
    pip install pytest pytest-cov ruff mypy pre-commit
    ```

5. **Set up pre-commit hooks:**
    ```bash
    pre-commit install
    ```

### Testing

Run tests using pytest:
```bash
pytest src/tests/ -v --cov=pyagenity_api
```

Or use the Makefile:
```bash
make test
```

### Publishing to PyPI

1. **Test your package locally:**
    ```bash
    make test-cli
    ```

2. **Publish to TestPyPI first:**
    ```bash
    make publish-test
    ```

3. **If everything works, publish to PyPI:**
    ```bash
    make publish
    ```


# Resources
https://keda.sh/
Get all the fixers
pytest --fixtures
https://www.tutorialspoint.com/pytest/pytest_run_tests_in_parallel.html

