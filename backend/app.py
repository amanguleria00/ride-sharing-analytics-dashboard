"""Flask application entry point."""

import logging
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from controller import api


def create_app(database_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = str(database_path or
                                  os.environ.get("RIDE_SHARING_DATABASE") or
                                  Path(__file__).with_name("ride_sharing.db"))
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": {"message": "Resource not found"}}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        app.logger.exception("Unexpected API failure")
        return jsonify({"error": {"message": "An unexpected server error occurred"}}), 500

    @app.before_request
    def ensure_database_available():
        if not Path(app.config["DATABASE"]).is_file():
            return jsonify({"error": {"message": "Database not initialized. Run python init_db.py."}}), 503

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
