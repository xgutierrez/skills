# Notebooks: estructura y reglas por capa

## Contenido

1. Tipos de notebook y nombres
2. Carpetas
3. Estructura común
4. Parámetros
5. Reglas de Databricks
6. Qué hace cada capa
7. Conexiones y secretos
8. Paso de datos entre tareas

## 1. Tipos de notebook y nombres

El prefijo dice qué hace el notebook y en qué etapa corre.

| Prefijo | Tipo | Nombre | Qué hace |
|---|---|---|---|
| `ext_` | Extracción | `ext_{fuente}_{dominio}` | Trae el dato de la fuente a un volumen, sin transformarlo |
| `brz_` | Bronze | `brz_{fuente}_{dominio}` | Carga el dato crudo en una tabla, todo como texto |
| `slv_` | Silver | `slv_{fuente}_{dominio}` | Limpia, tipa, renombra y quita duplicados |
| `gld_` | Gold | `gld_{tabla}` | Aplica reglas de negocio y construye hechos y dimensiones |
| `val_` | Validación | `val_{qué valida}` | Compara contra una referencia. No modifica datos |
| `cfg_` | Configuración | `cfg_{fuente o tema}` | Conexiones, rutas y constantes. Se incluye con `%run` |
| `utils_` | Utilidades | `utils_{tema}` | Funciones compartidas. Se incluye con `%run` |
| `tbl_` | Setup de tablas | `tbl_{capa}_{tabla}` | Crea tablas con su DDL |
| `vol_` | Setup de volúmenes | `vol_{capa}_{dominio}` | Crea esquemas y volúmenes |

- Minúsculas, guion bajo, sin tildes.
- Siempre `.ipynb`, no `.py`.
- No se numeran los notebooks (`01_`, `02_`): el orden lo define el job. Un número
  en el nombre obliga a renombrar cuando se inserta un paso.

## 2. Carpetas

```
{bundle}/
├── databricks.yml
├── resources/                      definición de jobs
├── src/
│   ├── conexiones/                 cfg_{fuente}.ipynb
│   ├── utils/                      utils_{tema}.ipynb
│   └── {fuente}_{dominio}/         un directorio por flujo
│       ├── ext_{fuente}_{dominio}.ipynb
│       ├── brz_{fuente}_{dominio}.ipynb
│       ├── slv_{fuente}_{dominio}.ipynb
│       └── setup/
│           ├── vol_brz_{dominio}.ipynb
│           ├── tbl_brz_{dominio}.ipynb
│           └── tbl_slv_{dominio}.ipynb
└── tests/
```

Un proyecto de modelo (gold) usa `src/{modelo}/` con sus `cfg_`, `gld_`, `val_` y
`setup/`.

## 3. Estructura común

Todo notebook sigue el mismo orden de celdas.

**Celda 1, Markdown: cabecera.**

```markdown
# slv_sharepoint_presupuesto

**Capa:** Silver · **Job:** `jb_orq_ingesta_sharepoint_presupuesto_eventual` · **Flujo:** `ext → brz → slv`

**Qué hace.** Tipa y normaliza el presupuesto mensual leído de bronze.

**Entrada:** `bronze_{ambiente}.sharepoint.presupuesto`
**Salida:** `silver_{ambiente}.sharepoint.presupuesto`, una fila por año, mes, canal y cuenta.

| Parámetro | Por defecto | Para qué |
|---|---|---|
| `ambiente` | `dev` | Catálogos de lectura y escritura |
| `fecha_ingesta` | vacío: hoy | Lote a procesar, AAAA-MM-DD |
```

**Celda 2, código: parámetros.** Widgets, lectura de sus valores, zona horaria de
la sesión y el mensaje `[INICIO]`.

```python
dbutils.widgets.text("ambiente", "dev", "Ambiente")
dbutils.widgets.text("fecha_ingesta", "", "Fecha de ingesta AAAA-MM-DD")

ambiente = dbutils.widgets.get("ambiente").strip() or "dev"
fecha_ingesta_parametro = dbutils.widgets.get("fecha_ingesta").strip()

spark.conf.set("spark.sql.session.timeZone", "America/Guayaquil")
print(f"[INICIO] slv_sharepoint_presupuesto | ambiente={ambiente}")
```

**Celdas `%run`**, una por celda, para `cfg_` y `utils_`.

**Celda de imports y constantes**: imports ordenados, nombres de catálogo, esquema y
tablas resueltos a partir de `ambiente`.

```python
catalogo_bronze = f"bronze_{ambiente}"
catalogo_silver = f"silver_{ambiente}"
esquema = "sharepoint"
tabla_origen = f"{catalogo_bronze}.{esquema}.presupuesto"
tabla_destino = f"{catalogo_silver}.{esquema}.presupuesto"
```

**Celdas de funciones**, si el notebook define alguna propia. Precedidas de un
Markdown `## Funciones`.

**Celdas de pasos.** Cada paso es un Markdown `## Paso N — título` seguido de su
celda de código. Si el paso tiene una regla de negocio, el Markdown la explica con
**Qué hace**, **Por qué** y **Cómo se calcula**.

**Última celda: cierre.** Publica lo que la tarea siguiente necesita y escribe
`[FIN]` con un resumen.

```python
print(f"[FIN] slv_sharepoint_presupuesto | filas escritas={filas_escritas}")
```

## 4. Parámetros

- Todo notebook que lee o escribe tablas declara `ambiente`. Con él arma los
  catálogos: nunca un catálogo fijo en el código.
