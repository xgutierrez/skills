# Perfil: pronaca

Convenciones de Pronaca y Toledano. Solo nombres y reglas: sin secretos ni correos.
Lo que ubica la infraestructura (organización de Azure DevOps, tenant, suscripción,
fábricas, workspaces) está en `identificadores.md`.

Un repositorio declara este perfil con la línea `Perfil de estándares: pronaca` en
su `AGENTS.md`.

## Identidad

| Dato | Valor |
|---|---|
| Nombre corto | `pronaca` |
| Países de los datos | `ecuador` (Pronaca), `panama` (Toledano) |
| Zona horaria de proceso | `America/Guayaquil` |
| Idioma del código y la documentación | Español |

## Catálogos y esquemas

| Capa | Catálogo |
|---|---|
| Bronze | `bronze_{ambiente}` |
| Silver | `silver_{ambiente}` |
| Gold | `gold_{ambiente}` |

Valores de `{ambiente}`: `dev` y `prd`.
Volumen de aterrizaje: `/Volumes/bronze_{ambiente}/{fuente}/raw/{dominio}/fecha_ingesta=AAAA-MM-DD/`.

## Secretos

| Dato | Valor |
|---|---|
| Scope de Pronaca | `sc-kv-bigdata-{ambiente}` |
| Scope de Toledano | `sc-kv-toledano-bigdata-{ambiente}` |
| Convención de nombres de clave | `sc-{sistema}-{dato}` |

Un proceso que corre con `ambiente=sandbox` lee los secretos del scope de `dev`.

## Repositorios y bundles

| Dato | Valor |
|---|---|
| Plataforma de git | Azure DevOps |
| Patrón del nombre del repositorio | `pronaca_{iniciativa}_{proyecto}` o `toledano_{iniciativa}_{proyecto}` |
| Prefijo del repositorio | `pronaca_` o `toledano_` |
| Carpeta en el workspace | El nombre del repositorio sin el prefijo `pronaca_` |
| Ramas | `dev` (por defecto) y `main` |
| Prefijo del job por target | `local`: `[LOCAL] ` · `dev`: `[DEV] ` · `main`: vacío |
| Grupo de variables del CI/CD | `vg-pronacadatabricks`, al que el pipeline añade `-{ambiente}` |
| Pipeline de despliegue | `.azure-pipelines/{bundle}_cd.yml` |

## Etiquetas obligatorias de los jobs

| Etiqueta | Valores admitidos |
|---|---|
| `proyecto` | `bigdata_pronaca`, `bigdata_toledano` |
| `area` | `datos`, `comercial`, `operaciones`, `rgm_mercadeo` |
| `tipo` | `ingesta`, `analitica`, `setup` |
| `modelo` | `transversal` o el nombre del modelo (`modelo_pnl`, `pedido_sugerido`…) |
| `frecuencia` | `diaria`, `semanal`, `mensual`, `anual`, `eventual` |
| `pais` | `ecuador`, `panama` |
| `gestion` | `bundle` |

Las escrituras `bigdata` y `big_data` para `proyecto` son antiguas: no se usan en
jobs nuevos. Si no hay certeza del valor de `modelo`, se pregunta si es transversal
o de un modelo concreto.

## Etiquetas de tablas

| Etiqueta | Valores admitidos | Dónde |
|---|---|---|
| `capa` | `consumo`, `interno` | Tablas gold |

## Particularidades

- Los avisos de inicio y fin de un proceso usan las plantillas de `avisos/`, con la
  barra roja corporativa, y las utilidades `utils_aviso_proceso` y
  `utils_envio_correos` cuando el repositorio las tiene.
- Skills propias de la empresa, en `skills/`: `pronaca-data-factory`,
  `pronaca-historias-usuario-ado`, `cotizar-sandbox-databricks` y `genie-pruebas`.
- Los modelos que cuadran contra cifras del área funcional leen sus fuentes de
  `gold_prd` también en desarrollo, mediante el parámetro `catalogo_fuente`.
