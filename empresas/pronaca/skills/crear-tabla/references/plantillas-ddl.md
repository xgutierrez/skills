# Plantillas de DDL

Cada plantilla va dentro de `spark.sql(f"""…""")` en el notebook `tbl_`, con
`{catalogo}` y `{esquema}` resueltos a partir del parámetro `ambiente`. Sustituye
los nombres y completa todos los comentarios.

Todas siguen el estándar común de `estandares-datos/references/tablas.md`: orden
de la DDL (§4), propiedades con su comentario en silver y gold (§7), dueño (§9) y
etiquetas (§10 y §11). Lo propio de cada capa se irá afinando en estas plantillas.

## Contenido

1. Bronze
2. Silver
3. Hecho (`fac_`)
4. Dimensión sin historia (`dim_`)
5. Dimensión con historia (SCD2)
6. Tabla de control
7. Vista de consumo
8. Dueño y etiquetas
9. Cambios de esquema

## 1. Bronze

Todo `STRING`, nombres de la fuente, tres columnas de linaje. Se agrupa por lote,
que es como se carga y se lee.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.pedidos (
    NumeroPedido   STRING  COMMENT 'Número de pedido, tal como llega de la fuente',
    CodigoCliente  STRING  COMMENT 'Código de cliente en el ERP',
    Importe        STRING  COMMENT 'Importe del pedido como texto; se tipa en silver',
    fecha_ingesta  DATE       NOT NULL COMMENT 'Fecha del lote extraído',
    fecha_proceso  TIMESTAMP  COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    archivo_origen STRING     COMMENT 'Ruta del archivo del volumen del que salió la fila'
)
COMMENT 'Pedidos del ERP sin transformar. Grano: una fila por línea del archivo de origen. Fuente: exportación diaria del ERP.'
CLUSTER BY (fecha_ingesta)
```

## 2. Silver

Tipos correctos, nombres en español, clave declarada como `NOT NULL`.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.pedidos (
    id_pedido      STRING         NOT NULL COMMENT 'Número de pedido en el ERP',
    id_cliente     STRING         NOT NULL COMMENT 'Código del cliente en el ERP',
    fecha_pedido   DATE           COMMENT 'Fecha en que se registró el pedido',
    estado         STRING         COMMENT 'Estado del pedido: ABIERTO, FACTURADO o ANULADO',
    monto_total    DECIMAL(18,4)  COMMENT 'Importe total del pedido en USD, con impuestos',
    cantidad_kg    DECIMAL(18,4)  COMMENT 'Kilogramos pedidos',
    es_urgente     BOOLEAN        COMMENT 'Verdadero si el pedido se marcó como urgente',
    fecha_ingesta  DATE           NOT NULL COMMENT 'Fecha del lote extraído',
    fecha_proceso  TIMESTAMP      COMMENT 'Momento de escritura de la fila (America/Guayaquil)'
)
COMMENT 'Pedidos del ERP limpios y tipados. Grano: una fila por pedido. Fuente: bronze.erp.pedidos.'
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Permite renombrar o borrar columnas sin recrear la tabla
    'delta.columnMapping.mode' = 'name',
    -- Permite ampliar el tipo de una columna (INT a BIGINT, más decimales) sin reescribir los datos
    'delta.enableTypeWidening' = 'true'
)
```

## 3. Hecho (`fac_`)

