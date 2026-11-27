from oem import auth

GOOGLE = {"client_id": "g", "client_secret": "s", "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"}
ORCID = {"client_id": "APP-1", "client_secret": "s", "server_metadata_url": "https://orcid.org/.well-known/openid-configuration",
         "client_kwargs": {"scope": "openid"}}


def test_named_providers_in_button_order():
    section = {"redirect_uri": "x", "cookie_secret": "y", "orcid": ORCID, "google": GOOGLE}
    assert [(p.key, p.label) for p in auth.configured_providers(section)] == [("google", "Google"), ("orcid", "ORCID")]


def test_incomplete_or_missing_provider_is_not_offered():
    assert auth.configured_providers({"orcid": {"client_id": "APP-1"}, "google": GOOGLE}) == [auth.Provider("google", "Google")]
    assert auth.configured_providers(None) == []
    assert auth.configured_providers({"redirect_uri": "x", "cookie_secret": "y"}) == []


def test_original_single_google_setup_still_works():
    section = {"redirect_uri": "x", "cookie_secret": "y", **GOOGLE}
    assert auth.configured_providers(section) == [auth.Provider(None, "Google")]


def test_provider_labels():
    assert auth.provider_label("orcid") == "ORCID"
    assert auth.provider_label("default") == "Google" and auth.provider_label(None) == "Google"


def test_display_name_falls_back_to_given_and_family_names():
    assert auth.display_name({"name": " Ana Ruiz "}) == "Ana Ruiz"
    assert auth.display_name({"given_name": "Ana", "family_name": "Ruiz", "sub": "0000-0002-1825-0097"}) == "Ana Ruiz"
    assert auth.display_name({"given_name": "Ana"}) == "Ana"
    assert auth.display_name({}) == ""
