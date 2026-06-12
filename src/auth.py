"""Email + shared-password access gate.

Colleagues sign in with their @wyzauto.com email and a single shared password
(set in secrets under [access].password). The email is a self-identified label —
the password is the actual gate — and each successful sign-in is logged to a
Google Sheet (see src/notify.py).
"""

import re

import streamlit as st

from src.notify import log_access

WYZ_DOMAIN = "@wyzauto.com"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _expected_password() -> str | None:
    try:
        return str(st.secrets["access"]["password"])
    except (KeyError, FileNotFoundError):
        return None


def require_login_or_stop() -> str:
    """Render the login form and stop until a valid email+password is given.

    Returns the authenticated @wyzauto.com email. Auth is held in session_state
    so the form only shows once per browser session.
    """
    if st.session_state.get("authed"):
        return st.session_state["email"]

    expected = _expected_password()
    if not expected:
        st.error("Access is not configured. Set `[access].password` in the app secrets.")
        st.stop()

    st.title("WYZauto Product Referential")
    st.caption("Internal tool — sign in with your WYZauto email to continue.")

    with st.form("login"):
        email = st.text_input("Work email", placeholder="you@wyzauto.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if not submitted:
        st.stop()

    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email) or not email.endswith(WYZ_DOMAIN):
        st.error("Please sign in with your **@wyzauto.com** email address.")
        st.stop()
    if password != expected:
        st.error("Incorrect password. Contact the data team if you need access.")
        st.stop()

    # Success — record it (best-effort) and enter the app.
    st.session_state["authed"] = True
    st.session_state["email"] = email
    log_access(email)
    st.rerun()
