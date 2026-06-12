"""Shared-token access gate.

Same model as the seller-trial dashboard: the app is deployed publicly, but data
is shown only to visitors carrying a valid `?token=...` in the URL. The token is a
single shared secret (this app has one internal audience, so there's no per-user
mapping like the seller dashboard's `[seller_tokens]`).

Set the token in Streamlit secrets:

    [access]
    token = "<random-string>"

Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(16))"
"""

import streamlit as st


def _expected_token() -> str | None:
    try:
        return str(st.secrets["access"]["token"])
    except (KeyError, FileNotFoundError):
        return None


def require_token_or_stop() -> None:
    """Stop rendering unless the URL carries the valid shared token.

    Streamlit's nav can drop query params on rerun, so a validated token is
    persisted in session_state and reflected back into the URL.
    """
    expected = _expected_token()
    if not expected:
        st.error(
            "Access is not configured. Set `[access].token` in the app secrets."
        )
        st.stop()

    token = st.query_params.get("token") or st.session_state.get("token")

    if token is None:
        st.title("WYZauto Product Referential")
        st.info(
            "This tool is internal. Please open it with the private link "
            "(it ends with `?token=...`). Contact the data team if you need one."
        )
        st.stop()

    if str(token) != expected:
        st.title("WYZauto Product Referential")
        st.error("This access link is not valid. Please check the link you received.")
        st.stop()

    # Valid — persist across reruns and keep it in the URL.
    st.session_state["token"] = str(token)
    if st.query_params.get("token") != str(token):
        st.query_params["token"] = str(token)