Claves de las dimensiones primero, después las medidas. Las medidas son aditivas
siempre que se pueda: los porcentajes y precios se calculan en la herramienta de
BI, no se guardan.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.fac_ventas_cliente_mes (
    anio            INT            NOT NULL COMMENT 'Año del periodo',
    mes             INT            NOT NULL COMMENT 'Mes del periodo, de 1 a 12',
    id_cliente      STRING         NOT NULL COMMENT 'Código del cliente; enlaza con dim_cliente',
    codigo_canal    STRING         NOT NULL COMMENT 'Código del canal comercial; enlaza con dim_canal',
    venta_bruta     DECIMAL(18,4)  COMMENT 'Venta bruta en USD, antes de descuentos',
    descuento       DECIMAL(18,4)  COMMENT 'Descuentos en factura y financieros, en USD',
    venta_neta      DECIMAL(18,4)  COMMENT 'Venta bruta menos descuento, en USD',
    cantidad_kg     DECIMAL(18,4)  COMMENT 'Kilogramos vendidos',
    total_pedidos   INT            COMMENT 'Número de pedidos del periodo',
    fecha_proceso   TIMESTAMP      COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    CONSTRAINT pk_fac_ventas_cliente_mes PRIMARY KEY (anio, mes, id_cliente, codigo_canal),
    CONSTRAINT fk_fac_ventas_cliente FOREIGN KEY (id_cliente)
        REFERENCES {catalogo}.{esquema}.dim_cliente (id_cliente)
)
COMMENT 'Ventas mensuales por cliente y canal. Grano: una fila por año, mes, cliente y canal. Fuente: silver.erp.pedidos.'
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Permite renombrar o borrar columnas sin recrear la tabla
    'delta.columnMapping.mode' = 'name',
    -- Permite ampliar el tipo de una columna (INT a BIGINT, más decimales) sin reescribir los datos
    'delta.enableTypeWidening' = 'true'
)
```

Si ya se sabe que casi todas las consultas filtran por periodo:
`CLUSTER BY (anio, mes)`.

## 4. Dimensión sin historia (`dim_`)

Una fila por entidad, con el valor vigente. Se recarga completa.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.dim_cliente (
    id_cliente      STRING     NOT NULL COMMENT 'Código del cliente en el ERP',
    nombre_cliente  STRING     COMMENT 'Razón social del cliente',
    codigo_canal    STRING     COMMENT 'Canal comercial al que pertenece',
    ciudad          STRING     COMMENT 'Ciudad de la dirección principal',
    es_activo       BOOLEAN    COMMENT 'Verdadero si el cliente está habilitado para comprar',
    fecha_proceso   TIMESTAMP  COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    CONSTRAINT pk_dim_cliente PRIMARY KEY (id_cliente)
)
COMMENT 'Clientes con sus atributos vigentes. Grano: una fila por cliente. Fuente: silver.erp.clientes.'
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Permite renombrar o borrar columnas sin recrear la tabla
    'delta.columnMapping.mode' = 'name',
    -- Permite ampliar el tipo de una columna (INT a BIGINT, más decimales) sin reescribir los datos
    'delta.enableTypeWidening' = 'true'
)
```

## 5. Dimensión con historia (SCD2)

