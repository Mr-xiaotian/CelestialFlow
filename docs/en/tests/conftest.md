# Global Test Configuration (conftest.py)

> Last Updated: 2026/05/23

## Purpose
Serves as the root-level configuration file for the entire `tests/` directory and initializes global state and environment variables required by the test environment.

## Core Features
- **Environment loading**: Automatically calls `dotenv.load_dotenv()` so configuration from the project root `.env` file, such as API keys and database connection strings, is available when tests start.

## Notes
- Pytest discovers this file automatically.
- Define global fixtures here when needed.

