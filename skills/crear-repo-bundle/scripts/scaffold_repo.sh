#!/usr/bin/env bash
# Crea en local el esqueleto de un repositorio con un bundle de Databricks.
#
# Los valores propios de la empresa (prefijo del repositorio, etiquetas, grupo de
# variables, zona horaria) llegan por argumento: salen del perfil de la empresa.
#
# SEGURIDAD: solo CREA carpetas nuevas. Si la ruta ya existe, ABORTA.
# Nunca hace rm -rf, ni sobrescribe un repo local existente.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Las plantillas viven en la skill estandares-datos, hermana de esta en el repositorio.
TEMPLATES="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../../estandares-datos/assets/bundle" 2>/dev/null && pwd || true)"
NUEVO_NOTEBOOK="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../../crear-notebook/scripts/nuevo_notebook.py"
ROOT_DIR="${REPOS_ROOT:-$PWD}"
PREFIJO_REPO=""
EMPRESA=""
VARIABLE_GROUP=""
ZONA_HORARIA="America/Guayaquil"

REPO_NAME=""
BUNDLE_NAME=""
ABREV=""
FREQ="mensual"
DESCRIPCION="Proyecto Databricks Asset Bundle (DAB)."
NOTIFICATION_EMAIL=""
TAG_PROYECTO=""
TAG_AREA="datos"
TAG_TIPO="analitica"
TAG_MODELO="transversal"
TAG_FRECUENCIA="mensual"
TAG_PAIS=""

usage() {
  cat <<'EOF'
Uso:
  scaffold_repo.sh --repo <repo> --bundle <bundle> --empresa <perfil> \\
      --tag-proyecto <valor> --tag-pais <valor> --variable-group <nombre> \\
      [--prefijo-repo empresa_] [--root <carpeta>] [--email <correo>] [--zona <zona horaria>] \\
      [--frecuencia mensual] [--descripcion "..."] [--tag-area datos] [--tag-tipo analitica] [--tag-modelo transversal]

SEGURIDAD: no elimina ni sobrescribe carpetas existentes.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --delete|--destroy|--force|--force-with-lease|-rf|--rm|--remove|delete|destroy)
      echo "ERROR SEGURIDAD: argumento prohibido '${arg}'. Este script solo CREA."
      exit 2
      ;;
  esac
done

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_NAME="$2"; shift 2 ;;
    --bundle) BUNDLE_NAME="$2"; shift 2 ;;
    --abrev) ABREV="$2"; shift 2 ;;
    --empresa) EMPRESA="$2"; shift 2 ;;
    --prefijo-repo) PREFIJO_REPO="$2"; shift 2 ;;
    --variable-group) VARIABLE_GROUP="$2"; shift 2 ;;
    --zona) ZONA_HORARIA="$2"; shift 2 ;;
    --tag-proyecto) TAG_PROYECTO="$2"; shift 2 ;;
    --tag-pais) TAG_PAIS="$2"; shift 2 ;;
    --plantillas) TEMPLATES="$2"; shift 2 ;;
    --frecuencia) FREQ="$2"; TAG_FRECUENCIA="$2"; shift 2 ;;
    --descripcion) DESCRIPCION="$2"; shift 2 ;;
    --email) NOTIFICATION_EMAIL="$2"; shift 2 ;;
    --tag-modelo) TAG_MODELO="$2"; shift 2 ;;
    --tag-tipo) TAG_TIPO="$2"; shift 2 ;;
    --tag-area) TAG_AREA="$2"; shift 2 ;;
    --root) ROOT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Arg desconocido: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "$REPO_NAME" || -z "$BUNDLE_NAME" ]]; then
  echo "ERROR: --repo y --bundle son obligatorios"
  usage
  exit 1
fi

for requerido in EMPRESA TAG_PROYECTO TAG_PAIS VARIABLE_GROUP; do
  if [[ -z "${!requerido}" ]]; then
    echo "ERROR: falta un valor del perfil de la empresa: ${requerido}"
    usage
    exit 1
  fi
done

if [[ ! -d "$TEMPLATES" ]]; then
  echo "ERROR: no se encontraron las plantillas de estandares-datos. Indica su carpeta con --plantillas."
  exit 1
fi

if [[ ! "$REPO_NAME" =~ ^[a-z0-9_]+$ ]]; then
  echo "ERROR: el repositorio va en minúsculas, con guion bajo: '$REPO_NAME'"
  exit 1
fi

if [[ -n "$PREFIJO_REPO" && "$REPO_NAME" != "${PREFIJO_REPO}"* ]]; then
  echo "ERROR: el repositorio debe empezar por '${PREFIJO_REPO}': '$REPO_NAME'"
  exit 1
fi

if [[ ! "$BUNDLE_NAME" =~ ^[a-z0-9_]+$ ]]; then
  echo "ERROR: bundle inválido: '$BUNDLE_NAME'"
  exit 1
fi

