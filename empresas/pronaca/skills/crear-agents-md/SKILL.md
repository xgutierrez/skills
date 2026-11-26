---
name: crear-agents-md
description: "Crea o actualiza el AGENTS.md (y el CLAUDE.md que lo importa) de un repositorio: la guía que un agente de IA carga al empezar, con el mapa del proyecto, sus comandos, las reglas que no se pueden romper, cómo comprobar un cambio y las trampas conocidas. Usar cuando el usuario pida crear el AGENTS.md, el CLAUDE.md, 'el archivo para el agente', 'prepara este repo para trabajar con IA', 'que el agente entienda este proyecto', o al empezar a trabajar en un repositorio que no lo tiene."
---

# Crear el AGENTS.md de un repositorio

Un agente de IA empieza cada sesión sin saber nada del proyecto y carga
automáticamente un archivo de instrucciones de la raíz. Ese archivo decide si
trabaja bien desde el primer minuto o rompe una regla que nadie le dijo.

Se generan dos archivos en la raíz:

- **`AGENTS.md`**: el contenido. Es el nombre que leen la mayoría de agentes.
- **`CLAUDE.md`**: una sola línea, `@AGENTS.md`, para que Claude Code cargue lo
  mismo sin duplicarlo.

`AGENTS.md` no es un resumen de la documentación. Es lo que un agente necesita para
**actuar** sin romper nada y que no puede deducir rápido del código.

## Flujo de trabajo

### 1. Mirar qué hay

- Si ya existe `AGENTS.md`, `CLAUDE.md` o reglas de otra herramienta
  (`.cursor/rules`, `.cursorrules`), léelos: sus instrucciones vigentes se
  conservan. No borres archivos de otras herramientas.
- Si existe `README.md` o una carpeta `docs/`, léelos: de ahí salen las reglas y
  las trampas, y a ellos se enlaza.
- Revisa `git status`: si hay un `AGENTS.md` con cambios sin confirmar, avisa antes
  de reescribirlo.

### 2. Entender el proyecto

Necesitas, y lo averiguas leyendo el repositorio:

| Dato | Dónde mirarlo |
|---|---|
| Qué hace y para quién | README, documentación, descripción de los jobs |
| Dónde está cada cosa | Estructura de carpetas |
| Cómo se valida, despliega y ejecuta | `databricks.yml`, CI/CD, README |
| En qué orden corre | Definición de los jobs en `resources/` |
| Qué reglas no se pueden romper | Notebooks de configuración, controles que detienen la carga, documentación |
| Qué parece un error y no lo es | Documentación, comentarios, brechas conocidas |
| Convenciones propias | Nombres de notebooks y tablas, estructura de las celdas |

En un proyecto de datos grande, si tienes la skill `documentar-proyecto`, su script
`scripts/inventario.py` da en segundos los jobs, las tareas y las tablas.

Lee los archivos de configuración completos y los notebooks que producen las tablas
finales. No hace falta leer todo: hace falta leer lo que define las reglas.

### 3. Resolver el perfil de la empresa

`AGENTS.md` declara para qué empresa es el repositorio, con la línea
`Perfil de estándares: <empresa>`. Con ella, la skill `estandares-datos` sabe qué
catálogos, etiquetas y scopes usar.

- En los proyectos de Pronaca la línea es `Perfil de estándares: pronaca`.
- Si el proyecto no es de Pronaca, omite la línea.

### 4. Preguntar lo que el código no dice

Una sola ronda, corta, y solo si falta: qué no debe tocar un agente sin permiso,
qué acuerdos con negocio no se pueden cambiar, qué trampas conoce el usuario. Si no
responde, escribe lo que conste en el repositorio y no inventes el resto.

### 5. Escribir

Usa la plantilla de `references/plantilla.md`. Reglas:

- **Menos de 200 líneas.** Se carga entero en cada sesión; cuanto más largo, peor
  lo sigue el agente. El detalle vive en la documentación y aquí se enlaza diciendo
  cuándo leerlo: "antes de tocar una fórmula, lee `docs/…`".
- **Instrucciones concretas y comprobables.** "Ejecuta `databricks bundle validate`
  antes de dar un cambio por terminado" sirve; "valida bien" no.
- **Las reglas que no se pueden romper**, cada una en una frase y con el archivo
  donde se aplica: invariantes de negocio, contratos de columnas, dónde vive la
  única copia de cada regla.
- **Las trampas conocidas**: lo que parece un error y no lo es, lo que no hay que
  "arreglar".
- **Qué requiere confirmación de una persona**: desplegar o ejecutar en producción,
  cambiar valores acordados con negocio, hacer commit o push.
- **Cómo comprobar un cambio**: comandos, validaciones y qué resultado esperar.
- **Nombres y rutas reales**, tal como están en el repositorio.
- **No repitas** lo que el agente ve solo (la lista completa de archivos) ni lo que
  ya dice otro documento.
- **Sin secretos, correos ni identificadores** de workspace.
- **Solo hechos del repositorio.** Si no consta, no se escribe.

Un proyecto pequeño tendrá un `AGENTS.md` corto: está bien. Elimina las secciones
sin contenido.

En un monorepo, el `AGENTS.md` de la raíz cubre lo común; añade uno dentro de un
bundle solo si ese bundle tiene reglas propias.

### 6. Comprobar

- Menos de 200 líneas: `wc -l AGENTS.md`.
- Cada ruta citada existe y cada comando es el real del proyecto.
- Cada función, constante o tabla que nombras aparece en el código.
- No quedan marcadores «…» de la plantilla.
- `CLAUDE.md` contiene `@AGENTS.md`.

Si tienes la skill `documentar-proyecto`, su `scripts/validar_docs.py` comprueba el
largo, los enlaces y los marcadores.

### 7. Entregar

Di qué archivos creaste, qué perfil declaraste, qué reglas y trampas incluiste y de
dónde salieron, y qué quedó por confirmar. No hagas commit: el usuario revisa y
decide.

## Actualizar uno existente

Cuando el proyecto cambie (un job nuevo, una regla nueva, una trampa descubierta):
cambia solo lo afectado, conserva lo demás y vuelve a comprobar el largo. Si
`AGENTS.md` pasa de 200 líneas, mueve el detalle a la documentación y deja el
enlace.
