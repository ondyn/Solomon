####
## Solomon - NetBox Configuration
##
## This file is mounted into the NetBox container at /etc/netbox/config/configuration.py
## All values are read from environment variables (set via .env file).
## See: https://docs.netbox.dev/en/stable/configuration/
####

import re
from os import environ
from typing import Any, Callable


def _read_secret(secret_name: str, default: str | None = None) -> str | None:
    """Read a Docker secret from /run/secrets/, fall back to default."""
    try:
        with open("/run/secrets/" + secret_name, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except EnvironmentError:
        return default


def _environ_get_and_map(
    variable_name: str,
    default: str | None = None,
    map_fn: Callable[[str], Any | None] = None,
) -> Any | None:
    """Get an env var and optionally transform it with map_fn."""
    env_value = environ.get(variable_name, default)
    if env_value is None:
        return env_value
    if not map_fn:
        return env_value
    return map_fn(env_value)


_AS_BOOL = lambda value: value.lower() == "true"
_AS_INT = lambda value: int(value)
_AS_LIST = lambda value: list(filter(None, value.split(" ")))


#########################
#   Required settings   #
#########################

ALLOWED_HOSTS = environ.get("ALLOWED_HOSTS", "*").split(" ")
if "*" not in ALLOWED_HOSTS and "localhost" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("localhost")

DATABASE = {
    "NAME": environ.get("DB_NAME", "netbox"),
    "USER": environ.get("DB_USER", ""),
    "PASSWORD": _read_secret("db_password", environ.get("DB_PASSWORD", "")),
    "HOST": environ.get("DB_HOST", "postgres"),
    "PORT": environ.get("DB_PORT", ""),
    "OPTIONS": {"sslmode": environ.get("DB_SSLMODE", "prefer")},
    "CONN_MAX_AGE": _environ_get_and_map("DB_CONN_MAX_AGE", "300", _AS_INT),
}

REDIS = {
    "tasks": {
        "HOST": environ.get("REDIS_HOST", "redis"),
        "PORT": _environ_get_and_map("REDIS_PORT", "6379", _AS_INT),
        "USERNAME": environ.get("REDIS_USERNAME", ""),
        "PASSWORD": _read_secret(
            "redis_password", environ.get("REDIS_PASSWORD", "")
        ),
        "DATABASE": _environ_get_and_map("REDIS_DATABASE", "0", _AS_INT),
        "SSL": _environ_get_and_map("REDIS_SSL", "False", _AS_BOOL),
        "INSECURE_SKIP_TLS_VERIFY": _environ_get_and_map(
            "REDIS_INSECURE_SKIP_TLS_VERIFY", "False", _AS_BOOL
        ),
    },
    "caching": {
        "HOST": environ.get(
            "REDIS_CACHE_HOST", environ.get("REDIS_HOST", "redis-cache")
        ),
        "PORT": _environ_get_and_map(
            "REDIS_CACHE_PORT", environ.get("REDIS_PORT", "6379"), _AS_INT
        ),
        "USERNAME": environ.get(
            "REDIS_CACHE_USERNAME", environ.get("REDIS_USERNAME", "")
        ),
        "PASSWORD": _read_secret(
            "redis_cache_password",
            environ.get("REDIS_CACHE_PASSWORD", environ.get("REDIS_PASSWORD", "")),
        ),
        "DATABASE": _environ_get_and_map("REDIS_CACHE_DATABASE", "1", _AS_INT),
        "SSL": _environ_get_and_map(
            "REDIS_CACHE_SSL", environ.get("REDIS_SSL", "False"), _AS_BOOL
        ),
        "INSECURE_SKIP_TLS_VERIFY": _environ_get_and_map(
            "REDIS_CACHE_INSECURE_SKIP_TLS_VERIFY",
            environ.get("REDIS_INSECURE_SKIP_TLS_VERIFY", "False"),
            _AS_BOOL,
        ),
    },
}

SECRET_KEY = _read_secret("secret_key", environ.get("SECRET_KEY", ""))

API_TOKEN_PEPPERS = {}
if api_token_pepper := _read_secret(
    "api_token_pepper_1", environ.get("API_TOKEN_PEPPER_1", "")
):
    API_TOKEN_PEPPERS.update({1: api_token_pepper})


#########################
#   Optional settings   #
#########################

CORS_ORIGIN_ALLOW_ALL = _environ_get_and_map("CORS_ORIGIN_ALLOW_ALL", "False", _AS_BOOL)
CORS_ORIGIN_WHITELIST = _environ_get_and_map(
    "CORS_ORIGIN_WHITELIST", "https://localhost", _AS_LIST
)
CORS_ORIGIN_REGEX_WHITELIST = [
    re.compile(r)
    for r in _environ_get_and_map("CORS_ORIGIN_REGEX_WHITELIST", "", _AS_LIST)
]

DEBUG = _environ_get_and_map("DEBUG", "False", _AS_BOOL)
DEVELOPER = _environ_get_and_map("DEVELOPER", "False", _AS_BOOL)
ISOLATED_DEPLOYMENT = _environ_get_and_map("ISOLATED_DEPLOYMENT", "False", _AS_BOOL)

# Email
EMAIL = {
    "SERVER": environ.get("EMAIL_SERVER", "localhost"),
    "PORT": _environ_get_and_map("EMAIL_PORT", "25", _AS_INT),
    "USERNAME": environ.get("EMAIL_USERNAME", ""),
    "PASSWORD": _read_secret("email_password", environ.get("EMAIL_PASSWORD", "")),
    "USE_SSL": _environ_get_and_map("EMAIL_USE_SSL", "False", _AS_BOOL),
    "USE_TLS": _environ_get_and_map("EMAIL_USE_TLS", "False", _AS_BOOL),
    "SSL_CERTFILE": environ.get("EMAIL_SSL_CERTFILE", ""),
    "SSL_KEYFILE": environ.get("EMAIL_SSL_KEYFILE", ""),
    "TIMEOUT": _environ_get_and_map("EMAIL_TIMEOUT", "10", _AS_INT),
    "FROM_EMAIL": environ.get("EMAIL_FROM", ""),
}

GRAPHQL_ENABLED = _environ_get_and_map("GRAPHQL_ENABLED", "True", _AS_BOOL)
METRICS_ENABLED = _environ_get_and_map("METRICS_ENABLED", "False", _AS_BOOL)
WEBHOOKS_ENABLED = _environ_get_and_map("WEBHOOKS_ENABLED", "True", _AS_BOOL)

MEDIA_ROOT = environ.get("MEDIA_ROOT", "/opt/netbox/netbox/media")

if "RELEASE_CHECK_URL" in environ:
    RELEASE_CHECK_URL = environ.get("RELEASE_CHECK_URL")

# Superuser creation
SKIP_SUPERUSER = _environ_get_and_map("SKIP_SUPERUSER", "true", _AS_BOOL)

# Granian web server
GRANIAN_WORKERS = _environ_get_and_map("GRANIAN_WORKERS", "4", _AS_INT)
GRANIAN_BACKPRESSURE = _environ_get_and_map("GRANIAN_BACKPRESSURE", "4", _AS_INT)

if "CHANGELOG_RETENTION" in environ:
    CHANGELOG_RETENTION = _environ_get_and_map("CHANGELOG_RETENTION", None, _AS_INT)

if "JOB_RETENTION" in environ:
    JOB_RETENTION = _environ_get_and_map("JOB_RETENTION", None, _AS_INT)

# Time zone - default to Czech Republic
TIME_ZONE = environ.get("TIME_ZONE", "Europe/Prague")

# Default language
if "DEFAULT_LANGUAGE" in environ:
    DEFAULT_LANGUAGE = environ.get("DEFAULT_LANGUAGE")

# NetBox Copilot AI agent
if "COPILOT_ENABLED" in environ:
    COPILOT_ENABLED = _environ_get_and_map("COPILOT_ENABLED", "false", _AS_BOOL)