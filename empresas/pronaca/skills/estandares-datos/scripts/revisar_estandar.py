#!/usr/bin/env python3
"""Revisa un repositorio de datos contra el estándar.

Recorre notebooks (.ipynb, .py), YAML de bundles y DDL, y lista cada incumplimiento
con su archivo. Es de solo lectura.

Uso:
    python3 revisar_estandar.py <ruta_repo> [--solo-errores] [--json salida.json]
                                [--archivos a.ipynb b.yml ...]

ERROR es una regla del estándar; AVISO es una recomendación o algo que conviene
mirar. Con --archivos se revisan solo esos archivos (rutas relativas al repo), útil
después de crear o editar algo.

Solo necesita Python 3. Para leer los YAML usa PyYAML si está instalado y, si no,
Ruby (incluido en macOS). Sale con código 1 si hay errores.
"""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter

try:
    import yaml
except ImportError:
    yaml = None
RUBY = shutil.which("ruby")

IGNORAR = {".git", ".venv", "venv", "node_modules", ".databricks", "__pycache__",
           ".terraform", "dist", "build", "_analisis"}
PREFIJOS = ("ext_", "brz_", "slv_", "gld_", "val_", "cfg_", "utils_", "tbl_", "vol_")
ETIQUETAS_LOG = {"INICIO", "INFO", "OK", "WARN", "ERROR", "SKIP", "FIN"}
ETIQUETAS_JOB = ("proyecto", "area", "tipo", "modelo", "frecuencia", "pais", "gestion")
FRECUENCIAS = ("diaria", "semanal", "mensual", "anual", "eventual")
# Un notebook mayor suele traer resultados guardados; analizarlo es lento y poco útil.
MAX_BYTES = 8_000_000
# A partir de este largo una función casi siempre hace más de una cosa.
MAX_LINEAS_FUNCION = 50
# Columnas que legítimamente son flotantes.
FLOTANTES_ADMITIDOS = re.compile(r"lat|lon|coord|pct|porcentaje|ratio|score|probabilidad", re.I)

TIPOS_SQL = r"STRING|INT|INTEGER|BIGINT|DOUBLE|FLOAT|DECIMAL\([^)]*\)|DECIMAL|DATE|TIMESTAMP_NTZ|TIMESTAMP|BOOLEAN|LONG|SMALLINT|TINYINT"
CREATE = re.compile(
    r"CREATE\s+(OR\s+REPLACE\s+)?TABLE(\s+IF\s+NOT\s+EXISTS)?\s+([`\w{}.$]+)\s*\((.*?)(?:\"\"\"|'''|;\s*$|\Z)",
    re.S | re.I | re.M)
COLUMNA = re.compile(rf"^\s*`?(\w+)`?\s+({TIPOS_SQL})\b(.*)$", re.M | re.I)


class Informe:
    def __init__(self):
        self.hallazgos = []

    def add(self, nivel, regla, archivo, detalle=""):
        self.hallazgos.append({"nivel": nivel, "regla": regla, "archivo": archivo, "detalle": detalle})

    def error(self, regla, archivo, detalle=""):
        self.add("ERROR", regla, archivo, detalle)

    def aviso(self, regla, archivo, detalle=""):
        self.add("AVISO", regla, archivo, detalle)


