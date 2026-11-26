#!/usr/bin/env python3
"""Revisa la documentación generada antes de entregarla.

Uso:
    python3 validar_docs.py <ruta_proyecto>

Comprueba, en README.md y docs/*.md (y los README de cada bundle):
  - Diagramas Mermaid: sintaxis que Azure DevOps no dibuja, tamaño excesivo,
    flechas dobles, nodos sin etiqueta legible.
  - Enlaces relativos que no apuntan a un archivo existente.
  - Marcadores de plantilla sin rellenar.
  - Posibles secretos copiados por error.
  - Que existan los documentos estándar y que cada diagrama tenga título y pie.
  - Que AGENTS.md no pase de 200 líneas y que CLAUDE.md lo importe.

Sale con código 1 si hay errores; las advertencias no bloquean.
"""
import os
import re
import sys

IGNORAR = {".git", ".venv", "venv", "node_modules", ".databricks", "__pycache__"}
ESTANDAR = ["README.md", "docs/01_entendimiento.md", "docs/02_arquitectura.md",
            "docs/03_fuentes_y_datos.md", "docs/04_operacion.md", "AGENTS.md", "CLAUDE.md"]
# La guía pide unos 15 nodos; se avisa a partir de 18 para no molestar por uno o dos de más.
MAX_NODOS = 18
# Un archivo de instrucciones para agentes se carga entero en cada sesión; la
# documentación de Claude Code recomienda no pasar de 200 líneas.
MAX_LINEAS_AGENTES = 200

BLOQUE = re.compile(r"```mermaid\n(.*?)```", re.S)
ENLACE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)")
# «instrucciones de plantilla», marcadores en mayúsculas y texto de relleno (ojo: "todo" es palabra española)
MARCADOR = re.compile(r"«[^»\n]{2,}»|<[A-ZÁÉÍÓÚÑ_ ]{4,}>|\bTODO:|\bTBD\b|\bXXX\b|[Ll]orem ipsum")
SECRETO = re.compile(r"(dapi[a-f0-9]{20,}|AKIA[0-9A-Z]{16}|(?:password|contrase[ñn]a|secret|token|pwd)\s*[:=]\s*[\"']?[^\s\"'<{$]{8,})", re.I)
NODO = re.compile(r"^\s*([A-Za-z_][\w]*)\s*[\[\(\{>]", re.M)


def archivos_md(raiz):
    for carpeta, dirs, archivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in IGNORAR]
        for a in archivos:
            if a.lower().endswith(".md"):
                yield os.path.join(carpeta, a)


def revisar_mermaid(codigo, donde, errores, avisos):
    lineas = [l for l in codigo.strip().splitlines() if l.strip() and not l.strip().startswith("%%")]
    if not lineas:
        errores.append(f"{donde}: diagrama vacío")
        return
    cabecera = lineas[0].strip()
    if cabecera.startswith("flowchart"):
        errores.append(f"{donde}: usa `graph LR`/`graph TD` en lugar de `flowchart` (Azure DevOps no lo dibuja)")
    if re.search(r"<br\s*/?>|<[a-z]+[^>]*>", codigo, re.I):
        errores.append(f"{donde}: contiene etiquetas HTML (p. ej. <br/>); Azure DevOps no las admite")
    if re.search(r"-{4,}>|={4,}>", codigo):
        errores.append(f"{donde}: flecha larga (---->); usa -->")
    if re.search(r"<-{1,3}>|<={1,3}>", codigo):
        errores.append(f"{donde}: flecha de doble punta; dibuja dos flechas o una sola con sentido claro")
    if re.search(r"\bfa:fa-", codigo):
        errores.append(f"{donde}: iconos Font Awesome no se dibujan en Azure DevOps")
    if cabecera.startswith("graph"):
        nodos = set(NODO.findall(codigo)) - {"subgraph", "classDef", "class", "style", "linkStyle", "end", "graph"}
        if len(nodos) > MAX_NODOS:
            avisos.append(f"{donde}: {len(nodos)} nodos; divide el diagrama en vistas más pequeñas (máx. {MAX_NODOS})")
        if not re.search(r"-->|-\.->|==>", codigo):
            avisos.append(f"{donde}: no tiene flechas; ¿falta el flujo?")
        abre = len(re.findall(r"^\s*subgraph\b", codigo, re.M))
        cierra = len(re.findall(r"^\s*end\s*$", codigo, re.M))
        if abre != cierra:
            errores.append(f"{donde}: {abre} subgraph y {cierra} end; no cuadran")
        for etiqueta in re.findall(r"\[([^\]\"]*[()/:;#][^\]\"]*)\]", codigo):
            avisos.append(f"{donde}: etiqueta con símbolos sin comillas: [{etiqueta}] → usa [\"{etiqueta}\"]")


