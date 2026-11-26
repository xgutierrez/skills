---
name: genie-pruebas
description: >-
  Prueba y compara agentes Databricks: Supervisor MIA y Genie (dev/prd).
  Resuelve alias sin pedir IDs. Usa cuando el usuario diga @dev, @prd,
  supervisor, mia, Genie, comparar supervisor vs Genie, probar agente,
  routing, o aliases ventas/dzs/rrhh/gastos/rentabilidad.
---

# Agentes Databricks: cómo probarlos

Los identificadores de agentes, endpoints y espacios Genie están en
[agents.md](agents.md).

El usuario **no pasa IDs**. Solo ambiente + alias + pregunta o tipo de prueba.

Catálogo: [agents.md](agents.md) · Detalle flujo: [flujo-supervisor.md](flujo-supervisor.md) · Frases: [ejemplos.md](ejemplos.md)

## 1. Ambiente (siempre primero)

| Dice el usuario | Ambiente | Notas |
|---|---|---|
| `@dev` / `dev` / nada | **DEV** | MCP actual = DEV (`adb-bigdata-dev`) |
| `@prd` / `prod` | **PRD** | Solo si MCP/perfil prd está listo; si no, avisar |

Abrir cada respuesta con: `Ambiente: DEV|PRD · Agente: <alias>`

## 2. Quién es quién

```
Usuario
  ├─ @dev supervisor / mia  → Multi-agente (enruta a Genies/RAG)
  └─ @dev rentabilidad|ventas|dzs|rrhh|gastos → Genie directo
```

- **Supervisor** (`mia`): entiende, elige subagente, puede **reescribir** la pregunta.
- **Genie**: ejecuta SQL sobre su space.
- Si supervisor y Genie dan distinto número → casi siempre fue **rewrite** del supervisor (ver § 5).

## 3. Cómo el usuario te habla (plantillas)

```
@dev supervisor: <pregunta de negocio>
@dev rentabilidad: <pregunta>
@dev compara supervisor vs rentabilidad: <pregunta>
@dev analiza routing: <pregunta>
```

Sin `@dev`/`@prd` → asumir **dev**. Sin alias claro → preguntar una vez o inferir (costo de servir / margen → `rentabilidad`).

## 4. Qué hacer tú (agente Cursor)

### A) Preguntar al supervisor
1. Resolver endpoint desde [agents.md](agents.md) (`<endpoint en agents.md>` en DEV).
2. Invocar serving: `POST /serving-endpoints/<endpoint>/invocations` con `{"input":[{"role":"user","content":"<pregunta>"}]}`.
3. En la traza reportar: Genie elegido (`name` del tool), `genie_query` reescrito, respuesta final.

### B) Preguntar a Genie directo
1. Resolver `space_id` por alias.
2. `start_conversation_and_wait` (SDK) o revisar conversación si ya existe.
3. Reportar: SQL, %/cifras, definición de métrica usada.

### C) Comparar supervisor vs Genie (modo preferido para regresiones)
Misma pregunta en A y B. Tabla:

| | Supervisor | Genie directo |
|---|---|---|
| Resultado | | |
| Pregunta usada | (reescrita?) | (literal?) |
| Fórmula/SQL | | |

Veredicto: ¿mismo número? si no → causa (rewrite / métrica distinta / filtro perdido).

### D) Solo analizar (sin ejecutar)
Si el usuario pega respuesta de la UI → evaluar routing, rewrite, filtros, formato.

## 5. Regla de oro (aprendida en costo de servir)

Si el usuario pide **% costo de servir + Área Comercial**:
- Genie debe usar **P&L del space**, no `30. Gasto distribuido / 08.Venta Neta`.
- Si el supervisor reescribió la métrica → marcarlo ❌ rewrite indebido.
- No inventes la fórmula: compara lo que cada uno ejecutó.

## 6. Plantilla de salida

```markdown
## Prueba agentes
- Ambiente: DEV
- Modo: supervisor | genie | comparar
- Pregunta: …

### Resultados
| Canal | Valor | Pregunta efectiva | Nota |
|---|---|---|---|
| Supervisor → <Genie> | … | … | |
| Genie <alias> | … | … | |

### Veredicto
✅ alineados / ⚠️ rewrite / ❌ routing o métrica incorrecta
- Siguiente: …
```