- Nombres estándar; no inventes variantes:

| Parámetro | Significado |
|---|---|
| `ambiente` | `dev` o `prd`: ambiente de escritura |
| `ambiente_fuentes` | Ambiente de lectura, cuando difiere del de escritura |
| `fecha_ingesta` | Lote a procesar, AAAA-MM-DD. Vacío: la fecha por defecto del proceso |
| `fecha_corte` | Fecha límite de un cálculo |
| `reprocesar_fechas` | Fechas AAAA-MM-DD separadas por coma |
| `dias_reproceso` | Cuántos días hacia atrás recalcular |

- Nombres en minúscula (`ambiente`, no `Ambiente`).
- El valor por defecto permite ejecutar el notebook a mano en desarrollo. Nunca
  apunta a producción.
- Los parámetros de fecha vacíos se resuelven en la zona horaria del perfil.

## 5. Reglas de Databricks

- `%run` va **solo en su celda**, sin nada más.
- Los widgets se declaran al inicio.
- Si un `%run` de utilidades deja widgets que el notebook no usa, se eliminan por
  nombre con `dbutils.widgets.remove`.
- SQL dentro de Python con `spark.sql(f"""…""")`, con nombres completos de tabla.
  Las celdas `%sql` se reservan para exploración, no para la carga.
- `display()` es para explorar. En un notebook que corre en un job no queda ninguno.
- Sin rutas `abfss://` ni `/mnt/`: los archivos viven en volúmenes (`/Volumes/…`).
- Al guardar, sin resultados de ejecución en las celdas: engordan el repositorio y
  pueden filtrar datos.

## 6. Qué hace cada capa

### Extracción (`ext_`)

- Lee de la fuente y **guarda el archivo tal como llega** en
  `/Volumes/bronze_{ambiente}/{fuente}/raw/{dominio}/fecha_ingesta=AAAA-MM-DD/`.
- No transforma, no tipa, no filtra columnas.
- Es idempotente: repetir la fecha reemplaza los archivos de ese directorio.
- Si no hay nada que extraer, termina con `dbutils.notebook.exit("SKIP: …")`.
- Publica con `taskValues` la fecha de ingesta y las rutas escritas.
- Cuando la fuente ya es una tabla accesible desde Databricks, no hace falta
  volumen: el flujo empieza en bronze o en silver.

### Bronze (`brz_`)

- Lee del volumen las rutas que publicó la extracción.
- Todas las columnas como `STRING`, con los nombres de la fuente.
- Añade `fecha_ingesta`, `fecha_proceso` y `archivo_origen`.
- Escribe con reemplazo selectivo por `fecha_ingesta`.
- No aplica reglas de negocio ni descarta filas.

### Silver (`slv_`)

- Renombra a `snake_case` en español con un diccionario de mapeo declarado al
  inicio: `"ColumnaFuente": ("columna_silver", "tipo", "comentario")`.
- Tipa, normaliza textos y fechas, y quita duplicados por la clave.
- Valida antes de escribir: claves sin nulos y sin repetidos.
- Escribe con reemplazo selectivo o `MERGE`.

### Gold (`gld_`)

- Un notebook por tabla o por grupo pequeño de tablas afines.
- Las reglas de negocio se explican en el Markdown de cada paso.
- Las constantes y listas del modelo viven en un `cfg_` compartido, no repetidas.
- Dimensiones antes que hechos.
- Controles de calidad que detienen la carga con `raise` si no se cumplen.

### Validación (`val_`)

- No modifica datos. Su cabecera lo dice.
- Informa con `[OK]`, `[WARN]` y `[ERROR]`, y termina con un resumen.
- Declara su tolerancia como parámetro.

### Setup (`tbl_`, `vol_`)

- Se puede ejecutar muchas veces sin efecto: `IF NOT EXISTS`.
- Un notebook por tabla o por grupo de tablas de un mismo flujo y capa.
- No está en el job rutinario; se corre a mano o en un job de setup.

## 7. Conexiones y secretos

- Cada fuente tiene un `cfg_{fuente}.ipynb` en `src/conexiones/` con sus
  constantes, la lectura de secretos y las funciones de conexión.
- Los secretos se leen con `dbutils.secrets.get(scope=…, key=…)`. El nombre del
  scope sale del perfil y depende del ambiente.
- Nunca un secreto, un token, una contraseña ni una cadena de conexión en el
  código, en un widget con valor por defecto ni en un `print`.
- Las llamadas a una API llevan `timeout` y comprueban el estado de la respuesta
  con `raise_for_status()`.
- El `cfg_` no ejecuta trabajo al incluirlo: solo define constantes y funciones.

## 8. Paso de datos entre tareas

- Una tarea entrega valores pequeños a la siguiente con `dbutils.jobs.taskValues`:
  rutas, fechas, listas cortas. Nunca datos.
- Las claves son estables y en español: `fecha_ingesta`, `rutas_volume`.
- La tarea que lee declara `debugValue` para poder ejecutarse a mano, y falla con un
  mensaje claro si el valor no llegó.

```python
dbutils.jobs.taskValues.set(key="fecha_ingesta", value=fecha_ingesta)

fecha_ingesta = dbutils.jobs.taskValues.get(
    taskKey="ext_sharepoint_presupuesto", key="fecha_ingesta", debugValue=""
)
if not fecha_ingesta:
    raise ValueError("fecha_ingesta no recibida desde ext_sharepoint_presupuesto")
```
