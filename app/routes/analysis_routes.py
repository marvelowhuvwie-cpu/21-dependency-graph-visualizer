import json

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from app.services.analysis_service import (
    AnalysisError,
    analyze_manifest,
)


analysis_bp = Blueprint("analysis", __name__)


def error_response(code, message, status_code):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
        }
    }), status_code


@analysis_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@analysis_bp.post("/api/analyze")
def analyze():
    if "file" not in request.files:
        return error_response(
            "MISSING_FILE",
            "Upload a manifest using the 'file' field.",
            400,
        )

    uploaded_file = request.files["file"]

    if not uploaded_file.filename:
        return error_response(
            "MISSING_FILENAME",
            "A filename is required.",
            400,
        )

    filename = uploaded_file.filename

    if filename not in {"package.json", "package-lock.json"}:
        return error_response(
            "UNSUPPORTED_FILE",
            "Only package.json and package-lock.json are supported.",
            415,
        )

    try:
        raw_content = uploaded_file.stream.read(
            current_app.config["MAX_CONTENT_LENGTH"] + 1
        )
    except RequestEntityTooLarge:
        return error_response(
            "UPLOAD_TOO_LARGE",
            "The uploaded file exceeds the maximum allowed size.",
            413,
        )

    if len(raw_content) > current_app.config["MAX_CONTENT_LENGTH"]:
        return error_response(
            "UPLOAD_TOO_LARGE",
            "The uploaded file exceeds the maximum allowed size.",
            413,
        )

    if not raw_content.strip():
        return error_response(
            "EMPTY_FILE",
            "The uploaded file is empty.",
            400,
        )

    try:
        manifest = json.loads(raw_content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return error_response(
            "INVALID_JSON",
            "The uploaded file must contain valid UTF-8 JSON.",
            400,
        )

    if not isinstance(manifest, dict):
        return error_response(
            "INVALID_MANIFEST",
            "The manifest must contain a JSON object.",
            422,
        )

    try:
        result = analyze_manifest(
            manifest=manifest,
            filename=filename,
            analyzer=current_app.config.get("DEPENDENCY_ANALYZER"),
        )
    except AnalysisError as exc:
        return error_response(
            exc.code,
            exc.message,
            exc.status_code,
        )
    except Exception:
        current_app.logger.exception(
            "Unexpected error during dependency analysis"
        )
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred during analysis.",
            500,
        )

    if current_app.config["ENABLE_ANALYSIS_HISTORY"]:
        from app.database.db import save_analysis

        save_analysis(
            current_app,
            result,
        )

    return jsonify(result), 200