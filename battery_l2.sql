-- Flattened product export: category = battery_l2
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
    MAX(IF(a.code = 'battery_model', ps.value, NULL)) AS `battery_model`,
    MAX(IF(a.code = 'battery_type', ps.value, NULL)) AS `battery_type`,
    MAX(IF(a.code = 'capacity', ps.value, NULL)) AS `capacity`,
    MAX(IF(a.code = 'cca', ps.value, NULL)) AS `cca`,
    MAX(IF(a.code = 'din_jis', ps.value, NULL)) AS `din_jis`,
    MAX(IF(a.code = 'height', ps.value, NULL)) AS `height`,
    MAX(IF(a.code = 'length', ps.value, NULL)) AS `length`,
    MAX(IF(a.code = 'product_series', ps.value, NULL)) AS `product_series`,
    MAX(IF(a.code = 'remark', ps.value, NULL)) AS `remark`,
    MAX(IF(a.code = 'side', ps.value, NULL)) AS `side`,
    MAX(IF(a.code = 'width', ps.value, NULL)) AS `width`
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
WHERE p.category = 'battery_l2'
ORDER BY p.brand, p.product_name;
