# Agentes por ambiente

## DEV (activo en MCP hoy)

Workspace: `8192491439151021` (`adb-bigdata-dev`)  
Host: `https://adb-8192491439151021.1.azuredatabricks.net`  
Perfil CLI: `DEFAULT` / `databricks_dev`

### Supervisores (Multi-Agent)

| Alias | display_name | supervisor_agent_id | endpoint |
|---|---|---|---|
| `supervisor` / `mia` | multi-agent-mia-dev | `250a2f2e-6339-40b7-a9f8-9561c8eb657d` | `mas-250a2f2e-endpoint` |
| `whatsapp` | multi-agent-whatsapp-dev | `ad06598d-2c89-48b2-902c-e8272ee22711` | `mas-ad06598d-endpoint` |

**Genie conectados al Supervisor MIA (UI Build):** ventas, dzs, rrhh, gastos, rentabilidad  
(El prompt del supervisor también menciona RAG KAs: PP, THUM, PMO, DACSOL + Custom Agent web.)

### Genie spaces

| Alias | Título | space_id | warehouse_id |
|---|---|---|---|
| `rrhh` | Genie Recursos Humanos y Desempeno Colaboradores | `01f14009f3761e65927a95ec9be27cdf` | `8af217ec77efb8bb` |
| `ventas-comercial` | Ventas y Rendimiento Comercial | `01f1805dcbd115f6997c9de81f1091ff` | `1c14abc6ed5aedbd` |
| `dzs` | Agente Genie Ventas DZs | `01f14a298e7f1eb7b67b5a132207047a` | `8af217ec77efb8bb` |
| `rentabilidad` | Agente Genie Rentabilidad Cliente Item TIBCO | `01f1650e75411441afdf1a4c03ee83d3` | `8af217ec77efb8bb` |
| `ventas` | Agente Genie Ventas | `01f0d4c1bfe810a8b1f21e84e1f1f318` | `8af217ec77efb8bb` |
| `gastos` | Genie Gastos Corporativos | `01f166d87a651d5aa4946908cdcbb23f` | `8af217ec77efb8bb` |
| `rrhh-analistas` | Genie RRHH Analistas (datos completos) | `01f159ef009f12f0a4a15a5179ddef02` | `8af217ec77efb8bb` |
| `waf` | WAF_ASSESSMENTv1.7.1_20260325_1523  Genie | `01f1285f762d147bbdff6d8ecaa17406` | `1c14abc6ed5aedbd` |

## PRD (pendiente)

Workspace: `3414404492188641`  
Perfil: `databricks_prd` (requiere re-login)  
Catálogo supervisor/Genie: _(vacío hasta autenticar)_

## Cómo pedirlo en el chat

```
@dev supervisor                    → multi-agent-mia-dev
@dev prueba supervisor: <pregunta>
@dev ventas                        → solo Genie Ventas
@prd supervisor                    → cuando exista catálogo prd
```

Sin `@dev`/`@prd` → asumir **dev**.
