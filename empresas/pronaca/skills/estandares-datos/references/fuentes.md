# Fuentes de cada regla

Qué dice cada fuente oficial y qué regla del estándar sale de ella. Las reglas
marcadas como "decisión propia" no vienen de una fuente: son convenciones del
usuario, elegidas para que todos sus proyectos se lean igual.

Consultado en noviembre de 2026. Si una regla parece desactualizada, vuelve a la
fuente antes de aplicarla.

**Última revisión de las reglas de tablas: 2026-11-28.** La sección 9 dice cuándo
volver a revisarlas.

## Contenido

1. Python
2. Tablas en Databricks
3. UDF
4. Asset Bundles
5. Gobierno y documentación
6. Decisiones propias
7. Marcos de referencia
8. Protección de datos personales
9. Revisión y radar

## 1. Python

| Fuente | Qué dice | Regla |
|---|---|---|
| [PEP 8](https://peps.python.org/pep-0008/) | Sangría de 4 espacios, líneas de 79 caracteres, orden de imports, `snake_case` para funciones y variables, mayúsculas para constantes | `python.md`, estilo y nombres |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring con comillas triples dobles; resumen de una línea en imperativo, terminado en punto; línea en blanco y detalle; documentar argumentos, retorno, efectos secundarios y excepciones. **No impone un formato** para listar argumentos | `python.md`, docstrings |
| [PEP 484](https://peps.python.org/pep-0484/) | Anotaciones de tipo en argumentos y retorno | `python.md`, tipos |

El formato de secciones `Args:` / `Returns:` / `Raises:` es una convención, no una
norma de Python: ver "Decisiones propias".

## 2. Tablas en Databricks

| Fuente | Qué dice | Regla |
|---|---|---|
| [Tablas administradas](https://docs.databricks.com/aws/en/tables/managed) | Son el tipo por defecto y recomendado. Solo ellas tienen optimización predictiva, clustering automático y caché de metadatos. Se crean sin `LOCATION`. Se recuperan con `UNDROP` durante 7 días. El acceso por ruta no está soportado | Tablas administradas, sin `LOCATION` |
| [Liquid clustering](https://docs.databricks.com/aws/en/delta/clustering) | Recomendado para todas las tablas nuevas; reemplaza al particionado y a `ZORDER`. Hasta cuatro claves; las claves necesitan estadísticas (primeras 32 columnas). `CLUSTER BY AUTO` exige tabla administrada, optimización predictiva y Runtime 15.4 LTS o superior. Las claves se cambian sin reescribir | `CLUSTER BY`, elección de claves |
| [Cuándo particionar](https://docs.databricks.com/aws/en/tables/partitions) | Con menos de 1 TB, no particionar. Entre 1 TB y 100 TB, liquid clustering en lugar de particionar. Cada partición debería tener al menos 1 GB | Nunca `PARTITIONED BY` |
| [Optimización predictiva](https://docs.databricks.com/aws/en/optimizations/predictive-optimization) | Ejecuta `OPTIMIZE`, `VACUUM` y `ANALYZE` sola en tablas administradas. Activa por defecto. Se comprueba con `DESCRIBE … EXTENDED` | Sin `OPTIMIZE` ni `VACUUM` programados |
| [Tamaño de archivos](https://docs.databricks.com/aws/en/delta/tune-file-size) | En tablas administradas el tamaño de archivo se ajusta solo; para tablas nuevas, configuración por defecto. Fijar un tamaño objetivo desactiva el ajuste automático | Sin `TBLPROPERTIES` de optimización |
| [Arquitectura medallón](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-architecture/deployment-guide/delta-lake) | Bronze conserva el dato crudo y es la fuente para reconstruir; silver limpia y tipa; gold sirve a negocio. Volúmenes para los archivos de aterrizaje. Ingesta idempotente. Calidad creciente por capa | Qué hace cada capa; carga repetible |
| [Buenas prácticas de Delta](https://docs.databricks.com/aws/en/delta/best-practices) | Al borrar y volver a crear una tabla, usar siempre `CREATE OR REPLACE TABLE`. No usar caché de Spark. Quitar configuraciones de Delta heredadas al subir de runtime | `tablas.md` §14: recreación planificada con `CREATE OR REPLACE`, nunca `DROP` + `CREATE` |
| [Propiedades de tabla](https://docs.databricks.com/aws/en/delta/table-properties) | Lista de propiedades y sus valores por defecto: `logRetentionDuration` 30 días, `deletedFileRetentionDuration` 7 días, `enableChangeDataFeed`, `enableRowTracking`, `enableTypeWidening` y `appendOnly` en falso, `columnMapping.mode` en `none` | `tablas.md` §7 |
| [Compatibilidad de features](https://docs.databricks.com/aws/en/delta/feature-compatibility) | Activar un *table feature* sube el protocolo; casi siempre es irreversible y puede romper a lectores externos. No fijar `minReaderVersion` ni `minWriterVersion` | `tablas.md` §7: preguntar por lectores externos |
| [Column mapping](https://docs.databricks.com/aws/en/delta/column-mapping) | Renombrar y borrar columnas son cambios de metadatos que exigen `columnMapping.mode`. El modo `name` se activa en tablas nuevas o existentes; `id` solo al crear | `columnMapping.mode = 'name'` en silver y gold |
| [Type widening](https://docs.databricks.com/aws/en/delta/type-widening) | Ampliaciones admitidas sin reescribir: enteros a mayores, `FLOAT` a `DOUBLE`, `DECIMAL` con más precisión, `DATE` a `TIMESTAMP_NTZ`. Runtime 15.4 LTS o superior | `enableTypeWidening` en silver y gold; §14 |
| [Actualizar el esquema](https://docs.databricks.com/aws/en/delta/update-schema) | `ADD COLUMNS` cambia el esquema sin escribir datos. `mergeSchema` por escritura; la configuración de sesión `autoMerge` no se recomienda en producción. Un cambio de esquema choca con escrituras concurrentes y corta los streams | `tablas.md` §14 |
| [Evolución del esquema](https://docs.databricks.com/aws/en/data-engineering/schema-evolution) | Un cambio de tipo no admitido por *type widening* exige reescribir con `overwriteSchema` | `tablas.md` §14: notebook de migración |
| [Esquema en Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema) | Modos `addNewColumns` (por defecto sin esquema), `rescue`, `failOnNewColumns` y `none`; columna `_rescued_data` | Bronze acepta columnas nuevas |
| [Restricciones](https://docs.databricks.com/aws/en/tables/constraints) | `NOT NULL` y `CHECK` se validan al escribir. `PRIMARY KEY` y `FOREIGN KEY` son informativas y pueden mejorar las consultas | `tablas.md` §8 |
| [Columnas generadas e identity](https://docs.databricks.com/aws/en/delta/generated-columns) | Una columna `IDENTITY` impide las transacciones concurrentes; solo `BIGINT`; valores no contiguos | Clave sustituta con hash, no `IDENTITY` |
| [Comentarios](https://docs.databricks.com/aws/en/comments) | Comentarios en todo objeto y columna. Guardar un comentario ejecuta un `ALTER` que puede interrumpir jobs | `tablas.md` §5 |
| [Etiquetas](https://docs.databricks.com/aws/en/database-objects/tags) | Máximo 50 por objeto; claves sin `. , - = / :`; texto plano, sin datos sensibles; *governed tags* con valores restringidos | `tablas.md` §11 |
| [Filtros de fila y máscaras](https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks) | Máscara de columna y filtro de fila con funciones SQL; se recomiendan políticas ABAC para muchas tablas | `tablas.md` §10 |
| [Recursos de un bundle](https://docs.databricks.com/aws/en/dev-tools/bundles/resources) | Un bundle declara catálogos, esquemas y volúmenes, pero no tablas | `tablas.md` §13: la DDL vive en el notebook `tbl_` |
| [Buenas prácticas de Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices) | Dueño por grupo, no por persona; *service principal* en producción; tablas administradas para todo lo nuevo | `tablas.md` §9 |

## 3. UDF

| Fuente | Qué dice | Regla |
|---|---|---|
| [Funciones definidas por el usuario](https://docs.databricks.com/aws/en/udf/) | Las funciones nativas de Spark están optimizadas y rinden mejor a escala; usar métodos de Spark para cargas grandes o periódicas. Las UDF de pandas son mucho más rápidas que las de Python por usar Arrow. Las UDF registradas en Unity Catalog tienen permisos y se pueden descubrir | Orden de preferencia de UDF |

## 4. Asset Bundles

| Fuente | Qué dice | Regla |
|---|---|---|
| [Configuración del bundle](https://docs.databricks.com/aws/en/dev-tools/bundles/settings) | Un único `databricks.yml` en la raíz del proyecto del bundle; `include` para repartir la configuración; un solo target por defecto; los targets sobrescriben los valores generales | Estructura, variables y targets |
| [Modos de despliegue](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes) | `mode: development` antepone `[dev usuario]`, pausa programaciones y permite ejecuciones simultáneas. `mode: production` valida la rama y exige `run_as` y permisos. Recomienda *service principal* en producción. Los `presets` ajustan prefijo, etiquetas y pausa | Target `local`; ver diferencias en `bundles.md` |

## 5. Gobierno y documentación

| Fuente | Qué dice | Regla |
|---|---|---|
| [Buenas prácticas de gobierno](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices) | Comentar todas las tablas y columnas; etiquetar los objetos; asignar dueño; definir convenciones de nombres, formatos y unidades | `COMMENT` y etiquetas obligatorios |

## 6. Decisiones propias

No vienen de una fuente oficial. Se mantienen iguales en todos los proyectos.

| Decisión | Motivo |
|---|---|
| Código, comentarios y mensajes en español | Idioma de trabajo del equipo y de negocio |
| Secciones `Args:` / `Returns:` / `Raises:` en los docstrings | PEP 257 no fija formato; se elige uno, compacto y reconocido por los editores |
| Prefijos de notebook `ext_`, `brz_`, `slv_`, `gld_`, `cfg_`, `utils_`, `tbl_`, `vol_`, `val_` | El nombre dice la etapa sin abrir el archivo |
| Notebooks sin numerar | El orden lo define el job |
| Tablas sin prefijo de capa | El catálogo `{capa}_{ambiente}` ya la indica |
| `fac_` para hechos y `dim_` para dimensiones | Una sola forma en todos los modelos |
| Linaje con `fecha_ingesta` y `fecha_proceso` | Dos nombres fijos en lugar de cinco variantes |
| Siete etiquetas de log fijas | Registros que se pueden buscar |
| DDL en notebooks de setup, `overwriteSchema` solo allí | El esquema se define en un solo lugar y no cambia en silencio |
| Jobs `jb_orq_{dominio}_{frecuencia}`, serverless | Convención ya usada en los proyectos |
| Targets `local`, `dev` y `main`, sin `mode` en los de CI/CD | Ver `bundles.md`, diferencias con la guía oficial |
| `task_key` igual al nombre del notebook | El job y el repositorio se leen igual |
| Orden fijo de la DDL y comentario `--` en cada propiedad | Toda tabla se lee igual y cada propiedad dice por qué está |
| Columnas sin número inicial; el número del reporte va en el `COMMENT` | Evita las comillas invertidas en SQL, DAX y Genie |
| `columnMapping` en modo `name`, no `id` | `name` se puede activar también en tablas existentes, así que lo nuevo y lo migrado quedan iguales |
| Notebook `tbl_` como primera tarea del job | Producción queda igual que desarrollo sin pasos a mano |
| Comentarios impersonales y con tildes | Se leen como documentación, no como instrucciones |
| Ruff como linter de Python, a 99 caracteres | Pendiente: se define en la fase de validaciones. PEP 8 admite hasta 99 si el equipo lo acuerda |

## 7. Marcos de referencia

| Marco | Qué se toma |
|---|---|
| [Databricks Well-Architected Lakehouse](https://docs.databricks.com/aws/en/lakehouse-architecture/) | Gobierno, fiabilidad y costo como criterios de diseño |
| [Arquitectura medallón](https://docs.databricks.com/aws/en/lakehouse/medallion) | Qué hace cada capa |
| Kimball, *The Data Warehouse Toolkit* | Grano declarado, hechos y dimensiones, dimensiones con historia (SCD2), medidas aditivas |
| [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/) | La DDL como contrato: esquema, significado, dueño y clasificación escritos en un solo lugar |
| [Expandir y contraer](https://martinfowler.com/bliki/ParallelChange.html) (*parallel change*) | Renombrar o borrar columnas sin romper a los consumidores |
| [PEP 8](https://peps.python.org/pep-0008/), [PEP 257](https://peps.python.org/pep-0257/), [PEP 484](https://peps.python.org/pep-0484/) | Estilo, docstrings y tipos del Python de los notebooks |

## 8. Protección de datos personales

| Fuente | Qué dice | Regla |
|---|---|---|
| Ley Orgánica de Protección de Datos Personales del Ecuador (LOPDP), Registro Oficial Suplemento 459, 26 de mayo de 2021 ([ficha oficial](https://www.gob.ec/regulaciones/ley-organica-proteccion-datos-personales-0)) | Art. 4: *dato personal* es el que identifica o hace identificable a una persona natural. Define *datos sensibles* (etnia, identidad de género, identidad cultural, religión, ideología, filiación política, pasado judicial, condición migratoria, orientación sexual, salud, biométricos, genéticos), *datos personales crediticios*, *datos relativos a la salud*, *anonimización* y *seudonimización* | Valores de la etiqueta `dato_personal` en el perfil |
| LOPDP, Art. 25 | Categorías especiales: datos sensibles, de niñas, niños y adolescentes, de salud, y de personas con discapacidad | Valores `sensible`, `nna`, `salud`, `discapacidad` |
| LOPDP, Art. 10 | Principios de pertinencia y minimización, y de conservación por el tiempo necesario | `tablas.md` §10: minimización |
| LOPDP, Art. 37 | Medidas de seguridad: anonimización, seudonimización o cifrado | `tablas.md` §10: hash en lugar del valor |
| [Reglamento General de la LOPDP](https://www.dspace.espol.edu.ec/bitstream/123456789/58917/1/REGLAMENTO%20GENERAL%20DE%20LA%20LEY%20ORG%C3%81NICA%20DE%20PROTECCI%C3%93N%20DE%20DATOS%20PERSONALES.pdf), Decreto Ejecutivo 904, Registro Oficial 435, 13 de noviembre de 2023 | Desarrolla la ley; no se revisó en detalle | Pendiente de revisar |

La LOPDP aplica a Pronaca (Ecuador). Para Toledano (Panamá) rige la Ley 81 de 2019
de Panamá, **pendiente de revisar**: hasta entonces se usa la misma clasificación.
Esto no es asesoría legal: la clasificación final la confirma el responsable de
protección de datos de la empresa.

## 9. Revisión y radar

Las reglas de tablas se revisan contra las fuentes cuando se cumple cualquiera de
estas condiciones. La skill `crear-tabla` lo comprueba al empezar y **pregunta al
usuario** antes de cambiar una regla, con el motivo concreto ("El CDF automático ya
es GA; ¿se actualiza la regla de `enableChangeDataFeed`?").

- Pasaron más de **6 meses** desde la fecha de última revisión de arriba.
- El usuario menciona un runtime, una función o una ley que no aparece aquí.
- Una función del radar pasó a disponibilidad general (GA).

Si el usuario acepta, se actualiza la regla en `tablas.md`, la fila de esta tabla
y la fecha de última revisión.

**Radar**: funciones que pueden cambiar una regla.

| Función | Estado en 2026-11 | Regla que cambiaría |
|---|---|---|
| CDF automático (sin propiedad, Runtime 19 o superior) | Nuevo | Dejar de usar `delta.enableChangeDataFeed` |
| Restricción `UNIQUE` | Public Preview (Runtime 18.2) | Declarar unicidad además de la `PRIMARY KEY` |
| `INSERT WITH SCHEMA EVOLUTION` | Runtime 18.1 o superior | Sintaxis de evolución de esquema en bronze |
| `ALTER TABLE … REPLACE PARTITIONED BY WITH CLUSTER BY` | Runtime 18.1 o superior | Migrar tablas particionadas sin recrearlas |
| *Catalog commits* (`delta.feature.catalogManaged`) | Se activa por actualización automática | Ninguna, salvo que pida configuración |
| Actualización eficiente de columnas (`enableColumnUpdates`) | Beta | Llenar una columna nueva sin reescribir las demás |
| Políticas ABAC para máscaras | Disponible | Máscaras por etiqueta `dato_personal` en lugar de por tabla |

Sin verificar en la documentación: si `RELY` en una `PRIMARY KEY` permite
optimizaciones adicionales, y si `DEFAULT` en una columna exige activar
`delta.feature.allowColumnDefaults`. Se confirman antes de usarlos.
