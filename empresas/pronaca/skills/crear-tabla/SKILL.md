---
name: crear-tabla
description: "Crea una tabla administrada de Unity Catalog bien diseñada y optimizada: genera el notebook de setup con el DDL completo (tipos correctos, COMMENT en tabla y columnas, CLUSTER BY, claves, linaje y etiquetas) para bronze, silver, hechos fac_ y dimensiones dim_. Usar siempre que el usuario pida crear una tabla, un hecho, una dimensión, un DDL, un CREATE TABLE, 'la tabla silver de X', 'modela esto en gold', o cuando pregunte cómo optimizar, particionar o clusterizar una tabla, o si su DDL está bien hecho."
---

# Crear una tabla

Produce un notebook `tbl_` de setup con el DDL de la tabla. El DDL se escribe una
vez, con todos sus comentarios, y la carga nunca vuelve a definir el esquema.

Las reglas están en la skill `estandares-datos`, archivo `references/tablas.md`:
léelo antes de escribir el DDL. Las plantillas por tipo de tabla están en
`references/plantillas-ddl.md` de esta skill.

## Flujo de trabajo

### 1. Reunir lo que define la tabla

No se puede diseñar una tabla sin estos datos. Dedúcelos del código y de los datos;
pregunta lo que falte, en una sola ronda.

| Dato | Cómo obtenerlo |
|---|---|
| Capa y tipo | Bronze, silver, hecho (`fac_`) o dimensión (`dim_`) |
| **Grano**: qué representa una fila | Lo define el negocio; si no está claro, pregunta. Sin grano no hay tabla |
| Columnas, con significado y unidad | Notebook que la carga, tabla de origen, archivo de la fuente |
| Clave: columnas que identifican una fila | El `GROUP BY` final, la clave del `MERGE`, la clave de la fuente |
| Cómo se consulta: por qué columnas se filtra | Reportes, consultas existentes, el usuario |
| Si la dimensión guarda historia | Pregunta: ¿importa cómo era el registro en el pasado? |
| Catálogo, esquema, etiquetas | Perfil de la empresa en `estandares-datos` |

Si la tabla ya existe en el workspace y tienes acceso, mira su definición y una
muestra antes de proponer cambios.

### 2. Diseñar

Decide y, si hay algo no obvio, explícalo al usuario en una línea:

- **Nombre** según el patrón: sin prefijo de capa; `fac_` o `dim_` en gold.
- **Tipos**: `DECIMAL` para importes y medidas, `STRING` para códigos, todo `STRING`
  en bronze.
- **Clave**: `NOT NULL` en sus columnas; `PRIMARY KEY` y `FOREIGN KEY` en gold.
- **Clustering**: `CLUSTER BY AUTO` por defecto. Claves explícitas solo si ya se
  sabe por qué columnas se filtra, con un máximo de cuatro y dentro de las primeras
  32 columnas. En bronze, `CLUSTER BY (fecha_ingesta)`.
- **Linaje**: `fecha_ingesta` y `fecha_proceso` según la capa.
- **Orden de columnas**: claves primero, después atributos, medidas y linaje.

No añadas `LOCATION`, `PARTITIONED BY`, `USING DELTA` ni `TBLPROPERTIES` de
optimización: en una tabla administrada Databricks ya se encarga, y fijarlos a mano
desactiva el ajuste automático.

### 3. Generar el notebook de setup

Usa el script de la skill `crear-notebook`:

```bash
python3 <ruta_crear-notebook>/scripts/nuevo_notebook.py --tipo tbl \
    --tabla fac_ventas_cliente_mes --esquema ventas --capa gold \
    --carpeta <bundle>/src/ventas/setup --zona America/Guayaquil
```

Completa el `CREATE TABLE` con la plantilla que corresponda de
`references/plantillas-ddl.md` y sustituye todos los marcadores `PENDIENTE:`.

Si ya existe un notebook `tbl_` para ese flujo y capa, añade la tabla allí en lugar
de crear otro archivo.

### 4. Escribir los comentarios

Es la parte que más valor deja y la que más se descuida.

- **Tabla**: contenido, grano y fuente. "Ventas mensuales por cliente. Grano: una
  fila por año, mes y cliente. Fuente: silver.erp.pedidos."
- **Cada columna**: significado de negocio, unidad y, si ayuda, origen o fórmula.
  "Venta neta en USD, después de descuentos en factura y financieros."
- Sin comillas simples dentro del texto del `COMMENT`; rompen el SQL.
- Si no conoces el significado de una columna, pregunta. Un comentario inventado
  es peor que ninguno.

### 5. Comprobar

- [ ] `CREATE TABLE IF NOT EXISTS`, con nombre completo `catalogo.esquema.tabla`
- [ ] Sin `LOCATION`, `PARTITIONED BY` ni `TBLPROPERTIES` de optimización
- [ ] `CLUSTER BY AUTO` o claves justificadas
- [ ] `COMMENT` de tabla con el grano y `COMMENT` en todas las columnas
- [ ] Sin `DOUBLE` ni `FLOAT` salvo coordenadas
- [ ] `NOT NULL` en la clave; claves primaria y foránea en gold
- [ ] Linaje con los nombres estándar
- [ ] Sin marcadores `PENDIENTE:`

```bash
python3 <ruta_estandares-datos>/scripts/revisar_estandar.py <repo>
```

### 6. Entregar

Indica el notebook creado, el grano y la clave elegidos, la decisión de clustering
y su motivo, y lo que queda por confirmar. Recuerda al usuario que el setup se
ejecuta una vez por ambiente antes de la primera carga. No lo ejecutes tú salvo que
lo pida.

## Revisar u optimizar una tabla existente

Cuando el usuario pregunte si una tabla está bien hecha o cómo optimizarla:

1. Lee su DDL (el notebook `tbl_` o `SHOW CREATE TABLE`).
2. Compáralo con la lista del paso 5 y con `estandares-datos/references/tablas.md`.
3. Informa qué cumple y qué no, con el cambio concreto para cada punto.
4. Propón los cambios como `ALTER TABLE`, no como recreación:

| Hallazgo | Cambio |
|---|---|
| Sin clustering | `ALTER TABLE t CLUSTER BY AUTO` |
| Particionada | `ALTER TABLE t REPLACE PARTITIONED BY WITH CLUSTER BY AUTO` (Runtime 18.1 o superior); en versiones anteriores, recrear y recargar |
| Propiedades de optimización manuales | `ALTER TABLE t UNSET TBLPROPERTIES (…)` |
| Columnas sin comentario | `ALTER TABLE t ALTER COLUMN c COMMENT '…'` |
| Tabla externa (`LOCATION`) | Migrar a administrada es un proyecto aparte: explícalo, no lo hagas en el momento |
| `DOUBLE` en importes | Cambiar el tipo exige reescribir la tabla: proponlo, no lo ejecutes |

No ejecutes un `ALTER` sobre una tabla existente sin que el usuario lo confirme, y
nunca sobre producción desde un notebook de desarrollo.
