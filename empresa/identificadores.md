# Identificadores de Pronaca

Valores que ubican la infraestructura de la empresa: las skills y
`configurar-equipo.sh` los leen de aquí. No contiene secretos: ni contraseñas ni
tokens. Las credenciales se obtienen iniciando sesión en cada equipo.

## Azure

| Dato | Valor |
|---|---|
| Tenant | `615f938f-b03f-4133-941d-b4145eb714a9` |
| Suscripción | `6b4af507-8a88-42a4-8c70-63e100bbbd2f` |
| Usuario de Azure CLI | `dxgutiec@pronaca.com` |
| Región | `eastus` |

## Azure DevOps

| Dato | Valor |
|---|---|
| Organización | `https://dev.azure.com/pronacadevops` |
| Proyecto | `BigData` |
| Proceso de trabajo | `Agile-PRONACA` |
| Área por defecto | `BigData` |
| Iteración por defecto | `BigData\Sprint 1` |
| Responsable por defecto de historias | `correo@pronaca.com` |
| Correo de notificaciones por defecto | `correo@pronaca.com` |
| Carpeta local de repositorios | `~/Documents/RepoTrabajo` |

## Data Factory

| El usuario dice | Fábrica | Grupo de recursos |
|---|---|---|
| ADF de Pronaca, desarrollo / dev | `adf-bigdata-dev-001` | `rg-bigdata-dev` |
| ADF de Pronaca, producción / prd / prod | `adf-bigdata-prd-001` | `rg-bigdata-prd` |
| ADF de Toledano, desarrollo / dev | `adf-bigdata-toledano-dev-001` | `rg-bigdata-toledano-dev` |
| ADF de Toledano, producción / prd / prod | `adf-bigdata-toledano-prd-001` | `rg-bigdata-toledano-prd` |

## Databricks

Un perfil de la CLI por workspace. `configurar-equipo.sh` crea los que falten.

| Perfil de la CLI | Empresa | Ambiente | Host |
|---|---|---|---|
| `databricks_dev` | Pronaca | `dev` | `https://adb-8192491439151021.1.azuredatabricks.net` |
| `databricks_prd` | Pronaca | `prd` | `https://adb-3414404492188641.1.azuredatabricks.net` |
| `toledano_dev` | Toledano | `dev` | `https://adb-1846297007681135.15.azuredatabricks.net` |
| `toledano_prd` | Toledano | `prd` | `https://adb-1134579937417385.5.azuredatabricks.net` |

Perfil de cuenta: `cuenta_databricks`, host `https://accounts.azuredatabricks.net`, cuenta `799b52f4-ed6b-4852-a6ea-79158e015f95`.

El perfil por defecto de desarrollo es `databricks_dev`.

Los agentes, endpoints y espacios Genie están en `skills/genie-pruebas/agents.md`.