def cargar_yaml(ruta):
    """Devuelve el contenido de un YAML como dict, o None si no se pudo leer."""
    try:
        if yaml is not None:
            with open(ruta, encoding="utf-8") as f:
                return yaml.safe_load(f)
        if RUBY:
            for expr in ("YAML.load_file(ARGV[0], aliases: true)", "YAML.load_file(ARGV[0])"):
                r = subprocess.run([RUBY, "-ryaml", "-rjson", "-e", f"puts JSON.dump({expr})", ruta],
                                   capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    return json.loads(r.stdout)
    except Exception:
        return None
    return None


def leer_notebook(ruta):
    """Devuelve (celdas, tiene_resultados). Cada celda es (tipo, texto)."""
    if ruta.endswith(".ipynb"):
        with open(ruta, encoding="utf-8") as f:
            nb = json.load(f)
        celdas, resultados = [], False
        for c in nb.get("cells", []):
            src = c.get("source", "")
            src = "".join(src) if isinstance(src, list) else src
            celdas.append((c.get("cell_type"), src))
            resultados = resultados or bool(c.get("outputs"))
        return celdas, resultados
    with open(ruta, encoding="utf-8", errors="replace") as f:
        texto = f.read()
    partes = re.split(r"^# COMMAND -+\s*$", texto, flags=re.M)
    celdas = []
    for p in partes:
        if re.search(r"^# MAGIC %md", p, re.M):
            celdas.append(("markdown", re.sub(r"^# MAGIC ?(%md)?", "", p, flags=re.M)))
        else:
            celdas.append(("code", re.sub(r"^# MAGIC ", "", p, flags=re.M)))
    return celdas, False


def revisar_funciones(codigo, rel, inf):
    limpio = "\n".join(l for l in codigo.splitlines() if not l.lstrip().startswith(("%", "!")))
    try:
        arbol = ast.parse(limpio)
    except SyntaxError:
        return
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.FunctionDef):
            continue
        nombre = nodo.name
        if not re.fullmatch(r"_{0,2}[a-z][a-z0-9_]*", nombre):
            inf.error("función: nombre en snake_case", rel, nombre)
        doc = ast.get_docstring(nodo)
        if not doc:
            inf.error("función: docstring obligatorio (PEP 257)", rel, nombre)
        else:
            primera = doc.strip().splitlines()[0].strip()
            if not primera.endswith("."):
                inf.aviso("función: el resumen del docstring termina en punto", rel, nombre)
            lineas = doc.strip().splitlines()
            if len(lineas) > 1 and lineas[1].strip():
                inf.aviso("función: línea en blanco tras el resumen del docstring", rel, nombre)
        args = [a for a in nodo.args.args + nodo.args.kwonlyargs if a.arg not in ("self", "cls")]
        if any(a.annotation is None for a in args):
            inf.error("función: tipos en todos los argumentos (PEP 484)", rel, nombre)
        if nodo.returns is None:
            inf.error("función: tipo de retorno (PEP 484)", rel, nombre)
        largo = nodo.end_lineno - nodo.lineno + 1
        if largo > MAX_LINEAS_FUNCION:
            inf.aviso(f"función: más de {MAX_LINEAS_FUNCION} líneas", rel, f"{nombre} ({largo})")
    if re.search(r"^\s*@udf|\budf\(", codigo, re.M) and "pandas_udf" not in codigo:
        inf.aviso("UDF de Python: comprobar si hay función nativa o usar pandas_udf", rel)
    if re.search(r"except\s*(Exception)?\s*:\s*\n\s*pass\b", codigo):
        inf.aviso("except que silencia errores (pass)", rel)
    if re.search(r"^\s*assert\s", codigo, re.M):
        inf.aviso("assert para validar datos: usar raise con mensaje", rel)


