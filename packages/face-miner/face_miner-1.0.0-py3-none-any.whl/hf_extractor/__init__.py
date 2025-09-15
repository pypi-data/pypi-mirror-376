# hf_extractor/__init__.py
# This file marks the `hf_extractor` directory as a Python package.
# It contains the application factory function, `create_app`.

from flask import Flask
from .config import Config

def create_app(config_class=Config):
    """
    Application factory function.
    
    Creates and configures the Flask application.
    This pattern is useful for creating multiple app instances
    for testing or different configurations.
    """
    # Create the Flask app instance
    app = Flask(__name__)
    
    # Load configuration from the Config object
    app.config.from_object(config_class)

    # Import and register the blueprint for the main routes
    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    return app
