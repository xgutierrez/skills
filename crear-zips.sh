#!/usr/bin/env bash
# Crea un .zip por cada skill de personal/ para subirlo a la app de Claude (Customize → Skills), a
# ChatGPT (Plugins → Skills → Create → Upload from your computer) o a Grok web.
#
# Antes de empaquetar comprueba cada SKILL.md:
#   - que tenga encabezado YAML con name y description;
#   - que name sea igual al nombre de la carpeta;
#   - que description tenga como máximo 200 caracteres (límite de la app de Claude).
# Si alguna skill no cumple, no crea ningún zip y dice qué arreglar.
#
# Solo empaqueta personal/: lo de empresas/ no se sube a cuentas personales.
#
# Los zip quedan en dist/<fecha-hora>/, una carpeta nueva cada vez: nunca
# sobrescribe un zip anterior. dist/ no se sube a git.
#
# Uso:
#   ./crear-zips.sh                 todas las skills
#   ./crear-zips.sh mi-estilo-correos   solo esa skill
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SALIDA="$REPO/dist/$(date +%Y%m%d-%H%M%S)"

python3 - "$REPO" "$SALIDA" "$@" <<'PY'
import os
import re
import sys
import zipfile

repo, salida, *pedidas = sys.argv[1:]
carpeta_skills = os.path.join(repo, "personal")
LIMITE = 200


def leer_encabezado(ruta: str) -> dict:
    """Devuelve name y description del encabezado YAML de un SKILL.md."""
    texto = open(ruta, encoding="utf-8").read()
    bloque = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not bloque:
        return {}
    campos, clave = {}, None
    for linea in bloque.group(1).splitlines():
        par = re.match(r"^([a-z_-]+):\s*(.*)$", linea)
        if par:
            clave, valor = par.group(1), par.group(2).strip()
            campos[clave] = "" if valor in (">-", ">", "|", "|-") else valor
        elif clave and linea.startswith(" "):
            campos[clave] = (campos[clave] + " " + linea.strip()).strip()
    for clave, valor in campos.items():
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            campos[clave] = valor[1:-1]
    return campos


skills = sorted(
    s for s in os.listdir(carpeta_skills)
    if os.path.isfile(os.path.join(carpeta_skills, s, "SKILL.md"))
)
if pedidas:
    faltan = [p for p in pedidas if p not in skills]
    if faltan:
        sys.exit(f"No existe la skill: {', '.join(faltan)}")
    skills = pedidas

errores = []
for skill in skills:
    campos = leer_encabezado(os.path.join(carpeta_skills, skill, "SKILL.md"))
    nombre, descripcion = campos.get("name", ""), campos.get("description", "")
    if not nombre or not descripcion:
        errores.append(f"{skill}: falta name o description en el encabezado")
        continue
    if nombre != skill:
        errores.append(f"{skill}: name es '{nombre}', debe ser igual a la carpeta")
    if len(descripcion) > LIMITE:
        errores.append(f"{skill}: description tiene {len(descripcion)} caracteres (máximo {LIMITE})")

if errores:
    print("No se creó ningún zip. Arregla esto primero:")
    for error in errores:
        print(f"  - {error}")
    sys.exit(1)

os.makedirs(salida)
for skill in skills:
    destino = os.path.join(salida, f"{skill}.zip")
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as archivo:
        base = os.path.join(carpeta_skills, skill)
        for raiz, carpetas, ficheros in os.walk(base):
            carpetas[:] = [c for c in carpetas if c not in ("__pycache__", ".git")]
            for fichero in ficheros:
                if fichero == ".DS_Store" or fichero.endswith(".pyc"):
                    continue
                ruta = os.path.join(raiz, fichero)
                archivo.write(ruta, os.path.join(skill, os.path.relpath(ruta, base)))
    print(f"  creado  {os.path.relpath(destino, repo)}")

print("\nSúbelos en:")
print("  Claude:  Customize → Skills → + → Create skill → Upload a skill")
print("  ChatGPT: Plugins → Skills → Create → Upload from your computer")
print("Si la skill ya estaba subida, borra la anterior antes de subir la nueva.")
PY
