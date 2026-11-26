# ===========================================================================
# Job: {{JOB_KEY}}
# Un task por notebook; task_key = nombre del notebook sin extension.
# Compute: serverless
# ===========================================================================

resources:
  jobs:
    {{JOB_KEY}}:
      name: "${var.job_name_prefix} {{JOB_KEY}}"
      description: |
        {{BUNDLE_NAME}}
        {{DESCRIPCION}}

      tags:
        proyecto: "{{TAG_PROYECTO}}"
        area: "{{TAG_AREA}}"
        tipo: "{{TAG_TIPO}}"
        modelo: "{{TAG_MODELO}}"
        frecuencia: "{{TAG_FRECUENCIA}}"
        pais: "{{TAG_PAIS}}"
        gestion: "bundle"

      max_concurrent_runs: 1
      queue:
        enabled: true

      schedule:
        quartz_cron_expression: "0 0 6 1 * ?"
        timezone_id: "{{ZONA_HORARIA}}"
        pause_status: ${var.pause_status}

      notification_settings:
        no_alert_for_skipped_runs: true

      parameters:
        - name: ambiente
          default: "${var.ambiente}"

      tasks:
        - task_key: {{NOTEBOOK}}
          notebook_task:
            notebook_path: ../src/{{FUENTE_DOMINIO}}/{{NOTEBOOK}}.ipynb
            base_parameters:
              ambiente: "{{job.parameters.ambiente}}"
