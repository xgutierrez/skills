---
name: avisos-proceso
description: "Arma los correos de inicio y de fin de un proceso de datos con una plantilla HTML fija: barra de color, ficha del proceso, ambiente, estado, horario y duración. Usar cuando el usuario pida notificaciones, avisos o correos de inicio y fin de un proceso, de una ejecución o de un job, o añadir avisos a un job existente."
---

# Avisos de inicio y fin de proceso

Cuando el usuario pida avisar del inicio y del fin de un proceso, usa estas
plantillas. No inventes otro diseño, otros colores ni otro pie: los destinatarios
reconocen el correo por su forma.

## Qué plantilla usar

1. Si la empresa tiene las suyas, úsalas:
   `empresa/avisos/plantilla_inicio.html` (carpeta `empresa/`: skill `estandares-datos`, sección 1) y
   `plantilla_fin.html`. Llevan su color de marca y su pie.
2. Si no, usa las neutras de esta skill: `assets/plantilla_inicio.html` y
   `assets/plantilla_fin.html`.

Si el repositorio ya tiene un notebook `utils_aviso_proceso` que arma el HTML y un
`utils_envio_correos` con la función de envío, úsalos en lugar de copiar las
plantillas. Si no existen, copia las dos plantillas al repositorio y rellena los
marcadores `__CLAVE__`.

## Cuándo sale cada correo

- **Inicio:** en la primera tarea del job. Publica la hora de inicio con
  `dbutils.jobs.taskValues` (clave `ts_inicio`) para el aviso de fin.
- **Fin:** en la última tarea, solo si el proceso terminó bien. Si falla, este
  correo no sale: lo cubre la alerta de fallo del job.
- El aviso de fin no incluye pasos del proceso, rutas ni archivos.

## Asunto

Sin fecha; la fecha va en el cuerpo.

- `[DEV] Inicio | {nombre_corto}`
- `[DEV] Finalizó | {nombre_corto}`

`DEV` en desarrollo, `PRD` en producción. `nombre_corto` es el nombre que se verá
en la bandeja, por ejemplo `Ventas semanal`.

## Textos que cambian

| Marcador | Inicio | Fin |
|---|---|---|
| `__TITULO__` | `Inicio de ejecución: {proceso}` | `Fin de ejecución: {proceso}` |
| `__PREHEADER__` | `Inició la ejecución del {proceso en minúscula inicial} · Ambiente: {ambiente en minúscula} · {d mmm aaaa, HH:MM}` | `Finalizó el {proceso en minúscula inicial} · Estado: exitoso · Duración: {duración}` |
| `__TITULAR__` | `Inició el {proceso_oracion}` | `Finalizó el {proceso_oracion}` |
| `__PROCESO__` | Nombre de la ficha, por ejemplo `Modelo semanal de ventas` | El mismo |
| `__AMBIENTE__` | `Desarrollo`, `Producción` o `Sandbox` | El mismo |
| `__FECHA_INICIO__` | `14 de octubre de 2026, 09:56 (GMT-5)` | La misma fecha, sin la zona |
| `__FECHA_FIN__` | No aplica | `14 de octubre de 2026, 10:14` |
| `__DURACION__` | No aplica | `18 min`, `2 h` o `2 h 7 min` |

`proceso_oracion` es el nombre dentro del titular, sin mayúscula inicial. Puede
llevar palabras que la ficha no lleva (`modelo semanal de ventas`).

La hora se calcula en la zona horaria del perfil de la empresa. En el correo, el
desfase (`(GMT-5)`) se escribe solo en la fecha de inicio del aviso de inicio, y
nunca el nombre de la ciudad salvo que el usuario lo pida.

## Lo que no se cambia

- El color de la barra y la estructura de la ficha.
- Insignia de inicio: `● INICIADO`, fondo `#DBEAFE`, texto `#1E40AF`.
- Insignia de fin: `✔ FINALIZADO CON ÉXITO`, fondo `#DCFCE7`, texto `#166534`.
- Estado en la ficha: inicio `Iniciado` en `#1E40AF`; fin `Exitoso` en `#166534`.
- Subtítulo de inicio: `Se te notificará cuando el proceso finalice.`
- Subtítulo de fin: `El proceso se completó sin errores.`
- El pie de la plantilla.

Un aviso de fallo, si más adelante se pide, usa insignia con fondo `#FEE2E2` y
texto `#991B1B`. No sustituye al correo de fin exitoso.

## Reglas de implementación

- Los destinatarios llegan por parámetro del job, nunca escritos en el notebook.
- Las credenciales de correo se leen de un secreto, con el scope del perfil.
- El envío no debe hacer fallar el proceso de datos: si el correo falla, se
  registra con `[WARN]` y el job sigue.
- El `task_key` de cada tarea de aviso es el nombre de su notebook.
