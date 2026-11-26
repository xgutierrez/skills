# {{REPO_NAME}}

{{DESCRIPCION}}

Databricks Asset Bundle. Perfil de estándares: {{EMPRESA}}.

---

## Estructura del Repositorio

```
{{REPO_NAME}}/
├── README.md
├── .gitignore
├── .azure-pipelines/
│   ├── variables.environment.yml
│   └── {{BUNDLE_NAME}}_cd.yml
└── {{BUNDLE_NAME}}/
    ├── databricks.yml
    ├── src/
    │   ├── conexiones/
    │   └── {{BUNDLE_NAME}}/
    │       └── {{NOTEBOOK}}.ipynb
    ├── resources/
    │   └── {{JOB_FILE}}.yml
    └── tests/
```

---

## Targets

| Target | Quién despliega | Cuándo | Workspace Path |
|--------|----------------|--------|----------------|
| `local` | Desarrollador | Antes de push | `/Workspace/Users/{email}/{{BUNDLE_NAME}}/local` |
| `dev` | CI/CD | Rama ≠ `main` | `/Workspace/{{WORKSPACE_FOLDER}}/{{BUNDLE_NAME}}/dev` |
| `main` | CI/CD | Rama `main` | `/Workspace/{{WORKSPACE_FOLDER}}/{{BUNDLE_NAME}}/main` |

---

## Comandos de Desarrollo

```bash
cd {{BUNDLE_NAME}}/

databricks bundle validate
databricks bundle deploy
databricks bundle run {{JOB_KEY}}
databricks bundle destroy --target local --auto-approve
```

---

## CI/CD

- **Pipeline ADO**: `{{REPO_NAME}}`
- **YAML**: `.azure-pipelines/{{BUNDLE_NAME}}_cd.yml`
- **Variable Groups**: `{{VARIABLE_GROUP}}-dev`, `{{VARIABLE_GROUP}}-main`
- **Trigger**: push a `dev`/`main` en path `{{BUNDLE_NAME}}/**`

---

## Tags Obligatorios (Jobs)

`proyecto`, `area`, `tipo`, `modelo`, `frecuencia`, `pais`, `gestion: bundle`
