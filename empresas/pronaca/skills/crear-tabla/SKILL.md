---
name: crear-tabla
description: "Crea una tabla administrada de Unity Catalog con el estándar común: genera el notebook de setup con el DDL completo (tipos, COMMENT en tabla y columnas, CLUSTER BY, claves y CHECK, propiedades con su comentario, dueño, etiquetas y clasificación de datos personales) para bronze, silver, hechos fac_ y dimensiones dim_, y gestiona los cambios de esquema. Usar siempre que el usuario pida crear una tabla, un hecho, una dimensión, un DDL, un CREATE TABLE, 'la tabla silver de X', 'modela esto en gold', agregar, renombrar o cambiar el tipo de una columna, o cuando pregunte cómo optimizar, clusterizar o si su DDL está bien hecho."
---

# Crear una tabla

Produce un notebook `tbl_` de setup con el DDL de la tabla. El DDL es el contrato:
se escribe una vez, con todos sus comentarios, y la carga nunca vuelve a definir el
esquema.

Las reglas están en `estandares-datos/references/tablas.md`: léelo antes de
escribir el DDL. Las plantillas por tipo de tabla están en
`references/plantillas-ddl.md` de esta skill. El grupo dueño y la clasificación de
datos personales están en el perfil de la empresa.

## Flujo de trabajo

### 0. Comprobar que las reglas siguen vigentes

Lee la fecha de "Última revisión de las reglas de tablas" en
`estandares-datos/references/fuentes.md` y su sección 9. Si se cumple alguna de las
condiciones de revisión (más de 6 meses, un runtime o función que no aparece, una
función del radar que pasó a GA), díselo al usuario en una línea y pregunta si se
actualiza la regla antes de seguir:

> "Las reglas de tablas se revisaron hace 7 meses y el CDF automático ya es GA.
> ¿Se revisa la regla de `enableChangeDataFeed` antes de crear la tabla?"

Si dice que no, sigue con las reglas actuales.

### 1. Reunir lo que define la tabla

Dedúcelo del código y de los datos; pregunta lo que falte, en una sola ronda.

| Dato | Cómo obtenerlo |
|---|---|
| Capa y tipo | Bronze, silver, hecho (`fac_`) o dimensión (`dim_`) |
| **Grano**: qué representa una fila | Lo define el negocio; si no está claro, pregunta. Sin grano no hay tabla |
| Columnas, con significado y unidad | Notebook que la carga, tabla de origen, archivo de la fuente |
| Clave: columnas que identifican una fila | El `GROUP BY` final, la clave del `MERGE`, la clave de la fuente |
| Reglas de dominio | Rangos y valores válidos: mes de 1 a 12, precio no negativo |
| Cómo se consulta: por qué columnas se filtra | Reportes, consultas existentes, el usuario |
| Si la dimensión guarda historia | Pregunta: ¿importa cómo era el registro en el pasado? |
| Columnas con datos personales | Nombres, cédulas, teléfonos, coordenadas de personas: clasifícalas con la tabla del perfil |
| Si algún sistema lee los archivos sin pasar por Databricks | Pregunta solo en silver y gold. Power BI no cuenta: lee a través de Databricks |
| Catálogo, esquema, dueño, etiquetas | Perfil de la empresa |

Si la tabla ya existe en el workspace y tienes acceso, mira su definición y una
muestra antes de proponer cambios.

### 2. Diseñar

Decide y, si hay algo no obvio, explícalo al usuario en una línea:

- **Nombre** según el patrón de `tablas.md` §2. Ninguna columna empieza con número.
- **Tipos**: `DECIMAL` para importes y medidas, `STRING` para códigos,
  `TIMESTAMP_NTZ` para la hora que trae la fuente, todo `STRING` en bronze.
- **Clave y restricciones**: `NOT NULL` en la clave, `CHECK` en las reglas de
  dominio, `PRIMARY KEY` y `FOREIGN KEY` en gold.
- **Clustering**: `CLUSTER BY AUTO` por defecto; claves explícitas solo si ya se
  sabe por qué columnas se filtra.
- **Propiedades**: en silver y gold, `columnMapping` y `enableTypeWidening`, cada
  una con su línea `--` que dice para qué sirve. Otras, solo las de `tablas.md` §7
  y con su motivo.
- **Datos personales**: la categoría de cada columna clasificada. Si alguna es
  sensible o de categoría especial, avísalo.
- **Linaje**: `fecha_ingesta` y `fecha_proceso` según la capa.

