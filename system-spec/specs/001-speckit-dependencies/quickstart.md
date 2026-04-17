# Quickstart: Spec Kit Dependencies

## Prerequisites

- Python 3.10+
- Docker (optional)

## Local Virtual Environment

Run the following commands to install dependencies which now natively include `specify-cli`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify Spec Kit installation:
```bash
specify --help
```

## Docker Environment

The Docker environment now seamlessly includes `specify-cli` alongside all existing backend dependencies.

```bash
docker build -t growth_analyzer_app .
docker run --rm -it growth_analyzer_app specify --help
```
