#!/usr/bin/env python3
"""
Generate one flattened-export SQL query per V2 product category.

Each query pivots that category's attribute codes (attribute.code) into columns
(value from product_specification.value), one row per product x price row.

The CATEGORY_CODES map below was pulled from wyzauto-v2-prod on 2026-06-11 with:

    SELECT p.category,
           STRING_AGG(DISTINCT a.code, ', ' ORDER BY a.code) AS attribute_codes
    FROM `wyzauto-v2-prod.base_tables.product` p
    JOIN `wyzauto-v2-prod.base_tables.product_specification` ps ON ps.product_id = p.id
    JOIN `wyzauto-v2-prod.base_tables.attribute` a ON a.id = ps.attribute_id
    GROUP BY p.category;

Re-run that query and update the map if attribute codes change.
"""
import os

PROJECT = "wyzauto-v2-prod"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# (country_code, price_type) combos present in product_price, pulled 2026-06-11 with:
#   SELECT DISTINCT country_code, price_type FROM `wyzauto-v2-prod.base_tables.product_price`;
# Each (product_id, country_code, price_type) is unique, so MAX() is a safe pivot.
# Each combo becomes a column: amount_<country_code>_<price_type>.
PRICE_COMBOS = [
    ("th", "recommended_price"),
    ("my", "recommended_price"),
]

