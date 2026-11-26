# Fuentes de cada regla

Qué dice cada fuente oficial y qué regla del estándar sale de ella. Las reglas
marcadas como "decisión propia" no vienen de una fuente: son convenciones del
usuario, elegidas para que todos sus proyectos se lean igual.

Consultado en noviembre de 2026. Si una regla parece desactualizada, vuelve a la
fuente antes de aplicarla.

## Contenido

1. Python
2. Tablas en Databricks
3. UDF
4. Asset Bundles
5. Gobierno y documentación
6. Decisiones propias

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
