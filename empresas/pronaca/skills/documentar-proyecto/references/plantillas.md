# Plantillas de los documentos

Usa estas estructuras tal cual. Los textos entre «comillas angulares» son
instrucciones para ti: sustitúyelos siempre y no dejes ninguno en el resultado.
Elimina la sección que no aplique en lugar de dejarla vacía.

## Contenido

1. `README.md`
2. `docs/01_entendimiento.md`
3. `docs/02_arquitectura.md`
4. `docs/03_fuentes_y_datos.md`
5. `docs/04_operacion.md`
6. README de un bundle (monorepos)
7. Registro de decisiones

---

## 1. `README.md`

Es la puerta de entrada. Debe poder leerse en dos minutos y llevar a todo lo demás.
No repite el detalle de `docs/`: lo resume y lo enlaza.

````markdown
# «nombre del proyecto»

«Una o dos frases en lenguaje llano: qué hace y para quién. Sin tecnología.»

| | |
|---|---|
| **Qué entrega** | «tablas, reporte, archivo o modelo que produce» |
| **Quién lo usa** | «área o rol; "Por confirmar" si no se sabe» |
| **Frecuencia** | «diaria, semanal, mensual, a demanda» |
| **Fuentes** | «sistemas de origen, separados por coma» |
| **Tecnología** | «p. ej. Databricks Asset Bundle, Unity Catalog, Azure DevOps» |
| **Responsable** | «equipo o persona; "Por confirmar" si no se sabe» |
| **Estado** | «En producción / En desarrollo / En desuso» |

## Vista general

**Diagrama 1. Contexto del proyecto**

```mermaid
«diagrama de contexto»
```

*Cómo leerlo:* «una o dos frases»

## Documentación

| Documento | Para qué sirve |
|---|---|
| [Entendimiento](docs/01_entendimiento.md) | Qué problema resuelve, reglas de negocio y glosario |
| [Arquitectura](docs/02_arquitectura.md) | Cómo está construido y cómo fluyen los datos |
| [Fuentes y datos](docs/03_fuentes_y_datos.md) | De dónde vienen los datos y qué tablas produce |
| [Operación](docs/04_operacion.md) | Cómo se ejecuta, se despliega y se resuelven fallos |

### Documentos complementarios

«Solo si existen: manuales de usuario, guías de Power BI, medidas DAX, preguntas
abiertas con negocio. Una fila por documento con su enlace y para qué sirve.»

## Inicio rápido

```bash
«los 2 a 4 comandos mínimos para validar y ejecutar en desarrollo»
```

El detalle de ambientes, parámetros y despliegue está en [Operación](docs/04_operacion.md).

## Estructura del repositorio

```
«árbol de carpetas hasta 2 o 3 niveles, con un comentario breve por carpeta»
```

---
*Última revisión de la documentación: «AAAA-MM-DD»*
````

---

## 2. `docs/01_entendimiento.md`

Lo escribe alguien que entiende el negocio para alguien que no conoce el proyecto.
Nada de nombres de notebooks aquí, salvo para enlazar. Si el proyecto es puramente
técnico (una ingesta), las "reglas de negocio" son las reglas de carga: qué se trae,
desde cuándo, con qué filtros.

````markdown
# Entendimiento del proyecto

«Párrafo inicial: qué problema existe, qué hace el proyecto al respecto y qué
resultado obtiene quien lo usa.»

## El problema

«Qué necesidad cubre. Qué pasaba antes o qué pasaría sin el proyecto.»

## Qué entrega

| Entregable | Qué es | Quién lo usa | Para qué decisión |
|---|---|---|---|
| «tabla / reporte / archivo» | «…» | «…» | «…» |

## Cómo funciona, en simple

«De 4 a 8 pasos numerados en lenguaje llano, del dato de origen al resultado. Cada
paso dice qué se hace y por qué. Es la versión narrada del diagrama de flujo.»

## Reglas de negocio

«Las reglas que cambian el resultado: filtros, perímetros, fórmulas, excepciones,
fechas de corte. Una tabla o lista numerada. Para cada regla: qué dice, por qué
existe y dónde está implementada (enlace al notebook).»

