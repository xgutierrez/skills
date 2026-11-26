---
name: crear-repo-bundle
description: "Crea un repositorio nuevo con un bundle de Databricks listo para desplegar: esqueleto local con la estructura estándar, repositorio en Azure DevOps, ramas dev y main, pipeline de despliegue y guía para agentes. Usar cuando el usuario pida crear un repo nuevo, un proyecto nuevo, 'un bundle nuevo', el esqueleto o scaffold de un proyecto de datos, o registrar el pipeline de CI/CD de un repositorio. Solo crea: nunca borra ni sobrescribe."
---

# Crear un repositorio con un bundle

Deja un proyecto nuevo funcionando de punta a punta: carpeta local, repositorio
remoto, ramas, pipeline de despliegue y un job que ya valida.

El contenido sigue la skill `estandares-datos` (`references/bundles.md`). Los valores
de la empresa salen de su perfil y de sus identificadores, en la carpeta
`empresa/` (cómo encontrarla: skill `estandares-datos`, sección 1).

## Seguridad: esta skill solo crea

| Acción | ¿Permitida? |
|---|---|
| `az repos create`, `az pipelines create` | Sí, solo si el nombre **no** existe |
| `az repos show`, `az repos list`, `az pipelines list` | Sí, son lecturas |
| `az repos update --default-branch` | Sí, solo en el repositorio recién creado |
| `git push` de las ramas nuevas `dev` y `main` | Sí, sin `--force` |
| `az repos delete`, `az pipelines delete`, borrar ramas | **Nunca** |
| `git push --force`, `git push --delete` | **Nunca** |
| Borrar o sobrescribir una carpeta, un repositorio o un pipeline existente | **Nunca**: detente y pregunta |

Si el usuario pide borrar, limpiar o recrear desde cero algo que ya existe:
niégate a hacerlo desde esta skill, explica que se hace a mano en la interfaz de
Azure DevOps con su aprobación, y no improvises un comando de borrado.

Los dos scripts refuerzan esta regla: rechazan argumentos de borrado y solo
permiten una lista cerrada de comandos `az`.

## Flujo de trabajo

```
Progreso:
- [ ] 1. Resolver la empresa y leer su perfil
- [ ] 2. Reunir los datos del proyecto
- [ ] 3. Validar nombres y que nada exista ya
- [ ] 4. Crear el esqueleto local
- [ ] 5. Crear el repositorio remoto y subir las ramas
- [ ] 6. Registrar el pipeline
- [ ] 7. Entregar
```

### 1. Resolver la empresa y leer su perfil

Lee:

- `empresa/perfil.md`: prefijo del
  repositorio, etiquetas admitidas, grupo de variables, zona horaria.
- `empresa/identificadores.md`:
  organización y proyecto de Azure DevOps, carpeta local de repositorios.

Si falta alguno, dilo y pide los datos; no los inventes.

### 2. Reunir los datos del proyecto

**Siempre se preguntan:**

1. **Nombre del repositorio**, con el patrón del perfil.
2. **Nombre del bundle**: `{iniciativa}_{proyecto}`.
3. **Correo para los avisos de fallo.** No hay valor por defecto: pregúntalo
   siempre. No lo tomes de otro proyecto ni lo dejes escrito en esta skill.

**Tienen valor por defecto**, que se confirma en una línea:

| Dato | Por defecto |
|---|---|
| Descripción corta | La que dé el usuario al pedir el proyecto |
| Frecuencia | `mensual` |
| Etiqueta `tipo` | `analitica` |
| Etiqueta `modelo` | `transversal` |
| Etiqueta `area` | La primera del perfil |
| Etiquetas `proyecto` y `pais` | Las del perfil; si hay varias, pregunta |

### 3. Validar

- Nombres en minúsculas, con guion bajo, sin tildes ni guiones.
- El repositorio empieza por el prefijo del perfil.
- La carpeta local no existe.
- El repositorio no existe en Azure DevOps: `az repos show --repository <repo>`.

Comprueba el acceso antes de crear nada:

```bash
az account show -o none
az devops configure --list
```

Si falla, guía al usuario a `az login` y `az devops login`. Nunca le pidas pegar
un token en el chat.

### 4. Crear el esqueleto local

```bash
bash <ruta_skill>/scripts/scaffold_repo.sh \
  --repo <repo> --bundle <bundle> --empresa <empresa> \
  --prefijo-repo <prefijo> --root <carpeta_local> \
  --tag-proyecto <valor> --tag-pais <valor> --variable-group <grupo> \
  --email <correo> --zona <zona_horaria> \
  --frecuencia mensual --descripcion "<descripcion>"
```

Crea:

```
<repo>/
├── README.md
├── AGENTS.md                     declara el perfil de estándares
├── CLAUDE.md
├── .gitignore
├── .azure-pipelines/
│   ├── variables.environment.yml
│   └── <bundle>_cd.yml
└── <bundle>/
    ├── databricks.yml            targets local, dev y main
    ├── resources/jb_orq_<bundle>_<frecuencia>.yml
    ├── src/
    │   ├── conexiones/
    │   └── <bundle>/gld_<bundle>.ipynb     notebook inicial
    └── tests/
```

Las plantillas son las de `estandares-datos/assets/bundle/`. Si la carpeta ya
existe, el script se detiene.

Revisa el resultado: que no queden marcadores `{{…}}` y, si tienes la CLI
autenticada, `databricks bundle validate` dentro del bundle.

### 5. Crear el repositorio remoto

```bash
bash <ruta_skill>/scripts/create_ado.sh \
  --org <organizacion_ado> --project <proyecto_ado> \
  --repo <repo> --bundle <bundle> --root <carpeta_local>
```

Crea el repositorio, hace el commit inicial, sube `dev` y `main` sin forzar, y deja
`dev` como rama por defecto. Si el repositorio ya existe, se detiene.

Con otra plataforma de git (GitHub, GitLab), este script no aplica: crea el
repositorio con la herramienta de esa plataforma, respetando las mismas reglas de
seguridad, y adapta el pipeline de despliegue.

### 6. Registrar el pipeline

Lo hace el mismo script. Para registrarlo por separado: `--pipeline-only`. Para
omitirlo: `--skip-pipeline`.

| Bundles en el repositorio | Nombre del pipeline |
|---|---|
| Uno | El nombre del repositorio |
| Varios | `<repo>_<sufijo del bundle>` |

### 7. Entregar

- Enlace del repositorio y del pipeline.
- Recordatorio: el primer despliegue puede pedir aprobar el acceso al ambiente y
  al grupo de variables en Azure DevOps.
- Siguiente paso: reemplazar el notebook inicial por la lógica real, con las skills
  `crear-ingesta`, `crear-notebook` y `crear-tabla`.

## Qué no hacer

- No poner `databricks.yml` en la raíz del repositorio.
- No usar `mode` en los targets `dev` y `main`.
- No inventar un grupo de variables: se usa el del perfil.
- No dejar escrito un correo, un token ni un identificador en el repositorio.
- No reutilizar esta skill para "arreglar" un repositorio existente borrándolo.
