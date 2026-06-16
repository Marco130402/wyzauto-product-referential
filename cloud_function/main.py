"""Product Referential export — streams the V2 spare-parts catalogue as CSV.

HTTP-triggered Cloud Function (deployed to wyzauto-v2-prod as
`productreferentialexport`) called by the admin hub's Product Referential page.
Accepts a `category` query param (leaf category code or "all_products") and
returns a UTF-8 CSV over HTTP.

Auth: Firebase ID token in the Authorization header (Bearer <token>).
BigQuery: uses Application Default Credentials — the function's service account
must have bigquery.jobs.create + bigquery.dataViewer on
wyzauto-v2-prod.base_tables.

SQL builders mirror generate_category_queries.py (the source-of-truth generator
in the repo root) so downloads never drift from the static .sql exports.
"""

import csv
import io
import json
import os

import firebase_admin
import flask
import functions_framework
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from google.cloud import bigquery

# --- CONFIGURATION ---
PROJECT = os.environ.get("BQ_PROJECT", "wyzauto-v2-prod")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "wyzauto-common")

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
}

# --- FIREBASE (lazy singleton) ---
def _ensure_firebase():
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})


# --- CATEGORY DATA (ported from generate_category_queries.py) ---
CATEGORY_CODES = {
    "4_wheelers": ["OE_marking", "aspect_ratio", "brand_special", "fitting_front_rear", "load_dual", "load_format", "load_index", "match_code", "pattern", "runflat", "season", "seat", "speed_index", "tech_marking", "tube_type", "tyre_structure", "tyre_type", "width_tyre"],
    "brake_pad": ["Thickness_2", "Width_2", "fitting_front_rear", "fitting_left_right", "height", "height_2", "possible_carmatch", "product_series", "productdetail", "remark", "thickness", "width"],
    "others_others": ["fitting_center_inner_outer", "fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "product_series", "productdetail", "remark"],
    "shock_absorber": ["fitting_front_rear", "fitting_left_right", "mounting_lwr_type", "mounting_upr_type", "possible_carmatch", "product_series", "remark", "shock_type", "stroke"],
    "brake_discs": ["brake_disc_type", "diameter_centering", "diameter_outer", "fitting_front_rear", "fitting_left_right", "height", "holes_nbr", "possible_carmatch", "product_series", "remark", "thickness", "thickness_min"],
    "2_wheelers": ["aspect_ratio", "fitting_front_rear", "load_dual", "load_index", "match_code", "pattern", "seat", "sidewall_logo", "speed_index", "tech_marking", "tube_type", "tyre_structure", "tyre_type", "vehicle_type_tyre", "width_tyre"],
    "filter_air": ["possible_carmatch", "remark"],
    "filter_oil": ["possible_carmatch", "remark"],
    "tie_rod_end": ["fitting_center_inner_outer", "fitting_front_rear", "fitting_left_right", "possible_carmatch"],
    "control_trailing_arm": ["fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "remark"],
    "battery_l2": ["battery_model", "battery_type", "capacity", "cca", "din_jis", "height", "length", "product_series", "remark", "side", "width"],
    "stabilizer_link": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "remark"],
    "wiper_blade": ["Wiperblade_length_2", "fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "productdetail", "remark", "wiper_blade_type", "wiperbade_length_1"],
    "shockabsorber_protectionkit": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "remark", "shock_type"],
    "filter_cabin_air": ["height", "length", "possible_carmatch", "product_model_cabinairfilter", "product_series", "remark", "width"],
    "brake_shoe": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "remark"],
    "engine_oil": ["engine_type", "oil_change_frequency", "oil_grade", "product_series", "productdetail", "remark", "viscosity_code", "volume_capacity"],
    "inner_tie_rod": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "remark"],
    "filter_transmission": ["possible_carmatch", "remark"],
    "ball_joint": ["fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "remark"],
    "filter_fuel": ["engine_type2", "possible_carmatch"],
    "lubricants_others": ["engine_type", "oil_change_frequency", "product_series", "productdetail", "viscosity_code", "volume_capacity"],
    "ignition_coil": ["possible_carmatch", "productdetail", "remark"],
    "spark_plug": ["Hexagon_Size", "Thread_diameter", "Thread_length", "possible_carmatch", "product_series", "productdetail", "remark"],
    "shock_absorber_spring": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "productdetail"],
    "transmission_oil": ["gear_type", "oil_change_frequency", "product_series", "productdetail", "remark", "transmission_oil_grade", "viscosity_code", "volume_capacity"],
    "brake_drums": ["diameter_centering", "diameter_outer", "fitting_front_rear", "fitting_left_right", "height", "holes_nbr", "possible_carmatch", "product_series", "remark", "thickness", "thickness_min"],
    "shock_spring_fullset": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series"],
    "coolants": ["Type_of_coolant", "boiling_point", "colour", "coolant_spec", "engine_type", "freezing_point", "oil_grade", "possible_carmatch", "product_series", "productdetail", "remark", "viscosity_code", "volume_capacity"],
    "grease": ["colour", "product_series", "product_spec_nlgi", "productdetail", "volume_capacity"],
    "tools_others": ["product_series", "productdetail", "remark"],
    "equipment_others": ["product_series", "productdetail", "remark"],
    "brake_fluid": ["grade_brakefluid", "productdetail", "remark", "volume_capacity"],
    "tools_diagnostics": ["productdetail", "remark"],
    "battery_package": ["productdetail", "remark"],
    "flushing_oil": ["engine_type", "productdetail", "volume_capacity"],
    "brake_kit": ["diameter_centering", "diameter_outer", "fitting_front_rear", "fitting_left_right", "height", "holes_nbr", "thickness", "thickness_min"],
    "battery_testing": ["productdetail", "remark"],
    # Categories with products but NO attribute specs -> base + parent + price columns only.
    "tyre_repair_prod_tools": [],
    "wheel_alignment": [],
    "tyre_changer": [],
    "wheel_balancer": [],
}

