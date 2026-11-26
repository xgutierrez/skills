# skills

Todas mis skills para agentes de IA en un solo repositorio: lo personal y lo de cada
empresa. En mi Mac solo clono este repositorio.

Cada empresa tiene su carpeta en `empresas/`, con exactamente lo que va en el
repositorio de esa empresa. `sincronizar-empresa.sh` la publica allí para que la use
su equipo, y trae de vuelta lo que el equipo mejore.

| Carpeta | Qué va | Dónde se usa |
|---|---|---|
| `personal/` | Lo que solo me sirve a mí: mi forma de escribir correos, `guardar-en-skill` | Mis equipos y mis cuentas de Claude y ChatGPT |
| `empresas/pronaca/` | El estándar de datos y las skills de Pronaca, con su perfil | Mi Mac y el repositorio de Pronaca, para todo el equipo |

## Instalar en el Mac

```bash
git clone https://github.com/xgutierrez/skills.git ~/Documents/RepoPersonal/skills
~/Documents/RepoPersonal/skills/instalar.sh
```

| Herramienta | Cómo le llegan las skills |
|---|---|
| Claude Code | Pronaca por `~/.claude/skills`; personal por la cuenta de Claude |
| Cursor y Grok | Leen `~/.claude/skills` y `~/.agents/skills`: les llega todo |
| Codex y ChatGPT de escritorio | Personal por `~/.agents/skills` (Pronaca con `--codex`) |
| App de Claude y ChatGPT web | Los `.zip` de `./crear-zips.sh`, solo de `personal/` |

Cada skill se enlaza en una sola carpeta para que ninguna herramienta la vea dos
veces.

## Publicar una empresa en su repositorio

La primera vez, con el repositorio de la empresa creado y **vacío**:

```bash
git remote add empresa-pronaca <url del repositorio de pronaca>
./sincronizar-empresa.sh pronaca subir
```

Después:

| Quiero | Comando |
|---|---|
| Que el equipo reciba mis cambios | `./sincronizar-empresa.sh pronaca subir` |
| Traer lo que mejoró el equipo | `./sincronizar-empresa.sh pronaca traer` |

Si `subir` es rechazado, es que el equipo subió algo: ejecuta `traer` y luego
`subir`. Nunca se fuerza un push.

El repositorio de la empresa solo recibe `empresas/<empresa>/`: nada de `personal/`
llega allí.

## Subir las skills personales a la app de Claude y a ChatGPT

```bash
./crear-zips.sh
```

Deja un `.zip` por skill en `dist/<fecha>/`, y comprueba antes que cada descripción
tenga como máximo 200 caracteres (límite de la app de Claude).

- Claude: Customize → Skills → + → Create skill → Upload a skill.
- ChatGPT: Plugins → Skills → Create → Upload from your computer (si tu plan lo
  permite).

## Mejorar una skill

1. Abre este repositorio en Cursor o Claude Code y pide el cambio (o "guarda esto en
   una skill").
2. Revisa el diff, haz commit y push.
3. Si es de una empresa: `./sincronizar-empresa.sh <empresa> subir`.
4. Si es personal y la usas en la app de Claude o ChatGPT: `./crear-zips.sh` y sube
   el `.zip` nuevo.

## Añadir otra empresa

Copia `empresas/pronaca/` como `empresas/<empresa>/`, cambia `empresa/perfil.md` e
`identificadores.md`, quita las skills que solo sirven en Pronaca y publícala con
`sincronizar-empresa.sh`.

## Estructura

```
skills/
├── instalar.sh              enlaza todo en el Mac
├── crear-zips.sh            .zip de personal/ para Claude y ChatGPT
├── sincronizar-empresa.sh   publica o trae empresas/<empresa> con git subtree
├── personal/                mis skills
└── empresas/
    └── pronaca/             lo que ve el repositorio de Pronaca
        ├── empresa/         perfil, identificadores, avisos
        └── skills/          12 skills
```

Este repositorio es **privado**: `empresas/*/empresa/identificadores.md` tiene
información interna. Nunca se guardan contraseñas ni tokens.