WORKSPACE_FOLDER="${REPO_NAME#"$PREFIJO_REPO"}"
JOB_KEY="jb_orq_${BUNDLE_NAME}_${FREQ}"
JOB_FILE="${JOB_KEY}"
NOTEBOOK="gld_${BUNDLE_NAME}"
REPO_PATH="${ROOT_DIR}/${REPO_NAME}"

if [[ -e "$REPO_PATH" ]]; then
  echo "ERROR SEGURIDAD: ya existe localmente: $REPO_PATH"
  echo "No se elimina ni se sobrescribe. Elige otro nombre o trabaja sobre el existente."
  exit 1
fi

# sed trata & y \ en el replacement como especiales
escape_sed_repl() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/&/\\&/g'
}

render() {
  local src="$1"
  local dst="$2"
  local desc_esc email_esc
  desc_esc="$(escape_sed_repl "$DESCRIPCION")"
  email_esc="$(escape_sed_repl "$NOTIFICATION_EMAIL")"
  sed \
    -e "s|{{REPO_NAME}}|${REPO_NAME}|g" \
    -e "s|{{BUNDLE_NAME}}|${BUNDLE_NAME}|g" \
    -e "s|{{WORKSPACE_FOLDER}}|${WORKSPACE_FOLDER}|g" \
    -e "s|{{JOB_KEY}}|${JOB_KEY}|g" \
    -e "s|{{JOB_FILE}}|${JOB_FILE}|g" \
    -e "s|{{NOTEBOOK}}|${NOTEBOOK}|g" \
    -e "s|{{FUENTE_DOMINIO}}|${BUNDLE_NAME}|g" \
    -e "s|{{VARIABLE_GROUP}}|${VARIABLE_GROUP}|g" \
    -e "s|{{ZONA_HORARIA}}|${ZONA_HORARIA}|g" \
    -e "s|{{EMPRESA}}|${EMPRESA}|g" \
    -e "s|{{FREQ}}|${FREQ}|g" \
    -e "s|{{DESCRIPCION}}|${desc_esc}|g" \
    -e "s|{{NOTIFICATION_EMAIL}}|${email_esc}|g" \
    -e "s|{{TAG_PROYECTO}}|${TAG_PROYECTO}|g" \
    -e "s|{{TAG_AREA}}|${TAG_AREA}|g" \
    -e "s|{{TAG_TIPO}}|${TAG_TIPO}|g" \
    -e "s|{{TAG_MODELO}}|${TAG_MODELO}|g" \
    -e "s|{{TAG_FRECUENCIA}}|${TAG_FRECUENCIA}|g" \
    -e "s|{{TAG_PAIS}}|${TAG_PAIS}|g" \
    "$src" > "$dst"
}

mkdir -p \
  "${REPO_PATH}/.azure-pipelines" \
  "${REPO_PATH}/${BUNDLE_NAME}/src/conexiones" \
  "${REPO_PATH}/${BUNDLE_NAME}/src/${BUNDLE_NAME}" \
  "${REPO_PATH}/${BUNDLE_NAME}/resources" \
  "${REPO_PATH}/${BUNDLE_NAME}/tests"

cp "${TEMPLATES}/gitignore" "${REPO_PATH}/.gitignore"
render "${TEMPLATES}/README.md.tpl" "${REPO_PATH}/README.md"
render "${TEMPLATES}/variables.environment.yml.tpl" "${REPO_PATH}/.azure-pipelines/variables.environment.yml"
render "${TEMPLATES}/bundle_cd.yml.tpl" "${REPO_PATH}/.azure-pipelines/${BUNDLE_NAME}_cd.yml"
render "${TEMPLATES}/databricks.yml.tpl" "${REPO_PATH}/${BUNDLE_NAME}/databricks.yml"
render "${TEMPLATES}/jb_orq.yml.tpl" "${REPO_PATH}/${BUNDLE_NAME}/resources/${JOB_FILE}.yml"
render "${TEMPLATES}/AGENTS.md.tpl" "${REPO_PATH}/AGENTS.md"
printf '@AGENTS.md\n' > "${REPO_PATH}/CLAUDE.md"

# Notebook inicial con la estructura estándar, para que el job valide desde el primer día.
if [[ -f "$NUEVO_NOTEBOOK" ]]; then
  python3 "$NUEVO_NOTEBOOK" --tipo gld --tabla "${BUNDLE_NAME}" --esquema "${BUNDLE_NAME}" \
    --nombre "${NOTEBOOK}" --carpeta "${REPO_PATH}/${BUNDLE_NAME}/src/${BUNDLE_NAME}" \
    --job "${JOB_KEY}" --zona "${ZONA_HORARIA}" >/dev/null
else
  echo "AVISO: no se encontró crear-notebook; crea a mano ${NOTEBOOK}.ipynb"
fi
touch "${REPO_PATH}/${BUNDLE_NAME}/tests/.gitkeep"
touch "${REPO_PATH}/${BUNDLE_NAME}/src/conexiones/.gitkeep"

echo "OK scaffold: ${REPO_PATH}"
echo "  bundle=${BUNDLE_NAME} job=${JOB_KEY} notebook=${NOTEBOOK} carpeta_workspace=${WORKSPACE_FOLDER}"
