-- Unified flattened product export: ALL categories, one row per product.
-- 71 attribute codes pivoted to columns (sparse -- NULL where N/A).
WITH cat AS (
  SELECT c.code AS leaf_code, parent.code AS parent_category
  FROM `wyzauto-v2-prod.base_tables.category` c
  LEFT JOIN `wyzauto-v2-prod.base_tables.category` parent ON parent.id = c.parent_id
),
prices AS (
  SELECT
    product_id,
    MAX(IF(country_code = 'th' AND price_type = 'recommended_price', amount, NULL)) AS amount_th_recommended_price,
    MAX(IF(country_code = 'my' AND price_type = 'recommended_price', amount, NULL)) AS amount_my_recommended_price
  FROM `wyzauto-v2-prod.base_tables.product_price`
  GROUP BY product_id
),
specs AS (
  SELECT
    ps.product_id,
    MAX(IF(a.code = 'Hexagon_Size', ps.value, NULL)) AS `Hexagon_Size`,
    MAX(IF(a.code = 'OE_marking', ps.value, NULL)) AS `OE_marking`,
    MAX(IF(a.code = 'Thickness_2', ps.value, NULL)) AS `Thickness_2`,
    MAX(IF(a.code = 'Thread_diameter', ps.value, NULL)) AS `Thread_diameter`,
    MAX(IF(a.code = 'Thread_length', ps.value, NULL)) AS `Thread_length`,
    MAX(IF(a.code = 'Type_of_coolant', ps.value, NULL)) AS `Type_of_coolant`,
    MAX(IF(a.code = 'Width_2', ps.value, NULL)) AS `Width_2`,
    MAX(IF(a.code = 'Wiperblade_length_2', ps.value, NULL)) AS `Wiperblade_length_2`,
    MAX(IF(a.code = 'aspect_ratio', ps.value, NULL)) AS `aspect_ratio`,
    MAX(IF(a.code = 'battery_model', ps.value, NULL)) AS `battery_model`,
    MAX(IF(a.code = 'battery_type', ps.value, NULL)) AS `battery_type`,
    MAX(IF(a.code = 'boiling_point', ps.value, NULL)) AS `boiling_point`,
    MAX(IF(a.code = 'brake_disc_type', ps.value, NULL)) AS `brake_disc_type`,
    MAX(IF(a.code = 'brand_special', ps.value, NULL)) AS `brand_special`,
    MAX(IF(a.code = 'capacity', ps.value, NULL)) AS `capacity`,
    MAX(IF(a.code = 'cca', ps.value, NULL)) AS `cca`,
    MAX(IF(a.code = 'colour', ps.value, NULL)) AS `colour`,
    MAX(IF(a.code = 'coolant_spec', ps.value, NULL)) AS `coolant_spec`,
    MAX(IF(a.code = 'diameter_centering', ps.value, NULL)) AS `diameter_centering`,
    MAX(IF(a.code = 'diameter_outer', ps.value, NULL)) AS `diameter_outer`,
    MAX(IF(a.code = 'din_jis', ps.value, NULL)) AS `din_jis`,
    MAX(IF(a.code = 'engine_type', ps.value, NULL)) AS `engine_type`,
    MAX(IF(a.code = 'engine_type2', ps.value, NULL)) AS `engine_type2`,
    MAX(IF(a.code = 'fitting_center_inner_outer', ps.value, NULL)) AS `fitting_center_inner_outer`,
    MAX(IF(a.code = 'fitting_front_rear', ps.value, NULL)) AS `fitting_front_rear`,
    MAX(IF(a.code = 'fitting_left_right', ps.value, NULL)) AS `fitting_left_right`,
    MAX(IF(a.code = 'fitting_upr_lwr', ps.value, NULL)) AS `fitting_upr_lwr`,
    MAX(IF(a.code = 'freezing_point', ps.value, NULL)) AS `freezing_point`,
    MAX(IF(a.code = 'gear_type', ps.value, NULL)) AS `gear_type`,
    MAX(IF(a.code = 'grade_brakefluid', ps.value, NULL)) AS `grade_brakefluid`,
    MAX(IF(a.code = 'height', ps.value, NULL)) AS `height`,
    MAX(IF(a.code = 'height_2', ps.value, NULL)) AS `height_2`,
    MAX(IF(a.code = 'holes_nbr', ps.value, NULL)) AS `holes_nbr`,
    MAX(IF(a.code = 'length', ps.value, NULL)) AS `length`,
    MAX(IF(a.code = 'load_dual', ps.value, NULL)) AS `load_dual`,
    MAX(IF(a.code = 'load_format', ps.value, NULL)) AS `load_format`,
    MAX(IF(a.code = 'load_index', ps.value, NULL)) AS `load_index`,
    MAX(IF(a.code = 'match_code', ps.value, NULL)) AS `match_code`,
    MAX(IF(a.code = 'mounting_lwr_type', ps.value, NULL)) AS `mounting_lwr_type`,
    MAX(IF(a.code = 'mounting_upr_type', ps.value, NULL)) AS `mounting_upr_type`,
    MAX(IF(a.code = 'oil_change_frequency', ps.value, NULL)) AS `oil_change_frequency`,
    MAX(IF(a.code = 'oil_grade', ps.value, NULL)) AS `oil_grade`,
    MAX(IF(a.code = 'pattern', ps.value, NULL)) AS `pattern`,
    MAX(IF(a.code = 'possible_carmatch', ps.value, NULL)) AS `possible_carmatch`,
    MAX(IF(a.code = 'product_model_cabinairfilter', ps.value, NULL)) AS `product_model_cabinairfilter`,
    MAX(IF(a.code = 'product_series', ps.value, NULL)) AS `product_series`,
    MAX(IF(a.code = 'product_spec_nlgi', ps.value, NULL)) AS `product_spec_nlgi`,
    MAX(IF(a.code = 'productdetail', ps.value, NULL)) AS `productdetail`,
    MAX(IF(a.code = 'remark', ps.value, NULL)) AS `remark`,
    MAX(IF(a.code = 'runflat', ps.value, NULL)) AS `runflat`,
    MAX(IF(a.code = 'season', ps.value, NULL)) AS `season`,
    MAX(IF(a.code = 'seat', ps.value, NULL)) AS `seat`,
    MAX(IF(a.code = 'shock_type', ps.value, NULL)) AS `shock_type`,
    MAX(IF(a.code = 'side', ps.value, NULL)) AS `side`,
    MAX(IF(a.code = 'sidewall_logo', ps.value, NULL)) AS `sidewall_logo`,
    MAX(IF(a.code = 'speed_index', ps.value, NULL)) AS `speed_index`,
    MAX(IF(a.code = 'stroke', ps.value, NULL)) AS `stroke`,
    MAX(IF(a.code = 'tech_marking', ps.value, NULL)) AS `tech_marking`,
    MAX(IF(a.code = 'thickness', ps.value, NULL)) AS `thickness`,
    MAX(IF(a.code = 'thickness_min', ps.value, NULL)) AS `thickness_min`,
    MAX(IF(a.code = 'transmission_oil_grade', ps.value, NULL)) AS `transmission_oil_grade`,
    MAX(IF(a.code = 'tube_type', ps.value, NULL)) AS `tube_type`,
    MAX(IF(a.code = 'tyre_structure', ps.value, NULL)) AS `tyre_structure`,
    MAX(IF(a.code = 'tyre_type', ps.value, NULL)) AS `tyre_type`,
    MAX(IF(a.code = 'vehicle_type_tyre', ps.value, NULL)) AS `vehicle_type_tyre`,
    MAX(IF(a.code = 'viscosity_code', ps.value, NULL)) AS `viscosity_code`,
    MAX(IF(a.code = 'volume_capacity', ps.value, NULL)) AS `volume_capacity`,
    MAX(IF(a.code = 'width', ps.value, NULL)) AS `width`,
    MAX(IF(a.code = 'width_tyre', ps.value, NULL)) AS `width_tyre`,
    MAX(IF(a.code = 'wiper_blade_type', ps.value, NULL)) AS `wiper_blade_type`,
    MAX(IF(a.code = 'wiperbade_length_1', ps.value, NULL)) AS `wiperbade_length_1`
  FROM `wyzauto-v2-prod.base_tables.product_specification` ps
  JOIN `wyzauto-v2-prod.base_tables.attribute` a ON a.id = ps.attribute_id
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
  pr.amount_th_recommended_price,
  pr.amount_my_recommended_price,
  s.* EXCEPT (product_id)
FROM `wyzauto-v2-prod.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id
LEFT JOIN specs s ON s.product_id = p.id
ORDER BY cat.parent_category, p.category, p.brand, p.product_name;