Cada cambio de un atributo crea una fila nueva. Úsala solo si negocio necesita
saber cómo era el registro en una fecha pasada; cuesta más de cargar y de consultar.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.{esquema}.dim_cliente (
    id_registro_cliente    STRING     NOT NULL COMMENT 'Clave sustituta de esta versión del cliente',
    id_cliente             STRING     NOT NULL COMMENT 'Código del cliente en el ERP; se repite en cada versión',
    nombre_cliente         STRING     COMMENT 'Razón social del cliente',
    codigo_canal           STRING     COMMENT 'Canal comercial al que pertenecía en esta versión',
    fecha_inicio_vigencia  DATE       NOT NULL COMMENT 'Primer día en que esta versión es válida',
    fecha_fin_vigencia     DATE       COMMENT 'Último día de validez; vacío en la versión vigente',
    es_vigente             BOOLEAN    NOT NULL COMMENT 'Verdadero en la versión actual del cliente',
    fecha_proceso          TIMESTAMP  COMMENT 'Momento de escritura de la fila (America/Guayaquil)',
    CONSTRAINT pk_dim_cliente PRIMARY KEY (id_registro_cliente)
)
COMMENT 'Clientes con historia de cambios. Grano: una fila por cliente y periodo de vigencia. Fuente: silver.erp.clientes.'
CLUSTER BY (id_cliente)
TBLPROPERTIES (
    -- Permite renombrar o borrar columnas sin recrear la tabla
    'delta.columnMapping.mode' = 'name',
    -- Permite ampliar el tipo de una columna (INT a BIGINT, más decimales) sin reescribir los datos
    'delta.enableTypeWidening' = 'true'
)
```

Los hechos enlazan con `id_registro_cliente` para conservar la versión vigente en
el momento del hecho. La carga usa `MERGE`: cierra la versión anterior
(`es_vigente = false`, `fecha_fin_vigencia`) e inserta la nueva.

## 6. Tabla de control

Registra qué se procesó, para no repetirlo.

```sql
CREATE TABLE IF NOT EXISTS {catalogo}.control_ingesta.ctr_archivos_procesados (
    fuente          STRING     NOT NULL COMMENT 'Sistema de origen del archivo',
    nombre_archivo  STRING     NOT NULL COMMENT 'Nombre del archivo procesado',
    huella          STRING     COMMENT 'Hash del contenido, para detectar reenvíos modificados',
    fecha_ingesta   DATE       NOT NULL COMMENT 'Lote en el que se procesó',
    fecha_proceso   TIMESTAMP  COMMENT 'Momento de escritura de la fila (America/Guayaquil)'
)
COMMENT 'Archivos ya cargados por cada fuente. Grano: una fila por archivo y lote.'
CLUSTER BY (fuente, fecha_ingesta)
```

## 7. Vista de consumo

```sql
CREATE OR REPLACE VIEW {catalogo}.{esquema}.vw_ventas_canal
COMMENT 'Venta neta mensual por canal. Grano: una fila por año, mes y canal.'
AS
SELECT anio, mes, codigo_canal, SUM(venta_neta) AS venta_neta
FROM {catalogo}.{esquema}.fac_ventas_cliente_mes
GROUP BY anio, mes, codigo_canal
```

## 8. Dueño y etiquetas

Después del `CREATE`, en celdas aparte del mismo notebook. El grupo y los valores de
las etiquetas salen del perfil de la empresa.

```sql
ALTER TABLE {catalogo}.{esquema}.fac_ventas_cliente_mes OWNER TO `{grupo_dueno}`
```

```sql
ALTER TABLE {catalogo}.{esquema}.fac_ventas_cliente_mes SET TAGS ('capa' = 'consumo')
```

Si la tabla tiene columnas con datos personales, una etiqueta por columna y otra en
la tabla:

```sql
ALTER TABLE {catalogo}.{esquema}.dim_cliente ALTER COLUMN telefono
SET TAGS ('dato_personal' = 'identificativo')
```

```sql
ALTER TABLE {catalogo}.{esquema}.dim_cliente SET TAGS ('dato_personal' = 'si')
```

## 9. Cambios de esquema

Debajo del `CREATE`, en el mismo notebook `tbl_`, para que el archivo siga siendo
la definición completa de la tabla. El árbol de decisión está en `tablas.md` §14.

```python
columnas = set(spark.table(tabla).columns)
if "codigo_vendedor" not in columnas:
    spark.sql(f"""
        ALTER TABLE {tabla} ADD COLUMNS (
            codigo_vendedor STRING COMMENT 'Vendedor que registró el pedido'
        )
    """)
    print(f"[OK] Columna agregada: {tabla}.codigo_vendedor")
```

Actualiza también el `CREATE` con la columna nueva, para que un ambiente que se
crea desde cero quede igual que uno migrado.

Una tabla creada antes del estándar se alinea sin recrearla:

```sql
ALTER TABLE {catalogo}.{esquema}.pedidos SET TBLPROPERTIES (
    'delta.columnMapping.mode' = 'name',
    'delta.enableTypeWidening' = 'true'
)
```
