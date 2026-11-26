---
name: pronaca-historias-usuario-ado
description: >-
  Redacta y crea historias de usuario y tareas en Azure DevOps de Pronaca llenando Como/Quiero/Para,
  Description y Acceptance Criteria, enlazando a la épica y asignando responsable.
  Usar cuando el usuario dicte en lenguaje libre una historia, pida crear HU/User
  Story/tarea en el backlog, colgarla de una épica, o mencione Como/Quiero/Para,
  criterios de aceptación o work items de ADO.
---

# Historias de usuario en Azure DevOps (Pronaca)

Los identificadores de la empresa (organización y proyecto de Azure DevOps, tenant,
responsable por defecto) están en
`empresa/identificadores.md` (cómo encontrarlo: skill `estandares-datos`, sección 1). Léelo antes de
ejecutar comandos y sustituye los marcadores `<ORGANIZACION>`, `<TENANT>` y
`<RESPONSABLE>`. Si el archivo no existe en este equipo, pide los datos al usuario.

El usuario dicta la necesidad en lenguaje libre y coloquial. La skill convierte ese dictado en un work item completo, con texto claro y orientado a la acción, y lo crea en ADO.

## Contexto fijo del entorno

| Dato | Valor |
|------|-------|
| Organización | `https://dev.azure.com/<ORGANIZACION>` |
| Proyecto por defecto | `BigData` |
| Proceso | `Agile-PRONACA` (heredado), WIT `Agile-PRONACA.UserStory` |
| Área por defecto | `BigData` |
| Iteración por defecto | `BigData\Sprint 1` (confirmar si hay sprint más reciente) |

Campos del formulario de User Story (labels vs nombre técnico):

| Label en el form | Reference name | Tipo |
|------------------|----------------|------|
| Como | `Custom.Como_hu_cf` | HTML |
| Quiero | `Custom.Quiero_hu_cf` | HTML |
| Para | `Custom.Para_hu_cf` | HTML |
| Description | `System.Description` | HTML |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | HTML |

Nunca renombrar los reference names `Custom.*_hu_cf`; solo se ajustan labels/orden del layout.

## Reparto de contenido (regla dura)

| Campo | Qué va | Qué NO va |
|-------|--------|-----------|
| **Título** | Acción + objeto, imperativo, sin “Como…” | Criterios, detalle técnico largo |
| **Como** | Solo el rol, 1 línea, sin la palabra “Como” | Verbos, beneficio, alcance |
| **Quiero** | La capacidad pedida, 1–2 líneas, sin “Quiero” | Criterios, pasos técnicos |
| **Para** | Beneficio de negocio medible, sin “Para” | Repetir el “Quiero” |
| **Description** | Alcance numerado, notas, supuestos, fuera de alcance | Repetir Como/Quiero/Para |
| **Acceptance Criteria** | Checklist binario (pasa/falla) | Narrativa de la historia |

Los campos son HTML: usar `<p>`, `<ol>`, `<ul>`, `<strong>`. En Como/Quiero/Para basta texto plano corto.

## Flujo de trabajo

1. **Interpretar el dictado**: identificar rol, capacidad, beneficio, entregables y la condición de aceptación que mencionó el usuario.
2. **Ubicar la épica** por título (nunca inventar IDs):
   ```bash
   az boards query --org https://dev.azure.com/<ORGANIZACION> --project BigData \
     --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.WorkItemType] = 'Epic' AND [System.Title] CONTAINS 'TEXTO'" -o json
   ```
3. **Mostrar el borrador** de los 6 campos al usuario antes de crear, si el dictado es ambiguo o falta el beneficio. Si el dictado es claro, crear directamente.
4. **Crear la User Story** con todos los campos llenos (ver plantilla).
5. **Enlazar a la épica** como hija.
6. **Crear las Tasks** (una por entregable) y colgarlas de la historia.
7. **Asignar** historia y tasks al responsable indicado.
8. **Verificar** y reportar IDs con enlaces.

## Plantilla de creación

