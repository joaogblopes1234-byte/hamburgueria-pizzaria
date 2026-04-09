import traceback

try:
    from app import app
except Exception as e:
    from flask import Flask
    app = Flask(__name__)
    err = traceback.format_exc()
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        import html
        return f"<h1>Vercel Boot Error</h1><pre>{html.escape(err)}</pre>", 500
