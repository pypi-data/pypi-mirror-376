# hf_extractor/main/__init__.py
# This file initializes the 'main' blueprint.
# Blueprints are used to organize a group of related routes and views.

from flask import Blueprint

# Create a Blueprint instance
# The first argument, 'main', is the blueprint's name.
# The second argument, __name__, helps Flask locate the blueprint's resources.
main_bp = Blueprint('main', __name__)

# Import the routes at the end to avoid circular dependencies.
# The routes module needs to import `main_bp` from this file.
from . import routes
