---
name: crear-ingesta
description: "Arma de principio a fin la ingesta de una fuente nueva en arquitectura medallón sobre Databricks: conexión, extracción a volumen, bronze, silver, setup de volumen y tablas, y el job del bundle con sus etiquetas. Usar siempre que el usuario pida ingestar, traer, cargar o integrar una fuente (una API, SharePoint, Excel, SFTP, Oracle, SQL Server, SAP), 'un pipeline nuevo', 'el flujo completo de X', o añadir un dominio nuevo a una ingesta existente. También para llevar una tabla hasta gold cuando hay que crear todo el camino."
---

# Crear una ingesta

Construye el flujo completo de una fuente: del sistema de origen a una tabla silver
lista para usar. Orquesta las skills `crear-notebook` y `crear-tabla` y aplica las
reglas de `estandares-datos`. Cárgalas antes de empezar.

```
fuente ──> volumen ──> bronze ──> silver ──> (gold)
  ext_       raw/       brz_       slv_       gld_
```

## Flujo de trabajo

### 1. Entender la fuente

Reúne esto antes de escribir nada. Mira primero el repositorio: si ya hay otra
ingesta de la misma fuente, su `cfg_` y su patrón se reutilizan.

| Dato | Por qué importa |
|---|---|
| Sistema y forma de acceso (API, archivo, base de datos) | Decide si hace falta volumen |
| Objeto concreto: endpoint, carpeta, tabla | Define la extracción |
| Autenticación y dónde están los secretos | El `cfg_` |
| Frecuencia y horario | El job y su nombre |
| Carga completa o incremental; cómo se identifica lo nuevo | La estrategia de escritura |
| Clave de cada registro | Deduplicación en silver |
| Volumen aproximado | Si hay que paginar o partir |
| Perfil de la empresa | Catálogos, scope, etiquetas, zona horaria |

Pregunta en una sola ronda lo que no esté en el repositorio. Si no tienes una
muestra de los datos, pídela: sin ella no se pueden escribir el mapeo de silver ni
los comentarios de columna.

### 2. Elegir el camino

| Fuente | Camino |
|---|---|
| Archivos o API (Excel, CSV, JSON, SharePoint, SFTP, REST) | `ext_` a volumen → `brz_` → `slv_` |
| Base de datos por JDBC | `ext_` a volumen si se quiere conservar la foto diaria; si no, `brz_` lee directo de la fuente |
| Tabla ya disponible en Databricks (otro catálogo, federación) | Sin volumen ni bronze propio: empieza en `slv_` o en `gld_` |

El volumen existe para conservar lo que llegó, tal como llegó: permite reconstruir
bronze sin volver a llamar a la fuente. Si la fuente ya es una tabla gobernada,
copiarla no aporta.

### 3. Proponer el plan

Antes de crear archivos, muestra al usuario la lista de lo que vas a crear y dónde,
y espera su visto bueno si implica más de un flujo o toca un job existente:

```
{bundle}/
├── resources/jb_orq_ingesta_{fuente}_{dominio}_{frecuencia}.yml
└── src/
    ├── conexiones/cfg_{fuente}.ipynb               (si no existe)
    └── {fuente}_{dominio}/
        ├── ext_{fuente}_{dominio}.ipynb
        ├── brz_{fuente}_{dominio}.ipynb
        ├── slv_{fuente}_{dominio}.ipynb
        └── setup/
            ├── vol_brz_{dominio}.ipynb             (si el volumen no existe)
            ├── tbl_brz_{dominio}.ipynb
            └── tbl_slv_{dominio}.ipynb
```

### 4. Construir, en este orden

Cada pieza se apoya en la anterior.

1. **Conexión.** `cfg_{fuente}` con la skill `crear-notebook` (`--tipo cfg`), si no
   existe. Constantes, secretos del scope del perfil y funciones de lectura con
   tipos y docstring.
2. **Setup.** El volumen (`--tipo vol`) y las dos tablas con la skill
   `crear-tabla`: bronze toda en `STRING` con `CLUSTER BY (fecha_ingesta)`; silver
   tipada, con su clave y `CLUSTER BY AUTO`.
3. **Extracción.** `ext_`: guarda el archivo sin tocar en
   `…/raw/{dominio}/fecha_ingesta=AAAA-MM-DD/` y publica `fecha_ingesta` y
   `rutas_volume`.
4. **Bronze.** `brz_`: lee las rutas publicadas, añade linaje y escribe con
   reemplazo selectivo por `fecha_ingesta`.
5. **Silver.** `slv_`: mapeo de columnas, tipos, deduplicación por la clave,
   validación y escritura.
6. **Job.** `resources/jb_orq_ingesta_{fuente}_{dominio}_{frecuencia}.yml` a partir
   de `estandares-datos/assets/bundle/jb_orq.yml.tpl`: una tarea por notebook con
   `task_key` igual a su nombre, `depends_on` en cadena, `ambiente` como parámetro y
   todas las etiquetas del perfil con `tipo: ingesta`.
7. **Target `main`.** Si el job debe avisar por correo, añade su sobrescritura de
   `email_notifications` en el target `main` de `databricks.yml`.

Si el bundle no existe todavía, créalo primero con las plantillas de
`estandares-datos/assets/bundle/` y las reglas de `references/bundles.md`.

### 5. Reglas del flujo

- **Repetible.** Lanzar dos veces la misma fecha deja el mismo resultado: la
  extracción reemplaza su directorio y cada capa reemplaza su lote.
- **Reprocesable.** El job acepta `fecha_ingesta` como parámetro para volver a
  cargar un día pasado.
- **Sin trabajo, sin error.** Si la fuente no trae nada nuevo, la extracción termina
  con `SKIP` y las tareas siguientes no fallan.
- **Cada capa hace solo lo suyo.** La extracción no transforma; bronze no tipa;
  silver no aplica reglas de negocio.
- **Los secretos, solo en el `cfg_`**, leídos del scope del perfil.

### 6. Comprobar

```bash
grep -rn "PENDIENTE:" <bundle>/src/{fuente}_{dominio}/     # sin resultados
python3 <ruta_estandares-datos>/scripts/revisar_estandar.py <repo>
cd <bundle> && databricks bundle validate
```

Repasa a mano la cadena: el `taskKey` y las claves que lee cada notebook coinciden
con lo que publica el anterior, y los nombres de tabla de la carga coinciden con
los del setup.

### 7. Entregar

Resume:

- Archivos creados y qué cambió en archivos existentes.
- Orden para la primera ejecución: `vol_`, `tbl_brz_`, `tbl_slv_` y después el job.
- Decisiones tomadas: clave, carga completa o incremental, clustering.
- Lo que queda por confirmar y lo que no pudiste validar.

No despliegues ni ejecutes el job salvo que el usuario lo pida, y nunca contra el
target `main`.

## Añadir un dominio a una ingesta existente

Reutiliza el `cfg_` y el volumen de esa fuente. Crea la carpeta
`src/{fuente}_{dominio}/` con sus tres notebooks y su setup, y decide con el
usuario si el dominio entra como tareas nuevas en el job existente o en un job
propio (lo segundo, si tiene otra frecuencia).

## Llegar hasta gold

Si además se pide el modelo de negocio: define con el usuario el grano de cada
hecho y las dimensiones, crea las tablas con `crear-tabla` y los notebooks `gld_`
con `crear-notebook`, dimensiones antes que hechos. Gold suele vivir en otro bundle
o en otra carpeta `src/{modelo}/`, con su propio job de `tipo: analitica`.
