# skills-pronaca: guía para agentes de IA

Repositorio con el estándar de ingeniería de datos de Pronaca, escrito como skills
para agentes (Claude Code, Cursor, Grok y Codex). Lo usa todo el equipo de datos. No es un
proyecto de datos: aquí se editan instrucciones, plantillas y scripts de apoyo.

Responde y escribe en español.

## Mapa rápido

| Necesitas | Está en |
|---|---|
| Una skill | `skills/<skill>/` |
| Reglas del estándar (Python, notebooks, tablas, bundles) | `skills/estandares-datos/references/` |
| Origen de cada regla | `skills/estandares-datos/references/fuentes.md` |
| Plantillas de bundle | `skills/estandares-datos/assets/bundle/` |
| Convenciones de Pronaca | `empresa/perfil.md` |
| Workspaces, tenant y organización de git | `empresa/identificadores.md` |
| Plantillas de correo con la marca | `empresa/avisos/` |
| Instalación | `instalar.sh` (Mac) y `configurar-equipo.sh` |

Cada skill es una carpeta con un `SKILL.md` (instrucciones) y, si hace falta,
`references/` (detalle que se lee a demanda), `scripts/` (se ejecutan) y `assets/`
(plantillas).

## Cómo llega una skill al agente

- **Mac:** `instalar.sh` crea un enlace por skill en `~/.claude/skills/` (lo leen
  Claude Code, Cursor y Grok); con `--codex`, también en `~/.agents/skills/` para
  Codex. Un cambio aquí se ve en la siguiente sesión, sin reinstalar.
