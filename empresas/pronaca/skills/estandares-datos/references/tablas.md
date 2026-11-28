# Tablas: estándar común de diseño, creación y evolución

Reglas que aplican a toda tabla, sin importar la capa. Lo propio de bronze, silver
y gold se afina en las plantillas de `crear-tabla`. El origen de cada regla está en
`fuentes.md`, sección 2.

## Contenido

1. Tablas administradas
2. Nombres
3. Tipos de dato
4. Estructura de la DDL
5. Comentarios
6. Clustering
7. Propiedades de la tabla
8. Claves y restricciones
9. Dueño de la tabla
10. Datos personales
11. Etiquetas
12. Columnas de linaje
13. Dónde vive la DDL y cuándo se ejecuta
14. Evolución del esquema
15. Estrategia de carga por capa
16. Vistas
17. Lista de comprobación

## 1. Tablas administradas

Todas las tablas son **administradas por Unity Catalog**: se crean sin `LOCATION`.
Solo ellas tienen optimización predictiva, clustering automático, ajuste del tamaño
de archivo y recuperación con `UNDROP` durante 7 días.

- Nunca `LOCATION` en un `CREATE TABLE`.
- Siempre con el nombre completo `catalogo.esquema.tabla`. Nunca por ruta.
- Los archivos crudos (Excel, JSON, CSV) van a un **volumen** administrado.
- Una tabla externa solo se justifica si otro sistema lee los archivos directamente.
  Es una excepción que se documenta en el `COMMENT`.

## 2. Nombres

| Objeto | Patrón | Ejemplo |
|---|---|---|
| Catálogo | `{capa}_{ambiente}` | `bronze_dev`, `silver_prd`, `gold_prd` |
| Esquema bronze y silver | La fuente | `silver_prd.sharepoint` |
| Esquema gold | El modelo o dominio de negocio | `gold_prd.modelo_pnl` |
| Tabla bronze y silver | `{dominio}`, sin prefijo de capa | `pedidos` |
| Hecho | `fac_{proceso}` y, si ayuda, su grano | `fac_ventas_cliente_mes` |
| Dimensión | `dim_{entidad}` | `dim_cliente` |
| Vista | `vw_{contenido}` | `vw_ventas_canal` |
| Vista de métricas | `mv_{indicador}` | `mv_usuarios_activos_mes` |
| Tabla de control | `ctr_{qué controla}` | `ctr_archivos_procesados` |
| Volumen | `raw` | `/Volumes/bronze_dev/sharepoint/raw/` |
| Restricción | `pk_{tabla}`, `fk_{tabla}_{referida}`, `ck_{tabla}_{regla}` | `ck_fac_ventas_mes_valido` |

- Minúsculas, guion bajo, sin tildes ni espacios, en español.
- La capa no se repite en el nombre: ya la dice el catálogo. `fac_`, no `fact_`.
- Columnas en `snake_case` y en español desde silver. Bronze conserva los nombres
  de la fuente.
- Prefijos de columna: `id_` identificador, `codigo_` código de negocio, `fecha_`
  fecha, `es_` / `tiene_` booleano, `total_` / `cantidad_` / `monto_` medida.
- **Un nombre de columna no empieza con número.** Obliga a escribirlo entre
  comillas invertidas en todo SQL. El número de una línea de reporte va en el
  `COMMENT`:

  ```sql
  `04_unidad_comun_kg`  DECIMAL(18,4)            -- no
  unidad_comun_kg       DECIMAL(18,4) COMMENT 'Línea 04 del P&L. Kilogramos…'  -- sí
  ```

## 3. Tipos de dato

| Uso | Tipo | Evitar |
|---|---|---|
| Importes, precios, costos | `DECIMAL(18,4)` salvo que el dominio pida otra precisión | `DOUBLE`, `FLOAT` |
| Pesos, volúmenes, cantidades con decimales | `DECIMAL(p,s)` | `DOUBLE`, `FLOAT` |
| Conteos | `INT` o `BIGINT` | `DOUBLE`, `STRING` |
| Latitud y longitud | `DOUBLE` | — |
| Fechas de negocio | `DATE` | `STRING` |
| Momento del proceso | `TIMESTAMP` | `STRING` |
| Fecha y hora tal como la trae la fuente, sin zona | `TIMESTAMP_NTZ` | `TIMESTAMP` (la reinterpreta según la zona de sesión) |
| Códigos e identificadores | `STRING`, aunque parezcan números | `INT` (pierde ceros a la izquierda) |
| Sí o no | `BOOLEAN` | `STRING` con "S"/"N" |