# category -> list of attribute codes present for that category
CATEGORY_CODES = {
    "4_wheelers": ["OE_marking", "aspect_ratio", "brand_special", "factory_price", "fitting_front_rear", "load_dual", "load_format", "load_index", "match_code", "pattern", "runflat", "season", "seat", "speed_index", "tech_marking", "tube_type", "tyre_structure", "tyre_type", "width_tyre"],
    "brake_pad": ["Thickness_2", "Width_2", "fitting_front_rear", "fitting_left_right", "height", "height_2", "possible_carmatch", "product_series", "productdetail", "remark", "thickness", "width"],
    "others_others": ["fitting_center_inner_outer", "fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "product_series", "productdetail", "remark"],
    "shock_absorber": ["fitting_front_rear", "fitting_left_right", "mounting_lwr_type", "mounting_upr_type", "possible_carmatch", "product_series", "remark", "shock_type", "stroke"],
    "brake_discs": ["brake_disc_type", "diameter_centering", "diameter_outer", "fitting_front_rear", "fitting_left_right", "height", "holes_nbr", "possible_carmatch", "product_series", "remark", "thickness", "thickness_min"],
    "2_wheelers": ["aspect_ratio", "fitting_front_rear", "load_dual", "load_index", "match_code", "pattern", "recommended_retail_price", "seat", "sidewall_logo", "speed_index", "tech_marking", "tube_type", "tyre_structure", "tyre_type", "vehicle_type_tyre", "width_tyre"],
    "filter_air": ["competitor_part_number", "possible_carmatch", "remark"],
    "filter_oil": ["competitor_part_number", "possible_carmatch", "remark"],
    "tie_rod_end": ["fitting_center_inner_outer", "fitting_front_rear", "fitting_left_right", "possible_carmatch"],
    "control_trailing_arm": ["fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "remark"],
    "battery_l2": ["battery_model", "battery_type", "capacity", "cca", "din_jis", "height", "length", "product_series", "remark", "side", "width"],
    "stabilizer_link": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "remark"],
    "wiper_blade": ["Wiperblade_length_2", "fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "productdetail", "remark", "wiper_blade_type", "wiperbade_length_1"],
    "shockabsorber_protectionkit": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "remark", "shock_type"],
    "filter_cabin_air": ["competitor_part_number", "height", "length", "possible_carmatch", "product_model_cabinairfilter", "product_series", "remark", "width"],
    "brake_shoe": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "product_series", "remark"],
    "engine_oil": ["engine_type", "oil_change_frequency", "oil_grade", "product_series", "productdetail", "remark", "viscosity_code", "volume_capacity"],
    "inner_tie_rod": ["fitting_front_rear", "fitting_left_right", "possible_carmatch", "remark"],
    "filter_transmission": ["competitor_part_number", "possible_carmatch", "remark"],
    "ball_joint": ["fitting_front_rear", "fitting_left_right", "fitting_upr_lwr", "possible_carmatch", "remark"],
    "filter_fuel": ["competitor_part_number", "engine_type2", "possible_carmatch"],
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

# leaf category -> its immediate parent category (the `parent_category` column).
# Pulled from wyzauto-v2-prod on 2026-06-12 with:
#   SELECT p.category AS leaf, ANY_VALUE(parent.code) AS parent
#   FROM `wyzauto-v2-prod.base_tables.product` p
#   LEFT JOIN `wyzauto-v2-prod.base_tables.category` c      ON c.code = p.category
#   LEFT JOIN `wyzauto-v2-prod.base_tables.category` parent ON parent.id = c.parent_id
#   GROUP BY p.category;
# Used by the download dashboard to build the parent -> leaf cascading selectors.
CATEGORY_PARENTS = {
    "battery_l2": "battery",
    "battery_package": "battery",
    "brake_discs": "braking",
    "brake_drums": "braking",
    "brake_kit": "braking",
    "brake_pad": "braking",
    "brake_shoe": "braking",
    "ignition_coil": "engine_system",
    "spark_plug": "engine_system",
    "battery_testing": "equipment_tools",
    "equipment_others": "equipment_tools",
    "tools_diagnostics": "equipment_tools",
    "tools_others": "equipment_tools",
    "tyre_changer": "equipment_tools",
    "tyre_repair_prod_tools": "equipment_tools",
    "wheel_alignment": "equipment_tools",
    "wheel_balancer": "equipment_tools",
    "filter_air": "filtration",
    "filter_cabin_air": "filtration",
    "filter_fuel": "filtration",
    "filter_oil": "filtration",
    "filter_transmission": "filtration",
    "brake_fluid": "lubricants",
    "coolants": "lubricants",
    "engine_oil": "lubricants",
    "flushing_oil": "lubricants",
    "grease": "lubricants",
    "lubricants_others": "lubricants",
    "transmission_oil": "lubricants",
    "others_others": "others",
    "ball_joint": "steering",
    "control_trailing_arm": "steering",
    "inner_tie_rod": "steering",
    "shock_absorber": "steering",
    "shock_absorber_spring": "steering",
    "shock_spring_fullset": "steering",
    "shockabsorber_protectionkit": "steering",
    "stabilizer_link": "steering",
    "tie_rod_end": "steering",
    "2_wheelers": "tyres",
    "4_wheelers": "tyres",
    "wiper_blade": "wiper_washer",
}


def quote_ident(code: str) -> str:
    """Backtick-quote a column alias (codes may contain mixed case / be reserved)."""
    return f"`{code}`"


# Maps each leaf category code to its immediate parent's code.
# Keyed by `code` (not id) because product.category_id is NULL for some rows,
# while product.category (the string) is always present.
CAT_CTE = f"""cat AS (
  SELECT c.code AS leaf_code, parent.code AS parent_category
  FROM `{PROJECT}.base_tables.category` c
  LEFT JOIN `{PROJECT}.base_tables.category` parent ON parent.id = c.parent_id
)"""


def build_query(category: str, codes: list[str]) -> str:
    price_lines = ",\n".join(
        f"    MAX(IF(country_code = '{cc}' AND price_type = '{pt}', amount, NULL)) "
        f"AS amount_{cc}_{pt}"
        for cc, pt in PRICE_COMBOS
    )
    price_select = ",\n".join(
        f"  pr.amount_{cc}_{pt}" for cc, pt in PRICE_COMBOS
    )

    # specs CTE only when the category actually has attribute codes
    if codes:
        pivot_lines = ",\n".join(
            f"    MAX(IF(a.code = '{c}', ps.value, NULL)) AS {quote_ident(c)}"
            for c in codes
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
        specs_cte = ""
        specs_join = ""
        specs_select = ""  # spec-less category: no attribute columns

    return f"""-- Flattened product export: category = {category}
-- One row per product. parent_category added; attribute codes and
-- price (country_code x price_type) flattened to columns.
WITH {CAT_CTE},
prices AS (
  SELECT
    product_id,
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
  ARRAY_TO_STRING(p.oem_number, ' | ') AS oem_number,
{price_select}{specs_select}
FROM `{PROJECT}.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id{specs_join}
WHERE p.category = '{category}'
ORDER BY p.brand, p.product_name;
"""


def build_unified_query() -> str:
    """One row per product across ALL categories. Sparse: every attribute code in
    the catalog becomes a column (NULL where it doesn't apply to that product)."""
    all_codes = sorted({c for codes in CATEGORY_CODES.values() for c in codes})
    pivot_lines = ",\n".join(
        f"    MAX(IF(a.code = '{c}', ps.value, NULL)) AS {quote_ident(c)}"
        for c in all_codes
    )
    price_lines = ",\n".join(
        f"    MAX(IF(country_code = '{cc}' AND price_type = '{pt}', amount, NULL)) "
        f"AS amount_{cc}_{pt}"
        for cc, pt in PRICE_COMBOS
    )
    price_select = ",\n".join(f"  pr.amount_{cc}_{pt}" for cc, pt in PRICE_COMBOS)
    return f"""-- Unified flattened product export: ALL categories, one row per product.
-- {len(all_codes)} attribute codes pivoted to columns (sparse -- NULL where N/A).
WITH {CAT_CTE},
prices AS (
  SELECT
    product_id,
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
  ARRAY_TO_STRING(p.oem_number, ' | ') AS oem_number,
{price_select},
  s.* EXCEPT (product_id)
FROM `{PROJECT}.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id
LEFT JOIN specs s ON s.product_id = p.id
ORDER BY cat.parent_category, p.category, p.brand, p.product_name;
"""


def main():
    for category, codes in CATEGORY_CODES.items():
        path = os.path.join(OUT_DIR, f"{category}.sql")
        with open(path, "w") as f:
            f.write(build_query(category, codes))
    with open(os.path.join(OUT_DIR, "all_products.sql"), "w") as f:
        f.write(build_unified_query())
    print(f"Wrote {len(CATEGORY_CODES)} category files + all_products.sql to {OUT_DIR}")


if __name__ == "__main__":
    main()
