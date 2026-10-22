import io

import pytest

from app import create_app


def example_result(**kwargs):
    """Return a valid sample analysis result."""

    return {
        "summary": {
            "projectName": "demo",
        },
        "nodes": [
            {
                "id": "project:demo",
                "label": "demo",
                "type": "project",
                "version": None,
            },
            {
                "id": "package:alpha",
                "label": "alpha",
                "type": "package",
                "version": "^1.0.0",
            },
        ],
        "edges": [
            {
                "source": "project:demo",
                "target": "package:alpha",
            },
        ],
        "cycles": [],
    }


@pytest.fixture
def app(tmp_path):
    def fake_analyzer(*, manifest, filename):
        return example_result()

    application = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 1024,
        "DATABASE": str(tmp_path / "test.db"),
        "ENABLE_ANALYSIS_HISTORY": False,
        "FRONTEND_ORIGINS": [
            "http://localhost:5500",
        ],
        "DEPENDENCY_ANALYZER": fake_analyzer,
    })

    return application


@pytest.fixture
def client(app):
    return app.test_client()


def upload(client, filename, content):
    return client.post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(content),
                filename,
            ),
        },
        content_type="multipart/form-data",
    )


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_successful_manifest_analysis(client):
    response = upload(
        client,
        "package.json",
        b'{"name":"demo","dependencies":{"alpha":"^1.0.0"}}',
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["summary"]["projectName"] == "demo"
    assert result["summary"]["nodeCount"] == 2
    assert result["summary"]["edgeCount"] == 1
    assert result["summary"]["cycleCount"] == 0


def test_successful_package_lock_upload(client):
    response = upload(
        client,
        "package-lock.json",
        b'{"name":"demo","lockfileVersion":3,"packages":{}}',
    )

    assert response.status_code == 200


def test_missing_upload(client):
    response = client.post("/api/analyze")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_FILE"


def test_unsupported_file_type(client):
    response = upload(
        client,
        "requirements.txt",
        b"Flask",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "UNSUPPORTED_FILE"


def test_empty_file(client):
    response = upload(
        client,
        "package.json",
        b"",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "EMPTY_FILE"


def test_invalid_json(client):
    response = upload(
        client,
        "package.json",
        b'{"name":',
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_JSON"


def test_manifest_must_be_json_object(client):
    response = upload(
        client,
        "package.json",
        b'["alpha", "beta"]',
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INVALID_MANIFEST"


def test_oversized_upload(client):
    response = upload(
        client,
        "package.json",
        b"x" * 2048,
    )

    assert response.status_code == 413


def test_circular_dependency_reporting(tmp_path):
    def circular_analyzer(*, manifest, filename):
        result = example_result()

        result["nodes"].append({
            "id": "package:beta",
            "label": "beta",
            "type": "package",
            "version": "1.0.0",
        })

        result["edges"].extend([
            {
                "source": "package:alpha",
                "target": "package:beta",
            },
            {
                "source": "package:beta",
                "target": "package:alpha",
            },
        ])

        result["cycles"] = [
            ["package:alpha", "package:beta"],
        ]

        return result

    app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 1024,
        "DATABASE": str(tmp_path / "cycle.db"),
        "ENABLE_ANALYSIS_HISTORY": False,
        "FRONTEND_ORIGINS": [],
        "DEPENDENCY_ANALYZER": circular_analyzer,
    })

    response = app.test_client().post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b'{"name":"demo"}'),
                "package.json",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["summary"]["cycleCount"] == 1
    assert result["cycles"] == [
        ["package:alpha", "package:beta"],
    ]


def test_invalid_analyzer_result_returns_error(client, app):
    app.config["DEPENDENCY_ANALYZER"] = (
        lambda **kwargs: {"nodes": "invalid"}
    )

    response = upload(
        client,
        "package.json",
        b'{"name":"demo"}',
    )

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == (
        "INVALID_ANALYSIS_RESULT"
    )


def test_unexpected_analyzer_error_is_sanitized(client, app):
    def failing_analyzer(**kwargs):
        raise RuntimeError("Internal database credentials")

    app.config["DEPENDENCY_ANALYZER"] = failing_analyzer

    response = upload(
        client,
        "package.json",
        b'{"name":"demo"}',
    )

    assert response.status_code == 500
    assert (
        "Internal database credentials"
        not in response.get_data(as_text=True)
    )


def test_analysis_history_is_stored_when_enabled(tmp_path):
    def fake_analyzer(*, manifest, filename):
        return example_result()

    database_path = tmp_path / "history.db"

    app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 1024,
        "DATABASE": str(database_path),
        "ENABLE_ANALYSIS_HISTORY": True,
        "FRONTEND_ORIGINS": [],
        "DEPENDENCY_ANALYZER": fake_analyzer,
    })

    response = app.test_client().post(
        "/api/analyze",
        data={
            "file": (
                io.BytesIO(b'{"name":"demo"}'),
                "package.json",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert database_path.exists()