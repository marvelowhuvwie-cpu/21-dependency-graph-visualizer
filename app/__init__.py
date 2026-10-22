import os
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from app.database.db import init_db
from app.routes.analysis_routes import analysis_bp


def create_app(test_config=None):
    app = Flask(__name__)

    project_root = Path(__file__).resolve().parent.parent
    default_database = project_root / "instance" / "dependency_graph.db"

    app.config.from_mapping(
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            str(default_database),
        ),
        ENABLE_ANALYSIS_HISTORY=False,
        FRONTEND_ORIGINS=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )

    if test_config:
        app.config.update(test_config)

    origins = app.config["FRONTEND_ORIGINS"]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
            },
            r"/health": {
                "origins": origins,
            },
        },
    )

    if app.config["ENABLE_ANALYSIS_HISTORY"]:
        init_db(app)

    app.register_blueprint(analysis_bp)

    @app.errorhandler(413)

    def handle_request_too_large(_error):
        return jsonify({
            "error": {
                "code": "UPLOAD_TOO_LARGE",
                "message": "The request exceeds the maximum allowed size.",
            }
        }), 413

    @app.errorhandler(404)

    def handle_not_found(_error):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested endpoint was not found.",
            }
        }), 404

    @app.errorhandler(500)
    
    def handle_internal_error(_error):
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected server error occurred.",
            }
        }), 500

    return app