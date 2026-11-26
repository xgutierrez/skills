variables:
  # ============================================================
  # COMUNES (no cambian entre bundles ni ambientes)
  # ============================================================
  Environment_devops: devops-databricks
  # Nombre base del Variable Group (el pipeline concatena -<environment>)
  Variable_Group: {{VARIABLE_GROUP}}
  # Carpeta raiz en el workspace donde se despliegan los bundles
  Workspace_Folder: {{WORKSPACE_FOLDER}}

  # ============================================================
  # PRODUCCION — main
  # ============================================================
  ${{ if eq(variables['Build.SourceBranchName'], 'main') }}:
    environment: main
    Bundle_Target: main

  # ============================================================
  # DESARROLLO — dev (incluye feature branches)
  # ============================================================
  ${{ if ne(variables['Build.SourceBranchName'], 'main') }}:
    environment: dev
    Bundle_Target: dev
