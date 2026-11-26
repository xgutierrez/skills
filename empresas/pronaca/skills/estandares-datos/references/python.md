# Python: funciones, UDF, mensajes y errores

## Contenido

1. Estilo (PEP 8)
2. Nombres
3. Tipos (PEP 484)
4. Docstrings (PEP 257)
5. Diseño de funciones
6. UDF
7. Mensajes de log
8. Errores
9. Comentarios
10. Ejemplo completo

## 1. Estilo (PEP 8)

- Sangría de 4 espacios, sin tabuladores.
- Líneas de hasta 79 caracteres en Python. Un literal SQL, HTML o una ruta larga
  puede pasarse: partirlo lo hace menos legible.
- Dos líneas en blanco antes de una función de nivel superior.
- Imports al inicio, en tres grupos separados por una línea en blanco: biblioteca
  estándar, terceros, PySpark. Un import por línea. Sin `import *`.
- Comparaciones con `None` usando `is` / `is not`.
- Sin código comentado ni celdas muertas.

```python
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
```

`functions` se importa siempre como `F` y `types` como `T`.

## 2. Nombres

| Elemento | Forma | Ejemplo |
|---|---|---|
| Variables y funciones | `snake_case`, en español | `fecha_corte`, `leer_archivo_excel` |
| Constantes | `MAYUSCULAS_CON_GUION` | `ZONA_HORARIA`, `COLUMNAS_CLAVE` |
| Clases | `PalabrasJuntas` | `ClienteApi` |
| DataFrames | prefijo `df_` y qué contienen | `df_ventas_limpias` |
| Booleanos | `es_`, `tiene_`, `debe_` | `es_reproceso` |

- Una función se llama con un verbo que dice qué devuelve o qué hace:
  `obtener_`, `leer_`, `calcular_`, `construir_`, `validar_`, `escribir_`.
- Sin nombres de una letra ni abreviaturas opacas (`df1`, `tmp`, `ctx`, `aux`).
- El prefijo `_` marca solo lo que de verdad es interno de un módulo de utilidades.

## 3. Tipos (PEP 484)

Todas las funciones llevan tipos en cada argumento y en el retorno. Dicen qué
espera la función sin abrirla, y permiten que el editor y los agentes detecten
errores antes de ejecutar.

```python
def filtrar_periodo(df: DataFrame, anio: int, mes: int | None = None) -> DataFrame:
```

- Usa los tipos nativos: `list[str]`, `dict[str, int]`, `tuple[str, ...]`,
  `str | None`. No hace falta importar `List` ni `Optional` de `typing`.
- Una función que no devuelve nada declara `-> None`.

## 4. Docstrings (PEP 257)

PEP 257 es la norma oficial de Python. Define el contenido y la estructura; no
impone un formato para listar argumentos.

**Lo que exige PEP 257:**

- Comillas triples dobles: `"""…"""`.
- Primera línea: un resumen en **imperativo**, que cabe en una línea y termina en
  punto. En español: "Devuelve…", "Calcula…", "Escribe…". No "Esta función devuelve…".
- Si hace falta más, una línea en blanco y después el detalle.
- El docstring de una función documenta su comportamiento, sus argumentos, lo que
  devuelve, sus efectos secundarios y las excepciones que lanza.
- El resumen no repite la firma.

**Decisión propia para el formato de los argumentos:** secciones `Args:`,
`Returns:` y `Raises:`. Es la disposición más compacta, la reconocen los editores y
ya es la que usan los repositorios. Se elige una sola para que todo se lea igual.

**Cuánto escribir:**

| Función | Docstring |
|---|---|
| Obvia por su nombre y sus tipos | Una línea |
| Con argumentos cuyo significado no es evidente, efectos secundarios (escribe una tabla, llama a una API) o errores propios | Resumen, detalle y secciones |

No documentes lo que el tipo ya dice ("anio: el año"). Documenta unidades, formatos,
valores admitidos, valores por defecto con significado y efectos.

```python
def calcular_margen(venta_neta: float, costo: float) -> float:
    """Devuelve el margen bruto: venta neta menos costo."""
    return venta_neta - costo


def escribir_particion(df: DataFrame, tabla: str, fecha_ingesta: str) -> int:
    """Reemplaza en la tabla las filas de una fecha de ingesta.

    La escritura es atómica: si falla, la tabla queda como estaba. Se puede
    repetir con la misma fecha sin duplicar filas.

    Args:
        df: Filas a escribir. Debe traer la columna `fecha_ingesta`.
        tabla: Nombre completo, `catalogo.esquema.tabla`.
        fecha_ingesta: Fecha a reemplazar, en formato AAAA-MM-DD.

    Returns:
        Número de filas escritas.

    Raises:
        ValueError: Si `df` trae fechas distintas de `fecha_ingesta`.
    """
```

## 5. Diseño de funciones

- **Una función hace una cosa.** Si el nombre necesita una "y", son dos funciones.
- **Corta.** Si pasa de unas 50 líneas, busca el paso que se puede separar.
- **Sin estado oculto.** Recibe por argumento lo que necesita: no lee widgets ni
  variables globales del notebook. Así se puede probar y reutilizar. Las únicas
  globales aceptables son constantes en mayúsculas y `spark` / `dbutils`.
- **Sin funciones de una línea que solo renombran otra llamada**, salvo que se usen
  varias veces.
- **Transformaciones como funciones de DataFrame a DataFrame**, para encadenarlas
  con `.transform()`:

```python
df_silver = (
    df_bronze
    .transform(renombrar_columnas)
    .transform(tipar_columnas)
    .transform(quitar_duplicados, claves=["id_pedido"])
)
```

