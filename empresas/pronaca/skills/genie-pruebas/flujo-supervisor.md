# Flujo Supervisor MIA → Genie

## DEV

| Campo | Valor |
|---|---|
| Nombre | `multi-agent-mia-dev` |
| Alias | `supervisor` / `mia` |
| ID | `<id en agents.md>` |
| Endpoint | `<endpoint en agents.md>` |
| Workspace | `adb-bigdata-dev` |

Genie típicos: `ventas`, `dzs`, `rrhh`, `gastos`, `rentabilidad`.

## Invocación desde Cursor (DEV)

```json
POST /serving-endpoints/<endpoint en agents.md>/invocations
{"input":[{"role":"user","content":"<pregunta>"}]}
```

En la respuesta mirar:
1. `function_call.name` → qué Genie eligió
2. `arguments.genie_query` → **qué le preguntó** (aquí se ve el rewrite)
3. Mensaje final del supervisor

## Genie directo

SDK: `w.genie.start_conversation_and_wait(space_id=..., content=<pregunta literal>)`

## Checklist de calidad

- [ ] Ambiente correcto
- [ ] Routing al Genie esperado
- [ ] `genie_query` no cambia métrica ni quita filtros
- [ ] Mismo sentido que Genie directo en pruebas de comparar
- [ ] Sin PII en RRHH de terceros
