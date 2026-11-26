# Tablas: diseño, creación, optimización y carga

## Contenido

1. Tablas administradas
2. Nombres
3. Tipos de dato
4. Comentarios y etiquetas
5. Clustering: qué va en lugar de particionar
6. Lo que no se configura a mano
7. Claves y restricciones
8. Columnas de linaje
9. Dónde vive el DDL
10. Estrategia de carga por capa
11. Vistas
12. Lista de comprobación

## 1. Tablas administradas

Todas las tablas son **administradas por Unity Catalog**: se crean sin `LOCATION`.
Databricks las recomienda como tipo por defecto y varias optimizaciones solo existen
para ellas: optimización predictiva, clustering automático, ajuste automático del
tamaño de archivo y recuperación con `UNDROP` durante 7 días.

- Nunca `LOCATION` en un `CREATE TABLE`. Con `LOCATION` la tabla es externa y pierde
  todo lo anterior.
- Siempre con el nombre completo `catalogo.esquema.tabla`. Nunca por ruta: el acceso
  por ruta a una tabla administrada no está soportado.
- Los archivos crudos (Excel, JSON, CSV) van a un **volumen** administrado, no a una
  tabla ni a una ruta `abfss://`.
- Una tabla externa solo se justifica si otro sistema necesita leer los archivos
  directamente. Es una excepción que se documenta en el `COMMENT`.

## 2. Nombres

| Objeto | Patrón | Ejemplo |
|---|---|---|
| Catálogo | `{capa}_{ambiente}` | `bronze_dev`, `silver_prd`, `gold_prd` |
| Esquema bronze y silver | La fuente | `silver_prd.sharepoint`, `bronze_dev.oracle_ventas` |
| Esquema gold | El modelo o dominio de negocio | `gold_prd.modelo_pnl` |
| Tabla bronze y silver | `{dominio}`, sin prefijo de capa | `pedidos`, `eventos_actividad` |
| Hecho | `fac_{proceso}` y, si ayuda, su grano | `fac_ventas_cliente_mes` |
| Dimensión | `dim_{entidad}` | `dim_cliente` |
| Vista | `vw_{contenido}` | `vw_ventas_canal` |
| Vista de métricas | `mv_{indicador}` | `mv_usuarios_activos_mes` |
| Tabla de control | `ctr_{qué controla}` | `ctr_archivos_procesados` |
| Volumen | `raw` | `/Volumes/bronze_dev/sharepoint/raw/` |

- Minúsculas, guion bajo, sin tildes ni espacios, en español.
- La capa no se repite en el nombre de la tabla: ya la dice el catálogo.
- `fac_`, no `fact_`.
- Columnas en `snake_case` y en español desde silver. Bronze conserva los nombres de
  la fuente.
- Prefijos de columna: `id_` identificador, `codigo_` código de negocio, `fecha_`
  fecha, `es_` / `tiene_` booleano, `total_` / `cantidad_` / `monto_` medida.

## 3. Tipos de dato

| Uso | Tipo | Evitar |
|---|---|---|
| Importes, precios, costos | `DECIMAL(18,4)` salvo que el dominio pida otra precisión | `DOUBLE`, `FLOAT` |
| Pesos, volúmenes, cantidades con decimales | `DECIMAL(p,s)` | `DOUBLE`, `FLOAT` |
| Conteos | `INT` o `BIGINT` | `DOUBLE`, `STRING` |
| Latitud y longitud | `DOUBLE` | — |
| Fechas de negocio | `DATE` | `STRING` |
| Marcas de tiempo | `TIMESTAMP` | `STRING` |
| Códigos e identificadores | `STRING`, aunque parezcan números | `INT` (pierde ceros a la izquierda) |
| Sí o no | `BOOLEAN` | `STRING` con "S"/"N" |

- **Bronze: todo `STRING`.** Bronze guarda lo que llegó; tipar ahí hace fallar la
  carga cuando la fuente cambia. Se tipa en silver.
- `DOUBLE` y `FLOAT` nunca para valores donde la precisión importa: acumulan error
  de redondeo al sumar.

## 4. Comentarios y etiquetas

Databricks recomienda comentar todas las tablas y columnas: es lo que alimenta el
catálogo, la búsqueda y a los asistentes de IA.

- **`COMMENT` de tabla**: una o dos frases con el contenido, el **grano** (qué es una
  fila) y la fuente. No "tabla silver de ventas".
- **`COMMENT` en cada columna**, en la misma línea que el tipo: significado de
  negocio, unidad y, si ayuda, origen o fórmula.
- **Etiquetas** con `ALTER TABLE … SET TAGS`: las que pida el perfil de la empresa.
  Como mínimo, en gold, `capa` = `consumo` o `interno`.
- Los comentarios salen del análisis de los datos, no se inventan. Si no se conoce
  el significado de una columna, se pregunta.