def revisar_ddl(codigo, rel, nombre, inf):
    es_migracion = nombre.startswith("mig_")
    es_setup = es_migracion or nombre.startswith(("tbl_", "vol_", "sch_")) \
        or "/setup/" in rel or "/00_setup/" in rel
    es_slv_gld = nombre.startswith(("tbl_slv_", "tbl_gld_"))
    creo_tabla = False
    for m in CREATE.finditer(codigo):
        creo_tabla = True
        reemplaza, si_no_existe, tabla, cuerpo = m.group(1), m.group(2), m.group(3), m.group(4)
        corto = tabla.split(".")[-1].strip("`{}")
        if not es_setup:
            inf.error("tabla: el DDL va en un notebook de setup (tbl_)", rel, corto)
        if reemplaza and not es_migracion:
            inf.error("tabla: CREATE OR REPLACE solo en un notebook de migración (mig_)", rel, corto)
        elif not si_no_existe:
            inf.error("tabla: usar CREATE TABLE IF NOT EXISTS", rel, corto)
        if tabla.count(".") < 2:
            inf.aviso("tabla: usar el nombre completo catalogo.esquema.tabla", rel, tabla)
        if re.search(r"\bLOCATION\b", cuerpo, re.I):
            inf.error("tabla: sin LOCATION (debe ser administrada)", rel, corto)
        if re.search(r"PARTITIONED\s+BY", cuerpo, re.I):
            inf.error("tabla: sin PARTITIONED BY (usar CLUSTER BY)", rel, corto)
        if not re.search(r"CLUSTER\s+BY", cuerpo, re.I):
            inf.error("tabla: falta CLUSTER BY (AUTO o claves)", rel, corto)
        if re.search(r"autoOptimize|targetFileSize", cuerpo, re.I):
            inf.error("tabla: sin TBLPROPERTIES de optimización manual", rel, corto)
        if re.search(r"minReaderVersion|minWriterVersion|delta\.appendOnly", cuerpo, re.I):
            inf.error("tabla: propiedad que no se fija a mano (protocolo o appendOnly)", rel, corto)
        if re.search(r"\bUSING\s+DELTA\b", cuerpo, re.I):
            inf.aviso("tabla: USING DELTA sobra (es el formato por defecto)", rel, corto)
        if es_slv_gld and not reemplaza:
            for prop in ("delta.columnMapping.mode", "delta.enableTypeWidening"):
                if prop not in cuerpo:
                    inf.aviso("tabla: silver y gold llevan columnMapping y enableTypeWidening",
                              rel, f"{corto}: falta {prop}")
        if not re.search(r"\)\s*(?:USING\s+DELTA\s*)?COMMENT\s+['\"]", cuerpo, re.I) and \
                not re.search(r"^\s*COMMENT\s+['\"]", cuerpo, re.I | re.M):
            inf.error("tabla: falta COMMENT de tabla", rel, corto)
        if corto.startswith("fact_"):
            inf.error("tabla: los hechos usan fac_, no fact_", rel, corto)
        if re.match(r"(brz|slv|gld|bronze|silver|gold)_", corto):
            inf.error("tabla: sin prefijo de capa en el nombre", rel, corto)
        columnas = COLUMNA.findall(cuerpo)
        sin_comentario = [c for c, t, resto in columnas if "COMMENT" not in resto.upper()]
        if sin_comentario:
            inf.error("tabla: todas las columnas llevan COMMENT", rel,
                      f"{corto}: {', '.join(sin_comentario[:6])}" + ("…" if len(sin_comentario) > 6 else ""))
        for c, t, _ in columnas:
            if c[0].isdigit():
                inf.aviso("tabla: el nombre de columna no empieza con número", rel, f"{corto}.{c}")
            if t.upper() in ("DOUBLE", "FLOAT") and not FLOTANTES_ADMITIDOS.search(c):
                inf.error("tabla: DECIMAL en lugar de DOUBLE/FLOAT", rel, f"{corto}.{c}")
            if c in ("fecha_carga", "fecha_actualizacion", "FECHA_INGESTA", "fecha_insercion"):
                inf.aviso("tabla: linaje con fecha_ingesta y fecha_proceso", rel, f"{corto}.{c}")
    if creo_tabla and es_setup and not re.search(r"\bOWNER\s+TO\b", codigo, re.I):
        inf.aviso("tabla: falta ALTER TABLE … OWNER TO con el grupo del perfil", rel)
    if re.search(r"\bZORDER\s+BY\b", codigo, re.I):
        inf.error("tabla: ZORDER no se usa (lo reemplaza CLUSTER BY)", rel)
    if re.search(r"^\s*(spark\.sql\(\s*f?[\"']+\s*)?(OPTIMIZE|VACUUM)\s+[`\w{]", codigo, re.I | re.M):
        inf.aviso("tabla: OPTIMIZE/VACUUM manual (lo hace la optimización predictiva)", rel)
    if re.search(r"\bDROP\s+TABLE\b", codigo, re.I):
        inf.aviso("DROP TABLE en el código", rel)


