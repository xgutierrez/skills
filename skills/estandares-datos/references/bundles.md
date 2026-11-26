# Asset Bundles: estructura, jobs, ambientes y despliegue

Estándar para proyectos con Databricks Asset Bundles (hoy Declarative Automation
Bundles). Parte de la documentación oficial y añade las decisiones propias del
usuario; donde las dos difieren, se indica.

## Contenido

1. Estructura del repositorio
2. Nombres
3. `databricks.yml`
4. Los tres targets
5. La variable `ambiente` y los parámetros del job
6. Jobs
7. Etiquetas
8. Despliegue (CI/CD)
9. Comandos y limpieza
10. Diferencias con la guía oficial
11. Lista de comprobación

Las plantillas están en `assets/bundle/`: `databricks.yml.tpl`, `jb_orq.yml.tpl`,
`bundle_cd.yml.tpl`, `variables.environment.yml.tpl`, `README.md.tpl`,
`AGENTS.md.tpl` y `gitignore`. Para un repositorio nuevo, la skill
`crear-repo-bundle` las aplica todas de una vez. Cópialas y
sustituye los marcadores `{{…}}` con los valores del perfil.

## 1. Estructura del repositorio

```
{repositorio}/
├── README.md
├── AGENTS.md
├── .gitignore
├── .azure-pipelines/
│   ├── variables.environment.yml
│   └── {bundle}_cd.yml              uno por bundle
└── {bundle}/
    ├── databricks.yml
    ├── resources/                   plano; el prefijo del archivo dice el tipo
    ├── src/
    └── tests/
```

- `databricks.yml` vive **dentro de la carpeta del bundle**, no en la raíz del
  repositorio. La guía oficial pide un único `databricks.yml` en la raíz del
  proyecto del bundle; aquí esa raíz es la carpeta del bundle, lo que permite varios
  bundles por repositorio.
- La carpeta del bundle se llama igual que `bundle.name`.
- Cada bundle es autocontenido: sus conexiones, su código, sus recursos. No hay
  carpeta compartida entre bundles.
- Con varios bundles, cada uno tiene su carpeta y su pipeline de despliegue.

## 2. Nombres

Solo minúsculas, guion bajo, sin tildes, sin espacios, sin guiones.

| Nivel | Patrón | Ejemplo |
|---|---|---|
| Repositorio | El del perfil; por lo general `{empresa}_{iniciativa}_{proyecto}` | `acme_shared_ingesta` |
| Bundle, uno por repositorio | `{iniciativa}_{proyecto}` | `shared_ingesta` |
| Bundle, varios por repositorio | `{iniciativa}_{proyecto}_{variante}` | `pedido_sugerido_directa` |
| Job orquestador | `jb_orq_{dominio}_{frecuencia}` | `jb_orq_ingesta_sharepoint_presupuesto_eventual` |
| Job de un solo paso | `jb_{dominio}_{frecuencia}` | `jb_inventario_workspaces_semanal` |
| Archivo de recurso | El nombre del recurso | `resources/jb_orq_modelo_pnl_mensual.yml` |
| Pipeline de despliegue | `{bundle}_cd.yml` | `shared_ingesta_cd.yml` |

Frecuencias admitidas al final del nombre del job: `diaria`, `semanal`, `mensual`,
`anual`, `eventual`.

Prefijos de recurso en `resources/`: `jb_` job, `pl_` pipeline declarativo, `dsh_`
tablero, `alt_` alerta, `mdl_` modelo.

## 3. `databricks.yml`

Variables estándar, con estos nombres:

| Variable | Para qué | Por defecto |
|---|---|---|
| `ambiente` | Ambiente lógico de los catálogos: `dev` o `prd` | `dev` |
| `pause_status` | Si la programación está activa | `PAUSED` |
| `job_name_prefix` | Prefijo visible del job | `[DEV] ` |
| `notification_email` | Destino de los avisos de fallo | vacío |
| `repo_name` | Carpeta raíz en el workspace; la inyecta el CI/CD | El del perfil |

Añade otras solo si el proyecto las necesita (`ambiente_fuentes`,
`catalogo_fuente`) y con `description`.

- Sin `workspace.host` en el archivo: lo aporta el CI/CD como variable de entorno,
  o el perfil de la CLI en desarrollo. Así el mismo archivo sirve en cualquier
  workspace.
- Sin correos personales ni identificadores de workspace escritos en el archivo.
- `include: resources/*.yml`.

## 4. Los tres targets

| Target | Quién despliega | Dónde queda | Programación | `mode` |
|---|---|---|---|---|
| `local` | El desarrollador, a mano | `/Workspace/Users/{usuario}/{bundle}/local` | Pausada | `development` |
| `dev` | CI/CD, rama de desarrollo | `/Workspace/{repo}/{bundle}/dev` | Pausada | sin `mode` |
| `main` | CI/CD, rama `main` | `/Workspace/{repo}/{bundle}/main` | Activa | sin `mode` |

- `local` es el target por defecto (`default: true`): un `bundle deploy` sin
  `--target` nunca toca un ambiente compartido.
- `local` usa `mode: development`, que según la documentación antepone
  `[dev usuario]` a los recursos, pausa las programaciones y permite ejecuciones
  simultáneas. Añade `presets.tags.owner` para identificar de quién es cada job.
- En `main`, `job_name_prefix` va vacío o con el prefijo que indique el perfil.
- Los avisos por correo se definen como sobrescritura del job dentro del target, no
  en el archivo del recurso: con la variable vacía el despliegue falla.

