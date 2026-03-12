import os

from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from .database import db

def create_app():
    # Serve frontend from dist directory
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Initialize database
    db.init_db()
    
    # Enable CORS for development
    CORS(app, origins=["http://localhost:5173", "http://localhost:5000"])

    from .routes import api
    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return {"status": "ok", "database": "sqlite", "frontend": "integrated"}

    # Serve static files (CSS, JS, images)
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(static_dir, 'assets'), filename)

    # Root route - serve React app
    @app.get("/")
    def index():
        if os.path.exists(os.path.join(static_dir, "index.html")):
            return send_file(os.path.join(static_dir, "index.html"))
        return {
            "message": "Driver AI Co-Pilot API", 
            "status": "Frontend not built. Run 'npm run build' first.",
            "api_endpoints": ["/api/auth/login", "/api/auth/signup", "/api/monitor/analyze"]
        }

    # Catch-all route for React Router (SPA)
    @app.route('/<path:path>')
    def serve_react_app(path):
        # Check if it's an API route
        if path.startswith('api/'):
            return {"error": "API endpoint not found"}, 404
        
        # Check if file exists in static folder
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        
        # Fallback to index.html for React Router
        if os.path.exists(os.path.join(static_dir, "index.html")):
            return send_file(os.path.join(static_dir, "index.html"))
        
        return {"error": "Frontend not built"}, 404

    return app
