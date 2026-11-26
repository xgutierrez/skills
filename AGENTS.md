# skills: guía para agentes de IA

Repositorio único con las skills de Xavier: las personales y las de cada empresa.
Aquí se editan instrucciones, plantillas y scripts de apoyo. Responde y escribe en
español.

## Mapa rápido

| Necesitas | Está en |
|---|---|
| Skills personales | `personal/<skill>/` |
| Todo lo de una empresa (lo que va a su repositorio) | `empresas/<empresa>/` |
| Skills de Pronaca, incluido el estándar de datos | `empresas/pronaca/skills/` |
| Reglas y comprobaciones de Pronaca | `empresas/pronaca/AGENTS.md` |
| Enlazar en el Mac | `instalar.sh` |
| Empaquetar lo personal para Claude y ChatGPT | `crear-zips.sh` |
| Publicar o traer una empresa | `sincronizar-empresa.sh` |

Cuando trabajes dentro de `empresas/<empresa>/`, sigue también su `AGENTS.md`.

## Reglas que no se pueden romper

1. **Nunca se guardan secretos**: ni contraseñas, ni tokens, ni datos de tarjetas.
2. **Lo de una empresa vive solo en `empresas/<empresa>/`.** Nada de una empresa va
   en `personal/`, y nada personal va en `empresas/`: esa carpeta se publica entera
   en el repositorio de la empresa.
3. **Los archivos `*.local.md` no se suben**: contienen cifras de negocio.
4. **Encabezado YAML válido** en cada `SKILL.md`: `name` igual al nombre de la
   carpeta; `description` en tercera persona diciendo qué hace y cuándo usarla. En
   `personal/`, como máximo 200 caracteres (límite de la app de Claude).
5. **Nombres de skill únicos** en todo el repositorio: si se repiten, el instalador
   omite uno.
6. **Los scripts solo dependen de Python 3 o de bash**, nunca sobrescriben un
   archivo existente y nunca hacen `push --force`.

## Cómo comprobar un cambio

1. `bash -n` sobre los scripts que tocaste.
2. `./crear-zips.sh` debe terminar sin errores si tocaste `personal/`.
3. Si tocaste `empresas/<empresa>/`, sigue la sección "Cómo comprobar un cambio" de
   su `AGENTS.md`.

## No hagas esto sin confirmación de una persona

- Hacer commit o push.
- Ejecutar `sincronizar-empresa.sh`: publica en el repositorio de la empresa o
  trae cambios de él.
- Ejecutar `instalar.sh --reemplazar` o `--desinstalar`.
- Subir un `*.local.md` o quitar algo del `.gitignore`.

## Trampas conocidas

- **Las skills se editan aquí**, no en `~/.claude/skills/` ni en `~/.agents/skills/`:
  ahí solo hay enlaces.
- **Una sesión ya abierta no ve los cambios.** La lista de skills se lee al iniciar.
- **Las skills personales no se enlazan en `~/.claude/skills/`** salvo con
  `--claude`: Claude Code las recibe desde la cuenta de Claude.
- **Si `sincronizar-empresa.sh subir` es rechazado**, el equipo subió cambios:
  primero `traer`, después `subir`.