def revisar_notebook(ruta, rel, inf):
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    try:
        celdas, resultados = leer_notebook(ruta)
    except Exception as e:
        inf.aviso("no se pudo leer el archivo", rel, str(e)[:80])
        return
    if not celdas:
        return
    codigo = "\n".join(t for tipo, t in celdas if tipo == "code")
    es_notebook = ruta.endswith(".ipynb") or "# Databricks notebook source" in codigo[:200]
    es_setup = nombre.startswith(("tbl_", "vol_", "sch_")) or "/setup/" in rel

    if es_notebook:
        if not nombre.startswith(PREFIJOS):
            inf.error("notebook: el nombre empieza por el prefijo de su capa", rel)
        if nombre != nombre.lower() or " " in nombre or "-" in nombre:
            inf.error("notebook: nombre en minúsculas, con guion bajo", rel)
        if ruta.endswith(".py"):
            inf.aviso("notebook: se trabaja con .ipynb, no .py", rel)
        if celdas[0][0] != "markdown":
            inf.error("notebook: la primera celda es la cabecera en Markdown", rel)
        elif not re.search(r"Qu[eé] hace", celdas[0][1]):
            inf.aviso("notebook: la cabecera dice «Qué hace»", rel)
        if resultados:
            inf.aviso("notebook: guardado con resultados de ejecución", rel)
        for tipo, t in celdas:
            if tipo == "code" and re.search(r"^\s*%run\b", t, re.M):
                otras = [l for l in t.strip().splitlines() if l.strip() and not l.strip().startswith(("%run", "#"))]
                if otras:
                    inf.error("notebook: %run va solo en su celda", rel)
                    break
        if not nombre.startswith(("cfg_", "utils_")):
            if "[INICIO]" not in codigo:
                inf.aviso("notebook: falta el mensaje [INICIO]", rel)
            if "[FIN]" not in codigo:
                inf.aviso("notebook: falta el mensaje [FIN]", rel)
        if re.search(r"\bdisplay\(", codigo) and not nombre.startswith("val_"):
            inf.aviso("notebook: display() en un notebook de job", rel)
        if re.search(r"^\s*%sql\b", codigo, re.M):
            inf.aviso("notebook: celdas %sql (usar spark.sql en la carga)", rel)

    for w in set(re.findall(r"dbutils\.widgets\.\w+\(\s*[\"'](\w+)", codigo)):
        if w != w.lower():
            inf.error("parámetro: nombre de widget en minúsculas", rel, w)
    otras = sorted({e for e in re.findall(r"print\(\s*f?[\"']\s*\[([A-ZÁÉÍÓÚ_]+)\]", codigo)} - ETIQUETAS_LOG)
    if otras:
        inf.error("log: solo las siete etiquetas estándar", rel, ", ".join(f"[{e}]" for e in otras))
    if re.search(r"(abfss?|wasbs?)://|[\"']/mnt/", codigo):
        inf.error("rutas: usar volúmenes, no abfss:// ni /mnt/", rel)
    usa = lambda opcion: re.search(rf"[\"']{opcion}[\"']\s*[,:]\s*[\"']?true", codigo, re.I)
    if usa("overwriteSchema") and not es_setup:
        inf.error("carga: overwriteSchema solo en setup", rel)
    if usa("mergeSchema") and not es_setup and not nombre.startswith("brz_"):
        inf.aviso("carga: mergeSchema fuera de bronze", rel)
    if re.search(r"(password|passwd|contrase[ñn]a|secret|token|api_?key)\s*=\s*[\"'][^\"'{}\s]{6,}[\"']", codigo, re.I):
        inf.error("seguridad: posible secreto escrito en el código", rel)
    if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", codigo):
        inf.aviso("seguridad: correo escrito en el código", rel)
    if re.search(r"\.(collect|toPandas)\(\)", codigo):
        inf.aviso("rendimiento: collect()/toPandas(); confirmar que el resultado es pequeño", rel)

    revisar_funciones(codigo, rel, inf)
    revisar_ddl(codigo, rel, nombre, inf)


