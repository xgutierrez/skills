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

## Dueño de las tablas

| Dato | Valor |
|---|---|
| Grupo dueño de toda tabla, vista y esquema nuevos | `gr_usr_area_datos_de_int` |

El *service principal* que ejecuta los jobs tiene que pertenecer a este grupo; si
no, el `ALTER` del setup falla después de ceder la propiedad.

## Etiquetas de tablas

| Etiqueta | Valores admitidos | Dónde |
|---|---|---|
| `capa` | `consumo`, `interno` | Tablas gold |
| `dato_personal` | `si` | Tabla con al menos una columna clasificada |
| `dato_personal` | Ver la tabla siguiente | Cada columna con datos personales |

## Clasificación de datos personales

Nomenclatura tomada de la Ley Orgánica de Protección de Datos Personales del Ecuador
(LOPDP), artículos 4 y 25. Para Panamá (Toledano) se usa la misma hasta revisar la
Ley 81 de 2019. Las fuentes están en `estandares-datos/references/fuentes.md`, §8.

| Valor de `dato_personal` | Qué es, según la LOPDP | Ejemplos |
|---|---|---|
| `identificativo` | Identifica o hace identificable a una persona natural (Art. 4) | Nombre, cédula, RUC de persona natural, correo, teléfono, dirección, coordenadas de un domicilio, nombre del encuestador |
| `crediticio` | Comportamiento económico de una persona natural para analizar su capacidad financiera (Art. 4) | Cupo de crédito, mora, historial de pagos de un cliente persona natural |
| `sensible` | Etnia, identidad de género o cultural, religión, ideología, filiación política, pasado judicial, condición migratoria, orientación sexual, biométricos, genéticos (Art. 4) | Huella, foto del rostro, nacionalidad o estatus migratorio |
| `salud` | Salud física o mental (Art. 4 y Art. 25) | Diagnóstico, incapacidad médica |
| `nna` | Datos de niñas, niños y adolescentes (Art. 25) | Hijos de un colaborador |
| `discapacidad` | Datos de personas con discapacidad relativos a la discapacidad (Art. 25) | Porcentaje de discapacidad |

Los datos de una empresa (RUC de persona jurídica, razón social) no son datos
personales. `sensible`, `salud`, `nna` y `discapacidad` son categorías especiales:
se avisa al usuario y se consulta con el responsable de protección de datos.

## Particularidades

- Los avisos de inicio y fin de un proceso usan las plantillas de `avisos/`, con la
  barra roja corporativa, y las utilidades `utils_aviso_proceso` y
  `utils_envio_correos` cuando el repositorio las tiene.
- Skills propias de la empresa, en `skills/`: `pronaca-data-factory`,
  `pronaca-historias-usuario-ado`, `cotizar-sandbox-databricks` y `genie-pruebas`.
- Los modelos que cuadran contra cifras del área funcional leen sus fuentes de
  `gold_prd` también en desarrollo, mediante el parámetro `catalogo_fuente`.
