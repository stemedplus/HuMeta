# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Researcher sign-in: which OpenID Connect providers are offered, and who signed in.

Researchers sign in with Google, ORCID, or Microsoft (work, school, or personal
accounts), through Streamlit's built-in OpenID Connect sign-in. Each provider is
a named table in the app's secrets, ``[auth.google]``, ``[auth.orcid]`` and
``[auth.microsoft]``, and gets its own button; a provider without a table is
not offered. A single unnamed provider written straight into ``[auth]`` (the
original Google-only setup) still works and is shown as Google.

Microsoft sign-in for any university uses one multi-tenant Entra app and
Microsoft's ``/common`` endpoint. That endpoint's discovery document gives its
issuer as a template, ``https://login.microsoftonline.com/{tenantid}/v2.0``,
which Authlib (used by Streamlit) compares literally against the real issuer in
each ID token, so every sign-in fails with ``invalid_claim: iss`` (Streamlit
issue #11391, Authlib issue #605). :func:`allow_microsoft_multitenant_issuer`
fixes this: only for a provider whose issuer is that template, it accepts an
issuer naming a real tenant, and only when it matches the token's ``tid``.
Everything else is checked by Authlib as before.

Only :func:`allow_microsoft_multitenant_issuer` imports Authlib, and nothing here
imports Streamlit, so the rest can be tested without either.
"""

from __future__ import annotations

import functools
import re
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
    Provider("microsoft", "Microsoft"),
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

    Google and Microsoft send ``name``. ORCID may send only ``given_name`` and
    ``family_name``.
    """
    name = str(claims.get("name") or "").strip()
    if name:
        return name
    parts = (str(claims.get(k) or "").strip() for k in ("given_name", "family_name"))
    return " ".join(p for p in parts if p)


# ---------- Microsoft multi-tenant issuer ----------

_TEMPLATE_ISSUER_MARK = "{tenantid}"
_GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_MICROSOFT_TENANT_ISSUER = re.compile(rf"\Ahttps://login\.microsoftonline\.com/(?P<tid>{_GUID})/v2\.0\Z")


def is_microsoft_tenant_issuer(claims: Mapping, issuer: object) -> bool:
    """True when ``issuer`` is a Microsoft v2.0 issuer for one tenant and names the token's own tenant (``tid``)."""
    match = _MICROSOFT_TENANT_ISSUER.match(str(issuer or ""))
    if not match:
        return False
    tid = str(claims.get("tid") or "")
    return bool(tid) and tid.lower() == match["tid"].lower()


def _claims_options_for(metadata: Mapping | None, claims_options: dict | None) -> dict | None:
    """Claims options that replace the exact issuer check when the discovered issuer is a template."""
    if claims_options is not None:
        return claims_options
    if _TEMPLATE_ISSUER_MARK not in str((metadata or {}).get("issuer") or ""):
        return None
    return {"iss": {"essential": True, "validate": is_microsoft_tenant_issuer}}


def allow_microsoft_multitenant_issuer() -> bool:
    """Let Authlib accept ID tokens from Microsoft's multi-tenant endpoint. Safe to call more than once.

    Patches Authlib's sync and async ``parse_id_token`` (Streamlit's Tornado and
    Starlette servers use one or the other). Returns False when Authlib isn't
    installed (sign-in isn't available then anyway).
    """
    try:
        from authlib.integrations.base_client import async_openid, sync_openid
    except ImportError:
        return False

    sync_cls = sync_openid.OpenIDMixin
    if not getattr(sync_cls.parse_id_token, "_humeta_patched", False):
        original_sync = sync_cls.parse_id_token

        @functools.wraps(original_sync)
        def parse_id_token(self, token, nonce, claims_options=None, *args, **kwargs):
            if claims_options is None and "id_token" in (token or {}):
                claims_options = _claims_options_for(self.load_server_metadata(), None)
            return original_sync(self, token, nonce, claims_options, *args, **kwargs)

        parse_id_token._humeta_patched = True
        sync_cls.parse_id_token = parse_id_token

    async_cls = async_openid.AsyncOpenIDMixin
    if not getattr(async_cls.parse_id_token, "_humeta_patched", False):
        original_async = async_cls.parse_id_token

        @functools.wraps(original_async)
        async def parse_id_token_async(self, token, nonce, claims_options=None, *args, **kwargs):
            if claims_options is None and "id_token" in (token or {}):
                claims_options = _claims_options_for(await self.load_server_metadata(), None)
            return await original_async(self, token, nonce, claims_options, *args, **kwargs)

        parse_id_token_async._humeta_patched = True
        async_cls.parse_id_token = parse_id_token_async
    return True