def revisar_bundle(ruta, rel, raiz, inf):
    doc = cargar_yaml(ruta)
    if doc is None:
        inf.aviso("bundle: no se pudo leer el YAML", rel)
        return
    carpeta = os.path.dirname(ruta)
    if os.path.abspath(carpeta) == os.path.abspath(raiz):
        inf.error("bundle: databricks.yml va dentro de la carpeta del bundle", rel)
    nombre = (doc.get("bundle") or {}).get("name")
    if nombre and os.path.basename(carpeta) != nombre and os.path.abspath(carpeta) != os.path.abspath(raiz):
        inf.aviso("bundle: la carpeta se llama igual que bundle.name", rel, f"{os.path.basename(carpeta)} ≠ {nombre}")
    targets = doc.get("targets") or {}
    for t in ("local", "dev", "main"):
        if t not in targets:
            inf.error("bundle: targets local, dev y main", rel, f"falta {t}")
    local = targets.get("local") or {}
    if local and not local.get("default"):
        inf.error("bundle: local es el target por defecto", rel)
    if local and local.get("mode") != "development":
        inf.error("bundle: local usa mode: development", rel)
    for t in ("dev", "main"):
        if (targets.get(t) or {}).get("mode"):
            inf.aviso("bundle: dev y main sin mode (lo gobierna el CI/CD)", rel, t)
    variables = doc.get("variables") or {}
    for v in ("ambiente", "pause_status", "job_name_prefix", "notification_email", "repo_name"):
        if v not in variables:
            inf.error("bundle: variables estándar", rel, f"falta {v}")
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    if re.search(r"^\s*host\s*:", texto, re.M):
        inf.aviso("bundle: sin workspace.host en el archivo", rel)
    if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", texto):
        inf.aviso("seguridad: correo escrito en databricks.yml", rel)


def revisar_recurso(ruta, rel, inf):
    doc = cargar_yaml(ruta)
    if not isinstance(doc, dict):
        return
    jobs = ((doc.get("resources") or {}).get("jobs")) or {}
    base = os.path.splitext(os.path.basename(ruta))[0]
    for clave, j in jobs.items():
        j = j or {}
        donde = f"{clave}"
        if not clave.startswith("jb_"):
            inf.error("job: el nombre empieza por jb_", rel, donde)
        if not clave.endswith(FRECUENCIAS) and not clave.endswith("_setup"):
            inf.error("job: el nombre termina en la frecuencia", rel, donde)
        if base != clave and len(jobs) == 1:
            inf.aviso("job: el archivo se llama igual que el job", rel, f"{base} ≠ {clave}")
        etiquetas = j.get("tags") or {}
        faltan = [e for e in ETIQUETAS_JOB if e not in etiquetas]
        if faltan:
            inf.error("job: etiquetas obligatorias", rel, f"{donde}: falta {', '.join(faltan)}")
        if etiquetas.get("gestion") not in (None, "bundle"):
            inf.error("job: gestion = bundle", rel, donde)
        frec = etiquetas.get("frecuencia")
        if frec and frec in FRECUENCIAS and not clave.endswith(frec) and not clave.endswith("_setup"):
            inf.aviso("job: la etiqueta frecuencia coincide con el nombre", rel, f"{donde}: {frec}")
        if j.get("job_clusters"):
            inf.aviso("job: serverless; un cluster propio es excepción justificada", rel, donde)
        if j.get("max_concurrent_runs") != 1:
            inf.aviso("job: max_concurrent_runs: 1", rel, donde)
        if not (j.get("queue") or {}).get("enabled"):
            inf.aviso("job: queue.enabled: true", rel, donde)
        if not j.get("description"):
            inf.aviso("job: description", rel, donde)
        if j.get("email_notifications"):
            inf.aviso("job: los avisos por correo se definen en el target, no en el recurso", rel, donde)
        prog = j.get("schedule") or {}
        if prog and not prog.get("timezone_id"):
            inf.error("job: timezone_id en la programación", rel, donde)
        if prog and "var.pause_status" not in str(prog.get("pause_status", "")):
            inf.aviso("job: pause_status: ${var.pause_status}", rel, donde)
        if "ambiente" not in [p.get("name") for p in j.get("parameters") or []]:
            inf.error("job: parámetro ambiente", rel, donde)
        for t in j.get("tasks") or []:
            ruta_nb = (t.get("notebook_task") or {}).get("notebook_path", "")
            if ruta_nb:
                nb = os.path.splitext(os.path.basename(ruta_nb))[0]
                if nb != t.get("task_key"):
                    inf.error("job: task_key igual al nombre del notebook", rel, f"{t.get('task_key')} ≠ {nb}")
                if not ruta_nb.endswith(".ipynb"):
                    inf.aviso("job: notebook_path con extensión .ipynb", rel, ruta_nb)
            for cl in ("existing_cluster_id", "new_cluster"):
                if t.get(cl):
                    inf.aviso("job: serverless; un cluster propio es excepción justificada", rel, t.get("task_key"))