```bash
ORG="https://dev.azure.com/<ORGANIZACION>"
PROJECT="BigData"
ASSIGNEE="<RESPONSABLE>"

COMO='rol de negocio'
QUIERO='capacidad solicitada'
PARA='beneficio de negocio'

DESC='<h3>Alcance</h3>
<ol>
  <li><strong>Entregable 1:</strong> ...</li>
</ol>
<p><strong>Notas:</strong> ...</p>'

CRIT='<ul>
  <li>Criterio verificable 1.</li>
  <li>Criterio verificable 2.</li>
</ul>'

ID=$(az boards work-item create --org "$ORG" --project "$PROJECT" --type "User Story" \
  --title "Titulo accionable" --assigned-to "$ASSIGNEE" \
  --area "BigData" --iteration "BigData\\Sprint 1" \
  --description "$DESC" -o tsv --query id)

az boards work-item update --id "$ID" --org "$ORG" --fields \
  "Custom.Como_hu_cf=$COMO" \
  "Custom.Quiero_hu_cf=$QUIERO" \
  "Custom.Para_hu_cf=$PARA" \
  "Microsoft.VSTS.Common.AcceptanceCriteria=$CRIT"

az boards work-item relation add --id "$ID" --org "$ORG" --relation-type parent --target-id EPICA_ID
```

Tasks: mismo patrón con `--type "Task"`, descripción breve en `<ul>` con los pasos, y `--relation-type parent --target-id` = ID de la historia.

Buscar el responsable por nombre antes de asignar:
```bash
az devops user list --org https://dev.azure.com/<ORGANIZACION> --top 500 -o json
```

## Redacción: antes y después

**Dictado del usuario:**
> "creación de 3 notebooks en databricks para copiar el csv al sftp, el xml generado por el modelo al sftp y el output del modelo a singlestore, el criterio son los 3 notebooks probados y corridos"

**Resultado:**

| Campo | Contenido |
|-------|-----------|
| Título | Crear 3 notebooks Databricks para salida Pedido Sugerido (CSV/XML a SFTP y output a SingleStore) |
| Como | equipo de datos de Pedido Sugerido Directa |
| Quiero | disponer de 3 notebooks en Databricks que automaticen la salida del modelo |
| Para | entregar el CSV y el XML al SFTP y persistir el output del modelo en SingleStore de forma repetible y auditable |
| Description | Alcance numerado: notebook CSV→SFTP, notebook XML→SFTP, notebook output→SingleStore + nota de asociación al flujo |
| Acceptance Criteria | Existen los 3 notebooks; CSV copiado al SFTP; XML copiado al SFTP; output persistido en SingleStore; los 3 probados y corridos con evidencia de ejecución OK |
| Tasks | Una por notebook, con verbos “crear, probar y correr” |

Cuando el usuario dé un criterio genérico (“probado y corrido”), expandirlo a un criterio por entregable **más** el criterio global de ejecución con evidencia.

## Convenciones de texto

- Español, tono directo, sin relleno; nombres propios de sistemas sin traducir (SFTP, SingleStore, Databricks, XML, CSV).
- Títulos de Task en formato `Notebook: <acción> <objeto>` o `<Componente>: <acción>`.
- Un entregable = una Task. Si el dictado menciona N artefactos, crear N tasks.
- Sin acentos dentro de valores pasados por `--fields` cuando haya riesgo de encoding en el shell; en `--description` (HTML) sí se usan normalmente.

## Autenticación

Si aparece `AADSTS50078` o `The requested resource requires user authentication`, la sesión MFA expiró:

```bash
az login --tenant "<TENANT>" \
  --scope "499b84ac-1321-427f-aa17-267ca6975798/.default"
```

Después reintentar el comando. Para WIQL vía REST usar `az rest ... --resource 499b84ac-1321-427f-aa17-267ca6975798`.

## Restricciones

- No crear, modificar ni borrar work items fuera de lo pedido; nada de `az repos delete`, `az pipelines delete` ni borrado de ramas.
- Cambios al layout del proceso (`Agile-PRONACA`) solo si el usuario lo pide explícitamente, vía:
  `PATCH /_apis/work/processes/{processId}/workItemTypes/{witRefName}/layout/pages/{pageId}/sections/{sectionId}/groups/{groupId}`
- No inventar IDs de épica, sprint ni usuarios: siempre consultarlos primero.

## Checklist antes de cerrar

- [ ] Título accionable, sin narrativa
- [ ] Como / Quiero / Para llenos en sus campos propios (no en Description)
- [ ] Description solo con alcance/notas
- [ ] Acceptance Criteria con criterios binarios, uno por entregable + ejecución con evidencia
- [ ] Historia enlazada a la épica correcta
- [ ] Una Task por entregable, todas colgadas de la historia
- [ ] Historia y Tasks asignadas al responsable indicado
- [ ] Reportar IDs y enlaces `https://dev.azure.com/<ORGANIZACION>/BigData/_workitems/edit/<id>`
