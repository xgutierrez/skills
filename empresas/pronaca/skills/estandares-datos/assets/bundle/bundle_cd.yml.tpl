trigger:
  branches:
    include:
      - dev
      - main
  paths:
    include:
      - {{BUNDLE_NAME}}/**
      - .azure-pipelines/**

pool:
  vmImage: ubuntu-latest

variables:
  - template: variables.environment.yml
  - group: "${{variables.Variable_Group}}-${{variables.environment}}"
  - name: Bundle_Path
    value: {{BUNDLE_NAME}}

stages:
  # ================================================================
  # Stage 1: Validar el bundle
  # ================================================================
  - stage: ValidateBundle
    displayName: Validar Bundle
    jobs:
      - deployment: BundleValidation
        environment: ${{variables.Environment_devops}}-${{variables.environment}}
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self

                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: '3.x'
                    addToPath: true
                    architecture: 'x64'
                  displayName: 'Use Python Version: 3'

                - script: |
                    curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
                    databricks --version
                  displayName: 'Instalar Databricks CLI'

                - task: AzureCLI@2
                  displayName: Get Databricks token
                  inputs:
                    azureSubscription: $(servicePrincipalName)
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      databricks_resource_id="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
                      accessToken=$(curl -X GET -H 'Content-Type: application/x-www-form-urlencoded' \
                        -d "grant_type=client_credentials&client_id=$servicePrincipalId&resource=$databricks_resource_id&client_secret=$servicePrincipalKey" \
                        https://login.microsoftonline.com/$tenantId/oauth2/token \
                        | jq -r .access_token)
                      echo "##vso[task.setvariable variable=DATABRICKS_TOKEN;issecret=true]$accessToken"
                    addSpnToEnvironment: true

                - script: |
                    set -euo pipefail

                    echo "=============================================="
                    echo "  Validando Bundle: ${{variables.environment}}"
                    echo "  Target: ${{variables.Bundle_Target}}"
                    echo "=============================================="

                    cd ${BUILD_REPOSITORY_LOCALPATH}/${{variables.Bundle_Path}}
                    databricks bundle validate --target ${{variables.Bundle_Target}} --var repo_name=$(Workspace_Folder)

                    echo "Bundle validado correctamente"
                  env:
                    DATABRICKS_HOST: https://$(databricksWorkspaceUrl)
                    DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)
                    BUILD_REPOSITORY_LOCALPATH: $(Build.Repository.LocalPath)
                  displayName: 'Validar Bundle'

  # ================================================================
  # Stage 2: Desplegar el bundle
  # ================================================================
  - stage: DeployBundle
    displayName: Desplegar Bundle
    dependsOn: ValidateBundle
    condition: succeeded()
    jobs:
      - deployment: BundleDeployment
        environment: ${{variables.Environment_devops}}-${{variables.environment}}
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self

                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: '3.x'
                    addToPath: true
                    architecture: 'x64'
                  displayName: 'Use Python Version: 3'

                - script: |
                    curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
                    databricks --version
                  displayName: 'Instalar Databricks CLI'

                - task: AzureCLI@2
                  displayName: Get Databricks token
                  inputs:
                    azureSubscription: $(servicePrincipalName)
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      databricks_resource_id="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
                      accessToken=$(curl -X GET -H 'Content-Type: application/x-www-form-urlencoded' \
                        -d "grant_type=client_credentials&client_id=$servicePrincipalId&resource=$databricks_resource_id&client_secret=$servicePrincipalKey" \
                        https://login.microsoftonline.com/$tenantId/oauth2/token \
                        | jq -r .access_token)
                      echo "##vso[task.setvariable variable=DATABRICKS_TOKEN;issecret=true]$accessToken"
                    addSpnToEnvironment: true

                - script: |
                    set -euo pipefail
                    IFS=$'\n\t'

                    echo "=============================================="
                    echo "  Desplegando Bundle: ${{variables.environment}}"
                    echo "  Target: ${{variables.Bundle_Target}}"
                    echo "  Workspace: $DATABRICKS_HOST"
                    echo "=============================================="

                    BUNDLE_DIR="${BUILD_REPOSITORY_LOCALPATH}/${{variables.Bundle_Path}}"
                    if [[ ! -f "${BUNDLE_DIR}/databricks.yml" ]]; then
                      echo "ERROR: databricks.yml not found in ${BUNDLE_DIR}"
                      exit 1
                    fi

                    cd "${BUNDLE_DIR}"
                    echo "Ejecutando: databricks bundle deploy --target ${{variables.Bundle_Target}} --var repo_name=$(Workspace_Folder)"
                    databricks bundle deploy --target ${{variables.Bundle_Target}} --var repo_name=$(Workspace_Folder)

                    echo ""
                    echo "=============================================="
                    echo "  Bundle desplegado exitosamente"
                    echo "=============================================="

                    databricks bundle summary --target ${{variables.Bundle_Target}} --var repo_name=$(Workspace_Folder)
                  env:
                    DATABRICKS_HOST: https://$(databricksWorkspaceUrl)
                    DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)
                    BUILD_REPOSITORY_LOCALPATH: $(Build.Repository.LocalPath)
                  displayName: 'Deploy Bundle a Databricks'
