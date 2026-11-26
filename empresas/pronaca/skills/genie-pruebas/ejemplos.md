# Ejemplos de uso (cópialos en el chat de Cursor)

## Uso diario — una frase

### Preguntar al multiagente
```
@dev supervisor: ¿Cuál es el porcentaje de costo de servir de consumo humano acumulado a mayo 2026, para el área comercial?
```

### Preguntar solo a un Genie
```
@dev rentabilidad: ¿Cuál es el porcentaje de costo de servir de consumo humano acumulado a mayo 2026, para el área comercial?
```

```
@dev ventas: ¿Cuánto fue la venta directa en enero 2026?
```

```
@dev dzs: ¿Cuánto vendieron los DZs en enero 2026?
```

### Comparar (el más útil)
```
@dev compara supervisor vs rentabilidad: ¿Cuál es el porcentaje de costo de servir de consumo humano acumulado a mayo 2026, para el área comercial?
```

Esperado del agente Cursor: tabla Supervisor vs Genie + si hubo rewrite + veredicto.

### Solo routing (¿a qué Genie iría?)
```
@dev analiza routing: ¿Cómo van las ventas?
```

Esperado: sell-in vs sell-out → debería aclarar o elegir ventas/dzs.

### Analizar algo que ya corriste en la UI
```
@dev analiza supervisor
Pregunta: …
Respuesta que me dio: …
```

---

## Aliases rápidos

| Escribes | Va a |
|---|---|
| `supervisor` / `mia` | multi-agent-mia-dev |
| `rentabilidad` | Genie Rentabilidad TIBCO |
| `ventas` | Genie Ventas (sell-in) |
| `dzs` | Genie Ventas DZs |
| `rrhh` | Genie RRHH |
| `gastos` | Genie Gastos Corporativos |

---

## Ejemplo completo de sesión

**Tú:**
```
@dev compara supervisor vs rentabilidad:
Cual es el porcentaje de costo de servir de consumo humano acumulado al mes de mayo del 2026, para el area comercial
```

**Cursor debería:**
1. Confirmar `Ambiente: DEV · Agente: supervisor + rentabilidad`
2. Llamar supervisor (`<endpoint en agents.md>`)
3. Llamar Genie rentabilidad (misma pregunta literal)
4. Devolver algo como:

```markdown
## Prueba agentes
- Ambiente: DEV
- Modo: comparar

| Canal | Valor | Pregunta efectiva | Nota |
|---|---|---|---|
| Supervisor → rentabilidad | 12.78% | reescrita con gasto distribuido/VN | rewrite |
| Genie rentabilidad | 5.18% | pregunta literal + P&L | OK space |

### Veredicto
⚠️ El supervisor cambió la métrica. Genie directo usó P&L Área Comercial.
```

---

## Producción (cuando esté conectado)

```
@prd supervisor: <misma pregunta de negocio>
@prd compara supervisor vs rentabilidad: <pregunta>
```

Sin catálogo PRD autenticado, Cursor debe decir que PRD no está listo (no mezclar IDs de DEV).
