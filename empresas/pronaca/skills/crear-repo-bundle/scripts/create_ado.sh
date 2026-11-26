#!/usr/bin/env bash
# Crea el repositorio, las ramas dev y main, y el pipeline en Azure DevOps.
#
# La organización y el proyecto llegan por argumento o por las variables de entorno
# ADO_ORG y ADO_PROJECT: salen de los identificadores de la empresa.
#
# SEGURIDAD: solo CREATE. Nunca delete/destroy/force-push.
# Allowlist de az: repos create|show|update(default-branch), pipelines create|show
set -euo pipefail

ORG="${ADO_ORG:-}"
PROJECT="${ADO_PROJECT:-}"
ROOT_DIR="${REPOS_ROOT:-$PWD}"

REPO_NAME=""
BUNDLE_NAME=""
PIPELINE_ONLY=0
SKIP_PIPELINE=0

usage() {
  cat <<'EOF'
Uso:
  create_ado.sh --org https://dev.azure.com/<organizacion> --project <proyecto> --repo <repo> --bundle <bundle>
  create_ado.sh --org https://dev.azure.com/<organizacion> --project <proyecto> --repo <repo> --bundle <bundle> --pipeline-only
  create_ado.sh --org https://dev.azure.com/<organizacion> --project <proyecto> --repo <repo> --bundle <bundle> --skip-pipeline

SEGURIDAD: este script NUNCA elimina repos, pipelines ni ramas remotas.
Solo crea. Si el repo/pipeline ya existe, aborta.

Prerrequisitos: az login + az devops login + defaults org/project.
EOF
}

# --- Guardrails: rechazar invocaciones peligrosas ---
for arg in "$@"; do
  case "$arg" in
    --delete|--destroy|--force|--force-with-lease|-rf|--rm|--remove|delete|destroy)
      echo "ERROR SEGURIDAD: argumento prohibido '${arg}'. Este script solo CREA."
      exit 2
      ;;
  esac
done

# Wrapper: solo permite subcomandos az explícitamente seguros
az_safe() {
  # $1 = resource (repos|pipelines), $2 = verb, resto = args
  local resource="${1:-}"
  local verb="${2:-}"
  shift 2 || true

  case "${resource}:${verb}" in
    repos:create|repos:show|pipelines:create|pipelines:show) ;;
    repos:update)
      # Solo --default-branch está permitido (sin delete)
      local joined=" $* "
      if [[ "$joined" == *" delete"* ]] || [[ "$joined" == *"--delete"* ]]; then
        echo "ERROR SEGURIDAD: az repos update con delete está prohibido"
        exit 2
      fi
      if [[ "$joined" != *" --default-branch "* ]] && [[ "$joined" != *" --default-branch="* ]]; then
        echo "ERROR SEGURIDAD: az repos update solo permitido con --default-branch"
        exit 2
      fi
      ;;
    devops:configure) ;;
    *)
      echo "ERROR SEGURIDAD: comando az no permitido: az ${resource} ${verb}"
      echo "Allowlist: repos create|show|update(--default-branch), pipelines create|show, devops configure"
      exit 2
      ;;
  esac

  az "${resource}" "${verb}" "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_NAME="$2"; shift 2 ;;
    --bundle) BUNDLE_NAME="$2"; shift 2 ;;
    --org) ORG="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --pipeline-only) PIPELINE_ONLY=1; shift ;;
    --skip-pipeline) SKIP_PIPELINE=1; shift ;;
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

if [[ -z "$ORG" || -z "$PROJECT" ]]; then
  echo "ERROR: faltan --org y --project (o ADO_ORG y ADO_PROJECT)"
  usage
  exit 1
fi

ORG_NAME="${ORG##*/}"
REPO_PATH="${ROOT_DIR}/${REPO_NAME}"
YAML_PATH=".azure-pipelines/${BUNDLE_NAME}_cd.yml"
SSH_URL="git@ssh.dev.azure.com:v3/${ORG_NAME}/${PROJECT}/${REPO_NAME}"
PIPELINE_NAME="${REPO_NAME}"

az_safe devops configure --defaults organization="${ORG}" project="${PROJECT}" >/dev/null

create_pipeline() {
  if az_safe pipelines show --name "${PIPELINE_NAME}" >/dev/null 2>&1; then
    echo "ERROR SEGURIDAD: el pipeline ya existe (${PIPELINE_NAME}). No se sobrescribe ni se elimina."
    exit 1
  fi
  echo "Creando pipeline ADO: ${PIPELINE_NAME} -> ${YAML_PATH}"
  az_safe pipelines create \
    --name "${PIPELINE_NAME}" \
    --repository "${REPO_NAME}" \
    --repository-type tfsgit \
    --branch dev \
    --yml-path "${YAML_PATH}" \
    --skip-first-run true \
    -o json
}

if [[ "$PIPELINE_ONLY" -eq 1 ]]; then
  create_pipeline
  exit 0
fi

if [[ ! -d "$REPO_PATH" ]]; then
  echo "ERROR: no existe scaffold local: $REPO_PATH"
  echo "Ejecuta primero scaffold_repo.sh"
  exit 1
fi

if az_safe repos show --repository "${REPO_NAME}" >/dev/null 2>&1; then
  echo "ERROR SEGURIDAD: el repo ya existe en ADO: ${REPO_NAME}"
  echo "No se elimina ni se sobrescribe. Elige otro nombre o continúa manualmente."
  exit 1
fi

echo "Creando repo ADO: ${REPO_NAME}"
az_safe repos create --name "${REPO_NAME}" -o json >/dev/null

cd "${REPO_PATH}"

if [[ ! -d .git ]]; then
  git init -b dev
fi

# Solo limpia la entrada local 'origin' del .git/config (NO borra el repo remoto).
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "${SSH_URL}"
else
  git remote add origin "${SSH_URL}"
fi

git add -A
if git diff --cached --quiet; then
  echo "WARN: no hay cambios para commit"
else
  git commit -m "$(cat <<EOF
chore: scaffold inicial DAB ${BUNDLE_NAME}

Estructura estándar con pipeline de despliegue y job inicial.
EOF
)"
fi

# Asegurar rama local dev
current="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current" != "dev" ]]; then
  git branch -M dev
fi

echo "Push rama dev (sin --force)..."
git push -u origin dev

echo "Crear y push rama main (sin --force)..."
if git show-ref --verify --quiet refs/heads/main; then
  echo "WARN: rama local main ya existe; se reutiliza (no se force-push)"
else
  git branch main
fi
git push -u origin main

echo "Default branch = dev"
az_safe repos update --repository "${REPO_NAME}" --default-branch dev -o none

if [[ "$SKIP_PIPELINE" -eq 0 ]]; then
  create_pipeline
fi

WEB_URL="${ORG}/${PROJECT}/_git/${REPO_NAME}"
echo ""
echo "OK (create-only; ningún delete ejecutado)"
echo "  repo:     ${WEB_URL}"
echo "  ssh:      ${SSH_URL}"
echo "  pipeline: ${PIPELINE_NAME}"
echo "  yaml:     ${YAML_PATH}"
echo "  local:    ${REPO_PATH}"
