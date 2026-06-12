-- Flattened product export: category = coolants
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
    MAX(IF(a.code = 'Type_of_coolant', ps.value, NULL)) AS `Type_of_coolant`,
    MAX(IF(a.code = 'boiling_point', ps.value, NULL)) AS `boiling_point`,
    MAX(IF(a.code = 'colour', ps.value, NULL)) AS `colour`,
    MAX(IF(a.code = 'coolant_spec', ps.value, NULL)) AS `coolant_spec`,
    MAX(IF(a.code = 'engine_type', ps.value, NULL)) AS `engine_type`,
    MAX(IF(a.code = 'freezing_point', ps.value, NULL)) AS `freezing_point`,
    MAX(IF(a.code = 'oil_grade', ps.value, NULL)) AS `oil_grade`,
    MAX(IF(a.code = 'possible_carmatch', ps.value, NULL)) AS `possible_carmatch`,
    MAX(IF(a.code = 'product_series', ps.value, NULL)) AS `product_series`,
    MAX(IF(a.code = 'productdetail', ps.value, NULL)) AS `productdetail`,
    MAX(IF(a.code = 'remark', ps.value, NULL)) AS `remark`,
    MAX(IF(a.code = 'viscosity_code', ps.value, NULL)) AS `viscosity_code`,
    MAX(IF(a.code = 'volume_capacity', ps.value, NULL)) AS `volume_capacity`
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
  ARRAY_TO_STRING(p.oem_number, ' | ') AS oem_number,
  pr.amount_th_recommended_price,
  pr.amount_my_recommended_price,
  s.* EXCEPT (product_id)
FROM `wyzauto-v2-prod.base_tables.product` p
LEFT JOIN cat ON cat.leaf_code = p.category
LEFT JOIN prices pr ON pr.product_id = p.id
LEFT JOIN specs s ON s.product_id = p.id
WHERE p.category = 'coolants'
ORDER BY p.brand, p.product_name;
