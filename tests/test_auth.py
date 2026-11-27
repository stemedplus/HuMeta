import asyncio
import sys
import types

import pytest

from oem import auth

GOOGLE = {"client_id": "g", "client_secret": "s", "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"}
ORCID = {"client_id": "APP-1", "client_secret": "s", "server_metadata_url": "https://orcid.org/.well-known/openid-configuration",
         "client_kwargs": {"scope": "openid"}}
MICROSOFT = {"client_id": "m", "client_secret": "s",
             "server_metadata_url": "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"}
TENANT = "72f988bf-86f1-41af-91ab-2d7cd011db47"
COMMON_METADATA = {"issuer": "https://login.microsoftonline.com/{tenantid}/v2.0"}


def test_named_providers_in_button_order():
    section = {"redirect_uri": "x", "cookie_secret": "y", "microsoft": MICROSOFT, "google": GOOGLE, "orcid": ORCID}
    assert [(p.key, p.label) for p in auth.configured_providers(section)] == [
        ("google", "Google"), ("orcid", "ORCID"), ("microsoft", "Microsoft")]


def test_incomplete_or_missing_provider_is_not_offered():
    assert auth.configured_providers({"orcid": {"client_id": "APP-1"}, "google": GOOGLE}) == [auth.Provider("google", "Google")]
    assert auth.configured_providers(None) == []
    assert auth.configured_providers({"redirect_uri": "x", "cookie_secret": "y"}) == []


def test_original_single_google_setup_still_works():
    section = {"redirect_uri": "x", "cookie_secret": "y", **GOOGLE}
    assert auth.configured_providers(section) == [auth.Provider(None, "Google")]


def test_provider_labels():
    assert auth.provider_label("orcid") == "ORCID"
    assert auth.provider_label("microsoft") == "Microsoft"
    assert auth.provider_label("default") == "Google" and auth.provider_label(None) == "Google"


def test_display_name_falls_back_to_given_and_family_names():
    assert auth.display_name({"name": " Ana Ruiz "}) == "Ana Ruiz"
    assert auth.display_name({"given_name": "Ana", "family_name": "Ruiz", "sub": "0000-0002-1825-0097"}) == "Ana Ruiz"
    assert auth.display_name({"given_name": "Ana"}) == "Ana"
    assert auth.display_name({}) == ""


@pytest.mark.parametrize("issuer,tid,ok", [
    (f"https://login.microsoftonline.com/{TENANT}/v2.0", TENANT, True),
    (f"https://login.microsoftonline.com/{TENANT.upper()}/v2.0", TENANT, True),
    (f"https://login.microsoftonline.com/{TENANT}/v2.0", "00000000-0000-0000-0000-000000000000", False),
    (f"https://login.microsoftonline.com/{TENANT}/v2.0", None, False),
    ("https://login.microsoftonline.com/{tenantid}/v2.0", TENANT, False),
    (f"https://evil.example.com/{TENANT}/v2.0", TENANT, False),
    (f"https://login.microsoftonline.com/{TENANT}/v2.0/extra", TENANT, False),
    (f"https://sts.windows.net/{TENANT}/", TENANT, False),
])
def test_microsoft_tenant_issuer(issuer, tid, ok):
    assert auth.is_microsoft_tenant_issuer({"tid": tid}, issuer) is ok


def test_issuer_check_is_replaced_only_for_the_template_issuer():
    options = auth._claims_options_for(COMMON_METADATA, None)
    assert options["iss"]["validate"] is auth.is_microsoft_tenant_issuer and options["iss"]["essential"]
    assert auth._claims_options_for({"issuer": "https://accounts.google.com"}, None) is None
    assert auth._claims_options_for({"issuer": "https://orcid.org"}, None) is None
    given = {"iss": {"values": ["x"]}}
    assert auth._claims_options_for(COMMON_METADATA, given) is given


@pytest.fixture
def fake_authlib(monkeypatch):
    """Stand-ins for Authlib's OpenID mixins that record the claims options they get."""
    seen = []

    class OpenIDMixin:
        metadata = COMMON_METADATA

        def load_server_metadata(self):
            return self.metadata

        def parse_id_token(self, token, nonce, claims_options=None, claims_cls=None, leeway=120):
            seen.append(claims_options)
            return "sync"

    class AsyncOpenIDMixin:
        metadata = COMMON_METADATA

        async def load_server_metadata(self):
            return self.metadata

        async def parse_id_token(self, token, nonce, claims_options=None, claims_cls=None, leeway=120):
            seen.append(claims_options)
            return "async"

    sync_mod = types.ModuleType("authlib.integrations.base_client.sync_openid")
    sync_mod.OpenIDMixin = OpenIDMixin
    async_mod = types.ModuleType("authlib.integrations.base_client.async_openid")
    async_mod.AsyncOpenIDMixin = AsyncOpenIDMixin
    base = types.ModuleType("authlib.integrations.base_client")
    base.sync_openid, base.async_openid = sync_mod, async_mod
    for name, mod in {"authlib": types.ModuleType("authlib"), "authlib.integrations": types.ModuleType("authlib.integrations"),
                      "authlib.integrations.base_client": base,
                      "authlib.integrations.base_client.sync_openid": sync_mod,
                      "authlib.integrations.base_client.async_openid": async_mod}.items():
        monkeypatch.setitem(sys.modules, name, mod)
    return OpenIDMixin, AsyncOpenIDMixin, seen


def test_patch_sets_tenant_issuer_check_for_microsoft_common(fake_authlib):
    OpenIDMixin, AsyncOpenIDMixin, seen = fake_authlib
    assert auth.allow_microsoft_multitenant_issuer() is True
    assert auth.allow_microsoft_multitenant_issuer() is True  # a second call doesn't wrap twice
    token = {"id_token": "x", "access_token": "y"}
    assert OpenIDMixin().parse_id_token(token, nonce="n") == "sync"
    assert asyncio.run(AsyncOpenIDMixin().parse_id_token(token, nonce="n")) == "async"
    assert [o["iss"]["validate"] for o in seen] == [auth.is_microsoft_tenant_issuer] * 2


def test_patch_leaves_other_providers_and_explicit_options_alone(fake_authlib):
    OpenIDMixin, _, seen = fake_authlib
    auth.allow_microsoft_multitenant_issuer()
    google = OpenIDMixin()
    google.metadata = {"issuer": "https://accounts.google.com"}
    google.parse_id_token({"id_token": "x"}, "n")
    OpenIDMixin().parse_id_token({"id_token": "x"}, "n", {"iss": {"values": ["mine"]}})
    assert seen == [None, {"iss": {"values": ["mine"]}}]


def test_patch_without_authlib_is_a_no_op(monkeypatch):
    monkeypatch.setitem(sys.modules, "authlib", None)
    assert auth.allow_microsoft_multitenant_issuer() is False
