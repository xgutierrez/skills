#!/usr/bin/env bash
# Publica la carpeta de una empresa en su propio repositorio, o trae los cambios
# que su equipo hizo allí. Usa git subtree: el repositorio de la empresa contiene
# exactamente lo que hay en empresas/<empresa>/, con su historial.
#
# Uso:
#   ./sincronizar-empresa.sh pronaca subir   publica empresas/pronaca en su repositorio
#   ./sincronizar-empresa.sh pronaca traer   trae a empresas/pronaca lo que cambió el equipo
#
# La primera vez, añade el repositorio de la empresa como remoto (debe estar vacío):
#   git remote add empresa-pronaca <url del repositorio de pronaca>
#
# Nunca fuerza: si el push es rechazado porque el equipo subió cambios, ejecuta
# primero "traer" y luego "subir".
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
EMPRESA="${1:-}"
ACCION="${2:-}"
RAMA="main"

uso() { sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
[[ -n "$EMPRESA" && ( "$ACCION" == "subir" || "$ACCION" == "traer" ) ]] || uso

cd "$REPO"
CARPETA="empresas/$EMPRESA"
REMOTO="empresa-$EMPRESA"

[[ -d "$CARPETA" ]] || { echo "No existe $CARPETA."; exit 1; }
if ! git remote get-url "$REMOTO" >/dev/null 2>&1; then
  echo "Falta el remoto $REMOTO. Añádelo una vez con:"
  echo "  git remote add $REMOTO <url del repositorio de $EMPRESA>"
  exit 1
fi
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Hay cambios sin confirmar. Haz commit (o stash) antes de sincronizar."
  exit 1
fi

case "$ACCION" in
  subir)
    echo "Publicando $CARPETA en $REMOTO/${RAMA}…"
    if ! git subtree push --prefix="$CARPETA" --rejoin "$REMOTO" "$RAMA"; then
      echo
      echo "El push fue rechazado: probablemente el equipo subió cambios."
      echo "Ejecuta primero: ./sincronizar-empresa.sh $EMPRESA traer"
      exit 1
    fi
    ;;
  traer)
    echo "Trayendo $REMOTO/$RAMA a ${CARPETA}…"
    git subtree pull --prefix="$CARPETA" "$REMOTO" "$RAMA" \
      -m "Trae los cambios del repositorio de $EMPRESA"
    ;;
esac

echo "Listo."