### 3. Generar el notebook de setup

Usa el script de la skill `crear-notebook`:

```bash
python3 <ruta_crear-notebook>/scripts/nuevo_notebook.py --tipo tbl \
    --tabla fac_ventas_cliente_mes --esquema ventas --capa gold \
    --carpeta <bundle>/src/ventas/setup --zona America/Guayaquil
```

El notebook tiene, en este orden:

1. `CREATE TABLE IF NOT EXISTS`, con la plantilla de `references/plantillas-ddl.md`
   y el orden de `tablas.md` §4.
2. Cambios de esquema (`ALTER … ADD COLUMNS` protegidos), si los hay.
3. Dueño: `ALTER TABLE … OWNER TO` con el grupo del perfil.
4. Etiquetas de la tabla y de cada columna con datos personales.

Sustituye todos los marcadores `PENDIENTE:`. Agrega el `tbl_` como **primera
tarea del job**, con la carga dependiendo de él (`tablas.md` §13).

### 4. Escribir los comentarios

Es la parte que más valor deja y la que más se descuida.

- **Tabla**: contenido, grano y fuente. El perímetro o filtro común va aquí, una
  vez. "Ventas mensuales por cliente. Grano: una fila por año, mes y cliente.
  Fuente: silver_prd.erp.pedidos."
- **Cada columna**: significado de negocio, unidad y, si ayuda, origen o fórmula.
- Impersonales, sin tutear, con tildes y sin comillas simples.
- Si no conoces el significado de una columna, pregunta. Un comentario inventado
  es peor que ninguno.

### 5. Comprobar

Repasa la lista de `tablas.md` §17 y ejecuta el revisor:

```bash
python3 <ruta_estandares-datos>/scripts/revisar_estandar.py <repo>
```

### 6. Entregar

Indica el notebook creado, el grano y la clave, la decisión de clustering y su
motivo, las columnas clasificadas como datos personales y lo que queda por
confirmar. No ejecutes el setup salvo que el usuario lo pida.

## Cambiar el esquema de una tabla existente

Cuando llega una columna nueva, o hay que renombrar o cambiar un tipo, sigue el
árbol de `tablas.md` §14. En resumen:

| Cambio | Dónde |
|---|---|
| Columna nueva | `ALTER … ADD COLUMNS` protegido en el mismo `tbl_`, y la columna también en el `CREATE` |
| Renombrar o borrar | Expandir y contraer, en varias entregas |
| Ampliar un tipo | `ALTER COLUMN … TYPE` (necesita `enableTypeWidening`) |
| Otro cambio de tipo o modelo rehecho | Notebook de migración `mig_`, que se ejecuta una vez; nunca en el `tbl_` |

Nunca propongas recrear la tabla para agregar una columna.

## Revisar u optimizar una tabla existente

1. Lee su DDL (el notebook `tbl_` o `SHOW CREATE TABLE`).
2. Compáralo con `tablas.md` §17.
3. Informa qué cumple y qué no, con el cambio concreto para cada punto.
4. Propón los cambios como `ALTER TABLE`, no como recreación:

| Hallazgo | Cambio |
|---|---|
| Sin clustering | `ALTER TABLE t CLUSTER BY AUTO` |
| Particionada | `ALTER TABLE t REPLACE PARTITIONED BY WITH CLUSTER BY AUTO` (Runtime 18.1 o superior); en versiones anteriores, recrear y recargar |
| Propiedades de optimización manuales | `ALTER TABLE t UNSET TBLPROPERTIES (…)` |
| Silver o gold sin las propiedades del estándar | `ALTER TABLE t SET TBLPROPERTIES ('delta.columnMapping.mode' = 'name', 'delta.enableTypeWidening' = 'true')` |
| Dueño es una persona | `ALTER TABLE t OWNER TO` el grupo del perfil |
| Columnas sin comentario | `ALTER TABLE t ALTER COLUMN c COMMENT '…'` |
| Datos personales sin etiquetar | `ALTER TABLE t ALTER COLUMN c SET TAGS ('dato_personal' = '…')` |
| Tabla externa (`LOCATION`) | Migrar a administrada es un proyecto aparte: explícalo, no lo hagas en el momento |
| `DOUBLE` en importes | Cambiar el tipo exige reescribir la tabla: proponlo, no lo ejecutes |

No ejecutes un `ALTER` sobre una tabla existente sin que el usuario lo confirme, y
nunca sobre producción desde un notebook de desarrollo.
