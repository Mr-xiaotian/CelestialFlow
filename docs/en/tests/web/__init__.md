# web Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/web/` covers API and page integration behavior in the CelestialFlow web layer, ensuring that status pulling, configuration pushes, structure display, and front-end static assets remain stable together.

## Included Test Files
- `test_routes.py`: Web API routes and request return values.
- `test_server.py`: Web server startup and integration behavior.

## How to Run

```bash
pytest tests/web -v
pytest tests/web -k "routes or server" -v
```

