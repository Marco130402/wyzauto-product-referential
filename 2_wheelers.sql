-- Flattened product export: category = 2_wheelers
-- One row per product. parent_category added; attribute codes and
-- price (country_code x price_type) flattened to columns.
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
    MAX(IF(a.code = 'aspect_ratio', ps.value, NULL)) AS `aspect_ratio`,
    MAX(IF(a.code = 'fitting_front_rear', ps.value, NULL)) AS `fitting_front_rear`,
    MAX(IF(a.code = 'load_dual', ps.value, NULL)) AS `load_dual`,
    MAX(IF(a.code = 'load_index', ps.value, NULL)) AS `load_index`,
    MAX(IF(a.code = 'match_code', ps.value, NULL)) AS `match_code`,
    MAX(IF(a.code = 'pattern', ps.value, NULL)) AS `pattern`,
    MAX(IF(a.code = 'seat', ps.value, NULL)) AS `seat`,
    MAX(IF(a.code = 'sidewall_logo', ps.value, NULL)) AS `sidewall_logo`,
    MAX(IF(a.code = 'speed_index', ps.value, NULL)) AS `speed_index`,
    MAX(IF(a.code = 'tech_marking', ps.value, NULL)) AS `tech_marking`,
    MAX(IF(a.code = 'tube_type', ps.value, NULL)) AS `tube_type`,
    MAX(IF(a.code = 'tyre_structure', ps.value, NULL)) AS `tyre_structure`,
    MAX(IF(a.code = 'tyre_type', ps.value, NULL)) AS `tyre_type`,
    MAX(IF(a.code = 'vehicle_type_tyre', ps.value, NULL)) AS `vehicle_type_tyre`,
    MAX(IF(a.code = 'width_tyre', ps.value, NULL)) AS `width_tyre`
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
WHERE p.category = '2_wheelers'
ORDER BY p.brand, p.product_name;
