from fitbit_training_toolkit_sdk.auth.pkce import (
    DEFAULT_SCOPES,
    generate_pkce_pair,
    get_authorization_url,
)


def test_pkce_pair_generation():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert verifier != challenge


def test_authorization_url_generation_official_params():
    _, challenge = generate_pkce_pair()
    url = get_authorization_url(
        client_id="test_client_id",
        code_challenge=challenge,
        expires_in=604800,
        prompt="consent",
    )
    assert "https://www.fitbit.com/oauth2/authorize" in url
    assert "client_id=test_client_id" in url
    assert f"code_challenge={challenge}" in url
    assert "code_challenge_method=S256" in url
    assert "expires_in=604800" in url
    assert "prompt=consent" in url
    assert "activity" in url
    assert "cardio_fitness" in url
    assert "sleep" in url
    assert len(DEFAULT_SCOPES) == 13