| # | Regla | Motivo | Dónde se aplica |
|---|---|---|---|

## Alcance y límites

- **Incluye:** «…»
- **No incluye:** «…»
- **Supuestos:** «…»

## Glosario

| Término | Significado |
|---|---|
| «sigla o término del negocio» | «definición en una línea» |

## Pendientes y preguntas abiertas

| Tema | Pregunta | A quién preguntar |
|---|---|---|
| «…» | «…» | «…» |
````

---

## 3. `docs/02_arquitectura.md`

````markdown
# Arquitectura

«Párrafo inicial: en tres o cuatro frases, cómo está construido. Qué plataforma,
qué patrón (p. ej. medallón bronze → silver → gold), cuántos jobs y qué producen.»

## Flujo de datos

**Diagrama 2. Flujo de datos**

```mermaid
«diagrama de flujo de datos»
```

*Cómo leerlo:* «…»

«Explicación por etapa: una subsección o fila por capa, diciendo qué ocurre en ella
y qué notebooks la ejecutan.»

| Etapa | Qué ocurre | Notebooks | Tablas resultantes |
|---|---|---|---|

## Componentes

| Componente | Tipo | Ubicación | Función |
|---|---|---|---|
| «job, pipeline, notebook de configuración, utilidades, tablero» | «…» | «ruta en el repo» | «…» |

## Orquestación

«Una subsección por job.»

### `«nombre del job»`

**Diagrama 3. Tareas de `«job»`**

```mermaid
«diagrama de orquestación»
```

*Cómo leerlo:* «…»

## Ambientes y despliegue

**Diagrama 4. Ambientes y despliegue**

```mermaid
«diagrama de ambientes»
```

*Cómo leerlo:* «…»

| Ambiente (target) | Quién despliega | Escribe en | Lee de |
|---|---|---|---|

## Decisiones de diseño

«Las decisiones que alguien nuevo cuestionaría: por qué se lee de producción en
desarrollo, por qué una tabla es vista materializada, por qué una fuente entra por
Excel. Solo las que consten en el código, los comentarios o la documentación previa;
no inventes motivos. Formato del apartado 7.»

## Seguridad y accesos

«Cómo se autentica contra cada fuente (nombre del scope y la clave del secreto,
nunca el valor), qué permisos necesita quien ejecuta y qué datos sensibles maneja.»

---
*Diagramas revisados por última vez: «AAAA-MM-DD»*
````

---

## 4. `docs/03_fuentes_y_datos.md`

Es el documento que más se consulta. Debe permitir responder "¿de dónde sale este
número?" sin abrir el código.

````markdown
# Fuentes y datos

«Párrafo inicial: cuántas fuentes usa, de qué sistemas, y cuáles son las tablas
finales que consume negocio.»

## Fuentes de datos

### Fuentes externas

Sistemas ajenos a la plataforma, de donde el proyecto extrae datos.

| Fuente | Sistema | Qué se trae | Cómo se conecta | Frecuencia | Notebook de extracción |
|---|---|---|---|---|---|
| «nombre» | «SAP, Oracle, SharePoint, API…» | «objeto, archivo o endpoint» | «JDBC, API REST, archivo en volumen…» | «…» | «enlace» |

### Fuentes internas

Tablas de la plataforma producidas por otros proyectos, que este proyecto solo lee.

| Tabla | Qué contiene | Proyecto que la produce | Usada en |
|---|---|---|---|
| `«catalogo.esquema.tabla»` | «…» | «proyecto o "Por confirmar"» | «notebook» |

## Linaje

**Diagrama 5. Linaje de tablas**

```mermaid
«diagrama de linaje»
```

*Cómo leerlo:* «…»

## Tablas que produce

| Tabla | Capa | Grano (una fila es…) | Contenido | Carga | Notebook |
|---|---|---|---|---|---|
| `«catalogo.esquema.tabla»` | «bronze / silver / gold» | «…» | «…» | «completa / incremental / merge» | «enlace» |

