---
name: documentar-proyecto
description: "Documenta en español un proyecto de datos o de código: entendimiento del negocio, arquitectura, fuentes de datos, tablas y operación, con diagramas Mermaid fáciles de leer, y genera el contexto para agentes de IA (AGENTS.md y CLAUDE.md). Escribe README.md y docs/ con una estructura estándar y reescribe la documentación previa. Usar siempre que el usuario pida documentar, redocumentar o actualizar la documentación de un proyecto, repositorio, bundle de Databricks, pipeline, job, modelo o ingesta; cuando pida un README, un diagrama de arquitectura o de flujo de datos, el linaje, un inventario de fuentes, un diccionario de datos o preparar un repositorio para trabajar con un agente de IA; o cuando diga 'explícame este proyecto por escrito', 'deja documentado esto' o 'qué hace este repo'. Pensada para Databricks (Asset Bundles, medallón, Unity Catalog), Azure Data Factory, Azure DevOps y Power BI; sirve para cualquier repositorio."
---

# Documentar un proyecto

El objetivo es que una persona que no conoce el proyecto lo entienda en diez minutos:
qué problema resuelve, de dónde salen los datos, cómo fluyen, qué entrega y cómo se opera.
La documentación se escribe en español, vive en el repositorio junto al código y cada
afirmación sale del código, no de suposiciones.

## Qué se entrega

Siempre la misma estructura, para que todos los proyectos se lean igual:

| Archivo | Responde a | Lector principal |
|---|---|---|
| `README.md` | ¿Qué es esto y por dónde empiezo? | Cualquiera |
| `docs/01_entendimiento.md` | ¿Qué problema de negocio resuelve y con qué reglas? | Negocio y analistas |
| `docs/02_arquitectura.md` | ¿Cómo está construido y cómo fluyen los datos? | Técnico |
| `docs/03_fuentes_y_datos.md` | ¿De dónde vienen los datos y qué tablas produce? | Técnico y analistas |
| `docs/04_operacion.md` | ¿Cómo se ejecuta, despliega y se resuelve un fallo? | Quien lo mantiene |
| `AGENTS.md` y `CLAUDE.md` | ¿Qué debe saber un agente de IA antes de tocar el código? | Agentes de IA |

Las plantillas exactas están en `references/plantillas.md`. Léelas antes de escribir.

La documentación va por capas: cada documento abre con lo que entiende negocio (un
párrafo y un diagrama) y baja después al detalle técnico. Así un mismo juego de
documentos sirve a los dos públicos sin duplicar nada.

Un proyecto pequeño tendrá documentos cortos; eso está bien. Una sección sin
contenido real se elimina en lugar de rellenarla. Es mejor poca documentación exacta
que mucha en mal estado.

## Flujo de trabajo

### 1. Ubicar el proyecto

Documenta el proyecto que el usuario indique; si no indica ninguno, el directorio
actual. Si la carpeta contiene varios repositorios, pregunta cuál (o confirma que
los quiere todos y hazlos uno por uno; cada repositorio es un trabajo independiente).

Revisa `git status` antes de empezar. Si hay cambios sin confirmar en `README.md` o
`docs/`, avisa al usuario: vas a reescribir esos archivos.

### 2. Levantar el inventario

Ejecuta el script; extrae en segundos lo que a mano tomaría leer cientos de archivos:

```bash
python3 <ruta_skill>/scripts/inventario.py <ruta_proyecto> --salida <carpeta_temporal>/inventario.json
```

El resumen que imprime da los bundles, jobs con sus tareas y dependencias,
programación, notebooks por capa, tablas que escribe y lee, indicios de fuentes
externas, Data Factory, CI/CD y la documentación existente. El JSON trae el detalle
por notebook (parámetros, `%run`, variables de ruta). Guarda el JSON fuera del
repositorio.

Los scripts solo necesitan Python 3. Para leer los YAML usan PyYAML si está
instalado y, si no, Ruby (incluido en macOS); sin ninguno de los dos, el script
avisa y hay que leer los `.yml` a mano o ejecutarlo con `uv run --with pyyaml`.

El script detecta tablas por patrones de texto: es un punto de partida, no la verdad.
`references/leer-el-proyecto.md` explica cómo interpretar cada tipo de proyecto
(bundle de Databricks, Data Factory, notebooks sueltos, monorepo con varios bundles,
proyectos que no son de datos) y qué leer a mano.

### 3. Leer lo que el inventario no puede decir

El inventario dice *qué* hay; el *porqué* está en el código y en los documentos previos.
Lee, en este orden:

1. **La documentación existente completa** (README, `docs/`, celdas Markdown de los
   notebooks). Suele contener reglas de negocio y decisiones que no se deducen del
   código. Es tu materia prima principal para `01_entendimiento.md`. Un README que
   solo trae la plantilla por defecto de Azure DevOps ("TODO: Give a short
   introduction…") no es documentación: se reemplaza sin más.
2. **Los notebooks de configuración** (`cfg_*`, `config/`): catálogos, esquemas,
   constantes y reglas.
3. **Los notebooks que producen las tablas finales** (gold, salidas de modelos,
   exportaciones): definen qué entrega el proyecto y con qué grano. Lee también
   los de creación de tablas (`tbl_*`, DDL): sus `COMMENT` de columna son el
   diccionario de datos ya escrito.
4. **Los notebooks de extracción**: confirman cada fuente externa (sistema, objeto,
   método de conexión).
5. En proyectos grandes, una muestra representativa por carpeta en lugar de todo.

Mientras lees, anota dos listas: **hechos confirmados** (con el archivo que los
respalda) y **dudas** que solo una persona puede responder.

### 4. Preguntar lo que no está en el código

Hay cosas que ningún repositorio dice: quién es el dueño funcional, quién usa el
resultado, por qué existe el proyecto. Si faltan y no están en la documentación
previa, haz al usuario una sola ronda de preguntas breves (máximo cuatro). Si no
responde o no sabe, escribe "Por confirmar" y regístralo en la sección de pendientes.
No inventes responsables, fechas ni cifras: un dato inventado en una documentación
hace desconfiar de todo lo demás.

### 5. Dibujar los diagramas

Los diagramas son lo primero que la gente mira y a menudo lo único. Lee
`references/diagramas.md` antes de dibujar: contiene las reglas de compatibilidad con
Azure DevOps (que dibuja solo un subconjunto de Mermaid), la paleta por capa y un
modelo de cada tipo.

El juego mínimo es:

| # | Diagrama | Dónde va | Qué muestra |
|---|---|---|---|
| 1 | Contexto | `README.md` | El proyecto como una caja: fuentes a la izquierda, consumidores a la derecha |
| 2 | Flujo de datos | `02_arquitectura.md` | Fuente → bronze → silver → gold → consumo, con las tablas reales |
| 3 | Orquestación | `02_arquitectura.md` | Tareas del job y sus dependencias, uno por job |
| 4 | Ambientes y despliegue | `02_arquitectura.md` | Ramas → CI/CD → targets → catálogos |
| 5 | Linaje de tablas | `03_fuentes_y_datos.md` | Qué tabla alimenta a cuál |

Añade otros solo si aclaran algo que el texto no logra (un diagrama entidad-relación
para un modelo dimensional, una secuencia para una integración con una API). Omite el
que no aplique: un proyecto sin CI/CD no lleva diagrama de despliegue.

### 6. Escribir

Sigue las plantillas de `references/plantillas.md` y estas reglas de estilo:

- **Español claro.** Frases cortas, voz activa, presente. Explica cada sigla la
  primera vez. Los nombres de tablas, jobs, columnas y comandos van en `código` y
  no se traducen.
- **Lo importante primero.** Cada documento abre con un párrafo que se entiende solo.
- **Tablas para lo tabular** (fuentes, tablas, parámetros, targets) y prosa para
  explicar el porqué.
- **Nombres reales.** Escribe `gold_prd.modelo_pnl.fac_pnl_resultado_canal`, no "la
  tabla de resultados". Cuando el catálogo depende del ambiente, usa la forma
  `gold_{ambiente}` y explica los valores posibles una vez.
- **Una sola fuente de verdad.** Cada dato vive en un único documento y los demás lo
  enlazan. Si el README y `04_operacion.md` repiten los comandos, uno de los dos
  quedará desactualizado.
- **No expliques la tecnología**; enlaza a la documentación oficial. Explica *este*
  proyecto.
- **Nunca copies secretos**: ni tokens, ni contraseñas, ni cadenas de conexión con
  credenciales. Nombra el *scope* y la clave del secreto, no su valor.
- **No copies datos personales** que aparezcan en la configuración (correos de
  aviso, usuarios). Di dónde está configurado ("correo definido por target en
  `databricks.yml`") o nombra el rol. Los responsables solo se escriben con nombre
  si el usuario los indica o ya figuraban en la documentación previa.
- **Solo hechos de este proyecto.** Lo que sepas en general sobre una tecnología o
  un sistema externo no es un hecho del proyecto: si el código no lo respalda, no lo
  uses para explicar por qué algo se hizo así.
- **Numera los diagramas de corrido** en todo el juego de documentos (Diagrama 1 en
  el README, 2 en adelante en `docs/`), para poder citarlos sin ambigüedad.
- **Señala lo que parezca un error** del código (una validación que usa columnas que
  no existen, un pendiente olvidado) como "Observación" en el documento que
  corresponda y en el resumen final. No lo corrijas: documentar no es arreglar.

### 7. Escribir el contexto para agentes de IA

Genera `AGENTS.md` y `CLAUDE.md` en la raíz con la skill `crear-agents-md`; cárgala
y sigue sus reglas y su plantilla. Ya tienes hecho lo que esa skill pide averiguar:
usa el inventario y lo que leíste, y enlaza desde `AGENTS.md` a los documentos de
`docs/` que acabas de escribir, diciendo cuándo leer cada uno.

### 8. Reescribir la documentación previa

La instrucción del usuario es reescribir todo con la estructura estándar. Hazlo así,
para no perder conocimiento por el camino:

1. **Migra antes de borrar.** Todo contenido previo que siga siendo cierto debe
   acabar en alguno de los documentos nuevos. Verifica contra el código lo que
   afirme sobre tablas, pasos o parámetros; si el documento y el código se
   contradicen, manda el código y lo anotas en el resumen final.
2. **Conserva lo que no es documentación de proyecto.** Manuales de usuario, medidas
   DAX, guías de Power BI, plantillas, actas o preguntas abiertas con negocio son
   contenido especializado: no los fusiones ni los borres. Déjalos en `docs/` y
   enlázalos desde el índice del README, en la sección "Documentos complementarios".
3. **Elimina los documentos cuyo contenido quedó migrado por completo** y renombra
   los que choquen con la numeración estándar (01–04), actualizando sus enlaces.
   Antes de renombrar o eliminar uno, busca su nombre en el código (`grep` en
   notebooks y YAML): si el código lo cita, déjalo con su nombre, porque no puedes
   corregir esa cita, y avisa del choque de numeración en el resumen final.
   Un documento largo y vivo (un paso a paso de reglas, una lista de brechas) no
   se resume para fusionarlo: se conserva como complementario y se enlaza.
4. **No toques nada fuera de `README.md`, `docs/`, `AGENTS.md`, `CLAUDE.md` y los
   README de cada bundle.** Ni código, ni YAML, ni notebooks.
5. **No hagas commit ni push.** El usuario revisa el diff y decide.

### 9. Validar

```bash
python3 <ruta_skill>/scripts/validar_docs.py <ruta_proyecto>
```

Corrige todos los `ERROR` (diagramas que Azure DevOps no dibujaría, enlaces rotos,
posibles secretos) y revisa los `AVISO`. Después haz una pasada de contraste: toma
cinco afirmaciones al azar de lo que escribiste (una tabla, un horario, una
dependencia, una fuente, un comando) y compruébalas en el código. Revisa en
particular los números ("7 tablas", "8 tareas"): cuéntalos de nuevo.

El validador revisa la forma de los diagramas, no los dibuja. Si hay Node
disponible y quieres certeza, analiza cada bloque con `mermaid.parse`; si no,
dilo en el resumen final para que el usuario abra la vista previa.

### 10. Entregar

Cierra con un resumen breve para el usuario:

- Qué archivos creaste, reescribiste, moviste o eliminaste.
- Las contradicciones que encontraste entre la documentación previa y el código.
- La lista de "Por confirmar": lo que necesita respuesta de una persona.
- Recordatorio de que nada está confirmado en git.

## Casos particulares

- **Monorepo con varios bundles** (por ejemplo, un repositorio de ingestas con un
  bundle por fuente): los cinco documentos de la raíz describen el conjunto y cada
  bundle lleva su propio `README.md` corto con su diagrama de flujo, sus fuentes y sus
  jobs. Detalles en `references/leer-el-proyecto.md`.
- **Proyecto muy grande** (cientos de pipelines o notebooks): documenta por dominios o
  carpetas, con un diagrama por dominio, y deja el inventario exhaustivo como tabla en
  `03_fuentes_y_datos.md`. No intentes un diagrama con todo.
- **Proyecto sin datos** (una librería, una herramienta, CI/CD): usa la misma
  estructura; `03_fuentes_y_datos.md` pasa a describir entradas y salidas, o se omite.
- **Solo piden una parte** ("hazme el diagrama de arquitectura", "actualiza el
  README", "prepara el repo para trabajar con un agente"): entrega solo esa parte
  con las mismas reglas, sin regenerar el resto.
- **Actualizar documentación ya generada con esta skill:** vuelve a levantar el
  inventario, compara con lo escrito y cambia solo lo que cambió. Actualiza la fecha
  de "Última revisión".

## Por qué estas reglas

La estructura y las reglas salen de guías públicas de Databricks, Microsoft, Google,
AWS, GitHub y Anthropic. `references/buenas-practicas.md` las resume con sus enlaces; consúltalo
cuando tengas que justificar una decisión o resolver un caso que este documento no
cubre.
