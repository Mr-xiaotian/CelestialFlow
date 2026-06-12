# web Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
`tests/web/` covers the interface and page integration behavior of the CelestialFlow Web layer, ensuring snapshot isolation, status push/pull, config push, task injection, error pagination filtering, and frontend static asset integration remain stable.

## Included Test Files
- `conftest.py`: Provides the `web_server` and `client` fixtures.
- `test_server.py`: Covers snapshot isolation, dashboard homepage, config API, status sync, task injection, and error pagination — Web API integration tests.

## How to Run

```bash
pytest tests/web -v
pytest tests/web/test_server.py -v
```
