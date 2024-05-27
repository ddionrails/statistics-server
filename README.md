# Statistics Server

Displays pre-calculated timeline statistics.

## Setup

- Set  `STATISTICS_BASE_PATH` environment variable.
```bash
export STATISTICS_BASE_PATH="/path/to/statistics/data"
```
- Run app through gunicorn.
```
gunicorn statistics_server.app:server -b 0.0.0.0:8081
```
