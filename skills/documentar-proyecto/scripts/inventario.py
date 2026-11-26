#!/usr/bin/env python3
"""Inventario de un proyecto de datos para documentarlo.

Recorre el proyecto y extrae, sin interpretar, los hechos que la documentación
necesita: bundles de Databricks, jobs y sus tareas, notebooks (título, parámetros,
tablas que leen y escriben, indicios de fuentes externas), pipelines de Data
Factory, pipelines de CI/CD y documentación existente.

Uso:
    python3 inventario.py <ruta_proyecto> [--salida inventario.json]

Imprime un resumen en Markdown por stdout. Con --salida guarda además el JSON
completo. Es solo lectura: nunca modifica el proyecto.

Las tablas se detectan por patrones de texto, así que el resultado es un punto de
partida fiable pero no perfecto: confirma en el notebook lo que resulte dudoso.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

try:
    import yaml
except ImportError:  # el inventario sigue funcionando sin los YAML
    yaml = None
RUBY = shutil.which("ruby")

IGNORAR_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".databricks",
                ".terraform", ".idea", ".vscode", "dist", "build", ".pytest_cache"}

CAPAS = [
    (r"^(ext|extract|extraccion)[_\- ]", "extraccion"),
    (r"^(brz|bro|bronze)[_\- ]", "bronze"),
    (r"^(slv|silver)[_\- ]", "silver"),
    (r"^(gld|gold)[_\- ]", "gold"),
    (r"^(val|test)[_\- ]", "validacion"),
    (r"^(cfg|config)[_\- ]", "configuracion"),
    (r"^(utils?|func)[_\- ]", "utilidades"),
    (r"^(tbl|sch|ddl|setup)[_\- ]", "setup"),
    (r"^(dsh|dashboard)[_\- ]", "dashboard"),
    (r"^(mdl|modelo|train|predic)", "modelo"),
]

FUENTES_EXTERNAS = {
    "Oracle": r"oracle|ojdbc",
    "SQL Server": r"sqlserver|mssql|pyodbc",
    "JDBC": r"\.format\(\s*[\"']jdbc[\"']\)|jdbc:",
    "SAP": r"\bsap\b|odata|\bhana\b",
    "SharePoint": r"sharepoint|graph\.microsoft\.com",
    "API REST": r"requests\.(get|post)|http\.client|urllib\.request",
    "ArcGIS": r"arcgis|survey123",
    "SFTP": r"sftp|paramiko",
    "S3": r"s3a?://|boto3",
    "Azure Storage": r"abfss?://|wasbs?://|dfs\.core\.windows\.net",
    "Volumen UC": r"/Volumes/",
    "Excel": r"read_excel|openpyxl|\.xlsx",
    "CSV": r"read_csv|\.format\(\s*[\"']csv[\"']\)|\.csv\(",
    "Power BI": r"api\.powerbi\.com|powerbi",
    "Genesys": r"genesys|mypurecloud",
    "Correo": r"smtplib|sendgrid|send_mail|envio_correo",
    "MLflow": r"\bmlflow\b",
    "Secretos": r"dbutils\.secrets\.get",
}

# nombre de tres partes: catalogo.esquema.tabla, admitiendo {variables} de f-string
PARTE = r"(?:[A-Za-z_]|\{[^{}\n]{1,60}\})(?:\w|\{[^{}\n]{1,60}\})*"
TRES_PARTES = re.compile(rf"(?<![\w.{{/])({PARTE}\.{PARTE}\.{PARTE})(?![\w.(])")
ESCRITURA_SQL = re.compile(
    r"(?:INSERT\s+(?:INTO|OVERWRITE)(?:\s+TABLE)?|MERGE\s+INTO|"
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP(?:ORARY)?\s+)?(?:MATERIALIZED\s+)?(?:TABLE|VIEW)(?:\s+IF\s+NOT\s+EXISTS)?|"
    r"(?<!\w)UPDATE|DELETE\s+FROM|TRUNCATE\s+TABLE|ALTER\s+TABLE|OPTIMIZE|COPY\s+INTO)\s+([`\w{}.]+)", re.I)
LECTURA_SQL = re.compile(r"(?:FROM|JOIN)\s+([`\w{}.]+)", re.I)
ESCRITURA_PY = re.compile(r"(?:saveAsTable|insertInto|forName\s*\(\s*spark\s*,|toTable|writeTo)\s*\(?\s*f?[\"']?([`\w{}.]+)")
# funciones propias de escritura: escribir_tabla_gold(df, tabla, ...), guardar_delta(df, "x.y.z")
ESCRITURA_AUX = re.compile(r"\b(?:escribir|guardar|grabar|persistir|write|save|upsert|merge)\w*\(\s*\w+\s*,\s*f?[\"']?([`\w{}.]+)")
LECTURA_PY = re.compile(r"(?:spark\.table|read\.table|readStream\.table|spark\.read\.table)\s*\(\s*f?[\"']?([`\w{}.]+)")
ASIGNACION = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*f?[\"']([^\"'\n]+)[\"']", re.M)
WIDGET = re.compile(r"dbutils\.widgets\.(?:text|dropdown|combobox|multiselect)\(\s*[\"']([^\"']+)[\"']\s*,\s*[\"']([^\"']*)[\"']")
RUN = re.compile(r"^\s*%run\s+(\S+)", re.M)
NO_TABLA = re.compile(r"^(spark|dbutils|df\w*|self|os|np|pd|F|T|col|sys|json|re|datetime|pyspark|com|org|www|http|https|plt|sns|mlflow|sklearn|logging)\.", re.I)
EXT_ARCHIVO = re.compile(r"\.(py|ipynb|sql|yml|yaml|json|csv|xlsx|txt|md|png|html|com|net|org|parquet|delta|whl)$", re.I)


def caminar(raiz):
    for carpeta, dirs, archivos in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR_DIRS)
        for a in sorted(archivos):
            yield os.path.join(carpeta, a)


def capa_de(nombre):
    base = os.path.splitext(os.path.basename(nombre))[0].lower()
    base = re.sub(r"^\d+[_\- .]*", "", base)
    for patron, capa in CAPAS:
        if re.search(patron, base):
            return capa
    return "otro"


def leer_notebook(ruta):
    """Devuelve (texto_codigo, lista_markdown)."""
    try:
        if ruta.endswith(".ipynb"):
            with open(ruta, encoding="utf-8") as f:
                nb = json.load(f)
            codigo, md = [], []
            for c in nb.get("cells", []):
                src = c.get("source", "")
                src = "".join(src) if isinstance(src, list) else src
                if c.get("cell_type") == "markdown" or src.lstrip().startswith("%md"):
                    md.append(re.sub(r"^\s*%md\s*", "", src))
                else:
                    codigo.append(src)
            return "\n".join(codigo), md
        with open(ruta, encoding="utf-8", errors="replace") as f:
            texto = f.read()
        md = [re.sub(r"^# MAGIC ?", "", m, flags=re.M)
              for m in re.findall(r"# MAGIC %md\n((?:# MAGIC.*\n?)+)", texto)]
        return texto, md
    except Exception as e:  # un archivo roto no debe detener el inventario
        return "", [f"(no se pudo leer: {e})"]


def es_tabla(nombre):
    n = nombre.replace("`", "").strip("'\" ")
    if NO_TABLA.match(n) or EXT_ARCHIVO.search(n) or " " in n:
        return False
    partes = n.split(".")
    # tres partes, o dos cuando la primera es una variable que ya trae catalogo.esquema
    if not (len(partes) == 3 or (len(partes) == 2 and re.fullmatch(r"\{[^{}]+\}", partes[0]))):
        return False
    return not any(p == "" or p.isdigit() for p in partes)


def resolver(nombre, variables):
    """Si el nombre es una variable asignada a un literal, devuelve el literal."""
    n = nombre.replace("`", "").strip("'\" ")
    m = re.fullmatch(r"\{?([A-Za-z_]\w*)\}?", n)
    if m and m.group(1) in variables:
        return variables[m.group(1)]
    return n


def analizar_codigo(codigo):
    variables = {k: v for k, v in ASIGNACION.findall(codigo)}
    # segunda pasada: variables compuestas del tipo f"{catalogo}.{esquema}.tabla"
    escribe, lee = set(), set()
    for patron, destino in ((ESCRITURA_SQL, escribe), (ESCRITURA_PY, escribe), (ESCRITURA_AUX, escribe),
                            (LECTURA_SQL, lee), (LECTURA_PY, lee)):
        for m in patron.findall(codigo):
            nombre = resolver(m, variables)
            if es_tabla(nombre):
                destino.add(nombre)
    mencionadas = {t for t in TRES_PARTES.findall(codigo) if es_tabla(t)}
    lee -= escribe
    otras = mencionadas - escribe - lee
    fuentes = sorted(k for k, p in FUENTES_EXTERNAS.items() if re.search(p, codigo, re.I))
    return {
        "parametros": [{"nombre": n, "defecto": d} for n, d in dict(WIDGET.findall(codigo)).items()],
        "ejecuta_run": sorted(set(RUN.findall(codigo))),
        "tablas_escribe": sorted(escribe),
        "tablas_lee": sorted(lee),
        "tablas_mencionadas_sin_clasificar": sorted(otras),
        "indicios_fuentes": fuentes,
        "variables_de_ruta": {k: v for k, v in variables.items()
                              if re.search(r"catalog|esquema|schema|tabla|table|ruta|path|url|volumen", k, re.I)},
    }


def titulo_y_resumen(md):
    titulo, resumen = "", ""
    for bloque in md:
        for linea in bloque.splitlines():
            l = linea.strip()
            if not l:
                continue
            if not titulo and l.startswith("#"):
                titulo = l.lstrip("# ").strip()
            elif not resumen and not l.startswith(("#", "|", "---", "```")):
                resumen = l[:400]
            if titulo and resumen:
                return titulo, resumen
    return titulo, resumen


def cargar_yaml(ruta):
    """Lee un YAML con PyYAML; si no está instalado, usa Ruby (viene con macOS)."""
    try:
        if yaml is not None:
            with open(ruta, encoding="utf-8") as f:
                return yaml.safe_load(f)
        if RUBY:
            r = subprocess.run([RUBY, "-ryaml", "-rjson", "-e",
                                "puts JSON.dump(YAML.load_file(ARGV[0], aliases: true))", ruta],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:  # versiones antiguas de Ruby no aceptan aliases:
                r = subprocess.run([RUBY, "-ryaml", "-rjson", "-e",
                                    "puts JSON.dump(YAML.load_file(ARGV[0]))", ruta],
                                   capture_output=True, text=True, timeout=30)
            return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:
        return None
    return None


def tarea_resumida(t):
    tipo, destino = "otro", ""
    for clave, campo in (("notebook_task", "notebook_path"), ("spark_python_task", "python_file"),
                         ("pipeline_task", "pipeline_id"), ("run_job_task", "job_id"),
                         ("sql_task", None), ("python_wheel_task", "entry_point"),
                         ("condition_task", None), ("for_each_task", None), ("dbt_task", None)):
        if clave in t:
            tipo = clave.replace("_task", "")
            destino = (t[clave] or {}).get(campo, "") if campo else ""
            if clave == "for_each_task":
                interna = (t[clave] or {}).get("task", {})
                destino = (interna.get("notebook_task") or {}).get("notebook_path", "")
            break
    return {
        "tarea": t.get("task_key"),
        "tipo": tipo,
        "destino": destino,
        "depende_de": [d.get("task_key") for d in t.get("depends_on", []) or []],
        "parametros": (t.get("notebook_task") or {}).get("base_parameters", {}) if tipo == "notebook" else {},
    }


def analizar_bundle(ruta_yml, raiz):
    carpeta = os.path.dirname(ruta_yml)
    doc = cargar_yaml(ruta_yml) or {}
    bundle = {
        "ruta": os.path.relpath(carpeta, raiz),
        "nombre": (doc.get("bundle") or {}).get("name"),
        "targets": {},
        "variables": {k: (v or {}).get("default") if isinstance(v, dict) else v
                      for k, v in (doc.get("variables") or {}).items()},
        "jobs": [], "pipelines": [], "otros_recursos": [],
    }
    for nombre, t in (doc.get("targets") or {}).items():
        t = t or {}
        bundle["targets"][nombre] = {
            "modo": t.get("mode"), "por_defecto": t.get("default", False),
            "variables": t.get("variables") or {},
        }
    archivos = [ruta_yml]
    rdir = os.path.join(carpeta, "resources")
    if os.path.isdir(rdir):
        archivos += [p for p in caminar(rdir) if p.endswith((".yml", ".yaml"))]
    for a in archivos:
        recursos = (cargar_yaml(a) or {}).get("resources") or {}
        for clave, j in (recursos.get("jobs") or {}).items():
            j = j or {}
            sch = j.get("schedule") or {}
            bundle["jobs"].append({
                "clave": clave, "nombre": j.get("name"),
                "archivo": os.path.relpath(a, raiz),
                "descripcion": j.get("description"),
                "programacion": {"cron": sch.get("quartz_cron_expression"),
                                 "zona_horaria": sch.get("timezone_id"),
                                 "estado": sch.get("pause_status")} if sch else None,
                "disparador": j.get("trigger"),
                "etiquetas": j.get("tags") or {},
                "parametros": [{"nombre": p.get("name"), "defecto": p.get("default")}
                               for p in j.get("parameters") or []],
                "notifica_por_correo": bool(j.get("email_notifications")),
                "tareas": [tarea_resumida(t) for t in j.get("tasks") or []],
            })
        for clave, p in (recursos.get("pipelines") or {}).items():
            p = p or {}
            bundle["pipelines"].append({"clave": clave, "nombre": p.get("name"),
                                        "catalogo": p.get("catalog"), "esquema": p.get("schema") or p.get("target"),
                                        "archivo": os.path.relpath(a, raiz)})
        for tipo, items in recursos.items():
            if tipo not in ("jobs", "pipelines"):
                bundle["otros_recursos"] += [f"{tipo}: {k}" for k in (items or {})]
    return bundle


def analizar_adf(carpeta, raiz):
    adf = {"ruta": os.path.relpath(carpeta, raiz), "pipelines": [], "servicios_vinculados": [],
           "disparadores": [], "total_datasets": 0}

    def cargar(sub):
        d = os.path.join(carpeta, sub)
        if not os.path.isdir(d):
            return
        for a in sorted(os.listdir(d)):
            if a.endswith(".json"):
                try:
                    with open(os.path.join(d, a), encoding="utf-8") as f:
                        yield json.load(f)
                except Exception:
                    continue

    for p in cargar("pipeline"):
        props = p.get("properties", {})
        acts = props.get("activities", [])
        adf["pipelines"].append({
            "nombre": p.get("name"), "carpeta": (props.get("folder") or {}).get("name"),
            "descripcion": props.get("description"),
            "actividades": [{"nombre": a.get("name"), "tipo": a.get("type"),
                             "depende_de": [d.get("activity") for d in a.get("dependsOn", [])],
                             "invoca": ((a.get("typeProperties") or {}).get("pipeline") or {}).get("referenceName")
                             or (a.get("typeProperties") or {}).get("notebookPath")}
                            for a in acts],
        })
    for s in cargar("linkedService"):
        adf["servicios_vinculados"].append({"nombre": s.get("name"), "tipo": s.get("properties", {}).get("type")})
    for t in cargar("trigger"):
        props = t.get("properties", {})
        rec = (props.get("typeProperties") or {}).get("recurrence") or {}
        adf["disparadores"].append({
            "nombre": t.get("name"), "tipo": props.get("type"), "estado": props.get("runtimeState"),
            "frecuencia": f"{rec.get('interval', '')} {rec.get('frequency', '')}".strip(),
            "pipelines": [(x.get("pipelineReference") or {}).get("referenceName") for x in props.get("pipelines", [])],
        })
    adf["total_datasets"] = sum(1 for _ in cargar("dataset"))
    return adf


def analizar_cicd(ruta, raiz):
    doc = cargar_yaml(ruta) or {}
    trig = doc.get("trigger")
    ramas, rutas = [], []
    if isinstance(trig, dict):
        ramas = (trig.get("branches") or {}).get("include", [])
        rutas = (trig.get("paths") or {}).get("include", [])
    elif isinstance(trig, list):
        ramas = trig
    grupos = []
    for v in doc.get("variables") or []:
        if isinstance(v, dict) and "group" in v:
            grupos.append(v["group"])
    return {"archivo": os.path.relpath(ruta, raiz), "ramas": ramas, "rutas": rutas,
            "grupos_variables": grupos,
            "etapas": [s.get("stage") for s in doc.get("stages") or [] if isinstance(s, dict)]}


def inventariar(raiz):
    raiz = os.path.abspath(raiz)
    inv = {"proyecto": os.path.basename(raiz), "ruta": raiz, "yaml_disponible": yaml is not None or bool(RUBY),
           "bundles": [], "data_factory": [], "cicd": [], "notebooks": [],
           "documentacion_existente": [], "otros_archivos": defaultdict(int)}
    for ruta in caminar(raiz):
        rel = os.path.relpath(ruta, raiz)
        nombre = os.path.basename(ruta)
        ext = os.path.splitext(nombre)[1].lower()
        if nombre == "databricks.yml":
            inv["bundles"].append(analizar_bundle(ruta, raiz))
        elif "azure-pipelines" in rel and ext in (".yml", ".yaml"):
            inv["cicd"].append(analizar_cicd(ruta, raiz))
        elif ext == ".md":
            with open(ruta, encoding="utf-8", errors="replace") as f:
                txt = f.read()
            inv["documentacion_existente"].append({
                "archivo": rel, "lineas": txt.count("\n") + 1,
                "titulos": re.findall(r"^#{1,2} +(.+)$", txt, re.M)[:12],
                "tiene_mermaid": "mermaid" in txt})
        elif ext in (".ipynb", ".py", ".sql") and "DataFactory" not in rel:
            if os.path.getsize(ruta) > 15_000_000:  # notebooks gigantes: suelen ser salidas guardadas
                inv["notebooks"].append({"archivo": rel, "capa": capa_de(nombre), "titulo": "",
                                         "resumen": "(omitido por tamaño; revisar a mano)", **analizar_codigo("")})
                continue
            codigo, md = leer_notebook(ruta)
            titulo, resumen = titulo_y_resumen(md)
            nb = {"archivo": rel, "capa": capa_de(nombre), "titulo": titulo, "resumen": resumen}
            nb.update(analizar_codigo(codigo))
            inv["notebooks"].append(nb)
        elif ext in (".dax", ".xlsx", ".pbix", ".knwf", ".knime", ".tf", ".sh", ".whl", ".toml"):
            inv["otros_archivos"][ext] += 1
    for carpeta, dirs, _ in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        if os.path.isdir(os.path.join(carpeta, "pipeline")) and os.path.isdir(os.path.join(carpeta, "linkedService")):
            inv["data_factory"].append(analizar_adf(carpeta, raiz))
    inv["otros_archivos"] = dict(inv["otros_archivos"])
    return inv


def resumen_md(inv):
    o = [f"# Inventario: {inv['proyecto']}", ""]
    if not inv["yaml_disponible"]:
        o += ["> AVISO: no hay lector de YAML (ni PyYAML ni Ruby); no se leyeron jobs ni targets. "
              "Ejecuta con `uv run --with pyyaml python3 inventario.py ...` o lee los .yml a mano.", ""]
    nbs = inv["notebooks"]
    por_capa = defaultdict(int)
    for n in nbs:
        por_capa[n["capa"]] += 1
    o.append(f"- Bundles: {len(inv['bundles'])} · Notebooks/scripts: {len(nbs)} · "
             f"Data Factory: {len(inv['data_factory'])} · CI/CD: {len(inv['cicd'])} · "
             f"Docs existentes: {len(inv['documentacion_existente'])}")
    o.append("- Notebooks por capa: " + ", ".join(f"{k}={v}" for k, v in sorted(por_capa.items())))
    if inv["otros_archivos"]:
        o.append("- Otros archivos relevantes: " + ", ".join(f"{k}×{v}" for k, v in inv["otros_archivos"].items()))
    fuentes = defaultdict(list)
    for n in nbs:
        for f in n["indicios_fuentes"]:
            fuentes[f].append(n["archivo"])
    if fuentes:
        o += ["", "## Indicios de fuentes externas (confirmar en el código)"]
        o += [f"- **{k}**: {len(v)} archivo(s), p. ej. `{v[0]}`" for k, v in sorted(fuentes.items())]
    for b in inv["bundles"]:
        o += ["", f"## Bundle `{b['nombre']}` ({b['ruta']})",
              "- Targets: " + ", ".join(f"{k} (modo {v['modo']})" for k, v in b["targets"].items())]
        for j in b["jobs"]:
            prog = j["programacion"]
            cuando = f"cron `{prog['cron']}` {prog['zona_horaria'] or ''} [{prog['estado'] or 'activo'}]" if prog else "sin programación (manual o disparador)"
            o.append(f"- Job `{j['nombre'] or j['clave']}`: {len(j['tareas'])} tareas · {cuando}")
            for t in j["tareas"]:
                dep = f" ← {', '.join(t['depende_de'])}" if t["depende_de"] else ""
                o.append(f"    - `{t['tarea']}` ({t['tipo']}) {t['destino']}{dep}")
        if b["pipelines"]:
            o.append("- Pipelines declarativos: " + ", ".join(p["nombre"] or p["clave"] for p in b["pipelines"]))
        if b["otros_recursos"]:
            o.append("- Otros recursos: " + ", ".join(b["otros_recursos"]))
    for a in inv["data_factory"]:
        tipos = sorted({s["tipo"] for s in a["servicios_vinculados"] if s["tipo"]})
        o += ["", f"## Data Factory ({a['ruta']})",
              f"- {len(a['pipelines'])} pipelines · {a['total_datasets']} datasets · {len(a['disparadores'])} disparadores",
              "- Tipos de servicios vinculados: " + ", ".join(tipos)]
    escritas, leidas = defaultdict(list), defaultdict(list)
    for n in nbs:
        for t in n["tablas_escribe"]:
            escritas[t].append(n["archivo"])
        for t in n["tablas_lee"]:
            leidas[t].append(n["archivo"])
    if escritas:
        o += ["", f"## Tablas que el proyecto escribe ({len(escritas)})"]
        o += [f"- `{t}` ← {os.path.basename(v[0])}" + (f" (+{len(v) - 1})" if len(v) > 1 else "")
              for t, v in sorted(escritas.items())[:80]]
    solo_leidas = {t: v for t, v in leidas.items() if t not in escritas}
    if solo_leidas:
        o += ["", f"## Tablas que lee y no produce: son sus fuentes internas ({len(solo_leidas)})"]
        o += [f"- `{t}` → {os.path.basename(v[0])}" + (f" (+{len(v) - 1})" if len(v) > 1 else "")
              for t, v in sorted(solo_leidas.items())[:80]]
    if inv["cicd"]:
        o += ["", "## CI/CD"]
        o += [f"- `{c['archivo']}` · ramas: {c['ramas']} · rutas: {c['rutas']} · grupos: {c['grupos_variables']}"
              for c in inv["cicd"]]
    if inv["documentacion_existente"]:
        o += ["", "## Documentación existente (leerla y reutilizar lo que siga siendo cierto)"]
        o += [f"- `{d['archivo']}` ({d['lineas']} líneas){' · con Mermaid' if d['tiene_mermaid'] else ''}"
              for d in inv["documentacion_existente"]]
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto", help="Ruta del proyecto a inventariar")
    ap.add_argument("--salida", help="Archivo donde guardar el JSON completo")
    args = ap.parse_args()
    if not os.path.isdir(args.proyecto):
        sys.exit(f"No existe la carpeta: {args.proyecto}")
    inv = inventariar(args.proyecto)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            json.dump(inv, f, ensure_ascii=False, indent=2)
    print(resumen_md(inv))
    if args.salida:
        print(f"\nJSON completo (detalle por notebook): {args.salida}")


if __name__ == "__main__":
    main()
