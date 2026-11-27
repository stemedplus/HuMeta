# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Researcher sign-in: which OpenID Connect providers are offered, and who signed in.

Researchers sign in with Google or ORCID, through Streamlit's built-in OpenID
Connect sign-in. Each provider is a named table in the app's secrets,
``[auth.google]`` and ``[auth.orcid]``, and gets its own button; a provider
without a table is not offered. A single unnamed provider written straight
into ``[auth]`` (the original Google-only setup) still works and is shown as
Google.

Nothing here imports Streamlit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    key: str | None  #: name of the [auth.<key>] table, passed to st.login; None = the unnamed [auth] provider
    label: str  #: shown on the button: "Sign in with <label>"


#: Providers the portal knows, in the order their buttons appear
KNOWN_PROVIDERS: tuple[Provider, ...] = (
    Provider("google", "Google"),
    Provider("orcid", "ORCID"),
)
_LABELS = {p.key: p.label for p in KNOWN_PROVIDERS}
_PROVIDER_KEYS = ("client_id", "client_secret", "server_metadata_url")


def configured_providers(auth_section: Mapping | None) -> list[Provider]:
    """The sign-in providers set up in the secrets' [auth] section, in button order."""
    if not auth_section:
        return []
    found = [p for p in KNOWN_PROVIDERS if _is_provider_table(auth_section.get(p.key))]
    if not found and _is_provider_table(auth_section):
        found = [Provider(None, "Google")]  # the original single-provider setup
    return found


def _is_provider_table(section: object) -> bool:
    # Streamlit's secrets tables are mapping-like but not always Mapping subclasses
    return hasattr(section, "get") and all(section.get(k) for k in _PROVIDER_KEYS)


def provider_label(provider_key: str | None) -> str:
    """'ORCID' for 'orcid'; the unnamed [auth] provider ('default' in st.user) is Google."""
    if not provider_key or provider_key == "default":
        return "Google"
    return _LABELS.get(provider_key, provider_key.title())


def display_name(claims: Mapping) -> str:
    """The signed-in researcher's name from their ID-token claims, or '' if it has none.

    Google sends ``name``. ORCID may send only ``given_name`` and
    ``family_name``.
    """
    name = str(claims.get("name") or "").strip()
    if name:
        return name
    parts = (str(claims.get(k) or "").strip() for k in ("given_name", "family_name"))
    return " ".join(p for p in parts if p)

