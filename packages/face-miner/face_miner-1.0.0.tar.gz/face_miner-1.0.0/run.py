# run.py
# This is the main entry point for the application.
# Its only job is to create and run the Flask app.

from hf_extractor import create_app

# Create an application instance using the factory pattern
app = create_app()

if __name__ == '__main__':
    # Run the app in debug mode on port 5050
    # Note: In a production environment, you would use a proper WSGI server
    # like Gunicorn or uWSGI instead of the Flask development server.
    app.run(debug=True, port=5050)
