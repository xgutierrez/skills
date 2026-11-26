# =============================================================================
# Databricks Asset Bundle: {{BUNDLE_NAME}}
# {{DESCRIPCION}}
# =============================================================================

bundle:
  name: {{BUNDLE_NAME}}

include:
  - resources/*.yml

variables:
  pause_status:
    description: "Estado del schedule (PAUSED o UNPAUSED)"
    default: PAUSED
  job_name_prefix:
    description: "Prefijo para nombres de jobs"
    default: "[DEV] "
  notification_email:
    description: "Email para notificaciones en produccion"
    default: ""
  repo_name:
    description: "Carpeta raiz en el workspace (inyectada por CI/CD)"
    default: "{{WORKSPACE_FOLDER}}"
  ambiente:
    description: "Ambiente logico para resolver catalogos UC (dev, prd)"
    default: "dev"

targets:

  # --- LOCAL: pruebas personales del desarrollador ---
  local:
    default: true
    mode: development
    workspace:
      root_path: /Workspace/Users/${workspace.current_user.userName}/${bundle.name}/${bundle.target}
    variables:
      pause_status: PAUSED
      job_name_prefix: "[LOCAL] "
      notification_email: "{{NOTIFICATION_EMAIL}}"
      ambiente: "dev"
    presets:
      tags:
        owner: ${workspace.current_user.userName}

  # --- DEV: desplegado por CI/CD desde rama distinta de main ---
  dev:
    workspace:
      root_path: /Workspace/${var.repo_name}/${bundle.name}/${bundle.target}
    variables:
      pause_status: PAUSED
      job_name_prefix: "[DEV] "
      ambiente: "dev"

  # --- MAIN: desplegado por CI/CD desde rama main ---
  main:
    workspace:
      root_path: /Workspace/${var.repo_name}/${bundle.name}/${bundle.target}
    variables:
      pause_status: UNPAUSED
      job_name_prefix: ""
      notification_email: "{{NOTIFICATION_EMAIL}}"
      ambiente: "prd"
    resources:
      jobs:
        {{JOB_KEY}}:
          email_notifications:
            on_failure:
              - ${var.notification_email}