PRICE_COMBOS = [("th", "recommended_price"), ("my", "recommended_price")]

_CAT_CTE = f"""cat AS (
  SELECT c.code AS leaf_code, parent.code AS parent_category
  FROM `{PROJECT}.base_tables.category` c
  LEFT JOIN `{PROJECT}.base_tables.category` parent ON parent.id = c.parent_id
)"""


def _q(code):
    """Backtick-quote a column alias."""
    return f"`{code}`"


# --- SQL BUILDERS ---
def _build_query(category, codes):
    price_lines = ",\n".join(
        f"    MAX(IF(country_code = '{cc}' AND price_type = '{pt}', amount, NULL)) AS amount_{cc}_{pt}"
        for cc, pt in PRICE_COMBOS
    )
    price_select = ",\n".join(f"  pr.amount_{cc}_{pt}" for cc, pt in PRICE_COMBOS)

    if codes:
        pivot_lines = ",\n".join(
            f"    MAX(IF(a.code = '{c}', ps.value, NULL)) AS {_q(c)}" for c in codes
        )
        specs_cte = f""",
specs AS (
  SELECT
    ps.product_id,
{pivot_lines}
  FROM `{PROJECT}.base_tables.product_specification` ps
  JOIN `{PROJECT}.base_tables.attribute` a ON a.id = ps.attribute_id
  GROUP BY ps.product_id
)"""
        specs_join = "\nLEFT JOIN specs s ON s.product_id = p.id"
        specs_select = ",\n  s.* EXCEPT (product_id)"
    else:
        specs_cte = specs_join = specs_select = ""

    return f"""WITH {_CAT_CTE},
prices AS (
  SELECT product_id,
{price_lines}
  FROM `{PROJECT}.base_tables.product_price`
  GROUP BY product_id
){specs_cte}
SELECT
  p.id AS product_id,
  p.brand,
  p.product_name,
  cat.parent_category,
  p.category,
  p.last_synced_at,
  p.sku_manufacturer,
{price_select}{specs_select}
FROM `{PROJECT}.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id{specs_join}
WHERE p.category = '{category}'
ORDER BY p.brand, p.product_name;
"""


