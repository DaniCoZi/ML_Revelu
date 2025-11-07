# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config

# Extensiones (una sola vez, fuera de create_app)
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

login_manager.login_view = "auth.login_page"  # a dónde redirigir si no está logueado

def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    )

    # Cargar configuración
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Rutas de salud/diagnóstico
    @app.get("/healthz")
    def healthz():
        return "ok", 200

    @app.get("/dbcheck")
    def dbcheck():
        try:
            with db.engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return "db ok", 200
        except Exception as e:
            return f"db error: {e}", 500

    # Importa modelos para que Alembic los detecte
    # (importa después de inicializar 'db')
    from app.models import user, post  # noqa: F401

    # Blueprints
    from app.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.controllers.main_controller import main_controller
    app.register_blueprint(main_controller)

    # Foro (API CRUD)
    from app.controllers.forum_controller import forum_bp
    app.register_blueprint(forum_bp)

    # Carga de usuario para Flask-Login
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import User
        return User.query.get(int(user_id))

    return app