-- Flattened product export: category = battery_testing
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
    MAX(IF(a.code = 'productdetail', ps.value, NULL)) AS `productdetail`,
    MAX(IF(a.code = 'remark', ps.value, NULL)) AS `remark`
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
WHERE p.category = 'battery_testing'
ORDER BY p.brand, p.product_name;