def recorrer(raiz, solo=None):
    if solo:
        for r in solo:
            p = os.path.join(raiz, r)
            if os.path.isfile(p):
                yield p
        return
    for carpeta, dirs, archivos in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR)
        for a in sorted(archivos):
            yield os.path.join(carpeta, a)


def revisar(raiz, solo=None):
    inf = Informe()
    revisados = Counter()
    for ruta in recorrer(raiz, solo):
        rel = os.path.relpath(ruta, raiz)
        nombre = os.path.basename(ruta)
        ext = os.path.splitext(nombre)[1].lower()
        if nombre == "databricks.yml":
            revisar_bundle(ruta, rel, raiz, inf)
            revisados["bundles"] += 1
        elif ext in (".yml", ".yaml") and f"{os.sep}resources{os.sep}" in ruta:
            revisar_recurso(ruta, rel, inf)
            revisados["recursos"] += 1
        elif ext in (".ipynb", ".py") and "DataFactory" not in rel:
            if os.path.getsize(ruta) > MAX_BYTES:
                inf.aviso("archivo muy grande: no se revisó", rel)
                continue
            revisar_notebook(ruta, rel, inf)
            revisados["notebooks y scripts"] += 1
    if yaml is None and not RUBY:
        inf.aviso("sin lector de YAML (PyYAML o Ruby): no se revisaron bundles ni jobs", ".")
    return inf, revisados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--solo-errores", action="store_true", help="No listar los avisos")
    ap.add_argument("--json", help="Guardar el detalle en este archivo")
    ap.add_argument("--archivos", nargs="+", help="Revisar solo estos archivos (rutas relativas al repo)")
    ap.add_argument("--resumen", action="store_true", help="Mostrar solo el resumen por regla")
    a = ap.parse_args()
    if not os.path.isdir(a.repo):
        sys.exit(f"No existe la carpeta: {a.repo}")

    inf, revisados = revisar(os.path.abspath(a.repo), a.archivos)
    hallazgos = [h for h in inf.hallazgos if not (a.solo_errores and h["nivel"] == "AVISO")]
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(hallazgos, f, ensure_ascii=False, indent=2)

    if not a.resumen:
        por_archivo = {}
        for h in hallazgos:
            por_archivo.setdefault(h["archivo"], []).append(h)
        for archivo in sorted(por_archivo):
            print(f"\n{archivo}")
            for h in sorted(por_archivo[archivo], key=lambda x: (x["nivel"] != "ERROR", x["regla"])):
                detalle = f" — {h['detalle']}" if h["detalle"] else ""
                print(f"  {h['nivel']:5} {h['regla']}{detalle}")

    errores = sum(1 for h in hallazgos if h["nivel"] == "ERROR")
    avisos = len(hallazgos) - errores
    print("\n" + "=" * 60)
    print("Revisado: " + ", ".join(f"{v} {k}" for k, v in revisados.items()))
    print(f"Errores: {errores} · Avisos: {avisos}")
    conteo = Counter((h["nivel"], h["regla"]) for h in hallazgos)
    if conteo:
        print("\nPor regla:")
        for (nivel, regla), n in sorted(conteo.items(), key=lambda x: (x[0][0] != "ERROR", -x[1])):
            print(f"  {n:4}  {nivel:5} {regla}")
    else:
        print("Todo cumple el estándar.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