- **Windows:** el repositorio se clona dentro de `%USERPROFILE%\.cursor\skills\` y
  Cursor busca las skills en las subcarpetas. Se actualiza con `git pull`.

Las skills encuentran el perfil en `empresa/`, dos niveles por encima de su carpeta
real. La regla completa está en `skills/estandares-datos/SKILL.md`, sección 1.

## Comandos

```bash
./instalar.sh                                    # enlaza las skills (Mac)
./configurar-equipo.sh --solo-revisar            # estado del equipo, sin cambiar nada
python3 skills/estandares-datos/scripts/revisar_estandar.py <repo> --resumen
python3 skills/crear-notebook/scripts/nuevo_notebook.py --help
bash -n instalar.sh && bash -n configurar-equipo.sh   # sintaxis de los scripts
```

## Reglas que no se pueden romper

1. **Nunca se guardan secretos**: ni contraseñas, ni tokens, ni cadenas de conexión
   con credenciales, en ningún archivo. Las credenciales se obtienen iniciando
   sesión en cada equipo.
2. **Los valores de Pronaca viven en `empresa/`.** Catálogos, scopes, etiquetas,
   organización de git y correos salen del perfil y de los identificadores, no se
   escriben dentro de las skills.
3. **Los archivos `*.local.md` no se suben**: contienen cifras de negocio. Están en
   `.gitignore`; no los renombres ni los cites con su contenido en otro archivo.
4. **Una regla vive en un solo lugar.** Las reglas del estándar están en
   `skills/estandares-datos/references/`; las demás skills las citan, no las copian.
5. **Toda regla indica su origen** en `fuentes.md`: una fuente oficial con su
   enlace, o "decisión propia". No presentes como oficial algo que no lo es.
6. **El encabezado de cada `SKILL.md` es YAML válido**: `name` en minúsculas con
   guiones e igual al nombre de la carpeta; `description` en tercera persona, de
   menos de 1.024 caracteres, diciendo qué hace y cuándo usarla.
7. **Nombres de skill únicos.** Si el nombre se repite en otro repositorio instalado,
   el instalador omite uno de los dos. Las skills propias de una sola área llevan el
   prefijo `pronaca-`.
8. **`SKILL.md` de menos de 500 líneas**; el detalle va en `references/`, enlazado
   directamente desde el `SKILL.md`. Una referencia de más de 100 líneas lleva
   índice.
9. **Los scripts solo dependen de Python 3 o de bash**, son de solo lectura salvo
   que su nombre diga lo contrario, y nunca sobrescriben un archivo existente.
10. **`crear-repo-bundle` solo crea.** Sus protecciones contra borrado
    (`--force`, `--delete`, lista cerrada de comandos `az`) no se quitan ni se
    relajan.

## Antes de cambiar algo

- Para cambiar una regla del estándar, edita la referencia correspondiente y, si la
  regla viene de una fuente, actualiza `fuentes.md`. Si el revisor la comprueba,
  ajusta también `revisar_estandar.py`.
- Para cambiar la estructura de un notebook generado, edita `nuevo_notebook.py` y
  la descripción de esa capa en `references/notebooks.md`: deben decir lo mismo.
- Para añadir una skill, crea su carpeta en `skills/` y añádela a la tabla del
  `README.md`.
- Al mover o renombrar una skill, busca su nombre en todo el repositorio: otras
  skills la citan por nombre.

## Cómo comprobar un cambio

1. `bash -n` sobre los scripts de shell que tocaste; `python3 -m py_compile` sobre
   los de Python.
2. Si cambiaste `nuevo_notebook.py`: genera un notebook de cada tipo en una carpeta
   temporal y ejecuta `revisar_estandar.py` sobre ella. Debe dar cero errores.
3. Si cambiaste `revisar_estandar.py`: ejecútalo sobre un repositorio real con
   `--resumen` y comprueba que termina y que los conteos son razonables.
4. Si cambiaste un `SKILL.md`: comprueba que el encabezado sigue siendo YAML válido
   y que las rutas que cita existen.
5. Antes de confirmar, `git diff --cached` no debe contener tokens ni contraseñas.

## No hagas esto sin confirmación de una persona

- Hacer commit o push.
- Quitar un archivo del `.gitignore` o subir un `*.local.md`.
- Ejecutar `instalar.sh --reemplazar` o `--desinstalar`: mueven o quitan skills
  instaladas en el equipo.
- Ejecutar `configurar-equipo.sh` sin `--solo-revisar`: abre inicios de sesión.
- Ejecutar `skills/crear-repo-bundle/scripts/create_ado.sh`: crea recursos reales
  en Azure DevOps.
- Cambiar un valor de `empresa/perfil.md` o `empresa/identificadores.md`.

## Trampas conocidas

- **Este repositorio se publica desde el repositorio personal de Xavier**
  (`empresas/pronaca/` de `skills`) con `git subtree`. Se puede editar y subir aquí
  con normalidad: él trae los cambios con `sincronizar-empresa.sh pronaca traer`.
  Nunca hagas `push --force` en este repositorio.
- **Los cambios se editan aquí, no en `~/.claude/skills/`.** Esas carpetas son
  enlaces a este repositorio.
- **Una sesión ya abierta no ve los cambios.** La lista de skills se lee al iniciar.
- **`instalar.sh` omite una skill si ya existe otra con el mismo nombre** que no
  viene de este repositorio. Si vienes del repositorio antiguo
  `skills-ingenieria-datos`, quita antes sus enlaces con su
  `instalar.sh --desinstalar`.
- **`skills/estandares-datos/references/bundles-pipelines-declarativos.md` y
  `bundles-alertas.md`** vienen de un kit de Databricks ya retirado y están en
  inglés. Está pendiente reemplazarlos por las skills oficiales.
- **El estándar es más estricto que los repositorios existentes.** Que
  `revisar_estandar.py` dé cientos de errores en un repositorio heredado es lo
  esperado.
- **`2ff814a6-…` en `bundle_cd.yml.tpl` y `499b84ac-…` en la skill de historias**
  no son identificadores privados: son los identificadores públicos de Azure
  Databricks y de Azure DevOps.

## Convenciones

- Carpetas de skill en minúsculas con guiones; en español.
- Instrucciones en imperativo y explicando el porqué, no listas de órdenes en
  mayúsculas.
- Marcadores de plantilla: `{{NOMBRE}}` en plantillas de bundle, `«texto»` en
  plantillas de documentos, `PENDIENTE:` en notebooks generados.
- Mensajes de commit en español, en imperativo, con un resumen de una línea.
