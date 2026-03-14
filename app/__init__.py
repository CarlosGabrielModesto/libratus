"""
app/__init__.py — Factory function da aplicação Flask (Application Factory Pattern).
"""

import os
from flask import Flask, render_template
from dotenv import load_dotenv

from .extensions import db
from .models.database import criar_tabelas


def create_app() -> Flask:
    """Cria e configura a instância da aplicação Flask."""

    load_dotenv()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # --- Configurações ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32))
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # --- Inicializa extensões ---
    db.init_app(app)

    with app.app_context():
        criar_tabelas()

    # --- Registra Blueprints ---
    from .controllers.auth import bp as auth_bp
    from .controllers.books import bp as books_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)

    # --- Handlers de erro globais ---
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    return app


def _build_db_uri() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, os.environ.get("DATA_DIR", "data"))
    os.makedirs(data_dir, exist_ok=True)
    return f"sqlite:///{data_dir}/libratus.db"