## 5. La variable `ambiente` y los parámetros del job

`ambiente` se resuelve al desplegar y llega a cada notebook como parámetro:

```yaml
# databricks.yml
variables:
  ambiente: { description: "Ambiente logico de los catalogos (dev, prd)", default: "dev" }
targets:
  main:
    variables: { ambiente: "prd" }

# resources/jb_orq_…yml
parameters:
  - name: ambiente
    default: "${var.ambiente}"
tasks:
  - task_key: slv_erp_pedidos
    notebook_task:
      notebook_path: ../src/erp_pedidos/slv_erp_pedidos.ipynb
      base_parameters:
        ambiente: "{{job.parameters.ambiente}}"
```

Para una prueba puntual con otro valor no hace falta redesplegar:
`databricks bundle run <job> --params ambiente=…`.

## 6. Jobs

- **Serverless.** No se define `job_clusters`, `new_cluster` ni
  `existing_cluster_id`. Un cluster propio es una excepción (una librería que
  serverless no admite, un requisito de red) y se justifica en un comentario del YAML.
- **Un `task_key` por notebook, con el mismo nombre** que el notebook, sin
  extensión. Así el registro del job y el repositorio se leen igual.
- `notebook_path` relativo desde `resources/`: `../src/…`, con extensión `.ipynb`.
- `depends_on` explícito. Las tareas sin dependencia entre sí corren en paralelo.
- `max_concurrent_runs: 1` y `queue.enabled: true`: una segunda ejecución espera en
  lugar de pisar a la primera.
- `timezone_id` con la zona del perfil y `pause_status: ${var.pause_status}`.
- `notification_settings.no_alert_for_skipped_runs: true`.
- `description` con qué hace el job, en dos o tres líneas.
- Comentario de cabecera en el YAML con el flujo, la frecuencia y el cómputo.
- Los notebooks de setup no van en el job rutinario. Si hay muchos, tienen su propio
  job `jb_{dominio}_setup` sin programación.
- Una tarea de validación que no debe detener el flujo usa `run_if`.

## 7. Etiquetas

Cada job lleva **todas** las etiquetas que define el perfil de la empresa, con los
valores admitidos allí. No se omite ninguna ni se inventan valores: se usan para
repartir costos y filtrar en la interfaz.

El conjunto habitual es: `proyecto`, `area`, `tipo`, `modelo`, `frecuencia`, `pais`
y `gestion: bundle`. La etiqueta `frecuencia` coincide con el sufijo del nombre del
job.

## 8. Despliegue (CI/CD)

Con Azure Pipelines:

- `.azure-pipelines/variables.environment.yml` traduce la rama al target: `main`
  despliega `main`; el resto, `dev`.
- `.azure-pipelines/{bundle}_cd.yml`, uno por bundle, se dispara con cambios en la
  carpeta de ese bundle y tiene dos etapas: validar y desplegar.
- Se autentica con un *service principal*; el host y las credenciales salen de un
  grupo de variables, nunca del repositorio.
- Pasa `--var repo_name=…` para fijar la carpeta del workspace.
- El despliegue por CI/CD copia los archivos al workspace: lo que corre en `dev` y
  `main` es exactamente un commit, y nadie lo edita a mano.

Otra plataforma de CI/CD sigue las mismas reglas: una rama por ambiente, identidad
de servicio, validar antes de desplegar.

## 9. Comandos y limpieza

```bash
cd {bundle}/
databricks bundle validate            # target local por defecto
databricks bundle deploy
databricks bundle run <job>
databricks bundle destroy --target local --auto-approve
```

- **Siempre `destroy` al terminar de probar en `local`.** Los jobs personales
  abandonados ensucian la vista de todo el equipo.
- No despliegues a `dev` ni a `main` desde tu máquina: es trabajo del CI/CD.
- Antes de dar un cambio por terminado, `bundle validate` sin errores.

## 10. Diferencias con la guía oficial

| Tema | Guía de Databricks | Este estándar | Motivo |
|---|---|---|---|
| `mode: production` en el target productivo | Lo recomienda: valida la rama, impide sobrescribir clusters y exige `run_as` y permisos | Sin `mode` en `dev` y `main` | El CI/CD ya garantiza rama e identidad; los nombres y rutas se controlan con variables propias |
| `run_as` con *service principal* en producción | Recomendado | Lo aporta el CI/CD: quien despliega es el *service principal* | Mismo efecto sin declararlo en cada bundle |
| Ubicación de `databricks.yml` | Raíz del proyecto del bundle | Carpeta del bundle dentro del repositorio | Varios bundles por repositorio |
| `workspace.host` | Recomienda declararlo en el target | Se omite | Lo inyecta el CI/CD; el archivo queda portable |

Si un proyecto nuevo no tiene CI/CD que cubra esas garantías, vuelve a la guía
oficial: `mode: production`, `run_as` y `permissions` en el target productivo.

## 11. Lista de comprobación

- [ ] `databricks.yml` dentro de la carpeta del bundle; carpeta igual a `bundle.name`
- [ ] Variables estándar presentes; sin host, correos ni identificadores escritos
- [ ] Targets `local` (por defecto, `mode: development`), `dev` y `main`
- [ ] Job `jb_orq_{dominio}_{frecuencia}` con todas las etiquetas del perfil
- [ ] Serverless; `max_concurrent_runs: 1`; cola activa; zona horaria del perfil
- [ ] `task_key` igual al nombre del notebook; `ambiente` como parámetro
- [ ] Avisos por correo definidos en el target, no en el recurso
- [ ] `databricks bundle validate` sin errores