def revisar(raiz):
    errores, avisos = [], []
    for esperado in ESTANDAR:
        if not os.path.isfile(os.path.join(raiz, esperado)):
            avisos.append(f"falta el documento estándar {esperado}")
    total_diagramas = 0
    for ruta in archivos_md(raiz):
        rel = os.path.relpath(ruta, raiz)
        with open(ruta, encoding="utf-8", errors="replace") as f:
            texto = f.read()
        for i, m in enumerate(BLOQUE.finditer(texto), 1):
            total_diagramas += 1
            donde = f"{rel} (diagrama {i})"
            revisar_mermaid(m.group(1), donde, errores, avisos)
            antes = texto[max(0, m.start() - 300):m.start()]
            despues = texto[m.end():m.end() + 300]
            if not re.search(r"\*\*Diagrama[^*]*\*\*", antes):
                avisos.append(f"{donde}: falta el título en negrita justo antes (**Diagrama N. …**)")
            if not re.search(r"C[oó]mo leerlo", despues, re.I):
                avisos.append(f"{donde}: falta la línea «Cómo leerlo» después del diagrama")
        sin_codigo = re.sub(r"```.*?```", "", texto, flags=re.S)
        for destino in ENLACE.findall(sin_codigo):
            if re.match(r"(https?:|mailto:|#)", destino):
                continue
            camino = destino.split("#")[0]
            if camino and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(ruta), camino))):
                errores.append(f"{rel}: enlace roto → {destino}")
        for m in MARCADOR.finditer(sin_codigo):
            avisos.append(f"{rel}: posible marcador sin rellenar «{m.group(0)}»")
        for m in SECRETO.finditer(texto):
            errores.append(f"{rel}: posible secreto en el texto «{m.group(0)[:25]}…»; quítalo")
    agentes = os.path.join(raiz, "AGENTS.md")
    if os.path.isfile(agentes):
        with open(agentes, encoding="utf-8", errors="replace") as f:
            n = f.read().count("\n") + 1
        if n > MAX_LINEAS_AGENTES:
            avisos.append(f"AGENTS.md: {n} líneas; pásalo a menos de {MAX_LINEAS_AGENTES} y enlaza el detalle a docs/")
    claude = os.path.join(raiz, "CLAUDE.md")
    if os.path.isfile(claude) and os.path.isfile(agentes):
        with open(claude, encoding="utf-8", errors="replace") as f:
            if "@AGENTS.md" not in f.read():
                avisos.append("CLAUDE.md: no importa AGENTS.md (@AGENTS.md); puede quedar una segunda copia desalineada")
    readme = os.path.join(raiz, "README.md")
    if os.path.isfile(readme):
        with open(readme, encoding="utf-8", errors="replace") as f:
            if "```mermaid" not in f.read():
                avisos.append("README.md: no tiene el diagrama de contexto")
    return errores, avisos, total_diagramas


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    errores, avisos, n = revisar(sys.argv[1])
    print(f"Diagramas revisados: {n}")
    for e in errores:
        print(f"ERROR  {e}")
    for a in avisos:
        print(f"AVISO  {a}")
    if not errores and not avisos:
        print("Todo en orden.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
