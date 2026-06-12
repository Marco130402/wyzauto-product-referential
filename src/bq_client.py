"""BigQuery client + live query runner.

Mirrors the seller-trial dashboard's `src/bq_client.py`, but the product
referential lives in `wyzauto-v2-prod.base_tables.*` — the same project that
bills — so data and billing project are identical here.

Service-account auth via `st.secrets["gcp_service_account"]`, with ADC fallback
for local dev. Unlike the dashboards, `run_query` is deliberately **uncached** so
every export reflects live BigQuery data (the app only runs it on an explicit
"Generate" click, so this stays cheap).
"""

import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# The flattened referential is sourced from base_tables in wyzauto-v2-prod.
DATA_PROJECT = "wyzauto-v2-prod"
BILLING_PROJECT = "wyzauto-v2-prod"


@st.cache_resource
def get_client() -> bigquery.Client:
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(credentials=creds, project=BILLING_PROJECT)
    return bigquery.Client(project=BILLING_PROJECT)


def run_query(sql: str):
    """Execute SQL and return a DataFrame. Uncached — always live."""
    client = get_client()
    return client.query(sql).to_dataframe()