- **Bronze: todo `STRING`.** Se tipa en silver.
- `DOUBLE` y `FLOAT` acumulan error de redondeo al sumar.

## 4. Estructura de la DDL

Toda DDL sigue el mismo orden, para que cualquier tabla se lea igual:

1. **Columnas**: clave del grano, atributos o dimensiones, medidas, linaje.
2. **Restricciones**: `pk_`, `fk_`, `ck_`.
3. **`COMMENT`** de la tabla.
4. **`CLUSTER BY`**.
5. **`TBLPROPERTIES`**: solo las de la sección 7, cada una con una línea `--` que
   dice para qué sirve.
6. Después del `CREATE`, en celdas aparte: **dueño** (sección 9) y **etiquetas**
   (secciones 10 y 11).

Formato: palabras clave en mayúsculas, una columna por línea, nombre, tipo y
`COMMENT` alineados. No se escribe `USING DELTA` (es el formato por defecto).

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.fac_ventas_cliente_mes (
    anio           INT            NOT NULL COMMENT 'Año del periodo',
    mes            INT            NOT NULL COMMENT 'Mes del periodo, de 1 a 12',
    id_cliente     STRING         NOT NULL COMMENT 'Código del cliente en el ERP; enlaza con dim_cliente',
    venta_neta     DECIMAL(18,4)  COMMENT 'Venta neta en USD, después de descuentos',
    cantidad_kg    DECIMAL(18,4)  COMMENT 'Kilogramos vendidos',
    fecha_proceso  TIMESTAMP      COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    CONSTRAINT pk_fac_ventas_cliente_mes PRIMARY KEY (anio, mes, id_cliente),
    CONSTRAINT fk_fac_ventas_cliente_mes_dim_cliente FOREIGN KEY (id_cliente)
        REFERENCES {catalogo}.{esquema}.dim_cliente (id_cliente),
    CONSTRAINT ck_fac_ventas_cliente_mes_mes_valido CHECK (mes BETWEEN 1 AND 12)
)
COMMENT 'Ventas mensuales por cliente. Grano: una fila por año, mes y cliente. Fuente: silver_prd.erp.pedidos.'
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Permite renombrar o borrar columnas sin recrear la tabla
    'delta.columnMapping.mode' = 'name',
    -- Permite ampliar el tipo de una columna (INT a BIGINT, más decimales) sin reescribir los datos
    'delta.enableTypeWidening' = 'true'
)
```

## 5. Comentarios

Alimentan el catálogo, la búsqueda, Genie y a los asistentes de IA.

- **`COMMENT` de tabla**, en tres partes: qué contiene, el **grano** (qué es una
  fila) y la fuente. Un filtro o perímetro que aplica a toda la tabla va aquí, una
  sola vez, no repetido en cada columna.
- **`COMMENT` en cada columna**, en la misma línea que el tipo: significado de
  negocio, unidad y, si ayuda, origen o fórmula.
- Tono impersonal, sin tutear: "Venta neta en USD", no "Usa esta columna para…".
- Con tildes. Sin comillas simples dentro del texto: rompen el SQL.
- Salen del análisis de los datos. Si no se conoce el significado de una columna,
  se pregunta. Un comentario inventado es peor que ninguno.
- Cambiar un comentario ejecuta un `ALTER`, que choca con las escrituras en curso:
  se hace con el job detenido o entre ejecuciones.

## 6. Clustering

**`CLUSTER BY`, nunca `PARTITIONED BY` ni `ZORDER`.**

| Forma | Cuándo |
|---|---|
| `CLUSTER BY AUTO` | **Por defecto.** Databricks elige las claves según cómo se consulta la tabla |
| `CLUSTER BY (col1, col2)` | Cuando ya se sabe por qué columnas se filtra o se une |

Al fijar claves a mano: máximo cuatro (lo normal es una o dos), dentro de las
**primeras 32 columnas**, y si dos columnas están muy correlacionadas, solo una.
Las claves se cambian después sin reescribir: `ALTER TABLE t CLUSTER BY AUTO`.

## 7. Propiedades de la tabla

**Regla: los valores por defecto de Databricks no se tocan. Las propiedades
funcionales sí, cada una con su línea de comentario.**

| Propiedad | Uso | Para qué sirve |
|---|---|---|
| `delta.columnMapping.mode = 'name'` | **Silver y gold, al crear** | Permite renombrar o borrar columnas sin recrear la tabla |
| `delta.enableTypeWidening = 'true'` | **Silver y gold, al crear** | Permite ampliar el tipo de una columna sin reescribir los datos |
| `delta.enableChangeDataFeed = 'true'` | Solo si un proceso lee los cambios de forma incremental | Registra qué filas se insertaron, cambiaron o borraron en cada versión |
| `delta.enableRowTracking = 'true'` | Solo si una vista materializada se refresca en incremental | Da un identificador estable a cada fila |
| `delta.logRetentionDuration` | Solo si se necesita consultar versiones de más de 30 días | Conserva el historial más tiempo; cuesta almacenamiento |

Lo que **no** se configura nunca:

| Propiedad u operación | Por qué |
|---|---|
| `delta.autoOptimize.*`, `delta.targetFileSize` | La tabla administrada ajusta sola el tamaño de archivo; fijarlo desactiva el ajuste |
| `OPTIMIZE`, `VACUUM`, `ANALYZE` programados | Los ejecuta la optimización predictiva |
| `delta.minReaderVersion`, `delta.minWriterVersion` | Databricks pide no fijarlos a mano |
| `delta.appendOnly` | Bloquea el reemplazo por lote (`replaceWhere`) que usa la carga |

Activar una propiedad funcional sube el protocolo de la tabla y casi nunca se puede
deshacer. Power BI lee a través de Databricks, así que no le afecta. Antes de
activarla, se pregunta si algún sistema lee los archivos de la tabla directamente,
sin pasar por Databricks.

## 8. Claves y restricciones

| Restricción | ¿Se valida al escribir? | Uso |
|---|---|---|
| `NOT NULL` | Sí: la escritura falla | Columnas de la clave del grano |
| `CHECK (expresión)` | Sí: la escritura falla | Reglas de dominio: `mes BETWEEN 1 AND 12`, `precio >= 0` |
| `PRIMARY KEY`, `FOREIGN KEY` | No, son informativas | Gold. Documentan el modelo; las usan Power BI y el optimizador |

- La unicidad de la clave se garantiza en la carga y se comprueba con una
  validación, porque la `PRIMARY KEY` no la impide.
- La clave de una dimensión con historia es una **clave sustituta** calculada con
  un hash de la clave de negocio y el inicio de vigencia (`sha2`, `xxhash64`). Es
  determinista: al recargar se obtiene el mismo valor. No se usan columnas
  `IDENTITY`, porque impiden las escrituras concurrentes y cambian al recargar.

## 9. Dueño de la tabla

El dueño es **un grupo, nunca una persona**: si alguien deja la empresa, la tabla
sigue administrada. El nombre del grupo está en el perfil de la empresa.

```sql
ALTER TABLE {catalogo}.{esquema}.{tabla} OWNER TO `{grupo_dueno}`
```

- Va en el notebook de setup, debajo del `CREATE`. Repetirlo no cambia nada.
- La identidad que ejecuta el job (el *service principal*) tiene que pertenecer al
  grupo o tener `MANAGE` sobre la tabla. Si no, pierde el permiso al ceder la
  propiedad, y el siguiente `ALTER` del setup falla.

## 10. Datos personales

Se clasifica toda columna que identifique o haga identificable a una persona
natural, según la ley de protección de datos del país. La nomenclatura (la
etiqueta y sus valores) está en el perfil de la empresa, que la toma de la ley.

- **Columna**: etiqueta con la categoría del dato.

  ```sql
  ALTER TABLE {tabla} ALTER COLUMN encuestador SET TAGS ('dato_personal' = 'identificativo')
  ```

- **Tabla**: si tiene al menos una columna clasificada, etiqueta de tabla que lo
  dice, para encontrarlas todas en el catálogo.
- **Minimización**: no se cargan columnas personales que el caso de uso no
  necesita. Si solo hacen falta para unir tablas, se guarda un hash
  (seudonimización) en lugar del valor.
- Una columna clasificada como sensible o de una categoría especial se avisa al
  usuario: puede necesitar una máscara (`ALTER COLUMN … SET MASK`) o un filtro de
  filas, que se definen con el área de seguridad.
- La clasificación final la confirma el responsable de protección de datos de la
  empresa. La skill propone; no decide sobre un caso dudoso.

## 11. Etiquetas

- Las que pida el perfil de la empresa, por capa y para datos personales.
- Claves en minúsculas con guion bajo. No admiten `. , - = / :`.
- Máximo 50 por objeto. Se guardan como texto plano: nunca un dato sensible en el
  valor.
- Cada columna se etiqueta en su propio `ALTER`.
- Si el administrador de la cuenta crea la etiqueta como *governed tag*, Databricks
  restringe los valores a los admitidos.

## 12. Columnas de linaje

| Columna | Tipo | Contenido |
|---|---|---|
| `fecha_ingesta` | `DATE` | Fecha de negocio del lote: a qué día corresponde el dato extraído |
| `fecha_proceso` | `TIMESTAMP` | Momento en que se escribió la fila, en la zona horaria del perfil |

- Bronze y silver llevan las dos. Bronze añade `archivo_origen` cuando viene de
  archivos. Gold lleva `fecha_proceso`, y `fecha_ingesta` solo si se carga por lote.
- No se usan otros nombres (`fecha_carga`, `fecha_actualizacion`, `FECHA_INGESTA`).
- El detalle por capa se define en las plantillas de `crear-tabla`.

## 13. Dónde vive la DDL y cuándo se ejecuta

- Cada tabla tiene su notebook de setup, `src/{flujo}/setup/tbl_{capa}_{tabla}.ipynb`,
  con `CREATE TABLE IF NOT EXISTS`, dueño, etiquetas y los cambios de esquema.
- **El notebook `tbl_` es la primera tarea del job**, y la carga depende de él. Se
  despliega con el bundle, así que producción queda igual que desarrollo sin pasos
  a mano. Si la tabla ya existe y no hay cambios, termina en segundos.

  ```yaml
  tasks:
    - task_key: tbl_slv_precios_cerdo
    - task_key: slv_precios_cerdo
      depends_on:
        - task_key: tbl_slv_precios_cerdo
  ```

- El notebook de carga **no crea la tabla** ni cambia su esquema.
- Los bundles no pueden declarar tablas. Un esquema o un volumen se declaran en el
  bundle solo si ese bundle es su único dueño: un `bundle destroy` los borra. Si el
  esquema es compartido (por ejemplo `sharepoint`), se crea en el setup con
  `CREATE SCHEMA IF NOT EXISTS … COMMENT`.
- Un setup no crea catálogos: los administra la plataforma.
- `DROP TABLE` nunca en un job.

## 14. Evolución del esquema

**Una columna nueva nunca obliga a recrear la tabla.** Según el cambio:

| Cambio | Qué se hace |
|---|---|
| Bronze recibe una columna nueva de la fuente | Se acepta sola (`mergeSchema`, o Auto Loader con `addNewColumns` o `rescue`). Bronze guarda lo que llega |
| Columna nueva en silver o gold | `ALTER TABLE … ADD COLUMNS (… COMMENT …)` en el notebook `tbl_`, protegido para que la segunda ejecución no falle. Solo cambia metadatos. Se agrega también al `CREATE` |
| Renombrar o borrar una columna | Patrón **expandir y contraer**: se agrega la columna nueva, se cargan las dos, se cambian los consumidores (Power BI, vistas) y después se borra la vieja. Necesita `columnMapping` |
| Ampliar un tipo (`INT` a `BIGINT`, más precisión en `DECIMAL`, `DATE` a `TIMESTAMP_NTZ`) | `ALTER TABLE … ALTER COLUMN … TYPE …`. Necesita `enableTypeWidening`; no reescribe datos |
| Cualquier otro cambio de tipo | Reescritura con `overwriteSchema` en un notebook de migración aparte (`mig_`), que se ejecuta una vez, con aviso a los consumidores |
| El modelo se rehízo por completo | `CREATE OR REPLACE TABLE` planificado, en un notebook de migración. Conserva el historial, los permisos y las máscaras. **Nunca** `DROP TABLE` seguido de `CREATE` |

```python
columnas = set(spark.table(tabla).columns)
if "codigo_vendedor" not in columnas:
    spark.sql(f"""
        ALTER TABLE {tabla} ADD COLUMNS (
            codigo_vendedor STRING COMMENT 'Vendedor que registró el pedido'
        )
    """)
