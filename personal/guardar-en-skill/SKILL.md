---
name: guardar-en-skill
description: "Guarda lo aprendido en la conversación en una skill: crea una nueva o mejora una existente en el repo correcto. Úsala cuando digan guarda esto en una skill, crea una skill o mejora la skill X."
---

# Guardar en una skill

Convierte lo que se acaba de resolver en una skill reutilizable, guardada dentro del
repositorio correcto y con el cambio a la vista antes de confirmarlo.

Todo vive en mi repositorio `skills`, separado por quién usa la skill:

| Carpeta | Qué va | Quién lo usa |
|---|---|---|
| `empresas/pronaca/skills/` | El estándar de datos (tablas, notebooks, bundles) y todo lo de Pronaca | Todo el equipo de datos |
| `personal/` | Mi forma de escribir correos y lo que solo me sirve a mí | Solo yo |

Si estás en el repositorio de Pronaca (el que usa el equipo), solo existen sus
skills en `skills/`: guárdalo ahí.

## Pasos

1. **Ubica el repositorio.** Trabaja dentro del clon (tiene un `AGENTS.md` en la
   raíz). Si no estás en uno, pregunta la ruta. Nunca escribas en
   `~/.claude/skills`, `~/.agents/skills`, `~/.cursor/skills` ni `~/.grok/skills`:
   ahí solo hay enlaces, y
   lo que quede fuera del repositorio no tiene respaldo.

2. **Pregunta lo mínimo.** Si no lo dijeron, una sola pregunta con opciones: ¿skill
   nueva o mejora de una existente?, ¿cuál?

3. **Elige la carpeta por quién la usará.** Si le sirve al equipo, o lleva nombres,
   tenant, workspaces o convenciones de Pronaca: `empresas/pronaca/skills/`. Si es
   solo mía: `personal/`. Si dudas, pregunta.

4. **Extrae solo lo reutilizable.** Reglas, pasos y ejemplos que sirvan la próxima
   vez. Deja fuera secretos, contraseñas, tokens, cifras de negocio y datos
   personales de terceros.

5. **Escribe o edita `<carpeta>/<nombre>/SKILL.md`.**
   - Encabezado YAML válido: `name` en minúsculas con guiones e igual al nombre de la
     carpeta; `description` entre comillas, en tercera persona, diciendo qué hace y
     cuándo usarla.
   - En `personal/`, la `description` tiene como máximo **200 caracteres**:
     es el límite para subirla a la app de Claude.
   - Cuerpo en imperativo, explicando el porqué de cada regla. Menos de 500 líneas;
     el detalle va en `references/`, enlazado desde el `SKILL.md`.
   - Una regla vive en un solo lugar: si ya existe en otra skill, cítala.
   - Nombre único en todo el repositorio; lo de una sola área de Pronaca lleva el
     prefijo `pronaca-`.

6. **Sigue el `AGENTS.md` de la raíz y, en `empresas/pronaca/`, también el suyo** para comprobar el cambio (sintaxis de
   scripts, revisor del estándar, rutas citadas).

7. **Muestra el cambio y espera.** Enseña el `git diff`. No hagas commit ni push sin
   que lo confirmen.

8. **Cierra con lo que falta.**
   - Skill nueva en el Mac: correr `./instalar.sh` una vez.
   - Skill de Pronaca: `./sincronizar-empresa.sh pronaca subir` para que la reciba el
     equipo (con su confirmación).
   - Skill de `personal/` que uso en la app de Claude o en ChatGPT web: correr
     `./crear-zips.sh` y volver a subir su `.zip`.
   - En todos los casos: abrir una sesión nueva para que se cargue.
