# {{REPO_NAME}}: guía para agentes de IA

{{DESCRIPCION}}

Perfil de estándares: {{EMPRESA}}

Responde y documenta en español. Aplica la skill `estandares-datos` a todo lo que
crees o edites.

## Mapa rápido

| Necesitas | Está en |
|---|---|
| Ambientes y variables | `{{BUNDLE_NAME}}/databricks.yml` |
| Definición del job | `{{BUNDLE_NAME}}/resources/{{JOB_FILE}}.yml` |
| Notebooks | `{{BUNDLE_NAME}}/src/` |
| Despliegue | `.azure-pipelines/{{BUNDLE_NAME}}_cd.yml` |

## Comandos

```bash
cd {{BUNDLE_NAME}}/
databricks bundle validate
databricks bundle deploy
databricks bundle run {{JOB_KEY}}
databricks bundle destroy --target local --auto-approve
```

## No hagas esto sin confirmación de una persona

- Desplegar o ejecutar con el target `main`.
- Hacer commit o push.

Completa esta guía con la skill `documentar-proyecto` cuando el proyecto tenga
lógica real: reglas que no se pueden romper, trampas conocidas y cómo comprobar un
cambio.