## 5. Clustering: qué va en lugar de particionar

Databricks recomienda **liquid clustering para todas las tablas nuevas**; reemplaza
al particionado y a `ZORDER`. Para tablas de menos de 1 TB la guía es directa: no
particionar.

**Regla: `CLUSTER BY`, nunca `PARTITIONED BY`.** Hay dos formas:

| Forma | Cuándo |
|---|---|
| `CLUSTER BY AUTO` | **Por defecto.** Databricks elige y ajusta las claves según cómo se consulta la tabla |
| `CLUSTER BY (col1, col2)` | Cuando ya se sabe por qué columnas se filtra y se quiere fijar desde el primer día |

`CLUSTER BY AUTO` requiere tabla administrada, optimización predictiva activa y
Databricks Runtime 15.4 LTS o superior (serverless lo cumple). Si la tabla es muy
pequeña o se consulta poco, puede no elegir claves: es correcto, no las necesita.

Al fijar claves a mano:

- Elige las columnas por las que más se **filtra** o se **une**: la fecha del
  periodo, el código de cliente, el canal.
- Máximo cuatro; lo normal es una o dos. En tablas de menos de 10 TB, más claves
  empeoran los filtros por una sola columna.
- El orden no importa. Si dos columnas están muy correlacionadas, pon solo una.
- La clave debe estar entre las **primeras 32 columnas**, que son las que tienen
  estadísticas.
- En bronze, donde se carga y se lee por lote: `CLUSTER BY (fecha_ingesta)`.

Las claves se pueden cambiar después sin reescribir la tabla:
`ALTER TABLE t CLUSTER BY (nueva_col)` o `ALTER TABLE t CLUSTER BY AUTO`.

## 6. Lo que no se configura a mano

En una tabla administrada, Databricks ya hace estas tareas. Configurarlas a mano
no ayuda y en algunos casos desactiva el ajuste automático.

| No hagas | Por qué |
|---|---|
| `TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' …, 'delta.autoOptimize.autoCompact' …)` | El tamaño de archivo se ajusta solo en tablas administradas. La guía pide configuración por defecto |
| `delta.targetFileSize` | Fijarlo desactiva el ajuste automático por tamaño de tabla |
| Jobs o celdas con `OPTIMIZE` o `VACUUM` programados | La optimización predictiva los ejecuta. Databricks recomienda desactivar los programados |
| `ZORDER BY` | Lo reemplaza el clustering; no son compatibles |
| `ANALYZE TABLE` rutinario | Lo ejecuta la optimización predictiva |

Para comprobar que la optimización predictiva está activa (lo está por defecto):

```sql
DESCRIBE SCHEMA EXTENDED catalogo.esquema;  -- campo "Predictive Optimization"
```

Si aparece desactivada, avisa al usuario: la activa el dueño del catálogo o del
esquema con `ALTER SCHEMA … ENABLE PREDICTIVE OPTIMIZATION`.

`OPTIMIZE tabla FULL` a mano solo tiene sentido una vez, después de cambiar las
claves de una tabla que ya tiene datos.

## 7. Claves y restricciones

- `NOT NULL` en las columnas que forman la clave. Sí se valida al escribir.
- `PRIMARY KEY` y `FOREIGN KEY` en gold. En Unity Catalog son **informativas**: no
  se validan al escribir, pero documentan el modelo, las usan las herramientas de BI
  y el optimizador. La unicidad se garantiza en la carga y se comprueba con una
  validación.
- La clave de una dimensión con historia es una clave sustituta
  (`id_registro_cliente`); el identificador de negocio (`id_cliente`) se repite en
  cada versión.

## 8. Columnas de linaje

Dos columnas fijas, con estos nombres en todas las capas donde apliquen:

| Columna | Tipo | Contenido |
|---|---|---|
| `fecha_ingesta` | `DATE` | Fecha de negocio del lote: a qué día corresponde el dato extraído |
| `fecha_proceso` | `TIMESTAMP` | Momento en que se escribió la fila, en la zona horaria del perfil |

- Bronze y silver llevan las dos. Bronze añade `archivo_origen` (`STRING`) cuando
  viene de archivos.
- Gold lleva `fecha_proceso`. `fecha_ingesta` solo si el hecho se carga por lote.
- No se usan otros nombres (`fecha_carga`, `fecha_actualizacion`, `FECHA_INGESTA`).

## 9. Dónde vive el DDL

- Cada tabla se crea en un notebook de setup, `setup/tbl_{capa}_{tabla}.ipynb`, con
  `CREATE TABLE IF NOT EXISTS`. Se puede ejecutar muchas veces sin perder datos.
- El notebook de carga **no crea la tabla**: la da por existente. Así el esquema
  está escrito en un solo lugar y con sus comentarios.