```

- `CREATE OR REPLACE TABLE` no va en el setup rutinario: se ejecutaría en cada
  corrida.
- `mergeSchema` y `overwriteSchema` no van en la carga rutinaria de silver ni gold:
  un cambio silencioso rompe a quien consume la tabla.
- Un cambio de esquema choca con las escrituras en curso y corta los streams que
  leen la tabla: se hace con el job detenido.
- Una tabla creada antes de este estándar se alinea con
  `ALTER TABLE … SET TBLPROPERTIES (…)`, sin recrearla.

## 15. Estrategia de carga por capa

Toda carga debe poder **repetirse sin duplicar**.

| Capa | Estrategia | Cómo |
|---|---|---|
| Volumen | Un directorio por lote | `…/raw/{dominio}/fecha_ingesta=AAAA-MM-DD/` |
| Bronze | Añadir por lote, reemplazando el lote si ya existe | `replaceWhere` por `fecha_ingesta` |
| Silver | Reemplazar el lote, o fusionar por clave si la fuente trae cambios | `replaceWhere` o `MERGE` |
| Gold, hecho | Reemplazar el periodo recalculado | `replaceWhere` por periodo |
| Gold, dimensión | Reemplazo completo, o `MERGE` si guarda historia | `overwrite` o `MERGE` |

```python
(
    df_lote.write
    .mode("overwrite")
    .option("replaceWhere", f"fecha_ingesta = '{fecha_ingesta}'")
    .saveAsTable(tabla_destino)
)
```

- El reemplazo selectivo es atómico y sustituye a `DELETE` seguido de `append`.
- Se escribe con `saveAsTable` o SQL sobre el nombre completo, nunca por ruta.
- Antes de escribir en silver o gold se valida: clave sin nulos, sin duplicados,
  conteo distinto de cero.

## 16. Vistas

- `CREATE OR REPLACE VIEW`: una vista no guarda datos, reemplazarla es seguro.
- Llevan `COMMENT` y dueño como las tablas.

## 17. Lista de comprobación

- [ ] `CREATE TABLE IF NOT EXISTS`, nombre completo, en un notebook `tbl_` que es la primera tarea del job
- [ ] Sin `LOCATION`, `PARTITIONED BY`, `USING DELTA` ni propiedades de optimización
- [ ] Orden: columnas, restricciones, `COMMENT`, `CLUSTER BY`, `TBLPROPERTIES`
- [ ] `CLUSTER BY AUTO` o claves justificadas dentro de las primeras 32 columnas
- [ ] `COMMENT` de tabla con contenido, grano y fuente; `COMMENT` en todas las columnas, impersonal
- [ ] Ninguna columna empieza con número
- [ ] `DECIMAL` en importes y medidas; bronze todo `STRING`
- [ ] `NOT NULL` en la clave; `CHECK` en reglas de dominio; `PRIMARY KEY` y `FOREIGN KEY` en gold
- [ ] Silver y gold con `columnMapping` y `enableTypeWidening`, cada una con su comentario
- [ ] Dueño: el grupo del perfil
- [ ] Columnas con datos personales etiquetadas; etiquetas del perfil aplicadas
- [ ] `fecha_ingesta` y `fecha_proceso` donde corresponda
- [ ] Un cambio de esquema es un `ALTER` protegido en el mismo `tbl_`, no una recreación
