"""WYZauto Product Referential — self-service download.

Lets internal colleagues download the V2 spare-parts product referential as CSV:
either the full catalog (all products, every attribute as a column) or a single
category (dense — only that category's attribute columns).

The SQL is built by the same source-of-truth generator that produces the static
`.sql` files in this folder, so downloads never drift from those exports.
"""

from datetime import date

import streamlit as st

st.set_page_config(
    page_title="WYZauto Product Referential",
    page_icon="🧩",
    layout="wide",
)

# Same directory as this app on Streamlit Cloud → imports resolve directly.
from generate_category_queries import (  # noqa: E402
    CATEGORY_CODES,
    CATEGORY_PARENTS,
    build_query,
    build_unified_query,
)
from src.auth import require_token_or_stop  # noqa: E402
from src.bq_client import run_query  # noqa: E402

require_token_or_stop()

FULL_LABEL = "Full referential (all products)"

# parent category -> sorted list of its leaf categories
LEAVES_BY_PARENT: dict[str, list[str]] = {}
for _leaf, _parent in CATEGORY_PARENTS.items():
    LEAVES_BY_PARENT.setdefault(_parent, []).append(_leaf)
for _parent in LEAVES_BY_PARENT:
    LEAVES_BY_PARENT[_parent].sort()

st.title("WYZauto Product Referential")
st.caption(
    "Download the V2 spare-parts catalogue as CSV — the full referential, or drill "
    "into a parent category and pick a specific category (exported with only its "
    "relevant attribute columns). Data is queried live from BigQuery each time you "
    "generate."
)

group = st.selectbox(
    "Category group",
    options=[FULL_LABEL] + sorted(LEAVES_BY_PARENT.keys()),
    index=0,
    help="Pick the full catalogue, or a parent category to narrow down.",
)

is_full = group == FULL_LABEL
if is_full:
    choice = None
    slug = "all_products"
else:
    choice = st.selectbox(
        "Category",
        options=LEAVES_BY_PARENT[group],
        index=0,
        help="The specific category to export (dense — only its attribute columns).",
    )
    slug = choice

if st.button("1 · Build export", type="primary"):
    sql = build_unified_query() if is_full else build_query(choice, CATEGORY_CODES[choice])
    with st.spinner("Querying BigQuery…"):
        df = run_query(sql)
    st.session_state["export"] = {
        "slug": slug,
        "csv": df.to_csv(index=False).encode("utf-8"),
        "rows": len(df),
        "cols": len(df.columns),
        "preview": df.head(50),
    }

export = st.session_state.get("export")
if export and export["slug"] == slug:
    st.success("Export ready — click **2 · Download CSV** below.")
    c1, c2 = st.columns(2)
    c1.metric("Products", f"{export['rows']:,}")
    c2.metric("Columns", export["cols"])

    st.download_button(
        "⬇️ 2 · Download CSV",
        data=export["csv"],
        file_name=f"product_referential_{slug}_{date.today().isoformat()}.csv",
        mime="text/csv",
        type="primary",
    )

    st.caption("Preview — first 50 rows")
    st.dataframe(export["preview"], use_container_width=True)
elif export:
    st.info("Selection changed — click **1 · Build export** to refresh the download.")
