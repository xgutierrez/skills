#!/usr/bin/env python3
"""Genera el esqueleto de un notebook de Databricks según su capa.

Crea un archivo .ipynb con las celdas estándar ya ordenadas: cabecera, parámetros,
imports, pasos numerados y cierre. Lo que debe completarse queda marcado con
"PENDIENTE:" para buscarlo y sustituirlo.

Uso:
    python3 nuevo_notebook.py --tipo slv --fuente sharepoint --dominio presupuesto \\
        --carpeta ruta/al/bundle/src/sharepoint_presupuesto

    python3 nuevo_notebook.py --tipo gld --tabla fac_ventas_cliente_mes \\
        --esquema ventas --carpeta ruta/al/bundle/src/ventas

Tipos: ext, brz, slv, gld, val, cfg, utils, tbl, vol.
No sobrescribe un archivo existente. No necesita dependencias.
"""
import argparse
import json
import os
import sys

TIPOS = ("ext", "brz", "slv", "gld", "val", "cfg", "utils", "tbl", "vol")
CAPA = {"ext": "Extracción", "brz": "Bronze", "slv": "Silver", "gld": "Gold",
        "val": "Validación", "cfg": "Configuración", "utils": "Utilidades",
        "tbl": "Setup de tablas", "vol": "Setup de volúmenes"}
P = "PENDIENTE:"


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)}


def py(texto):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": texto.strip("\n").splitlines(keepends=True)}


def cabecera(nombre, tipo, que_hace, entrada, salida, job, flujo, parametros):
    filas = "\n".join(f"| `{n}` | {d} | {p} |" for n, d, p in parametros)
    tabla = f"\n| Parámetro | Por defecto | Para qué |\n|---|---|---|\n{filas}\n" if parametros else ""
    linea = f"**Capa:** {CAPA[tipo]}"
    if job:
        linea += f" · **Job:** `{job}`"
    if flujo:
        linea += f" · **Flujo:** `{flujo}`"
    cuerpo = f"# {nombre}\n\n{linea}\n\n**Qué hace.** {que_hace}\n"
    if entrada:
        cuerpo += f"\n**Entrada:** {entrada}  \n**Salida:** {salida}\n"
    return md(cuerpo + tabla)


def parametros_py(nombre, zona, extra=""):
    return py(f'''
dbutils.widgets.text("ambiente", "dev", "Ambiente")
{extra}
ambiente = dbutils.widgets.get("ambiente").strip() or "dev"

spark.conf.set("spark.sql.session.timeZone", "{zona}")
print(f"[INICIO] {nombre} | ambiente={{ambiente}}")
''')


FECHA_WIDGET = 'dbutils.widgets.text("fecha_ingesta", "", "Fecha de ingesta AAAA-MM-DD (vacío: hoy)")'
P_AMB = ("ambiente", "`dev`", "Catálogos de lectura y escritura")
P_FECHA = ("fecha_ingesta", "vacío: hoy", "Lote a procesar, AAAA-MM-DD")

RESOLVER_FECHA = '''
from datetime import datetime
from zoneinfo import ZoneInfo

fecha_ingesta = dbutils.widgets.get("fecha_ingesta").strip() or datetime.now(
    ZoneInfo("{zona}")
).strftime("%Y-%m-%d")
'''


