---
name: estandares-datos
description: "Aplica el estándar de ingeniería de datos del usuario al escribir o revisar código en proyectos Databricks: Python (PEP 8, PEP 257, tipos), notebooks por capa, tablas administradas de Unity Catalog, arquitectura medallón y Asset Bundles. Usar siempre que se cree, edite o revise un notebook, una función, una UDF, un CREATE TABLE, un job o un databricks.yml; cuando el usuario pida 'buenas prácticas', 'estándar', 'revisa si cumple', 'optimiza la tabla' o 'valida el bundle'; y antes de usar las skills crear-notebook, crear-tabla o crear-ingesta, que dependen de estas reglas. Los valores propios de la empresa están en su perfil."
---

# Estándares de ingeniería de datos

Reglas para que todo proyecto de datos se vea y se comporte igual, sin importar quién
o qué agente lo escriba. Aplícalas sin pedir confirmación de estilo; pregunta solo
cuando haya una ambigüedad de negocio.

Cada regla dice de dónde sale: una fuente oficial o una decisión propia del usuario.
Las fuentes están en `references/fuentes.md`.

## 1. Dónde está el perfil de la empresa

Las reglas son generales; los valores concretos (catálogos, etiquetas, scopes de
secretos, nombres de repositorio, zona horaria) viven en la carpeta `empresa/` de la
raíz del repositorio `skills-pronaca`, dos niveles por encima de la carpeta de esta
skill (`<carpeta de la skill>/../../empresa/`):

| Archivo | Contenido |
|---|---|
| `perfil.md` | Convenciones: catálogos, scopes, etiquetas, nombres, zona horaria |
| `identificadores.md` | Lo que ubica la infraestructura: workspaces de Databricks y sus perfiles de la CLI, organización de git, tenant, suscripción |
| `avisos/` | Plantillas de correo con la marca de la empresa |

Las demás skills del repositorio usan esta misma carpeta y la llaman "la carpeta
`empresa/`".

1. Si la carpeta de la skill es un enlace (así se instala en el Mac), resuelve
   primero su ruta real (`cd <carpeta> && pwd -P`) y sube dos niveles desde ahí.
2. Si `empresa/perfil.md` no aparece, dilo y pide al usuario los valores que
   necesites. No inventes ninguno.

## 2. Qué leer según la tarea

| Tarea | Lee |
|---|---|
| Escribir o revisar funciones, UDF, imports, logs, manejo de errores | `references/python.md` |
| Crear o editar un notebook, cualquier capa | `references/notebooks.md` |
| Crear, alterar u optimizar una tabla; elegir tipos; cargar datos | `references/tablas.md` |
| Crear o validar un bundle, un job, un target o el CI/CD | `references/bundles.md` |
| Añadir un pipeline declarativo (Lakeflow) a un bundle | `references/bundles-pipelines-declarativos.md` |
| Añadir una alerta de SQL a un bundle | `references/bundles-alertas.md` |
| Justificar una regla o resolver un caso no previsto | `references/fuentes.md` |

## 3. Las reglas que más se rompen

Un resumen para tener siempre presente. El detalle y el porqué están en las referencias.

**Código**
- Español en variables, funciones, comentarios, docstrings y mensajes. No se traducen
  nombres de APIs, de tablas heredadas ni de columnas de la fuente.
- Toda función lleva tipos en argumentos y retorno, y docstring según PEP 257.
- Funciones nativas de Spark antes que cualquier UDF.
- Sin secretos, correos ni identificadores de workspace en el código.

**Notebooks**
- El nombre empieza por la capa: `ext_`, `brz_`, `slv_`, `gld_`, `cfg_`, `utils_`,
  `tbl_`, `vol_`, `val_`.
- Primera celda Markdown con qué hace, entrada y salida. Widgets en la segunda.
- `%run` solo en su celda. Pasos numerados. Mensajes con etiqueta fija.

**Tablas**
- Administradas por Unity Catalog: nunca `LOCATION`.
- `CREATE TABLE IF NOT EXISTS`, en un notebook de setup, no en la carga.
- `CLUSTER BY`, nunca `PARTITIONED BY`. Sin propiedades de optimización manuales.
- `COMMENT` en la tabla y en todas las columnas. `DECIMAL` para importes y medidas.
- Hechos `fac_`, dimensiones `dim_`. Sin prefijo de capa: el catálogo ya la dice.
- Linaje: `fecha_ingesta` (DATE) y `fecha_proceso` (TIMESTAMP).
- `overwriteSchema` solo en setup, nunca en la carga rutinaria.

**Bundles**
- `databricks.yml` dentro de la carpeta del bundle. Targets `local`, `dev`, `main`.
- Jobs `jb_orq_{dominio}_{frecuencia}`, serverless, con todas las etiquetas del perfil.
- `task_key` igual al nombre del notebook, sin extensión.

## 4. Revisar un repositorio

Para medir cuánto cumple un repositorio, o comprobar lo que acabas de escribir:

```bash
python3 <ruta_skill>/scripts/revisar_estandar.py <ruta_repo>
```

Lista cada incumplimiento con su archivo y cierra con un resumen por regla. Con
`--solo-errores` omite los avisos; con `--json <archivo>` guarda el detalle. Solo
necesita Python 3 (usa PyYAML si está instalado, o Ruby, para leer los YAML). Es de
solo lectura.

Después de crear o modificar código, ejecútalo sobre el repositorio y corrige los
`ERROR` de los archivos que tocaste. No corrijas archivos que no tocaste salvo que
el usuario lo pida: en un repositorio heredado habrá muchos, y arreglarlos es otra
tarea.

## 5. Código heredado

Las reglas aplican a lo nuevo. En un repositorio que no las cumple:

- Lo que crees nuevo sigue el estándar.
- Lo que edites conserva el estilo del archivo, salvo que el usuario pida migrarlo.
- No renombres tablas, columnas, jobs ni notebooks existentes: otros procesos y
  reportes dependen de esos nombres.
- Si una regla choca con una convención del repositorio, dilo y pregunta.

## 6. Mantener el estándar

Cuando el usuario acuerde una práctica nueva o cambie una regla, actualiza la
referencia correspondiente en esta skill en el mismo momento, y `fuentes.md` si la
regla viene de una fuente oficial. Estas skills viven en un repositorio git: recuerda
al usuario que el cambio hay que confirmarlo y subirlo para que llegue a sus otros
equipos.