- Las funciones compartidas por varios notebooks van en un `utils_<tema>.ipynb`.
  Las de conexión, en `cfg_<fuente>.ipynb`.
- No uses `collect()` ni `toPandas()` sobre datos de tamaño desconocido: traen todo
  al driver. Son válidos sobre resultados pequeños y acotados (una lista de fechas,
  un conteo).

## 6. UDF

Orden de preferencia, según la documentación de Databricks:

1. **Funciones nativas de Spark** (`pyspark.sql.functions`) y SQL. Están optimizadas
   para ejecución distribuida y son siempre la primera opción en un proceso que
   corre de forma periódica.
2. **UDF de SQL**, si la lógica se expresa en SQL y se va a reutilizar.
3. **`pandas_udf`**, si no hay función nativa. Trabaja por lotes con Arrow y es
   mucho más rápida que una UDF de Python fila a fila.
4. **UDF de Python** (`@udf`), solo para volúmenes pequeños o lógica imposible de
   vectorizar.

Reglas:

- Antes de escribir una UDF, comprueba que no exista función nativa. Casi siempre
  existe (`regexp_extract`, `transform`, `aggregate`, `from_json`, `when`).
- Declara siempre el tipo de retorno.
- Una UDF que usarán varios equipos o notebooks se registra en Unity Catalog, para
  que tenga permisos y se pueda descubrir. Una de uso local queda en la sesión.
- Documenta en el docstring por qué no bastó una función nativa.

```python
@F.pandas_udf("string")
def normalizar_ruc(ruc: pd.Series) -> pd.Series:
    """Devuelve el RUC con 13 dígitos, rellenando con ceros a la izquierda.

    Se usa pandas_udf porque la regla depende de un dígito verificador que no se
    puede expresar con funciones nativas.
    """
    return ruc.str.replace(r"\D", "", regex=True).str.zfill(13)
```

## 7. Mensajes de log

Los notebooks informan con `print` y una etiqueta fija al inicio. Solo estas siete:

| Etiqueta | Cuándo |
|---|---|
| `[INICIO]` | Primera línea: nombre del notebook y parámetros |
| `[INFO]` | Un dato del avance: rutas, conteos, fechas |
| `[OK]` | Un paso o una validación que terminó bien |
| `[WARN]` | Algo anómalo que no detiene el proceso |
| `[ERROR]` | Justo antes de lanzar una excepción |
| `[SKIP]` | Un paso que se omite a propósito, y por qué |
| `[FIN]` | Última línea: nombre del notebook y resumen |

```python
print(f"[INICIO] slv_ventas_pedidos | ambiente={ambiente} fecha_ingesta={fecha_ingesta}")
print(f"[INFO] Filas leídas de bronze: {filas_bronze}")
print(f"[OK] Sin duplicados por id_pedido")
print(f"[FIN] slv_ventas_pedidos | filas escritas={filas_escritas}")
```

- Un mensaje dice qué pasó y con qué valores. "Procesando…" no sirve.
- Nunca se imprime un secreto, un token ni un dato personal.
- No uses otras etiquetas (`[AVISO]`, `[ALERTA]`, `[DEL]`): son variantes de las
  anteriores y dificultan buscar en los registros.

## 8. Errores

- **Falla pronto y con un mensaje que permita actuar**: qué se esperaba, qué llegó
  y dónde.

```python
if not rutas_archivos:
    raise ValueError(
        "No se recibieron rutas desde ext_ventas_pedidos. "
        "Revisa que la extracción haya encontrado archivos para la fecha."
    )
```

- Usa la excepción que corresponde: `ValueError` para un dato inválido,
  `FileNotFoundError` para un archivo ausente, `RuntimeError` para un estado
  inesperado.
- `except` captura la excepción concreta. Un `except Exception: pass` esconde
  fallos reales; solo se admite para limpiar algo que puede no existir, con un
  comentario que lo diga.
- Un control de calidad que debe detener la carga usa `raise` con mensaje. No uses
  `assert` para validar datos: se puede desactivar y su mensaje es pobre.
- Un notebook que termina sin trabajo por hacer sale con
  `dbutils.notebook.exit("SKIP: <motivo>")`, no con una excepción.

## 9. Comentarios

- Un comentario por bloque lógico, que diga **qué hace** o **por qué** se tomó una
  decisión no obvia. No uno por línea.
- En la celda principal, los pasos se marcan: `# Paso 1 — Leer bronze`.
- Prohibido el comentario que justifica el cambio ("porque el usuario lo pidió",
  "arreglo temporal"). Eso va en el mensaje del commit.

## 10. Ejemplo completo

```python
def quitar_duplicados(
    df: DataFrame,
    claves: list[str],
    columna_orden: str = "fecha_proceso",
) -> DataFrame:
    """Devuelve una fila por clave, conservando la más reciente.

    Args:
        df: Datos de entrada.
        claves: Columnas que identifican un registro.
        columna_orden: Columna que decide cuál fila se conserva; gana el valor
            más alto.

    Returns:
        DataFrame con las mismas columnas y sin claves repetidas.

    Raises:
        ValueError: Si alguna clave o la columna de orden no existe en `df`.
    """
    faltantes = [c for c in [*claves, columna_orden] if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas ausentes en el DataFrame: {faltantes}")

    ventana = Window.partitionBy(*claves).orderBy(F.col(columna_orden).desc())
    return (
        df.withColumn("_orden", F.row_number().over(ventana))
        .filter(F.col("_orden") == 1)
        .drop("_orden")
    )
```