def _build_unified_query():
    all_codes = sorted({c for codes in CATEGORY_CODES.values() for c in codes})
    pivot_lines = ",\n".join(
        f"    MAX(IF(a.code = '{c}', ps.value, NULL)) AS {_q(c)}" for c in all_codes
    )
    price_lines = ",\n".join(
        f"    MAX(IF(country_code = '{cc}' AND price_type = '{pt}', amount, NULL)) AS amount_{cc}_{pt}"
        for cc, pt in PRICE_COMBOS
    )
    price_select = ",\n".join(f"  pr.amount_{cc}_{pt}" for cc, pt in PRICE_COMBOS)
    return f"""WITH {_CAT_CTE},
prices AS (
  SELECT product_id,
{price_lines}
  FROM `{PROJECT}.base_tables.product_price`
  GROUP BY product_id
),
specs AS (
  SELECT
    ps.product_id,
{pivot_lines}
  FROM `{PROJECT}.base_tables.product_specification` ps
  JOIN `{PROJECT}.base_tables.attribute` a ON a.id = ps.attribute_id
  GROUP BY ps.product_id
)
SELECT
  p.id AS product_id,
  p.brand,
  p.product_name,
  cat.parent_category,
  p.category,
  p.last_synced_at,
  p.sku_manufacturer,
{price_select},
  s.* EXCEPT (product_id)
FROM `{PROJECT}.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id
LEFT JOIN specs s ON s.product_id = p.id
ORDER BY cat.parent_category, p.category, p.brand, p.product_name;
"""


# --- ENTRY POINT ---
@functions_framework.http
def product_referential_export(request):
    # CORS preflight
    if request.method == "OPTIONS":
        return ("", 204, _CORS)

    if request.method != "GET":
        return ("", 405, {**_CORS, "Allow": "GET, OPTIONS"})

    json_headers = {**_CORS, "Content-Type": "application/json"}

    # Auth — verify Firebase ID token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return (json.dumps({"error": "Unauthorized"}), 401, json_headers)
    try:
        _ensure_firebase()
        firebase_auth.verify_id_token(auth_header[7:])
    except Exception as exc:
        print(f"Token verification failed: {exc}")
        return (json.dumps({"error": "Invalid token"}), 401, json_headers)

    # Resolve SQL
    category = request.args.get("category", "all_products")
    if category != "all_products" and category not in CATEGORY_CODES:
        return (json.dumps({"error": f"Unknown category: {category}"}), 400, json_headers)

    # Run BigQuery query
    try:
        client = bigquery.Client(project=PROJECT)
        if category == "all_products":
            sql = _build_unified_query()
        else:
            sql = _build_query(category, CATEGORY_CODES[category])
        result = client.query(sql).result()
    except Exception as exc:
        print(f"BigQuery error: {exc}")
        return (json.dumps({"error": "Export failed. Please try again later."}), 500, json_headers)

    def _generate():
        buf = io.StringIO()
        writer = None

        for row in result:
            row_dict = dict(row.items())
            if writer is None:
                writer = csv.DictWriter(buf, fieldnames=list(row_dict.keys()))
                writer.writeheader()
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate(0)
            writer.writerow(row_dict)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

        if writer is None:
            # Empty result — yield headers only
            writer = csv.DictWriter(buf, fieldnames=[f.name for f in result.schema])
            writer.writeheader()
            yield buf.getvalue()

        print(f"✅ Exported category={category}")

    return flask.Response(
        _generate(),
        status=200,
        headers={
            **_CORS,
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f'attachment; filename="product_referential_{category}.csv"',
        },
    )