«Marca cuáles son de consumo (las lee negocio) y cuáles internas.»

## Diccionario de datos

«Una subsección por tabla de consumo (gold o salida final). Para tablas internas
basta la fila de la tabla anterior. Toma tipos y descripciones del DDL, de los
comentarios de columna o del código; si una columna no tiene descripción deducible,
escribe "Por confirmar" en lugar de adivinar.»

### `«catalogo.esquema.tabla»`

| Columna | Tipo | Descripción | Origen o fórmula |
|---|---|---|---|

## Calidad y validaciones

| Validación | Qué comprueba | Dónde | Qué pasa si falla |
|---|---|---|---|

## Otras salidas

«Archivos exportados, correos, tableros, modelos registrados: qué se genera, dónde
queda y quién lo recibe.»
````

---

## 5. `docs/04_operacion.md`

Lo lee quien tiene que ejecutar, desplegar o arreglar el proyecto, quizá con prisa.
Comandos copiables y tablas; poca prosa.

````markdown
# Operación

«Párrafo inicial: cuándo corre, cuánto tarda si se sabe, y qué hacer primero si falla.»

## Jobs

| Job | Qué hace | Programación | Zona horaria | Avisos |
|---|---|---|---|---|
| `«job»` | «…» | «en palabras: "domingos a las 11:00" (cron `…`)» | «…» | «correo a…» |

### Tareas de `«job»`

| Orden | Tarea | Notebook | Depende de | Qué hace |
|---|---|---|---|---|

## Parámetros

| Parámetro | Dónde se define | Valor por defecto | Para qué sirve |
|---|---|---|---|

## Ejecutar en desarrollo

```bash
«comandos»
```

## Despliegue

«Cómo llega un cambio a producción: ramas, pipeline de CI/CD, grupos de variables,
aprobaciones. Enlaza al diagrama 4 de Arquitectura en vez de repetirlo.»

| Rama | Pipeline | Target | Ambiente |
|---|---|---|---|

## Requisitos previos

«Lo que debe existir antes de la primera ejecución: esquemas, tablas de
configuración, secretos, permisos, notebooks de setup y su orden.»

## Reprocesos

«Cómo volver a cargar un periodo o una fecha: qué parámetro usar y qué efectos tiene.»

## Problemas frecuentes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|

«Solo los que consten en el código (mensajes de error controlados, validaciones) o
en la documentación previa. Si no hay ninguno conocido, elimina la sección.»

## Contactos

| Rol | Quién |
|---|---|
| Responsable técnico | «o "Por confirmar"» |
| Responsable funcional | «o "Por confirmar"» |
````

---

## 6. README de un bundle (monorepos)

En un repositorio con varios bundles, cada uno lleva un README corto. El detalle
común (ambientes, CI/CD, convenciones) vive en los documentos de la raíz.

````markdown
# «nombre del bundle»

«Una frase: qué trae o qué calcula.»

| | |
|---|---|
| **Fuente** | «…» |
| **Destino** | «catálogos y esquemas» |
| **Jobs** | «lista con su frecuencia» |

**Diagrama. Flujo de `«bundle»`**

```mermaid
«flujo de datos del bundle»
```

*Cómo leerlo:* «…»

## Tablas

| Tabla | Capa | Contenido | Notebook |
|---|---|---|---|

## Particularidades

«Solo lo que distingue a este bundle del resto: autenticación propia, parámetros,
reprocesos, límites de la fuente.»

Ver la [documentación general](../README.md) para ambientes, despliegue y convenciones.
````

---

## 7. Registro de decisiones

Dentro de `02_arquitectura.md`, cada decisión de diseño sigue este formato breve.
Una decisión por entrada; si una decisión cambia, se añade una nueva que reemplaza a
la anterior en lugar de editarla.

```markdown
### D1. «título de la decisión»

- **Contexto:** «qué situación obligaba a decidir»
- **Decisión:** «qué se eligió»
- **Consecuencias:** «qué implica, bueno y malo»
- **Estado:** «Vigente / Reemplazada por D«n»»
```
