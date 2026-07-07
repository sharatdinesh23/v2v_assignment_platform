import reflex as rx

config = rx.Config(
    app_name="code_arena",
    # Reflex runs its own backend; the FastAPI app is mounted via api_transformer
    # (see code_arena/code_arena.py)
    telemetry_enabled=False,
)
