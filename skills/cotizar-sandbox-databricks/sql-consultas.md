# SQL — consumo real de sandboxes

MCP: `user-databricks-prd` → `execute_sql`. No hace falta `warehouse_id` salvo que falle el default.

Filtro de sandboxes: `lower(w.workspace_name) LIKE 'adb-sandbox-%'`.

## 1. Inventario

```sql
SELECT
  workspace_id,
  workspace_name,
  status,
  workspace_url,
  create_time
FROM system.access.workspaces_latest
WHERE lower(workspace_name) LIKE 'adb-sandbox-%'
ORDER BY workspace_name
```

## 2. USD lista y DBU por workspace-mes

Join de precios: vigencia del SKU al `usage_start_time`.

```sql
SELECT
  w.workspace_name,
  date_trunc('month', u.usage_date) AS mes,
  ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.effective_list.default, lp.pricing.default)), 2) AS usd_lista,
  ROUND(SUM(u.usage_quantity), 2) AS dbus,
  COUNT(DISTINCT u.identity_metadata.run_as) AS identidades_run_as
FROM system.billing.usage u
INNER JOIN system.access.workspaces_latest w
  ON u.workspace_id = w.workspace_id
LEFT JOIN system.billing.list_prices lp
  ON u.cloud = lp.cloud
  AND u.sku_name = lp.sku_name
  AND u.usage_unit = lp.usage_unit
  AND u.usage_start_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_start_time < lp.price_end_time)
WHERE lower(w.workspace_name) LIKE 'adb-sandbox-%'
  AND u.usage_date >= add_months(current_date(), -18)
GROUP BY 1, 2
ORDER BY 1, 2
```

## 3. Mix de producto (ventana a elegir; ajustar fechas)

```sql
SELECT
  w.workspace_name,
  u.billing_origin_product,
  ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.effective_list.default, lp.pricing.default)), 2) AS usd_lista,
  ROUND(SUM(u.usage_quantity), 2) AS dbus
FROM system.billing.usage u
INNER JOIN system.access.workspaces_latest w
  ON u.workspace_id = w.workspace_id
LEFT JOIN system.billing.list_prices lp
  ON u.cloud = lp.cloud
  AND u.sku_name = lp.sku_name
  AND u.usage_unit = lp.usage_unit
  AND u.usage_start_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_start_time < lp.price_end_time)
WHERE lower(w.workspace_name) LIKE 'adb-sandbox-%'
  AND u.usage_date >= DATE '2025-12-01'
GROUP BY 1, 2
ORDER BY 1, 3 DESC NULLS LAST
```

Para un solo workspace de referencia, añadir `AND w.workspace_name = 'adb-sandbox-…'`.

## 4. Identidades distintas en meses maduros (referencia)

```sql
SELECT
  date_trunc('month', u.usage_date) AS mes,
  COUNT(DISTINCT u.identity_metadata.run_as) AS identidades_run_as
FROM system.billing.usage u
INNER JOIN system.access.workspaces_latest w
  ON u.workspace_id = w.workspace_id
WHERE w.workspace_name = 'adb-sandbox-trade'  -- reemplazar
  AND u.usage_date >= DATE '2025-12-01'
GROUP BY 1
ORDER BY 1
```

`identity_metadata.run_as` es la mejor aproximación a “quién consumió cómputo”. No equivale 1:1 a licencias ni a headcount de negocio.

## 5. Reparto clásico vs serverless (para estimar infraestructura Azure)

El DBU serverless ya incluye la infraestructura; solo la porción clásica paga VM de Azure aparte. Las VMs reales se miden con la query 6 y se valoran con el API de precios (abajo).

```sql
SELECT
  CASE WHEN u.product_features.is_serverless THEN 'serverless' ELSE 'clasico' END AS tipo_computo,
  ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.effective_list.default, lp.pricing.default)), 2) AS usd_lista
FROM system.billing.usage u
INNER JOIN system.access.workspaces_latest w
  ON u.workspace_id = w.workspace_id
LEFT JOIN system.billing.list_prices lp
  ON u.cloud = lp.cloud
  AND u.sku_name = lp.sku_name
  AND u.usage_unit = lp.usage_unit
  AND u.usage_start_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_start_time < lp.price_end_time)
WHERE w.workspace_name = 'adb-sandbox-…'  -- referencia
  AND u.usage_date >= DATE '…' AND u.usage_date < DATE '…'  -- meses maduros
GROUP BY 1
```

## 6. Horas reales de VM por tipo de nodo (cómputo clásico)

```sql
SELECT
  nt.node_type,
  COUNT(DISTINCT nt.instance_id) AS instancias,
  ROUND(SUM((unix_timestamp(nt.end_time) - unix_timestamp(nt.start_time)) / 3600.0), 1) AS horas_vm
FROM system.compute.node_timeline nt
INNER JOIN system.access.workspaces_latest w
  ON nt.workspace_id = w.workspace_id
WHERE w.workspace_name = 'adb-sandbox-…'  -- referencia
  AND nt.start_time >= TIMESTAMP '…' AND nt.start_time < TIMESTAMP '…'  -- meses maduros
GROUP BY 1
ORDER BY 3 DESC
```

## 7. Región Azure predominante

```sql
SELECT u.usage_metadata.source_region AS region, COUNT(*) AS registros
FROM system.billing.usage u
INNER JOIN system.access.workspaces_latest w
  ON u.workspace_id = w.workspace_id
WHERE lower(w.workspace_name) LIKE 'adb-sandbox-%'
  AND u.usage_metadata.source_region IS NOT NULL
  AND u.usage_metadata.source_region != 'INTERNET'
GROUP BY 1
ORDER BY 2 DESC
```

## Precios oficiales Azure (API pública, consultar en cada cotización)

Sin autenticación; devuelve JSON. Tomar `retailPrice` del `productName` **sin** "Windows" (Databricks corre Linux) y tipo `Consumption` (no Spot ni Low Priority).

VMs (reemplazar región y `armSkuName` según queries 6 y 7):

```text
https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'eastus' and serviceName eq 'Virtual Machines' and priceType eq 'Consumption' and armSkuName eq 'Standard_D8ds_v5'
```

Almacenamiento ADLS Gen2 (USD por GB/mes, `Hot LRS Data Stored`):

```text
https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'eastus' and serviceName eq 'Storage' and contains(productName, 'Data Lake Storage Gen2') and meterName eq 'Hot LRS Data Stored'
```

Red: el cargo NETWORKING ya está incluido en el consumo Databricks (query 2); no sumar aparte.