def celdas(a):
    n, z, f, d = a.nombre, a.zona, a.fuente, a.dominio
    flujo = "ext → brz → slv"
    if a.tipo == "ext":
        return [
            cabecera(n, "ext", f"{P} qué trae y de dónde.", f"{P} sistema y objeto de origen",
                     f"`/Volumes/bronze_{{ambiente}}/{f}/raw/{d}/fecha_ingesta=AAAA-MM-DD/`",
                     a.job, flujo, [P_AMB, P_FECHA]),
            parametros_py(n, z, FECHA_WIDGET),
            py(f"%run ../conexiones/cfg_{f}"),
            py(RESOLVER_FECHA.format(zona=z) + f'''
ruta_destino = f"/Volumes/bronze_{{ambiente}}/{f}/raw/{d}/fecha_ingesta={{fecha_ingesta}}"
print(f"[INFO] Destino: {{ruta_destino}}")
'''),
            md("## Paso 1 — Extraer de la fuente"),
            py(f"# {P} leer de la fuente con las funciones de cfg_{f}.\n# No transformar: el archivo se guarda tal como llega."),
            md("## Paso 2 — Guardar en el volumen"),
            py(f'''
dbutils.fs.mkdirs(ruta_destino)
rutas_escritas: list[str] = []
# {P} escribir cada archivo en ruta_destino y añadir su ruta a rutas_escritas.

if not rutas_escritas:
    print("[SKIP] La fuente no devolvió archivos para la fecha.")
    dbutils.notebook.exit("SKIP: sin archivos para la fecha")
'''),
            md("## Paso 3 — Publicar para la tarea de bronze"),
            py(f'''
import json

dbutils.jobs.taskValues.set(key="fecha_ingesta", value=fecha_ingesta)
dbutils.jobs.taskValues.set(key="rutas_volume", value=json.dumps(rutas_escritas))
print(f"[FIN] {n} | archivos={{len(rutas_escritas)}}")
'''),
        ]
    if a.tipo == "brz":
        return [
            cabecera(n, "brz", f"{P} qué carga. Todas las columnas quedan como texto.",
                     f"`/Volumes/bronze_{{ambiente}}/{f}/raw/{d}/`",
                     f"`bronze_{{ambiente}}.{f}.{d}`, una fila por {P} grano.", a.job, flujo, [P_AMB]),
            parametros_py(n, z),
            py(f'''
import json

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

tabla_destino = f"bronze_{{ambiente}}.{f}.{d}"
'''),
            md("## Paso 1 — Recibir las rutas de la extracción"),
            py(f'''
fecha_ingesta = dbutils.jobs.taskValues.get(
    taskKey="ext_{f}_{d}", key="fecha_ingesta", debugValue=""
)
rutas_json = dbutils.jobs.taskValues.get(
    taskKey="ext_{f}_{d}", key="rutas_volume", debugValue=""
)
if not fecha_ingesta or not rutas_json:
    raise ValueError("fecha_ingesta o rutas_volume no recibidas desde ext_{f}_{d}")

rutas_archivos = json.loads(rutas_json)
print(f"[INFO] Archivos a cargar: {{len(rutas_archivos)}}")
'''),
            md("## Paso 2 — Leer los archivos como texto"),
            py(f"# {P} leer rutas_archivos en df_crudo, todas las columnas STRING,\n# conservando los nombres de la fuente."),
            md("## Paso 3 — Añadir linaje y escribir"),
            py(f'''
df_bronze = (
    df_crudo
    .withColumn("fecha_ingesta", F.lit(fecha_ingesta).cast("date"))
    .withColumn("fecha_proceso", F.current_timestamp())
    .withColumn("archivo_origen", F.col("_metadata.file_path"))
)

# Reemplazo selectivo: repetir la fecha no duplica filas.
(
    df_bronze.write
    .mode("overwrite")
    .option("replaceWhere", f"fecha_ingesta = '{{fecha_ingesta}}'")
    .saveAsTable(tabla_destino)
)

dbutils.jobs.taskValues.set(key="fecha_ingesta", value=fecha_ingesta)
print(f"[FIN] {n} | tabla={{tabla_destino}} fecha_ingesta={{fecha_ingesta}}")
'''),
        ]
    if a.tipo == "slv":
        return [
            cabecera(n, "slv", f"{P} qué limpia y normaliza.", f"`bronze_{{ambiente}}.{f}.{d}`",
                     f"`silver_{{ambiente}}.{f}.{d}`, una fila por {P} grano.", a.job, flujo, [P_AMB]),
            parametros_py(n, z),
            py(f'''
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

tabla_origen = f"bronze_{{ambiente}}.{f}.{d}"
tabla_destino = f"silver_{{ambiente}}.{f}.{d}"
COLUMNAS_CLAVE = ["{P} columnas que identifican una fila"]
'''),
            md("## Mapeo de columnas\n\nFormato: `\"columna_fuente\": (\"columna_silver\", \"tipo\")`. "
               "Los comentarios de columna viven en el DDL de la tabla."),
            py(f'''
MAPEO_COLUMNAS: dict[str, tuple[str, str]] = {{
    # {P} "ColumnaFuente": ("columna_silver", "string"),
}}
'''),
            md("## Paso 1 — Leer el lote de bronze"),
            py(f'''
fecha_ingesta = dbutils.jobs.taskValues.get(
    taskKey="brz_{f}_{d}", key="fecha_ingesta", debugValue=""
)
if not fecha_ingesta:
    raise ValueError("fecha_ingesta no recibida desde brz_{f}_{d}")

df_bronze = spark.table(tabla_origen).filter(F.col("fecha_ingesta") == fecha_ingesta)
'''),
            md("## Paso 2 — Renombrar, tipar y quitar duplicados"),
            py(f'''
df_silver = df_bronze.select(
    *[
        F.col(f"`{{origen}}`").cast(tipo).alias(destino)
        for origen, (destino, tipo) in MAPEO_COLUMNAS.items()
    ],
    "fecha_ingesta",
).withColumn("fecha_proceso", F.current_timestamp())

# {P} normalizaciones propias del dominio (textos, fechas, unidades).
df_silver = df_silver.dropDuplicates(COLUMNAS_CLAVE)
'''),
            md("## Paso 3 — Validar"),
            py(f'''
filas_sin_clave = df_silver.filter(
    " OR ".join(f"{{columna}} IS NULL" for columna in COLUMNAS_CLAVE)
).limit(1).count()
if filas_sin_clave:
    print("[ERROR] Hay filas con la clave vacía.")
    raise ValueError(f"Filas sin clave en {{tabla_origen}} para {{fecha_ingesta}}")
print("[OK] Claves completas")
'''),
            md("## Paso 4 — Escribir"),
            py(f'''
# Reemplazo selectivo: repetir la fecha no duplica filas.
(
    df_silver.write
    .mode("overwrite")
    .option("replaceWhere", f"fecha_ingesta = '{{fecha_ingesta}}'")
    .saveAsTable(tabla_destino)
)
print(f"[FIN] {n} | tabla={{tabla_destino}} fecha_ingesta={{fecha_ingesta}}")
'''),
        ]
    if a.tipo == "gld":
        t, e = a.tabla, a.esquema
        return [
            cabecera(n, "gld", f"{P} qué calcula y para quién.", f"{P} tablas de origen",
                     f"`gold_{{ambiente}}.{e}.{t}`, una fila por {P} grano.", a.job, "", [P_AMB]),
            parametros_py(n, z),
            py(f"%run ./cfg_{e}"),
            py(f'''
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

tabla_destino = f"gold_{{ambiente}}.{e}.{t}"
'''),
            md(f"## Paso 1 — {P} título\n\n**Qué hace.** {P}\n\n**Por qué.** {P}\n\n**Cómo se calcula.**\n\n1. {P}"),
            py(f"# {P} lectura y transformación."),
            md("## Paso 2 — Controles\n\nSi alguno falla, la carga se detiene y la tabla queda como estaba."),
            py(f'''
# {P} controles de calidad: claves únicas, identidades, conteos.
# Usar raise con un mensaje que diga qué se esperaba y qué llegó.
'''),
            md("## Paso 3 — Escribir"),
            py(f'''
# {P} elegir la estrategia:
#   hecho por periodo -> replaceWhere por el periodo recalculado
#   dimensión pequeña -> overwrite completo, sin overwriteSchema
#   dimensión con historia -> MERGE
print(f"[FIN] {n} | tabla={{tabla_destino}}")
'''),
        ]
    if a.tipo == "val":
        return [
            cabecera(n, "val", f"{P} qué compara y contra qué. No modifica datos.", f"{P} tablas que revisa",
                     "Informe en pantalla.", "", "",
                     [P_AMB, ("tolerancia_pct", "`0.5`", "Diferencia porcentual admitida")]),
            parametros_py(n, z, 'dbutils.widgets.text("tolerancia_pct", "0.5", "Tolerancia en porcentaje")'),
            py('tolerancia_pct = float(dbutils.widgets.get("tolerancia_pct"))\nhallazgos: list[str] = []'),
            md(f"## Paso 1 — {P} control"),
            py(f"# {P} calcular el control. Si no se cumple:\n#     hallazgos.append(\"descripción con los valores\")"),
            md("## Resumen"),
            py(f'''
if hallazgos:
    for hallazgo in hallazgos:
        print(f"[WARN] {{hallazgo}}")
    print(f"[FIN] {n} | hallazgos={{len(hallazgos)}}")
else:
    print("[OK] Todos los controles pasaron")
    print("[FIN] {n} | hallazgos=0")
'''),
        ]
    if a.tipo == "cfg":
        return [
            md(f"# {n}\n\n**Capa:** Configuración\n\n**Qué hace.** {P} conexión o constantes que define.\n\n"
               f"**Uso:** `%run` desde los notebooks que lo necesitan. Al incluirlo no ejecuta trabajo: "
               f"solo define constantes y funciones.\n\n| Función | Para qué |\n|---|---|\n| `{P}` | {P} |"),
            py('dbutils.widgets.text("ambiente", "dev", "Ambiente")\nambiente = dbutils.widgets.get("ambiente").strip() or "dev"'),
            md("## Constantes y secretos"),
            py(f'''
import requests

# El nombre del scope sale del perfil de la empresa y depende del ambiente.
SCOPE_SECRETOS = f"{P}-{{ambiente}}"
TIEMPO_ESPERA_SEGUNDOS = 60  # una llamada normal responde en segundos

# {P} leer cada secreto con dbutils.secrets.get(scope=SCOPE_SECRETOS, key="...").
# Nunca imprimir su valor.
'''),
            md("## Funciones"),
            py(f'''
def {P.lower().rstrip(":")}_obtener_datos(parametro: str) -> dict:
    """{P} resumen en imperativo.

    Args:
        parametro: {P}

    Returns:
        {P}

    Raises:
        requests.HTTPError: Si la fuente responde con un error.
    """
    raise NotImplementedError
'''),
            py(f'print("[OK] {n} cargado | ambiente=" + ambiente)'),
        ]
    if a.tipo == "utils":
        return [
            md(f"# {n}\n\n**Capa:** Utilidades\n\n**Qué hace.** {P} tema de las funciones.\n\n"
               f"**Uso:** `%run` desde los notebooks que las necesitan. No lee widgets ni tablas al incluirlo.\n\n"
               f"| Función | Para qué |\n|---|---|\n| `{P}` | {P} |"),
            py("from pyspark.sql import DataFrame\nfrom pyspark.sql import functions as F"),
            md("## Funciones"),
            py(f'''
def {P.lower().rstrip(":")}_transformar(df: DataFrame, columna: str) -> DataFrame:
    """{P} resumen en imperativo.

    Args:
        df: {P}
        columna: {P}

    Returns:
        {P}
    """
    raise NotImplementedError
'''),
        ]
    if a.tipo == "tbl":
        t, e, capa = a.tabla, a.esquema, a.capa
        return [
            md(f"# {n}\n\n**Capa:** Setup de tablas\n\n**Qué hace.** Crea `{capa}_{{ambiente}}.{e}.{t}` si no existe. "
               f"Se puede ejecutar varias veces sin perder datos.\n\n"
               f"| Parámetro | Por defecto | Para qué |\n|---|---|---|\n| `ambiente` | `dev` | Catálogo donde se crea |"),
            py(f'''
dbutils.widgets.text("ambiente", "dev", "Ambiente")
ambiente = dbutils.widgets.get("ambiente").strip() or "dev"

catalogo = f"{capa}_{{ambiente}}"
esquema = "{e}"
print(f"[INICIO] {n} | catalogo={{catalogo}}")
'''),
            md("## Paso 1 — Asegurar el esquema"),
            py('spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.{esquema}")'),
            md(f"## Paso 2 — Crear `{t}`"),
            py(f'''
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {{catalogo}}.{{esquema}}.{t} (
    -- {P} columnas: nombre TIPO [NOT NULL] COMMENT 'significado, unidad y origen'
    fecha_proceso TIMESTAMP COMMENT 'Momento de escritura de la fila ({z})'
)
COMMENT '{P} contenido. Grano: una fila por ... Fuente: ...'
CLUSTER BY AUTO
""")
print(f"[OK] Tabla {{catalogo}}.{{esquema}}.{t} creada o ya existente")
'''),
            md("## Paso 3 — Etiquetas"),
            py(f'''
# {P} etiquetas que pida el perfil de la empresa.
# spark.sql(f"ALTER TABLE {{catalogo}}.{{esquema}}.{t} SET TAGS ('capa' = 'consumo')")
print("[FIN] {n}")
'''),
        ]
    # vol
    return [
        md(f"# {n}\n\n**Capa:** Setup de volúmenes\n\n**Qué hace.** Crea el esquema y el volumen donde aterrizan "
           f"los archivos de `{f}`. Se ejecuta una vez por ambiente.\n\n"
           f"| Parámetro | Por defecto | Para qué |\n|---|---|---|\n| `ambiente` | `dev` | Catálogo donde se crea |"),
        py(f'''
dbutils.widgets.text("ambiente", "dev", "Ambiente")
ambiente = dbutils.widgets.get("ambiente").strip() or "dev"

catalogo = f"bronze_{{ambiente}}"
esquema = "{f}"
volumen = "raw"
print(f"[INICIO] {n} | catalogo={{catalogo}}")
'''),
        md("## Paso 1 — Crear esquema y volumen"),
        py(f'''
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {{catalogo}}.{{esquema}}")
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {{catalogo}}.{{esquema}}.{{volumen}}
COMMENT 'Archivos crudos de {f}, un directorio por dominio y fecha de ingesta'
""")
print(f"[FIN] {n} | volumen=/Volumes/{{catalogo}}/{{esquema}}/{{volumen}}")
'''),
    ]


