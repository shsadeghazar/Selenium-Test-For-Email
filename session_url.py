import json
from urllib.parse import urlparse


def _origin(url):
    parsed = urlparse(url)
    default_port = (
        parsed.port is None
        or (parsed.scheme == "https" and parsed.port == 443)
        or (parsed.scheme == "http" and parsed.port == 80)
    )
    port = "" if default_port else f":{parsed.port}"
    return f"{parsed.scheme.lower()}://{(parsed.hostname or '').lower()}{port}"


def resolve_app_base_url(default_base_url, session_path="session.json"):
    """Use the path captured at login, while preserving old direct-login sessions."""
    try:
        with open(session_path, "r", encoding="utf-8") as session_file:
            saved_base_url = json.load(session_file).get("app_base_url")
    except (FileNotFoundError, OSError, ValueError, AttributeError):
        return default_base_url

    if not isinstance(saved_base_url, str) or not saved_base_url.strip():
        return default_base_url

    saved_base_url = saved_base_url.strip()
    if _origin(saved_base_url) != _origin(default_base_url):
        return default_base_url

    return saved_base_url.rstrip("/") + "/"
