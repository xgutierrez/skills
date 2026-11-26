#!/usr/bin/env bash
# Enlaza todas mis skills en el Mac (o en Linux), desde este único repositorio.
#
#   personal/*                ->  ~/.agents/skills/   (Cursor, Grok, Codex, ChatGPT de escritorio)
#   empresas/<e>/skills/*     ->  ~/.claude/skills/   (Claude Code, Cursor y Grok)
#
# Cada skill va a una sola carpeta para que ninguna herramienta la vea dos veces:
# Cursor y Grok leen las dos. Claude Code no lee ~/.agents/skills; las skills
# personales le llegan por la cuenta de Claude (sube los .zip de crear-zips.sh).
#
# Uso:
#   ./instalar.sh                     personal + todas las empresas de empresas/
#   ./instalar.sh --empresa pronaca   personal + solo esa empresa (se puede repetir)
#   ./instalar.sh --sin-empresas      solo personal
#   ./instalar.sh --claude            además enlaza personal/ en ~/.claude/skills
#   ./instalar.sh --codex             además enlaza las empresas en ~/.agents/skills
#   ./instalar.sh --reemplazar        mueve a un respaldo lo que exista con el mismo nombre
#   ./instalar.sh --desinstalar       quita los enlaces que apuntan a este repositorio
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CLAUDE="$HOME/.claude/skills"
AGENTS="$HOME/.agents/skills"
RESPALDO="$HOME/.respaldo-skills/$(date +%Y%m%d-%H%M%S)"
REEMPLAZAR=0
DESINSTALAR=0
SIN_EMPRESAS=0
PERSONAL_EN_CLAUDE=0
EMPRESAS_EN_AGENTS=0
EMPRESAS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --empresa) EMPRESAS+=("$2"); shift 2 ;;
    --sin-empresas) SIN_EMPRESAS=1; shift ;;
    --claude) PERSONAL_EN_CLAUDE=1; shift ;;
    --codex) EMPRESAS_EN_AGENTS=1; shift ;;
    --reemplazar) REEMPLAZAR=1; shift ;;
    --desinstalar) DESINSTALAR=1; shift ;;
    -h|--help) sed -n '2,19p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Argumento desconocido: $1"; exit 1 ;;
  esac
done

if [[ "$SIN_EMPRESAS" -eq 0 && ${#EMPRESAS[@]} -eq 0 ]]; then
  for carpeta in "$REPO"/empresas/*/; do
    [[ -d "${carpeta}skills" ]] && EMPRESAS+=("$(basename "$carpeta")")
  done
fi
for empresa in ${EMPRESAS[@]+"${EMPRESAS[@]}"}; do
  [[ -d "$REPO/empresas/$empresa/skills" ]] || { echo "No existe empresas/$empresa/skills."; exit 1; }
done

es_nuestro() { [[ -L "$1" && "$(readlink "$1")" == "$REPO"/* ]]; }

enlazar() {  # enlazar <origen> <enlace>
  local origen="$1" enlace="$2" nombre etiqueta
  nombre="$(basename "$enlace")"; etiqueta="$(basename "$(dirname "$(dirname "$enlace")")")"
  if [[ -L "$enlace" && "$(readlink "$enlace")" == "$origen" ]]; then
    echo "  ya estaba   $nombre"
  elif es_nuestro "$enlace"; then
    rm "$enlace"; ln -s "$origen" "$enlace"; echo "  actualizado $nombre"
  elif [[ -L "$enlace" && ! -e "$enlace" ]]; then
    # Enlace roto (apunta a una carpeta que ya no existe): se reemplaza sin preguntar.
    rm "$enlace"; ln -s "$origen" "$enlace"; echo "  reparado    $nombre (el enlace anterior estaba roto)"
  elif [[ -e "$enlace" || -L "$enlace" ]]; then
    if [[ "$REEMPLAZAR" -eq 1 ]]; then
      mkdir -p "$RESPALDO/$etiqueta"
      mv "$enlace" "$RESPALDO/$etiqueta/$nombre"
      ln -s "$origen" "$enlace"
      echo "  reemplazado $nombre (respaldo en $RESPALDO/$etiqueta/)"
    else
      echo "  OMITIDO     $nombre: ya existe y no viene de este repositorio (usa --reemplazar)"
    fi
  else
    ln -s "$origen" "$enlace"; echo "  instalado   $nombre"
  fi
}

enlazar_carpeta() {  # enlazar_carpeta <carpeta con skills> <destino>
  local origen="$1" destino="$2" skill
  for skill in "$origen"/*/; do
    [[ -f "${skill}SKILL.md" ]] || continue
    enlazar "${skill%/}" "$destino/$(basename "$skill")"
  done
}

if [[ "$DESINSTALAR" -eq 1 ]]; then
  for destino in "$CLAUDE" "$AGENTS" "$HOME/.cursor/skills" "$HOME/.grok/skills"; do
    [[ -d "$destino" ]] || continue
    echo "== $destino"
    for enlace in "$destino"/*; do
      if es_nuestro "$enlace"; then rm "$enlace"; echo "  quitado     $(basename "$enlace")"; fi
    done
  done
  exit 0
fi

mkdir -p "$AGENTS"
[[ -d "$HOME/.claude" ]] && mkdir -p "$CLAUDE"

# Quita enlaces de este repositorio cuya skill ya no existe.
for destino in "$CLAUDE" "$AGENTS"; do
  [[ -d "$destino" ]] || continue
  for enlace in "$destino"/*; do
    if es_nuestro "$enlace" && [[ ! -e "$enlace" ]]; then
      rm "$enlace"; echo "  quitado     $(basename "$enlace") (ya no existe en el repositorio)"
    fi
  done
done

echo "== personal -> $AGENTS"
enlazar_carpeta "$REPO/personal" "$AGENTS"
if [[ "$PERSONAL_EN_CLAUDE" -eq 1 && -d "$CLAUDE" ]]; then
  echo "== personal -> $CLAUDE"
  enlazar_carpeta "$REPO/personal" "$CLAUDE"
fi

for empresa in ${EMPRESAS[@]+"${EMPRESAS[@]}"}; do
  if [[ -d "$CLAUDE" ]]; then
    echo "== $empresa -> $CLAUDE"
    enlazar_carpeta "$REPO/empresas/$empresa/skills" "$CLAUDE"
  else
    echo "· Claude Code no está instalado; $empresa se enlaza en $AGENTS."
    enlazar_carpeta "$REPO/empresas/$empresa/skills" "$AGENTS"
  fi
  if [[ "$EMPRESAS_EN_AGENTS" -eq 1 && -d "$CLAUDE" ]]; then
    echo "== $empresa -> $AGENTS (--codex)"
    enlazar_carpeta "$REPO/empresas/$empresa/skills" "$AGENTS"
  fi
done

echo
echo "Listo. Abre una sesión nueva en cada herramienta para que cargue los cambios."
