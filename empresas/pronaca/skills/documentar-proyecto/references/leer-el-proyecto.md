# Cómo leer cada tipo de proyecto

Guía para pasar del inventario a los hechos que la documentación necesita. Lee solo
la sección del tipo de proyecto que tengas delante.

## Contenido

1. Databricks Asset Bundle
2. Convención de nombres de notebooks
3. Cómo confirmar fuentes y tablas
4. Azure Data Factory
5. Notebooks sueltos (sin bundle)
6. Monorepo con varios bundles
7. CI/CD en Azure DevOps
8. Power BI, DAX y otros artefactos
9. Proyectos que no son de datos
10. Qué hacer cuando el inventario se queda corto

## 1. Databricks Asset Bundle

Se reconoce por un `databricks.yml`. Estructura habitual:

```
<repo>/
├── .azure-pipelines/        CI/CD
├── docs/
└── <bundle>/
    ├── databricks.yml       nombre, variables y targets (ambientes)
    ├── resources/*.yml      jobs, pipelines, tableros
    ├── src/                 notebooks
    └── tests/
```

| Dato para la documentación | Dónde está |
|---|---|
| Ambientes y a qué catálogo escribe cada uno | `targets` y `variables` en `databricks.yml` |
| Jobs, tareas y dependencias | `resources/*.yml` → `tasks[].depends_on` |
| Horario | `schedule.quartz_cron_expression` y `timezone_id` |
| Si está activo o pausado | `schedule.pause_status` (a menudo una variable por target) |
| Parámetros | `parameters` del job, `base_parameters` de la tarea y `dbutils.widgets` del notebook |
| Avisos por correo | `email_notifications` |
| Etiquetas de gobierno | `tags` (proyecto, área, frecuencia, país) |
| Tableros desplegados | recursos `dashboards` y archivos `*.lvdash.json` |

**Cron de Quartz en palabras.** Tiene seis o siete campos: segundo, minuto, hora, día
del mes, mes, día de la semana, año. `0 0 10 ? * SUN *` es "domingos a las 10:00".
`0 30 6 * * ?` es "todos los días a las 06:30". Escribe siempre la versión en palabras
y deja el cron entre paréntesis.

**Variables por target.** Valores como `${var.ambiente}` se resuelven distinto en cada
target. Documenta la tabla ambiente → valor, no la variable.

## 2. Convención de nombres de notebooks

El prefijo suele indicar la etapa. Úsalo para ubicar cada notebook en el diagrama:

| Prefijo | Etapa | Qué hace normalmente |
|---|---|---|
| `ext_` | Extracción | Trae el dato de la fuente a un volumen o zona de aterrizaje |
| `brz_`, `bro_` | Bronze | Carga el dato crudo en tabla, sin transformar |
| `slv_` | Silver | Limpia, tipa, renombra y deduplica |
| `gld_` | Gold | Aplica reglas de negocio y agrega para consumo |
| `val_` | Validación | Compara contra una referencia y alerta |
| `cfg_` | Configuración | Constantes, rutas, credenciales; se incluye con `%run` |
| `utils_` | Utilidades | Funciones compartidas |
| `tbl_`, `sch_` | Setup | Crea esquemas y tablas (DDL); corre una vez |
| `jb_`, `jb_orq_` | Job | Definición de un job u orquestador (en `resources/`) |
| `dsh_` | Tablero | Definición de un tablero |
| `fac_`, `dim_`, `mv_` | Tablas | Hechos, dimensiones y vistas materializadas |

Si el proyecto no sigue la convención (notebooks numerados `01_`, `02_`…), deduce la
etapa por lo que lee y escribe. Describe lo que hay; no renombres nada.

## 3. Cómo confirmar fuentes y tablas

El inventario clasifica por patrones de texto. Antes de escribirlo como hecho:

- **Tablas con variables** (`{catalogo}.{esquema}.fac_x`): resuélvelas con el
  notebook de configuración y los widgets. Documenta `gold_{ambiente}.modelo.fac_x`
  y explica los valores de `{ambiente}`.
- **"Tablas que lee y no produce"**: son las fuentes internas. Averigua qué proyecto
  las produce si está en la misma carpeta de trabajo; si no, "Por confirmar".
- **"Mencionadas sin clasificar"**: mira el notebook; suelen ser lecturas dentro de
  SQL dinámico o nombres en comentarios.
- **Notebooks sin tablas detectadas**: no significa que no escriban. Suelen armar el
  nombre con una función o un diccionario de configuración (`cfg["esquema_gold_fqn"]`)
  y escribir con una función propia. Mira `variables_de_ruta` en el JSON y abre el
  notebook de utilidades para resolver el nombre completo.
- **La misma tabla aparece dos veces** (una desde el notebook `tbl_*` que la crea y
  otra desde el que la carga, con variables distintas): es una sola tabla.
- **Indicios de fuentes externas**: son palabras clave, hay falsos positivos. Una
  fuente es real cuando ves la conexión: un `spark.read.format("jdbc")`, una llamada
  HTTP, la lectura de un archivo. Anota sistema, objeto, método y dónde está la
  credencial (scope y clave del secreto, nunca el valor).
