"""Access logging — append each successful login to a Google Sheet.

Reuses the BigQuery service account (st.secrets["gcp_service_account"]) with the
Sheets scope. The target sheet must be **shared with the service account email as
an Editor**, and the Google Sheets API must be enabled on its project. The sheet
id goes in secrets under [notify].sheet_id.

Logging is best-effort: any failure is swallowed so a misconfigured sheet never
blocks a colleague from signing in.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

_BKK = ZoneInfo("Asia/Bangkok")
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _sheet_id() -> str | None:
    notify = st.secrets.get("notify", {})
    sid = notify.get("sheet_id") if hasattr(notify, "get") else None
    return str(sid) if sid else None


def log_access(email: str) -> None:
    """Append (timestamp, email) to the access-log sheet. Never raises."""
    sheet_id = _sheet_id()
    if not sheet_id or "gcp_service_account" not in st.secrets:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=_SCOPES
        )
        ws = gspread.authorize(creds).open_by_key(sheet_id).sheet1
        ts = datetime.now(_BKK).isoformat(timespec="seconds")
        ws.append_row([ts, email], value_input_option="USER_ENTERED")
    except Exception as exc:  # noqa: BLE001 — logging must never block login
        print(f"[notify] access-log failed: {exc}")
