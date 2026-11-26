# Plantilla de `AGENTS.md`

Los textos entre «comillas angulares» son instrucciones para ti: sustitúyelos
siempre y no dejes ninguno. Elimina la sección que no aplique en lugar de dejarla
vacía. El resultado debe tener menos de 200 líneas.

````markdown
# «nombre del proyecto»: guía para agentes de IA

«Dos o tres frases: qué hace el proyecto, para quién y con qué tecnología.»

Perfil de estándares: «empresa»

Responde y documenta en español. Los nombres de tablas, columnas y jobs no se traducen.
Aplica la skill `estandares-datos` a todo lo que crees o edites.

## Mapa rápido

| Necesitas | Está en |
|---|---|
| «reglas y constantes compartidas» | `«ruta»` |
| «definición del job» | `«ruta»` |
| «cargas, por etapa» | `«ruta»` |
| «validaciones» | `«ruta»` |
| «documentación» | `docs/` (índice en `README.md`) |

## Cómo fluye

«De 3 a 6 líneas: el orden real de las tareas y qué produce cada una. Sin diagrama:
el agente lee texto. Enlaza a `docs/02_arquitectura.md` para el detalle.»

## Comandos

```bash
«validar»
«desplegar en desarrollo»
«ejecutar»
```

## Reglas que no se pueden romper

«Lista numerada de invariantes: reglas de negocio, identidades que deben cerrar,
contratos de columnas, dónde vive la única copia de cada regla. Cada una en una
frase, con el archivo donde se aplica.»

## Antes de cambiar algo

- «Qué leer antes de tocar cada tipo de cosa: "antes de tocar una fórmula, lee
  `docs/…`".»
- «Dónde se cambia cada tipo de regla, para no duplicarla.»
- «Qué hay que recargar o volver a ejecutar después de un cambio.»

## Cómo comprobar un cambio

«Pasos concretos: comando de validación, notebooks de control, qué resultado
esperar y qué tolerancia se admite.»

## No hagas esto sin confirmación de una persona

- «Desplegar o ejecutar contra producción.»
- «Cambiar valores acordados con negocio (ajustes fijos, perímetros).»
- «Hacer commit o push.»
- «Lo que aplique a este proyecto.»

## Trampas conocidas

«Lo que parece un error y no lo es; limitaciones aceptadas; comportamientos
sorprendentes. Cada una con su explicación en una línea y, si existe, el enlace a
la brecha o decisión que la documenta.»

## Convenciones

«Nombres de notebooks, tablas y jobs; parámetros estándar; catálogos por ambiente;
estilo de código y de comentarios propio del repositorio.»

## Mantener la documentación

Si cambias una regla, una tabla, un parámetro o una tarea del job, actualiza en el
mismo cambio el documento que lo describe: «tabla breve de qué cambio toca qué
documento».
````

`CLAUDE.md`, también en la raíz, contiene solo esto:

```markdown
@AGENTS.md
```

Así Claude Code carga el mismo contenido y hay una sola copia que mantener. Si
hiciera falta una instrucción solo para Claude Code, va debajo de esa línea.
