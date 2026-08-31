"""Shared helpers for Solomon Issues."""

import re
import secrets
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext as _
from netbox.context import current_request

#: Excludes vowels and easily confused glyphs so codes can be read from a label.
CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_LENGTH = 10
TOKEN_LENGTH = 32

_SPLIT_RE = re.compile(r"[,;\s]+")


def get_plugin_settings():
    return settings.PLUGINS_CONFIG.get("solomon_issues", {})


def get_setting(name, default=None):
    return get_plugin_settings().get(name, default)


def generate_code(length=CODE_LENGTH):
    """Return an opaque, human-transcribable code used in public QR URLs."""
    return "".join(secrets.choice(CODE_ALPHABET) for _index in range(length))


def generate_token(length=TOKEN_LENGTH):
    """Return an unguessable token used for reporter access links."""
    return secrets.token_urlsafe(length)[:length]


def split_emails(value):
    """Split a free-text recipient list into individual addresses."""
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        candidates = value
    else:
        candidates = _SPLIT_RE.split(str(value))
    return [address.strip() for address in candidates if address and address.strip()]


def validate_email_list(value):
    for address in split_emails(value):
        try:
            validate_email(address)
        except ValidationError:
            raise ValidationError(
                _("%(address)s is not a valid e-mail address.") % {"address": address}
            )


def get_public_base_url(request=None):
    """Resolve the absolute base URL used for QR codes and e-mail links."""
    configured = (get_setting("public_base_url") or "").strip()
    if configured:
        return configured.rstrip("/")
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    host = next(
        (h for h in settings.ALLOWED_HOSTS if h not in ("*", "")),
        "localhost:8000",
    )
    scheme = "http" if host.startswith(("localhost", "127.0.0.1")) else "https"
    return f"{scheme}://{host}"


def build_public_url(path, request=None):
    return f"{get_public_base_url(request)}{path}"


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def public_languages():
    """Ordered mapping of language codes offered on public pages to their names."""
    configured = get_setting("public_languages") or ["en", "cs"]
    supported = dict(settings.LANGUAGES)
    return {code: supported.get(code, code) for code in configured if code in supported}


@contextmanager
def anonymous_write(request):
    """Detach NetBox change logging, which cannot attribute an AnonymousUser."""
    if request is not None and request.user.is_authenticated:
        yield
        return
    token = current_request.set(None)
    try:
        yield
    finally:
        current_request.reset(token)
