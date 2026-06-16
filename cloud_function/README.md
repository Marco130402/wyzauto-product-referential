# productreferentialexport — Cloud Function

HTTP Cloud Function (gen2, Python 3.11) that powers the admin hub's **Product
Referential** page. Given a `category` query param it runs the matching export
query against BigQuery and streams back a UTF-8 CSV.

- **Project / region:** `wyzauto-v2-prod` / `asia-southeast1`
- **Entry point:** `product_referential_export`
- **Auth:** Firebase ID token — `Authorization: Bearer <token>`
- **Caller:** `client/src/pages/ProductReferential.tsx` in `wyzauto-admin-hub`,
  via `VITE_PRODUCT_REFERENTIAL_FUNCTION_URL`.

## Source of truth

The SQL builders and `CATEGORY_CODES` map here **mirror
`../generate_category_queries.py`** (the generator that also produces the static
`.sql` exports and feeds the Streamlit dashboard). Keep the two in sync — when
the generator changes, port the change here and redeploy.

## `category` values

| Value | Export |
|---|---|
| `all_products` (default) | Unified export — every attribute code as a column |
| `<leaf category code>`   | Dense export — only that category's attribute columns |

## Deploy

```bash
gcloud functions deploy productreferentialexport \
  --gen2 --runtime python311 --region asia-southeast1 \
  --project wyzauto-v2-prod \
  --entry-point product_referential_export \
  --trigger-http --timeout 540s --memory 1Gi \
  --source .
```

`function.json` records the deployed config (entry point, trigger, timeout,
memory, and the Secret Manager bindings for `FIREBASE_PROJECT_ID` / `BQ_PROJECT`).
