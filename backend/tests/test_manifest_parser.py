import json

import pytest

from backend.app.parsers.manifest_parser import (
    ManifestParseError,
    parse_manifest,
)


def test_parse_manifest_with_all_fields(tmp_path):
    manifest_data = {
        "name": "test-project",
        "dependencies": {
            "express": "^4.18.2",
            "axios": "^1.6.0",
        },
        "devDependencies": {
            "jest": "^29.7.0",
        },
    }
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    assert parse_manifest(manifest_file) == {
        "project_name": "test-project",
        "dependencies": {
            "express": "^4.18.2",
            "axios": "^1.6.0",
        },
        "dev_dependencies": {"jest": "^29.7.0"},
    }


def test_parse_manifest_without_optional_fields(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text("{}", encoding="utf-8")

    assert parse_manifest(manifest_file) == {
        "project_name": None,
        "dependencies": {},
        "dev_dependencies": {},
    }


def test_parse_manifest_with_empty_dependencies(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text(
        json.dumps({
            "name": "empty-project",
            "dependencies": {},
            "devDependencies": {},
        }),
        encoding="utf-8",
    )

    result = parse_manifest(manifest_file)
    assert result["project_name"] == "empty-project"
    assert result["dependencies"] == {}
    assert result["dev_dependencies"] == {}


def test_parse_manifest_with_invalid_json(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text('{"name": "broken-project",', encoding="utf-8")

    with pytest.raises(ManifestParseError, match="invalid JSON"):
        parse_manifest(manifest_file)


def test_parse_manifest_with_missing_file(tmp_path):
    with pytest.raises(ManifestParseError, match="does not exist"):
        parse_manifest(tmp_path / "missing.json")


def test_parse_manifest_with_non_object_json(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text('["express", "axios"]', encoding="utf-8")

    with pytest.raises(ManifestParseError, match="JSON object"):
        parse_manifest(manifest_file)


def test_parse_manifest_with_invalid_dependencies_type(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text(
        json.dumps({
            "name": "test-project",
            "dependencies": ["express", "axios"],
        }),
        encoding="utf-8",
    )

    with pytest.raises(
        ManifestParseError,
        match="dependencies.*must be an object",
    ):
        parse_manifest(manifest_file)


def test_parse_manifest_with_non_string_version(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text(
        json.dumps({
            "name": "test-project",
            "dependencies": {"express": 123},
        }),
        encoding="utf-8",
    )

    with pytest.raises(ManifestParseError, match="must be a string"):
        parse_manifest(manifest_file)


def test_parse_manifest_with_non_string_name(tmp_path):
    manifest_file = tmp_path / "package.json"
    manifest_file.write_text(
        json.dumps({
            "name": 123,
            "dependencies": {},
        }),
        encoding="utf-8",
    )

    with pytest.raises(ManifestParseError, match="name.*must be a string"):
        parse_manifest(manifest_file)
