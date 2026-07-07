import reflex as rx
import sys
from dotenv import load_dotenv
import os 

load_dotenv()

# Conditionally use localhost:8000 for local development ('run' command)
# to avoid connecting to the production server when developing locally.
is_dev = "run" in sys.argv or any("reflex" in arg for arg in sys.argv) and not any("export" in arg for arg in sys.argv)
api_url = "http://localhost:8000" if is_dev else os.getenv("API_URL", "http://localhost:8000")

config = rx.Config(
    app_name="code_arena",
    # Reflex runs its own backend; the FastAPI app is mounted via api_transformer
    # (see code_arena/code_arena.py)
    telemetry_enabled=False,
    api_url=api_url,
)
