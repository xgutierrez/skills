---
name: pronaca-data-factory
description: "Resuelve y consulta las fábricas de Azure Data Factory de Pronaca y Toledano, de desarrollo y de producción, con Azure CLI. Usar cuando el usuario diga ADF, Data Factory, 'el adf de pronaca', 'el adf de toledano', fábrica de desarrollo o de producción, o pregunte por pipelines, triggers o ejecuciones de ADF. Nunca asume la fábrica: dice a cuál se conecta o pregunta."
---

# Data Factory de Pronaca y Toledano

Consulta con Azure CLI. No instales ni uses un MCP de Data Factory.

Los nombres de las fábricas, sus grupos de recursos, el tenant y la suscripción
están en `empresa/identificadores.md` (cómo encontrarlo: skill `estandares-datos`, sección 1),
sección "Data Factory". Léelo antes de ejecutar cualquier comando. Si el archivo no
existe en este equipo, dilo y pide al usuario los datos; no los adivines.

## Nunca asumas la fábrica

En la respuesta di a qué fábrica te estás conectando, por su nombre. Si no lo
sabes, pregunta a cuál conectarte y no ejecutes Azure CLI.

Solo hay fábrica conocida cuando el pedido nombra las dos cosas: **empresa**
(Pronaca o Toledano) y **ambiente** (desarrollo o producción). No la deduzcas del
repositorio abierto, de otro proyecto ni de un turno anterior. "El mismo" o "ese
ADF" solo vale si en este pedido ya quedó dicho cuál es.

| El usuario dice | Qué fila usar del archivo de identificadores |
|---|---|
| ADF de Pronaca, desarrollo / dev | Pronaca, desarrollo |
| ADF de Pronaca, producción / prd / prod | Pronaca, producción |
| ADF de Toledano, desarrollo / dev | Toledano, desarrollo |
| ADF de Toledano, producción / prd / prod | Toledano, producción |

"Pronaca" es la fábrica de big data, no la de Toledano. Sin ambiente, pregunta si
es desarrollo o producción. "Desarrollo" o "producción" sin empresa: pregunta si es
Pronaca o Toledano.

## Acceso

Si Azure CLI devuelve `AADSTS50078` o un 401, pide renovar la autenticación y
detente:

```bash
az login --tenant "<tenant>"
```

Comprueba la fábrica solo si la llamada falla:

```bash
az datafactory show --name <fabrica> --resource-group <rg> --query name -o tsv
```

## Consultas

Sustituye `<fabrica>` y `<rg>` con la fila resuelta.

```bash
az datafactory pipeline list --factory-name <fabrica> --resource-group <rg> --query "[].name" -o tsv

az datafactory pipeline show --factory-name <fabrica> --resource-group <rg> --name <pipeline>

az datafactory pipeline-run query-by-factory \
  --factory-name <fabrica> --resource-group <rg> \
  --last-updated-after <inicio-utc> --last-updated-before <fin-utc> \
  --filters operand=Status operator=Equals values=Failed

az datafactory trigger list --factory-name <fabrica> --resource-group <rg> --query "[].{name:name, state:properties.runtimeState}" -o table
```

Para las actividades de una ejecución:
`az datafactory activity-run query-by-pipeline-run` con `--run-id`,
`--last-updated-after` y `--last-updated-before`.

El nombre de un pipeline de un proyecto se busca en ese repositorio. Si no está,
lista los pipelines de la fábrica resuelta y confirma cuál es antes de seguir.

## Producción

En las fábricas de producción, solo lectura. Lanzar, cancelar, reejecutar o cambiar
un pipeline, trigger, dataset o linked service exige un pedido explícito con el
nombre del recurso. En desarrollo se puede ejecutar solo si el usuario lo pide.