- `CREATE OR REPLACE TABLE` no se usa: borra los datos y el historial.
- `DROP TABLE` nunca en un job.
- Un cambio de esquema se hace con `ALTER TABLE … ADD COLUMN` en el mismo notebook
  de setup, debajo del `CREATE`.
- `overwriteSchema` y `mergeSchema` no van en la carga rutinaria: un cambio de
  esquema silencioso en producción rompe a quien consume la tabla. La única
  excepción es bronze, que puede usar `mergeSchema` para aceptar columnas nuevas de
  la fuente.

```sql
CREATE TABLE IF NOT EXISTS gold_dev.ventas.fac_ventas_cliente_mes (
    anio              INT            NOT NULL COMMENT 'Año del periodo',
    mes               INT            NOT NULL COMMENT 'Mes del periodo, de 1 a 12',
    id_cliente        STRING         NOT NULL COMMENT 'Código del cliente en el ERP',
    venta_neta        DECIMAL(18,4)  COMMENT 'Venta neta en USD, después de descuentos',
    cantidad_kg       DECIMAL(18,4)  COMMENT 'Kilogramos vendidos',
    fecha_proceso     TIMESTAMP      COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    CONSTRAINT pk_fac_ventas_cliente_mes PRIMARY KEY (anio, mes, id_cliente),
    CONSTRAINT fk_ventas_cliente FOREIGN KEY (id_cliente)
        REFERENCES gold_dev.ventas.dim_cliente (id_cliente)
)
COMMENT 'Ventas mensuales por cliente. Grano: una fila por año, mes y cliente. Fuente: silver.erp.pedidos.'
CLUSTER BY AUTO;
```

No lleva `USING DELTA` (es el formato por defecto), ni `LOCATION`, ni
`PARTITIONED BY`, ni `TBLPROPERTIES` de optimización.

## 10. Estrategia de carga por capa

Toda carga debe poder **repetirse sin duplicar**: si el job falla y se relanza, el
resultado es el mismo.

| Capa | Estrategia | Cómo |
|---|---|---|
| Volumen | Un directorio por lote | `…/raw/{dominio}/fecha_ingesta=AAAA-MM-DD/` |
| Bronze | Añadir por lote, reemplazando el lote si ya existe | `replaceWhere` por `fecha_ingesta` |
| Silver | Reemplazar el lote, o fusionar por clave si la fuente trae cambios | `replaceWhere` o `MERGE` |
| Gold, hecho | Reemplazar el periodo recalculado | `replaceWhere` por periodo |
| Gold, dimensión | Reemplazo completo, o `MERGE` si guarda historia | `overwrite` o `MERGE` |

**Reemplazo selectivo.** Es atómico: borra y escribe en una sola transacción.
Sustituye al patrón `DELETE` seguido de `append`, que deja la tabla a medias si
falla entre los dos pasos.

```python
(
    df_lote.write
    .mode("overwrite")
    .option("replaceWhere", f"fecha_ingesta = '{fecha_ingesta}'")
    .saveAsTable(tabla_destino)
)
```

**Fusión por clave**, cuando llegan altas y cambios:

```python
(
    DeltaTable.forName(spark, tabla_destino).alias("destino")
    .merge(df_cambios.alias("origen"), "destino.id_pedido = origen.id_pedido")
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)
```

**Reemplazo completo**, solo para tablas pequeñas que se recalculan enteras:
`mode("overwrite")` sin `overwriteSchema`.

Reglas comunes:

- Escribe con `saveAsTable` o SQL sobre el nombre completo, nunca por ruta.
- Antes de escribir en silver o gold, valida lo que hace falta: claves sin nulos,
  sin duplicados, conteo distinto de cero.
- No hagas `df.count()` solo para imprimirlo si el DataFrame es caro de calcular:
  lee el conteo del historial de la tabla después de escribir.

## 11. Vistas

- `CREATE OR REPLACE VIEW`: una vista no guarda datos, reemplazarla es seguro.
- Sirven para exponer a consumo un subconjunto o un cálculo sobre gold.
- Llevan `COMMENT` como las tablas.

## 12. Lista de comprobación

- [ ] Sin `LOCATION`, sin `PARTITIONED BY`, sin `TBLPROPERTIES` de optimización
- [ ] `CREATE TABLE IF NOT EXISTS`, en un notebook `tbl_` de setup
- [ ] `CLUSTER BY AUTO` o claves justificadas, dentro de las primeras 32 columnas
- [ ] `COMMENT` de tabla con el grano, y `COMMENT` en todas las columnas
- [ ] `DECIMAL` en importes y medidas; bronze todo `STRING`
- [ ] `NOT NULL` en claves; `PRIMARY KEY` y `FOREIGN KEY` en gold
- [ ] `fecha_ingesta` y `fecha_proceso` donde corresponda
- [ ] Nombre sin prefijo de capa; `fac_` o `dim_` en gold
- [ ] La carga se puede repetir sin duplicar y no cambia el esquema
