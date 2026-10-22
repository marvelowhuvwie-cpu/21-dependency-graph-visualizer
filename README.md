# Dependency Graph Visualizer

A small developer tool for exploring package dependencies and identifying circular dependencies. The repository contains a Flask API, a plain HTML/CSS/JavaScript frontend, and Python modules for manifest parsing, graph construction, and cycle detection.

## Project layout

- `app/` — Flask application, API routes, analysis service, and optional SQLite history support.
- `backend/app/graph/` — dependency graph models, graph building, and cycle-detection algorithms.
- `backend/app/parsers/` — package manifest parsing utilities.
- `frontend/` — browser interface and JavaScript modules.
- `backend/tests/` — tests for the graph and manifest-parser modules.
- `tests/` — API and frontend-related tests.
- `sample_data/package.json` — a small sample Node.js package manifest.

## Requirements

- Python 3.10 or newer
- pip
- A modern web browser

## Setup on Windows (PowerShell)

Open a terminal in the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, you can use the environment's Python directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Setup on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install the root `requirements.txt` for the Flask application and its dependencies. Avoid committing virtual environments; they are local to each machine.

## Run the Flask API

From the repository root, with the environment activated:

```bash
python run.py
```

The server defaults to `http://127.0.0.1:5000`.

- Health check: `GET http://127.0.0.1:5000/health`
- Manifest analysis: `POST http://127.0.0.1:5000/api/analyze` using multipart form data with a file field named `file`.

The API accepts `package.json` and `package-lock.json` uploads, with a maximum upload size of 5 MiB. Invalid or unsupported uploads return structured JSON errors.

**Integration note:** the Flask analysis service currently expects an analyzer to be supplied through application configuration. If it is not configured, `/api/analyze` returns `ANALYZER_NOT_CONFIGURED` (HTTP 503). The graph and parser modules under `backend/app/` are present, but the repository still needs to connect them to the Flask API for end-to-end analysis.

## Run tests

Run all Python tests from the repository root:

```bash
python -m pytest -v
```

The pytest configuration discovers both `tests/` and `backend/tests/`. On Windows, use `py -m pytest -v` if the `python` command is unavailable.

The repository also contains JavaScript test files in `tests/frontend/`, but there is not yet a package manifest or configured npm test script for them.

## Example manifest

The included `sample_data/package.json` declares `express` and `axios` as dependencies and `jest` as a development dependency. It can be used as sample input once the API analyzer integration is connected.

## Current scope and next steps

The repository has graph construction, manifest parsing, cycle-detection modules, a Flask upload endpoint, and a browser frontend. Important next steps are to connect the backend modules to the API analysis service, ensure the full API/frontend test suites run reliably, and document the actual end-to-end user flow once that integration is complete.
