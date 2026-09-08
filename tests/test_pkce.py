from fitbit_training_toolkit_sdk.auth.pkce import (
    generate_pkce_pair,
    get_authorization_url,
)


def test_pkce_pair_generation():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert verifier != challenge


def test_authorization_url_generation():
    _, challenge = generate_pkce_pair()
    url = get_authorization_url(client_id="test_client_id", code_challenge=challenge)
    assert "https://www.fitbit.com/oauth2/authorize" in url
    assert "client_id=test_client_id" in url
    assert f"code_challenge={challenge}" in url
    assert "code_challenge_method=S256" in url
