# Buenas prácticas y fuentes

Cada regla de esta skill sale de una guía pública de una empresa de referencia. Este
archivo dice qué recomienda cada una y cómo se aplicó. Consultado en noviembre de 2026.

## Contenido

1. Databricks: qué documentar por capa, diccionario de datos, linaje
2. Microsoft: diagramas, decisiones de arquitectura, Mermaid en Azure DevOps
3. Google: principios de documentación, README, estilo
4. AWS: registro de decisiones
5. GitHub: diagramas como texto
6. Anthropic: contexto para agentes de IA
7. Resumen: de la práctica a la regla

## Databricks

**Qué documentar en cada capa del medallón.** La guía de despliegue de Databricks
pide documentar, en bronze, las fuentes y los horarios de ingesta; en silver, la
lógica de transformación y las reglas de negocio; en gold, el linaje desde bronze
hasta gold, y publicar los productos de datos con un dueño claro. También pide
documentar la propiedad y el ciclo de vida de las tablas.
→ De ahí salen las tablas de fuentes (con frecuencia), de reglas de negocio y el
diagrama de linaje, y el campo "Responsable".
Fuente: [Phase 6: Design Delta Lake architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/deployment-guide/delta-lake)

**Descripciones, etiquetas y diccionario de datos.** Las buenas prácticas de gobierno
de Databricks recomiendan comentar todas las tablas y columnas, incluyendo origen y
sensibilidad del dato; etiquetar los objetos; mantener un diccionario de datos
estándar con definiciones, formatos y valores aceptables; asignar un dueño a cada
objeto; y revisar a mano los comentarios generados por IA antes de guardarlos.
→ De ahí salen el diccionario de datos de las tablas de consumo, la regla de no
adivinar descripciones ("Por confirmar") y la revisión final del usuario.
Fuente: [Best practices for data and AI governance](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices)

**Linaje.** Unity Catalog registra el linaje automáticamente hasta el nivel de
columna y Databricks recomienda usarlo para analizar el impacto antes de un cambio.
→ El diagrama de linaje de la documentación es un resumen legible; para el detalle
exacto, remite al linaje de Unity Catalog en Catalog Explorer.
Fuente: [Best practices for data and AI governance](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices)

## Microsoft

**Cómo hacer diagramas de arquitectura.** El Azure Well-Architected Framework
recomienda: notación estándar; flechas siempre con dirección y sin doble punta;
etiquetar todo; consistencia de colores y formas; exactitud por encima de la
simplicidad; metadatos en cada diagrama (título, fecha de actualización); leyenda
cuando los estilos tienen significado; no depender solo del color; mostrar por capas
en lugar de sobrecargar (contexto → contenedores → componente o secuencia); y guardar
la fuente del diagrama en el mismo repositorio que el código.
→ Son las reglas de claridad de `diagramas.md`, el orden contexto → flujo → job, el
título y la línea "Cómo leerlo" de cada diagrama, y la elección de Mermaid en texto.
Fuente: [Create architecture design diagrams](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/design-diagrams)

**Diagrama de flujo de datos.** La misma guía define que debe mostrar cómo el dato
entra, se transforma, se almacena y sale, destacando fuentes, destinos, etapas de
transformación y si el movimiento es por lotes o en tiempo real.
→ Es el diagrama 2 y por eso las flechas llevan la frecuencia.
Fuente: [Create architecture design diagrams](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/design-diagrams)

**Registro de decisiones de arquitectura.** Microsoft recomienda registrar cada
decisión relevante con su contexto, opciones y consecuencias, en control de versiones,
y no editar las aceptadas sino reemplazarlas por una nueva.
→ Sección "Decisiones de diseño" y plantilla 7.
Fuente: [Maintain an architecture decision record](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)