- **Grano de una tabla**: está en el `GROUP BY` final, en la clave del `MERGE` o en
  la clave primaria del DDL.
- **Tipo de carga**: `overwrite` o `CREATE OR REPLACE` es completa; `MERGE` o
  `replaceWhere` es incremental; `append` solo añade.
- **Descripciones de columnas**: busca `COMMENT` en el DDL, diccionarios de mapeo en
  silver y las celdas Markdown del notebook.

## 4. Azure Data Factory

Se reconoce por carpetas `pipeline/`, `dataset/`, `linkedService/` y `trigger/`.

| Dato | Dónde está |
|---|---|
| Sistemas de origen y destino | `linkedService/*.json` → `properties.type` |
| Qué se copia | Actividades `Copy` de cada pipeline y los `dataset` que referencian |
| Orquestación | Actividades `ExecutePipeline` y `dependsOn` |
| Notebooks que invoca | Actividades `DatabricksNotebook` → `notebookPath` |
| Horarios | `trigger/*.json` → `recurrence` y `runtimeState` (`Started` es activo) |

Una factoría con cientos de pipelines no se documenta pipeline por pipeline:
agrúpalos por carpeta (`properties.folder`) o por prefijo, identifica los
orquestadores maestros (los que solo tienen `ExecutePipeline`) y dibuja el flujo a
partir de ellos. Lista el resto en una tabla. Señala los que no tienen disparador ni
son llamados por otro: probablemente estén en desuso, pero dilo como observación, no
como hecho.

## 5. Notebooks sueltos (sin bundle)

Proyectos antiguos con una carpeta `Databricks/` y sin `databricks.yml`. No hay
definición de jobs en el repositorio, así que:

- El orden de ejecución se deduce de los `%run`, de `dbutils.notebook.run`, de la
  numeración de los archivos y de los pipelines de Data Factory que los invoquen.
- La programación probablemente está en Data Factory o configurada a mano en el
  workspace. Si no consta en el repositorio, escribe "Por confirmar: la programación
  no está en el repositorio".

## 6. Monorepo con varios bundles

Un repositorio con varios `databricks.yml` (típico en ingestas compartidas).

- Los cinco documentos de la raíz describen el conjunto: qué fuentes cubre, un
  diagrama de contexto con todos los bundles como cajas, las convenciones comunes y
  una tabla resumen (bundle, fuente, destino, jobs, frecuencia).
- Cada bundle recibe un `README.md` propio con la plantilla 6 de `plantillas.md`.
- Lo común (ambientes, CI/CD, utilidades) se escribe una vez en la raíz.
- Si hay varias copias del mismo repositorio en ramas distintas (carpetas con el
  mismo nombre y un sufijo), son ramas de trabajo: documenta solo la principal salvo
  que el usuario pida otra cosa.

## 7. CI/CD en Azure DevOps

En `.azure-pipelines/` o `azure-pipelines/`:

- `trigger.branches` y `trigger.paths`: qué cambios disparan el despliegue.
- `variables.group`: grupos de variables (suelen terminar en el ambiente).
- Los pasos con `databricks bundle validate` y `databricks bundle deploy -t <target>`
  indican a qué target va cada rama.
- `variables.environment.yml` suele mapear rama → ambiente.

## 8. Power BI, DAX y otros artefactos

- Archivos `.dax` y guías de reportes: no los reescribas; enlázalos como documentos
  complementarios y nombra en `03_fuentes_y_datos.md` qué tablas alimentan qué reporte.
- Plantillas Excel (`.xlsx`): son entradas que alguien llena a mano. Trátalas como
  fuente externa e indica quién las llena y dónde se suben, si consta.
- Flujos KNIME, scripts de análisis exploratorio, transcripciones: son material de
  trabajo, no parte del proceso productivo. Menciónalos en una línea en la
  estructura del repositorio y no los documentes a fondo.

## 9. Proyectos que no son de datos

Para una librería, una API o una herramienta, mantén los mismos cinco archivos:

- Entendimiento: qué resuelve y para quién.
- Arquitectura: componentes y cómo se comunican (diagrama de contexto y de
  componentes en lugar de medallón).
- `03_fuentes_y_datos.md` pasa a ser "Entradas y salidas" o "Interfaz": qué recibe,
  qué devuelve, qué almacena. Si no aporta, se omite.
- Operación: instalar, configurar, ejecutar, probar, desplegar.

Lee el manifiesto (`pyproject.toml`, `package.json`, `requirements.txt`), el punto de
entrada, las pruebas (dicen qué se espera del código) y la configuración de CI.

## 10. Qué hacer cuando el inventario se queda corto

- **No hay lector de YAML**: el script avisa. Ejecútalo con
  `uv run --with pyyaml python3 inventario.py …` o lee los `.yml` directamente.
- **Proyecto en otro lenguaje o estructura**: usa el inventario para lo que
  encuentre y completa leyendo. La estructura de los documentos no cambia.
- **Notebooks enormes omitidos**: el resumen los marca; ábrelos por partes.
- **El código contradice a la documentación previa**: manda el código. Anótalo para
  el resumen final.
