---
name: crear-notebook
description: "Crea un notebook de Databricks con la estructura estándar de su capa: extracción a volumen, bronze, silver, gold, validación, configuración de conexiones, utilidades o setup. Usar siempre que el usuario pida crear, generar o empezar un notebook, 'un silver de X', 'el bronze de esta fuente', 'un cfg para conectarme a Y', 'un utils con funciones de Z' o 'un notebook de validación', aunque no diga la palabra plantilla. También al convertir un notebook existente al formato estándar."
---

# Crear un notebook

Genera el esqueleto con un script y después lo completa con la lógica real. El
script garantiza que el orden de celdas, los parámetros, los mensajes y el cierre
sean siempre iguales; tu trabajo es el contenido.

Las reglas que aplican están en la skill `estandares-datos`: lee su
`references/notebooks.md` y `references/python.md` antes de escribir la lógica. Si
no la tienes cargada, cárgala primero.

## Flujo de trabajo

### 1. Entender qué se pide

Necesitas saber, y lo deduces del repositorio antes de preguntar:

| Dato | Dónde mirarlo |
|---|---|
| Tipo de notebook | Lo que pide el usuario; la tabla de abajo |
| Fuente y dominio, o tabla y esquema | Carpetas de `src/`, notebooks vecinos |
| Carpeta de destino | La del flujo: `src/{fuente}_{dominio}/` o `src/{modelo}/` |
| Job que lo ejecutará | `resources/*.yml` |
| Zona horaria y catálogos | Perfil de la empresa en `estandares-datos` |
| Notebooks `cfg_` y `utils_` disponibles | `src/conexiones/`, `src/utils/` |

Pregunta solo lo que no esté en el repositorio y cambie el resultado: el grano de
la tabla, la clave, una regla de negocio.

| Tipo | Cuándo |
|---|---|
| `ext` | Traer datos de una fuente externa a un volumen |
| `brz` | Cargar los archivos del volumen en una tabla, sin transformar |
| `slv` | Limpiar, tipar y renombrar lo que hay en bronze |
| `gld` | Construir un hecho o una dimensión con reglas de negocio |
| `val` | Comparar una tabla contra una referencia, sin modificarla |
| `cfg` | Definir la conexión a una fuente, o las constantes de un modelo |
| `utils` | Agrupar funciones que usan varios notebooks |
| `tbl`, `vol` | Crear tablas o volúmenes; para tablas usa la skill `crear-tabla` |

### 2. Generar el esqueleto

```bash
python3 <ruta_skill>/scripts/nuevo_notebook.py --tipo slv \
    --fuente sharepoint --dominio presupuesto \
    --carpeta <bundle>/src/sharepoint_presupuesto \
    --job jb_orq_ingesta_sharepoint_presupuesto_eventual \
    --zona America/Guayaquil
```

| Tipo | Argumentos obligatorios |
|---|---|
| `ext`, `brz`, `slv` | `--fuente`, `--dominio` |
| `gld` | `--tabla`, `--esquema` |
| `tbl` | `--tabla`, `--esquema`, `--capa` |
| `vol` | `--fuente` |
| `cfg`, `utils`, `val` | `--tema` |

El nombre se arma con el patrón estándar; `--nombre` lo fija si hace falta. El
script no sobrescribe: si el archivo existe, se detiene. Solo necesita Python 3.

### 3. Completar la lógica

El esqueleto marca con `PENDIENTE:` cada punto que falta. Complétalos todos:

- **Cabecera:** qué hace, entrada, salida con su grano, y la tabla de parámetros
  al día si añadiste alguno.
- **Pasos:** código real. Añade o quita pasos según el flujo; cada uno con su
  Markdown `## Paso N — título` y numeración corrida.
- **Funciones:** con tipos y docstring. Si una función sirve a otros notebooks,
  va a un `utils_`, no aquí.
- **Reglas de negocio:** en el Markdown del paso, con **Qué hace**, **Por qué** y
  **Cómo se calcula**.

Quita lo que el esqueleto trae y este notebook no usa: un `%run` a un `cfg_` que no
existe, un parámetro que no aplica.

Edita el `.ipynb` conservando su estructura JSON: cada celda con `cell_type`,
`metadata`, `source` y, las de código, `outputs` vacío y `execution_count` nulo.

### 4. Conectar con el resto

Un notebook suelto no corre. Según el tipo:

- **Añádelo al job** en `resources/`, con `task_key` igual al nombre del notebook,
  su `depends_on` y `ambiente` en `base_parameters`. Reglas en
  `estandares-datos/references/bundles.md`.
- Si escribe una tabla que no existe, crea su setup con la skill `crear-tabla`.
- Si lee valores de otra tarea, comprueba que el `taskKey` y la clave coincidan
  con los que publica esa tarea.

### 5. Comprobar

```bash
grep -c "PENDIENTE:" <notebook>            # debe dar 0
python3 <ruta_estandares-datos>/scripts/revisar_estandar.py <repo>
databricks bundle validate                 # desde la carpeta del bundle
```

Corrige los `ERROR` del revisor en los archivos que tocaste. Si no puedes ejecutar
`bundle validate` (sin CLI o sin autenticación), dilo en el resumen.

### 6. Entregar

Resume en pocas líneas: qué notebook creaste y dónde, qué cambió en el job, qué
decisiones tomaste (clave, estrategia de escritura) y qué queda por confirmar. No
ejecutes el notebook ni despliegues el bundle salvo que el usuario lo pida.

## Convertir un notebook existente

Cuando el usuario pida pasar un notebook viejo al estándar:

1. Lee el notebook completo y anota qué lee, qué escribe y qué reglas aplica.
2. Genera el esqueleto del tipo que corresponda, con otro nombre si el original no
   sigue el patrón.
3. Traslada la lógica paso a paso, sin cambiar el resultado. Renombra variables y
   añade tipos y docstrings; no cambies cálculos.
4. No borres el original ni cambies el job: deja que el usuario compare y decida.
   Renombrar un notebook rompe el job que lo llama.