**Mermaid en Azure DevOps.** Azure DevOps admite un subconjunto de Mermaid: no admite
la mayoría de etiquetas HTML, Font Awesome, la sintaxis `flowchart` (hay que usar
`graph`) ni la flecha larga `---->`.
→ Reglas de compatibilidad de `diagramas.md` y comprobaciones del validador.
Fuente: [Markdown syntax for files, widgets, wikis](https://learn.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance?view=azure-devops)

## Google

**Principios de documentación.** La guía de estilo de Google propone: documentación
mínima viable (pocos documentos exactos valen más que muchos en mal estado);
actualizar la documentación en el mismo cambio que el código; borrar la documentación
muerta; preferir lo bueno a lo perfecto; y no duplicar (enlazar en lugar de reescribir).
→ Cinco documentos fijos y cortos, eliminar secciones vacías, "una sola fuente de
verdad", enlazar a la documentación oficial y borrar lo ya migrado.
Fuente: [Documentation Best Practices](https://google.github.io/styleguide/docguide/best_practices.html)

**Qué lleva un README.** Debe estar en la raíz y decir para qué sirve el código, a
quién contactar, su estado, cómo usarlo y dónde está la documentación ampliada.
→ Plantilla del README (ficha, estado, inicio rápido, índice).
Fuente: [READMEs](https://google.github.io/styleguide/docguide/READMEs.html)

**Estilo de redacción.** Voz activa, frases claras, texto de enlace descriptivo,
fechas sin ambigüedad.
→ Reglas de estilo del paso "Escribir" y fechas en formato AAAA-MM-DD.
Fuente: [Google developer documentation style guide](https://developers.google.com/style/highlights)

## AWS

**Registro de decisiones.** AWS recomienda un registro por decisión, con contexto,
decisión y consecuencias, un estado visible (propuesta, aceptada, reemplazada) e
inmutabilidad una vez aceptada.
→ Refuerza la plantilla 7.
Fuente: [Architectural decision records: best practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/best-practices.html)

## GitHub

**Diagramas como texto.** GitHub dibuja Mermaid dentro de bloques de código
`mermaid` en archivos Markdown, incidencias y pull requests.
→ Se usa el bloque ```` ```mermaid ````, que funciona también en VS Code y Databricks.
Fuente: [Creating diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)

## Anthropic

**Archivo de instrucciones del proyecto.** La documentación de Claude Code recomienda
un archivo de instrucciones en la raíz con la arquitectura, los comandos y las
convenciones del proyecto; que tenga menos de 200 líneas, porque los archivos largos
consumen contexto y se siguen peor; que use encabezados y viñetas; y que las
instrucciones sean específicas y comprobables ("usa sangría de 2 espacios" en lugar
de "formatea bien"). Para compartir un solo archivo con otros agentes, recomienda
`AGENTS.md` y, donde haga falta, un `CLAUDE.md` que lo importe con `@AGENTS.md`.
→ Paso "Escribir el contexto para agentes de IA" y plantilla 8.
Fuente: [How Claude remembers your project](https://code.claude.com/docs/en/memory)

## Resumen: de la práctica a la regla

| Práctica | Fuente | Dónde se aplica en la skill |
|---|---|---|
| Documentar fuentes y horarios, reglas y linaje por capa | Databricks | `03_fuentes_y_datos.md`, `01_entendimiento.md` |
| Diccionario de datos y dueño por objeto | Databricks | Diccionario y ficha del README |
| Revisar lo que genera la IA | Databricks | "Por confirmar" y resumen final |
| Diagramas por capas, con flechas dirigidas y etiquetas | Microsoft | Juego de cinco diagramas |
| Metadatos y fuente del diagrama en el repositorio | Microsoft | Título, "Cómo leerlo", fecha, Mermaid |
| Registro de decisiones | Microsoft, AWS | "Decisiones de diseño" |
| Documentación mínima, sin duplicar, actualizada con el código | Google | Estructura fija y reglas de estilo |
| README como puerta de entrada | Google | Plantilla del README |
| Instrucciones para agentes: breves, concretas, un solo archivo | Anthropic | `AGENTS.md` y `CLAUDE.md` |
