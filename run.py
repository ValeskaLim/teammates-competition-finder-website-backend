from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG_MODE", "False") == "True"
    app.run(host="0.0.0.0", port=5002, debug=debug_mode)
