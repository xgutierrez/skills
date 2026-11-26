#!/usr/bin/env bash
# Deja un equipo listo para trabajar en Pronaca.
#
# Qué hace, en orden:
#   1. Comprueba que estén las herramientas: git, python3, databricks y az.
#   2. Instala las skills de este repositorio (llama a instalar.sh).
#   3. Lee los workspaces de empresa/identificadores.md y, por cada uno,
#      crea el perfil de la CLI de Databricks que falte. Para eso abre el navegador
#      y tú inicias sesión: no se copia ni se guarda ningún token en este repositorio.
#   4. Comprueba la sesión de Azure contra el tenant de la empresa y, si falta,
#      ofrece iniciarla.
#   5. Deja configurados la organización y el proyecto por defecto de Azure DevOps.
#   6. Muestra un resumen de lo que quedó listo y de lo que falta.
#
# Qué NO hace: no copia credenciales, no toca tus repositorios de trabajo, no
# despliega nada y no borra perfiles existentes. Antes de cada inicio de sesión
# pregunta; se puede ejecutar las veces que haga falta.
#
# Uso:
#   ./configurar-equipo.sh
#   ./configurar-equipo.sh --solo-revisar    no cambia nada
#   ./configurar-equipo.sh --si              no pregunta antes de cada login
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
EMPRESA="pronaca"
SOLO_REVISAR=0
SIN_PREGUNTAR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --solo-revisar) SOLO_REVISAR=1; shift ;;
    --si) SIN_PREGUNTAR=1; shift ;;
    -h|--help) sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Argumento desconocido: $1"; exit 1 ;;
  esac
done

IDENT="$REPO/empresa/identificadores.md"
if [[ ! -f "$IDENT" ]]; then
  echo "No existe $IDENT"
  exit 1
fi

PENDIENTES=()
ok()      { echo "  [OK]    $1"; }
falta()   { echo "  [FALTA] $1"; PENDIENTES+=("$1"); }
titulo()  { echo; echo "== $1"; }

confirmar() {  # confirmar "<pregunta>"
  [[ "$SOLO_REVISAR" -eq 1 ]] && return 1
  [[ "$SIN_PREGUNTAR" -eq 1 ]] && return 0
  local respuesta
  read -r -p "  $1 [s/N] " respuesta
  [[ "$respuesta" =~ ^[sS]$ ]]
}

# Devuelve el valor de una fila "| Dato | `valor` |" del archivo de identificadores.
valor_de() { grep -m1 -E "^\| *$1 *\|" "$IDENT" | awk -F'|' '{print $3}' | tr -d '` ' ; }

# ---------------------------------------------------------------- 1. Herramientas
titulo "Herramientas"
for herramienta in git python3 databricks az; do
  if command -v "$herramienta" >/dev/null 2>&1; then
    ok "$herramienta"
  else
    falta "instalar $herramienta"
  fi
done

# ---------------------------------------------------------------------- 2. Skills
titulo "Skills"
if [[ "$SOLO_REVISAR" -eq 1 ]]; then
  for destino in "$HOME/.claude/skills" "$HOME/.grok/skills"; do
    if [[ -d "$destino" ]]; then
      n="$(find "$destino" -maxdepth 1 -type l -lname "$REPO/*" | wc -l | tr -d ' ')"
      echo "  $destino: $n skills de este repositorio"
    fi
  done
else
  "$REPO/instalar.sh" | sed 's/^/  /'
fi

# ------------------------------------------------------ 3. Perfiles de Databricks
titulo "Workspaces de Databricks"
if command -v databricks >/dev/null 2>&1; then
  # Filas de la tabla: | `perfil` | Empresa | `ambiente` | `https://...` |
  grep -E '^\| *`[A-Za-z0-9_]+` *\|.*https://' "$IDENT" | while IFS='|' read -r _ perfil _ _ host _; do
    perfil="$(echo "$perfil" | tr -d '` ')"
    host="$(echo "$host" | tr -d '` ')"
    if grep -q "^\[$perfil\]" "$HOME/.databrickscfg" 2>/dev/null; then
      # El perfil existe; se comprueba que la sesión siga vigente.
      if databricks current-user me --profile "$perfil" >/dev/null 2>&1; then
        echo "  [OK]    $perfil -> $host"
      else
        echo "  [FALTA] $perfil existe pero la sesión venció"
        if confirmar "¿Renovar la sesión de $perfil ahora?" </dev/tty; then
          databricks auth login --host "$host" --profile "$perfil" </dev/tty
        fi
      fi
    else
      echo "  [FALTA] perfil $perfil -> $host"
      if confirmar "¿Crear el perfil $perfil e iniciar sesión en el navegador?" </dev/tty; then
        databricks auth login --host "$host" --profile "$perfil" </dev/tty
      fi
    fi
  done
else
  falta "CLI de Databricks: sin ella no se crean los perfiles"
fi

# --------------------------------------------------------------------- 4. Azure
titulo "Azure"
TENANT="$(valor_de 'Tenant')"
if command -v az >/dev/null 2>&1; then
  ACTUAL="$(az account show --query tenantId -o tsv 2>/dev/null || true)"
  if [[ -n "$TENANT" && "$ACTUAL" == "$TENANT" ]]; then
    ok "sesión iniciada en el tenant de $EMPRESA"
  else
    echo "  [FALTA] sin sesión en el tenant de $EMPRESA"
    if [[ -n "$TENANT" ]] && confirmar "¿Iniciar sesión en Azure ahora?"; then
      az login --tenant "$TENANT" >/dev/null && ok "sesión iniciada"
    else
      PENDIENTES+=("az login --tenant <tenant de $EMPRESA>")
    fi
  fi

  # ---------------------------------------------------------- 5. Azure DevOps
  ORG="$(valor_de 'Organización')"
  PROYECTO="$(valor_de 'Proyecto')"
  if [[ -n "$ORG" && -n "$PROYECTO" ]]; then
    if [[ "$SOLO_REVISAR" -eq 1 ]]; then
      echo "  Azure DevOps por defecto sería: $ORG / $PROYECTO"
    elif az extension show --name azure-devops >/dev/null 2>&1; then
      az devops configure --defaults organization="$ORG" project="$PROYECTO" && ok "Azure DevOps por defecto: $PROYECTO"
    else
      falta "extensión de Azure DevOps: az extension add --name azure-devops"
    fi
  fi
fi

# ------------------------------------------------------------------- 6. Resumen
titulo "Resumen"
if [[ ${#PENDIENTES[@]} -eq 0 ]]; then
  echo "  Equipo listo para trabajar con $EMPRESA."
else
  echo "  Queda pendiente:"
  printf '    - %s\n' "${PENDIENTES[@]}"
fi
echo "  Abre una sesión nueva de Claude Code o de Cursor para que cargue las skills."
