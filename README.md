# Product referential exports (V2 — `wyzauto-v2-prod`)

Flattened, one-row-per-product exports of the V2 spare-parts product catalogue. Each
product's variable attributes (normally stored as long rows in `product_specification`)
are **pivoted into columns**, alongside base product fields, the category parent, and
recommended prices per country.

## Contents

| File | What it is |
|---|---|
| `generate_category_queries.py` | Generator. Holds the source-of-truth maps and emits all `.sql` below. Run it to regenerate. |
| `<category>.sql` × 42 | One query per **leaf** category (e.g. `4_wheelers.sql`, `brake_pad.sql`, `spark_plug.sql`). Dense — only that category's attribute columns. |
| `all_products.sql` | Single unified query: all categories, one row per product, every attribute code as a column (sparse). |

Regenerate everything:

```bash
cd "Data rationalization/product_exports"
python3 generate_category_queries.py
```

## Output shape

Every query returns **one row per product** (verified: 51,439 rows = 51,439 distinct
`product.id`, no fan-out). Columns:

| Column | Source | Notes |
|---|---|---|
| `product_id` | `product.id` | |
| `brand` | `product.brand` | |
| `product_name` | `product.product_name` | |
| `parent_category` | `category` tree | Immediate parent of the leaf category (see below). |
| `category` | `product.category` | The leaf category code. |
| `last_synced_at` | `product.last_synced_at` | |
| `sku_manufacturer` | `product.sku_manufacturer` | |
| `oem_number` | `product.oem_number` | REPEATED array flattened with `ARRAY_TO_STRING(.., ' \| ')`. |
| `amount_th_recommended_price` | `product_price` | Pivoted from `(country_code, price_type)`. |
| `amount_my_recommended_price` | `product_price` | NULL for TH-only products. |
| *attribute columns* | `product_specification.value` | One column per `attribute.code` relevant to the category. STRING-typed (e.g. `"40.0000"`), since `value` is STRING. |

`all_products.sql` is the same with the **union of all 74 attribute codes** as columns
(84 columns total: 8 base + 2 price + 74 attribute); attribute columns are NULL where the
code doesn't apply to that product's category.

## Source tables & joins

- `base_tables.product` — base catalogue (one row per product).
- `base_tables.product_specification` — long attribute rows: `(product_id, attribute_id, value)`.
- `base_tables.attribute` — attribute definitions; `code` is the human name, `metric_unit` the unit.
  **Singular `attribute`** is canonical — the plural `attributes` table was removed.
- `base_tables.product_price` — `(product_id, country_code, price_type, amount)`.
- `base_tables.category` — self-referencing tree via `parent_id`.

### Pivot pattern

```sql
MAX(IF(a.code = 'X', ps.value, NULL)) AS X   -- attribute column
MAX(IF(country_code='th' AND price_type='recommended_price', amount, NULL)) AS amount_th_recommended_price
```

Specs and prices are each pre-aggregated to one row per product in their own CTE, then
`LEFT JOIN`ed — this keeps the grain at one row per product and avoids a
spec × price cartesian product.

## Key facts / gotchas

1. **Attribute table is `attribute` (singular).** The plural `attributes` no longer exists.
   Link: `product_specification.attribute_id → attribute.id`.
2. **`product.category_id` is NULL for ~494 products**, but `product.category` (the string)
   is always populated. So the category hierarchy is resolved by joining the `category`
   tree on **`code`, not `id`**, keyed off `product.category`.
3. **Category hierarchy is 3 levels.** 7 level-1 roots (`battery`, `braking`, `filtration`,
   `lubricants`, `others`, `steering`, `tyres`) hold no products directly; products attach at
   the **leaf** (level 2 or 3). `parent_category` is the leaf's immediate parent —
   e.g. `brake_pad → braking` (L2→L1), `spark_plug → engine_system` (L3→L2).
4. **42 leaf categories have products.** 38 have attribute specs (full pivot); 4 have none
   (`tyre_repair_prod_tools`, `wheel_alignment`, `tyre_changer`, `wheel_balancer`) — their
   files carry base + parent + price columns only.
5. **Attribute values are STRINGs** (the source column type) — cast in BI/SQL as needed.

## Refreshing the maps

The generator embeds two maps pulled from BigQuery on 2026-06-11. Re-run these and update
the dicts if the catalogue changes:

```sql
-- CATEGORY_CODES : category -> attribute codes
SELECT p.category, STRING_AGG(DISTINCT a.code, ', ' ORDER BY a.code) AS attribute_codes
FROM `wyzauto-v2-prod.base_tables.product` p
JOIN `wyzauto-v2-prod.base_tables.product_specification` ps ON ps.product_id = p.id
JOIN `wyzauto-v2-prod.base_tables.attribute` a ON a.id = ps.attribute_id
GROUP BY p.category;

-- PRICE_COMBOS : (country_code, price_type) pairs -> amount_<cc>_<pt> columns
SELECT DISTINCT country_code, price_type FROM `wyzauto-v2-prod.base_tables.product_price`;
```

Categories with products but **no** specs won't appear in the first query — add them to
`CATEGORY_CODES` with an empty list `[]` (as the 4 above are) so they still get a file.

## Download dashboard (Streamlit)

`streamlit_app.py` is a small self-service web app for colleagues. Pick **Full
referential**, or drill **parent group → category** (cascading selectors), then a
two-step **1 · Build export** (runs the live query) → **2 · Download CSV**. It imports
the source-of-truth maps and builders (`build_unified_query`, `build_query`,
`CATEGORY_CODES`, `CATEGORY_PARENTS`) from `generate_category_queries.py`, so downloads
and the parent grouping never drift from the `.sql` files. Data is queried **live** from
`wyzauto-v2-prod` on each build (no caching). The download is two-step because
`st.download_button` needs the bytes ready at render time — building once then
downloading avoids re-querying on every interaction.

Files: `streamlit_app.py`, `src/bq_client.py` (BQ client, project = `wyzauto-v2-prod`),
`src/auth.py` (shared-token gate), `requirements.txt`, `.streamlit/`.

### Run locally

```bash
cd "Data rationalization/product_exports"
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # paste SA JSON + set a token
.venv/bin/streamlit run streamlit_app.py
# open http://localhost:8501/?token=<your-token>
```

### Access model

Deployed as a **public** Streamlit Community Cloud app, but data shows only with a valid
`?token=` (same pattern as the seller-trial dashboard). Set the token under `[access]` in
secrets; generate one with `python -c "import secrets; print(secrets.token_urlsafe(16))"`.
Share `https://<app>.streamlit.app/?token=<token>` with colleagues.

### Deploy

Push to the GitHub repo Streamlit Cloud reads → share.streamlit.io → New app → main file
path `Data rationalization/product_exports/streamlit_app.py` → paste secrets
(`[gcp_service_account]` block + `[access] token`) → Deploy. Reuses the read-only SA
`claude-bq-reader@wyzauto-v2-prod` (needs `bigquery.jobs.create` + `dataViewer` on
`base_tables`).