def nombre_por_defecto(a):
    if a.tipo in ("ext", "brz", "slv"):
        return f"{a.tipo}_{a.fuente}_{a.dominio}"
    if a.tipo == "gld":
        return f"gld_{a.tabla}"
    if a.tipo == "tbl":
        prefijo = {"bronze": "brz", "silver": "slv", "gold": "gld"}[a.capa]
        return f"tbl_{prefijo}_{a.tabla}"
    if a.tipo == "vol":
        return f"vol_brz_{a.dominio or a.fuente}"
    return f"{a.tipo}_{a.tema or a.fuente}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tipo", required=True, choices=TIPOS)
    ap.add_argument("--carpeta", required=True, help="Carpeta donde se crea el notebook")
    ap.add_argument("--fuente", help="Sistema de origen (ext, brz, slv, cfg, vol)")
    ap.add_argument("--dominio", help="Dominio o entidad (ext, brz, slv, vol)")
    ap.add_argument("--tabla", help="Nombre de la tabla (gld, tbl)")
    ap.add_argument("--esquema", help="Esquema de la tabla (gld, tbl)")
    ap.add_argument("--capa", choices=("bronze", "silver", "gold"), help="Capa de la tabla (tbl)")
    ap.add_argument("--tema", help="Tema del notebook (cfg, utils, val)")
    ap.add_argument("--job", default="", help="Job que lo ejecuta, para la cabecera")
    ap.add_argument("--zona", default="America/Guayaquil", help="Zona horaria del perfil de la empresa")
    ap.add_argument("--nombre", help="Nombre del notebook sin extensión; por defecto se arma con el patrón estándar")
    a = ap.parse_args()

    requeridos = {"ext": ("fuente", "dominio"), "brz": ("fuente", "dominio"), "slv": ("fuente", "dominio"),
                  "gld": ("tabla", "esquema"), "tbl": ("tabla", "esquema", "capa"), "vol": ("fuente",),
                  "cfg": (), "utils": (), "val": ()}[a.tipo]
    faltan = [f"--{r}" for r in requeridos if not getattr(a, r)]
    if a.tipo in ("cfg", "utils", "val") and not (a.tema or a.fuente):
        faltan.append("--tema")
    if faltan:
        sys.exit(f"Para --tipo {a.tipo} faltan: {', '.join(faltan)}")

    a.nombre = a.nombre or nombre_por_defecto(a)
    if not a.nombre.startswith(a.tipo + "_"):
        sys.exit(f"El nombre debe empezar por '{a.tipo}_': {a.nombre}")
    if a.nombre != a.nombre.lower() or " " in a.nombre or "-" in a.nombre:
        sys.exit(f"El nombre va en minúsculas, con guion bajo y sin espacios: {a.nombre}")

    ruta = os.path.join(a.carpeta, a.nombre + ".ipynb")
    if os.path.exists(ruta):
        sys.exit(f"Ya existe {ruta}; no se sobrescribe.")
    os.makedirs(a.carpeta, exist_ok=True)
    notebook = {"cells": celdas(a),
                "metadata": {"language_info": {"name": "python"}},
                "nbformat": 4, "nbformat_minor": 5}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)
        f.write("\n")
    pendientes = sum("".join(c["source"]).count(P) for c in notebook["cells"])
    print(f"Creado: {ruta}")
    print(f"Celdas: {len(notebook['cells'])} · marcadores PENDIENTE por completar: {pendientes}")


if __name__ == "__main__":
    main()
