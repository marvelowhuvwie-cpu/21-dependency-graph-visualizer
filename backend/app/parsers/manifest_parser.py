import json
from pathlib import Path
from typing import Any


class ManifestParseError(Exception):
    """Raised when a manifest cannot be parsed or validated."""


def parse_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """
    Read and validate a package.json manifest.

    Returns a predictable dictionary containing the project name,
    regular dependencies, and development dependencies.
    """
    path = Path(manifest_path)

    if not path.is_file():
        raise ManifestParseError(
            f"Manifest file does not exist: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ManifestParseError(
            f"Manifest contains invalid JSON: {error}"
        ) from error
    except OSError as error:
        raise ManifestParseError(
            f"Could not read manifest file: {error}"
        ) from error

    if not isinstance(manifest, dict):
        raise ManifestParseError(
            "Manifest must contain a JSON object."
        )

    project_name = manifest.get("name")
    if project_name is not None and not isinstance(project_name, str):
        raise ManifestParseError(
            "The 'name' field must be a string."
        )

    dependencies = _extract_dependencies(manifest, "dependencies")
    dev_dependencies = _extract_dependencies(manifest, "devDependencies")

    return {
        "project_name": project_name,
        "dependencies": dependencies,
        "dev_dependencies": dev_dependencies,
    }


def _extract_dependencies(
    manifest: dict[str, Any],
    section_name: str,
) -> dict[str, str]:
    """Extract and validate a dependency section."""
    dependencies = manifest.get(section_name, {})

    if not isinstance(dependencies, dict):
        raise ManifestParseError(
            f"The '{section_name}' field must be an object."
        )

    for package_name, version in dependencies.items():
        if not isinstance(package_name, str) or not package_name:
            raise ManifestParseError(
                f"Invalid package name in '{section_name}'."
            )

        if not isinstance(version, str):
            raise ManifestParseError(
                f"Version for '{package_name}' in "
                f"'{section_name}' must be a string."
            )

    return dependencies
