#!/usr/bin/env bash
# Enlaza las skills de este repositorio en el Mac (o en Linux).
#
# Crea un enlace por skill hacia este repositorio, así que un `git pull` actualiza
# todo sin volver a instalar.
#
#   skills/*  ->  ~/.claude/skills/   (lo leen Claude Code, Cursor y Grok)
#             ->  ~/.agents/skills/   (Codex y ChatGPT de escritorio, solo con --codex)
#
# Cada skill va a una sola carpeta para que ninguna herramienta la vea dos veces:
# Cursor y Grok leen tanto ~/.claude/skills como ~/.agents/skills. Usa --codex solo
# si trabajas lo de Pronaca en Codex, y revisa en Cursor que no salgan repetidas.
#
# En Windows no hace falta este script: clona el repositorio dentro de
# %USERPROFILE%\.cursor\skills\ y Cursor encuentra las skills solo.
#
# Uso:
#   ./instalar.sh                 instala o actualiza los enlaces
#   ./instalar.sh --codex         además enlaza en ~/.agents/skills
#   ./instalar.sh --reemplazar    mueve a un respaldo lo que exista con el mismo nombre
#   ./instalar.sh --desinstalar   quita los enlaces que apuntan a este repositorio
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
DESTINOS=("$HOME/.claude/skills")
RESPALDO="$HOME/.respaldo-skills/$(date +%Y%m%d-%H%M%S)"
REEMPLAZAR=0
DESINSTALAR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex) DESTINOS+=("$HOME/.agents/skills"); shift ;;
    --reemplazar) REEMPLAZAR=1; shift ;;
    --desinstalar) DESINSTALAR=1; DESTINOS=("$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.grok/skills" "$HOME/.cursor/skills"); shift ;;
    -h|--help) sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Argumento desconocido: $1"; exit 1 ;;
  esac
done

# Un enlace es "nuestro" si apunta dentro de este repositorio, exista o no su destino.
es_nuestro() { [[ -L "$1" && "$(readlink "$1")" == "$REPO"/* ]]; }

enlazar() {  # enlazar <origen> <enlace> <etiqueta>
  local origen="$1" enlace="$2" etiqueta="$3" nombre
  nombre="$(basename "$enlace")"
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

for destino in "${DESTINOS[@]}"; do
  herramienta="$(basename "$(dirname "$destino")")"
  if [[ "$destino" != */.agents/skills && ! -d "$(dirname "$destino")" ]]; then
    echo "· $herramienta no está instalado en este equipo; se omite."
    continue
  fi
  if [[ "$DESINSTALAR" -eq 1 && ! -d "$destino" ]]; then continue; fi
  mkdir -p "$destino"
  echo "== $destino"

  if [[ "$DESINSTALAR" -eq 1 ]]; then
    for enlace in "$destino"/*; do
      if es_nuestro "$enlace"; then rm "$enlace"; echo "  quitado     $(basename "$enlace")"; fi
    done
    continue
  fi

  # Quita enlaces de este repositorio cuya skill ya no existe.
  for enlace in "$destino"/*; do
    if es_nuestro "$enlace" && [[ ! -e "$enlace" ]]; then
      rm "$enlace"; echo "  quitado     $(basename "$enlace") (ya no existe en el repositorio)"
    fi
  done

  for skill in "$REPO"/skills/*/; do
    [[ -f "${skill}SKILL.md" ]] || continue
    enlazar "${skill%/}" "$destino/$(basename "$skill")" "$herramienta"
  done
done

echo
echo "Listo. Abre una sesión nueva en cada herramienta para que cargue los cambios."
