from datetime import datetime
import markdown
from flask import Flask, render_template
from config import Config
from models import db
from database import init_db
from auth import auth_bp
from routes.main_routes import main_bp
from routes.chat_routes import chat_bp
from routes.study_routes import study_bp
from routes.quiz_routes import quiz_bp
from routes.progress_routes import progress_bp
from routes.admin_routes import admin_bp
from ai_provider import AIProvider


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(admin_bp)

    # Template filters
    @app.template_filter("markdown")
    def render_markdown(text):
        if not text:
            return ""
        return markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        )

    # Global context processor
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "ai_engine_info": AIProvider.get_active_provider_info(),
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    # Ensure database tables and seed data exist
    init_db(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=Config.PORT, debug=Config.DEBUG)