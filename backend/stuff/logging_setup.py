from stuff.settings import get_settings
import logging

def setup_logging():
    settings = get_settings()
    if isinstance(settings, dict):
        level = settings.get("LOG_LEVEL", settings.get("app", {}).get("log_level", "INFO"))
    else:
        level = getattr(settings, "LOG_LEVEL", "INFO")
        app = getattr(settings, "app", None)
        if isinstance(app, dict) and level == "INFO":
            level = app.get("log_level", level)
    level = str(level).upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # When debugging, keep provider HTTP/client logs visible; otherwise mute
    # to WARNING (errors still surface, debug noise hidden).
    _quiet = logging.INFO if level == "DEBUG" else logging.WARNING
    for name in ("LiteLLM", "LiteLLM Router", "httpx", "httpcore", "openai"):
        logging.getLogger(name).setLevel(_quiet)
