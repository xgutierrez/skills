# skills-pronaca

El estándar de ingeniería de datos de Pronaca, escrito como *skills* para agentes de
IA (Claude Code, Cursor, Grok y Codex). Lo usa todo el equipo: quien mejora una skill la
mejora para todos.

Este repositorio es **privado**: `empresa/identificadores.md` no tiene secretos,
pero sí información interna. Nunca se guardan contraseñas ni tokens.

## Qué hay

| Skill | Para qué | Cuando digo… |
|---|---|---|
| [`estandares-datos`](skills/estandares-datos/SKILL.md) | Las reglas: Python, notebooks, tablas, medallón y bundles. Incluye el revisor | "revisa si cumple el estándar", "valida el bundle" |
| [`crear-repo-bundle`](skills/crear-repo-bundle/SKILL.md) | Crea un repositorio nuevo con su bundle, ramas y pipeline. Solo crea, nunca borra | "crea un repo nuevo" |
| [`crear-ingesta`](skills/crear-ingesta/SKILL.md) | Arma el flujo completo de una fuente: conexión, volumen, bronze, silver y job | "ingesta la fuente X" |
| [`crear-notebook`](skills/crear-notebook/SKILL.md) | Genera un notebook con la estructura de su capa | "crea el silver de X" |
| [`crear-tabla`](skills/crear-tabla/SKILL.md) | Genera el DDL de una tabla administrada, optimizada y comentada | "crea la tabla fac_ventas" |
| [`avisos-proceso`](skills/avisos-proceso/SKILL.md) | Correos de inicio y fin de un proceso con plantilla fija | "añade avisos al job" |
| [`crear-agents-md`](skills/crear-agents-md/SKILL.md) | Crea el `AGENTS.md` de un repositorio | "crea el AGENTS.md" |
| [`documentar-proyecto`](skills/documentar-proyecto/SKILL.md) | Documenta un repositorio con diagramas | "documenta este proyecto" |
| [`pronaca-data-factory`](skills/pronaca-data-factory/SKILL.md) | Consulta las fábricas de Data Factory de Pronaca y Toledano | "el ADF de pronaca dev" |
| [`pronaca-historias-usuario-ado`](skills/pronaca-historias-usuario-ado/SKILL.md) | Crea historias de usuario y tareas en Azure DevOps | "crea la HU de…" |
| [`genie-pruebas`](skills/genie-pruebas/SKILL.md) | Prueba y compara el Supervisor MIA y los Genie de dev y prd | "@dev ventas…", "compara supervisor vs Genie" |
| [`cotizar-sandbox-databricks`](skills/cotizar-sandbox-databricks/SKILL.md) | Estima el costo de un sandbox con el consumo real y arma el correo | "cotiza un sandbox" |

```
fuente ──> volumen ──> bronze ──> silver ──> gold (fac_ / dim_)
  ext_       raw/       brz_       slv_        gld_
```

La carpeta [`empresa/`](empresa/) tiene lo que las skills leen de Pronaca:

| Archivo | Contenido |
|---|---|
| `perfil.md` | Convenciones: catálogos, scopes, etiquetas, nombres, zona horaria |
| `identificadores.md` | Workspaces de Databricks y sus perfiles, organización de git, tenant, suscripción |
| `avisos/` | Plantillas de correo con la marca |
| `*.local.md` | Cifras de negocio: **no se suben** (están en `.gitignore`) |

## Instalar

### Windows (Cursor)

Clona el repositorio dentro de la carpeta de skills de Cursor. No hace falta ningún
script: Cursor busca las skills dentro de las subcarpetas.

```powershell
git clone <url-del-repo> "$env:USERPROFILE\.cursor\skills\skills-pronaca"
```

Abre Cursor, ve a **Customize → Skills** y comprueba que aparecen.

### Mac (Claude Code, Cursor, Grok y Codex)

```bash
git clone <url-del-repo> ~/skills-pronaca
~/skills-pronaca/instalar.sh
```

`instalar.sh` crea un enlace por skill en `~/.claude/skills/`, que leen Claude Code,
Cursor y Grok. Cada skill va a una sola carpeta para que ninguna herramienta la vea
dos veces.

Para Codex o ChatGPT de escritorio, añade `--codex`: enlaza también en
`~/.agents/skills/`. Como Cursor y Grok leen las dos carpetas, revisa después que no
salgan repetidas.

No las subas a tu cuenta de Claude ni de ChatGPT: llevan información interna.

Para dejar además la CLI de Databricks, Azure y Azure DevOps listas:

```bash
~/skills-pronaca/configurar-equipo.sh --solo-revisar   # solo mira
~/skills-pronaca/configurar-equipo.sh                  # arregla lo que falte
```

### Si dice OMITIDO

Ya hay en `~/.claude/skills` una carpeta con ese nombre que no es un enlace a este
repositorio (una copia vieja). Para dejar la última versión:

```bash
./instalar.sh --reemplazar
```

Mueve lo viejo a un respaldo (el mensaje dice dónde) y crea el enlace. No borra nada.
En Windows: borra o renombra la carpeta vieja en `%USERPROFILE%\.cursor\skills\` y
clona de nuevo.

## Mantener al día

| Equipo | Para actualizar |
|---|---|
| Windows | `git pull` en `%USERPROFILE%\.cursor\skills\skills-pronaca` |
| Mac | `git pull`; `./instalar.sh` solo si se añadió o quitó una skill |

Después, abre una sesión nueva: las herramientas leen las skills al iniciar.

## Mejorar una skill

1. Abre la carpeta del repositorio en Cursor o Claude Code.
2. Pide el cambio ("actualiza crear-tabla con…") y revisa el diff.
3. Haz commit y push. Los demás lo reciben con `git pull`.

Las skills se editan aquí, nunca en `~/.claude/skills/`: ahí solo hay enlaces.

## Revisar un repositorio

```bash
python3 skills/estandares-datos/scripts/revisar_estandar.py <ruta_repo> --resumen
```

## De dónde salen las reglas

Cada regla indica su origen en
[`fuentes.md`](skills/estandares-datos/references/fuentes.md): documentación oficial
de Databricks, los PEP de Python (8, 257 y 484) o una decisión propia.

## Cómo llega aquí

Este repositorio es la carpeta `empresas/pronaca/` del repositorio personal de su
autor, publicada con `git subtree`. Quien lo mantiene edita allí y publica con
`sincronizar-empresa.sh pronaca subir`; lo que mejore el equipo aquí se trae de vuelta
con `traer`. Por eso no se reescribe el historial ni se fuerzan pushes.

## Estructura

```
skills-pronaca/
├── instalar.sh            enlaza las skills (Mac)
├── configurar-equipo.sh   skills, perfiles de Databricks y sesiones de Azure
├── empresa/               perfil, identificadores y avisos de Pronaca
└── skills/                una carpeta por skill, cada una con su SKILL.md
```
