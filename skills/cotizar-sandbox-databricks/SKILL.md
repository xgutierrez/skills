---
name: cotizar-sandbox-databricks
description: >-
  Estima el presupuesto de un workspace Databricks sandbox a partir del
  consumo real del tenant (system.billing) y genera un correo de cotización
  con escenarios bajo/base/alto. Usar cuando el usuario pida cotizar,
  estimar, presupuestar o cuantificar un sandbox Databricks, costos de
  ambiente sandbox, partida 2027, o una solicitud de presupuesto de un área
  (RRHH, Finanzas, Trade, etc.) para un workspace sandbox.
---

# Cotizar sandbox Databricks

Estima **solo consumo Databricks a precio de lista (USD)**. Nunca inventar montos: primero consultar system tables vía MCP `user-databricks-prd` (`execute_sql`). Las tablas `system.*` son de cuenta (visibles desde PRD). Si MCP DEV está caído, usar PRD igual.

Convención de nombre: `adb-sandbox-<area>` (datos, finanzas, mercadeo, trade, …).

## Entrada (preguntar solo lo que falte)

Obligatorio para el estimado:

- Área solicitante y destinatario del correo (nombre)
- Número de personas / desarrolladores
- Cuántos desarrollan en un día típico (concurrencia)
- **Horas activas al día por persona** (sesiones con cómputo encendido; si no saben, asumir 4 h y decirlo)
- Patrón tentativo: notebooks interactivos, SQL Warehouse, Jobs, Genie/AI, Apps

Hacer estas preguntas básicas (con la herramienta de preguntas si está disponible) antes de calcular; mejoran mucho la precisión. Opcional: sandbox de referencia (`adb-sandbox-…`) y volumen estimado de datos en GB (para almacenamiento); si no los dan, elegir referencia con datos (paso 3) y asumir 250 GB.

No bloquear el estimado por cuenta contable ni dimensión: se piden en el correo.

Supuesto de plataforma si no dicen lo contrario: **un cómputo de propósito general + un SQL Warehouse compartidos**, apagado por inactividad.

## Flujo

1. Listar sandboxes y consumo mensual (SQL en [sql-consultas.md](sql-consultas.md)).
2. Armar ficha por workspace: meses con gasto, USD lista, DBUs, identidades `run_as`, mix `billing_origin_product`.
3. Elegir **un** sandbox de referencia:
   - El que indique el usuario, si existe y tiene meses maduros.
   - Si no: el más parecido en **identidades activas** y **mix de producto** al patrón pedido.
   - No usar un sandbox **idle** (casi sin gasto tras el arranque) como base de un equipo que sí va a trabajar.
   - No usar un outlier de alto consumo (p. ej. mercadeo ~USD 1.5k–2.5k/mes) para un equipo chico de exploración, salvo que el área declare uso intensivo equivalente.
4. **Normalizar meses**: excluir los 2 primeros meses de vida del workspace (ramp-up) y el mes calendario en curso si está incompleto. Excluir meses con USD por debajo del 10 % de la mediana del resto (casi apagado). Si quedan menos de 3 meses, avisar y usar lo disponible.
5. Calcular Databricks:
   - `usd_mes_ref` = promedio de meses maduros
   - `n_ref` = promedio de identidades distintas `run_as` en esos meses (mínimo 1)
   - `usd_persona_mes` = `usd_mes_ref / n_ref`
   - `factor_concurrencia` = `desarrollan_al_dia / personas` (acotar 0.25–1.25). Si no hay “al día”, usar 1.
   - `factor_horas` = `horas_activas_dia / 4` (acotar 0.5–1.5; 4 h es la intensidad implícita de la referencia)
   - **Base** = `usd_persona_mes * personas * factor_concurrencia * factor_horas`
   - **Bajo** = percentil 25 de meses maduros, mismo escalado (adopción gradual + apagado estricto)
   - **Alto** = percentil 75 (si hay ≥4 meses; si no, `max(meses)`) escalado, **× 1.15** de contingencia
6. Estimar **infraestructura Azure** con datos reales del tenant (facturada aparte; nunca usar factores o tarifas inventadas):
   - **VMs del cómputo clásico**: horas reales por tipo de nodo de la referencia en los meses maduros, con la query 6 de [sql-consultas.md](sql-consultas.md) (`system.compute.node_timeline`). El serverless no genera VM aparte: su infraestructura ya viene en el precio del DBU (verificar reparto con la query 5).
   - **Región**: `source_region` predominante del consumo (query 7).
   - **Precios oficiales vigentes**: API pública Azure Retail Prices (URLs listas en [sql-consultas.md](sql-consultas.md)); tomar el precio Linux Consumption por `armSkuName` y región para las VMs, y `Hot LRS Data Stored` de ADLS Gen2 para almacenamiento. Consultar el API en cada cotización; no memorizar tarifas.
   - `azure_vm_mes` = Σ(horas_vm × precio_hora) ÷ meses maduros, escalado con los mismos factores que Base.
   - `azure_storage_mes` = GB estimados por el área × precio real por GB/mes.
   - Red: el cargo NETWORKING ya viene medido dentro del consumo Databricks del paso 2; no añadir nada extra.
   - `azure_mes` = `azure_vm_mes + azure_storage_mes`. Sumarlo a los tres escenarios; **no** desglosar el monto Azure en el correo (solo en la tabla interna al usuario).
   - **Solicitud** = redondear el alto anual (con Azure incluido) al **ciento** hacia arriba (mensual coherente: anual/12)
7. Mostrar al usuario (antes o junto al correo) una tabla corta: referencia elegida, ventana de meses, USD/mes crudo, n_ref, factores, estimación Azure y mix de productos. Luego redactar el correo.

Redondear USD a entero en el correo. Internamente usar 2 decimales.

## Correo de salida

Español, **conciso** y **atemporal** (sirve en cualquier momento, no atado a un año de presupuesto). Seguir [plantilla-correo.md](plantilla-correo.md) al pie. No copiar números del ejemplo; salen de este cálculo.

Incluir siempre:

- Tabla Escenario: Bajo / Base / Alto / Solicitud recomendada (mensual y anual USD, columna Uso). Los montos ya incluyen la estimación Azure.
- Metodología en 1–2 frases: consumo real de un sandbox equivalente del ecosistema, escalado al tamaño y ritmo del equipo, con 15 % de contingencia en el alto.
- Recomendar el **escenario alto** en una frase.
- Alcance: precio de lista USD + infraestructura Azure estimada (indicar el monto mensual de Azure); **sin** descuentos contractuales ni licencias de visualización.
- Control: apagado automático, etiquetado/política de presupuesto (cuenta/dimensión), responsable del área.
- Pedir: número de cuenta contable y número de dimensión; ticket en mesa de servicios al área de Datos.

Prohibido en el correo:

- Atarlo a un año o partida específica (“presupuesto 2027”, “durante 2027”): usar formulaciones neutras (“para su planificación presupuestaria”).
- Nombrar el área dueña del sandbox de referencia (“el de Trade”): decir “un sandbox equivalente que ya opera en nuestro ecosistema”.
- Párrafos largos de metodología (ventanas de fechas, normalizaciones, factores): eso va en la tabla al usuario, no al correo.
- Justificaciones tipo “es más sencillo no ejecutar un presupuesto aprobado que gestionar una ampliación”.
- Cierres de relleno (“con gusto revisamos el detalle en una reunión”).

## Guardrails

- Solo `SELECT` / `SHOW` / `DESCRIBE` en MCP. Nunca DML.
- Precio: `pricing.effective_list.default` (si es null, `pricing.default`). SKUs sin precio de lista (a veces Genie): reportar DBU y marcar USD como no tasado; no fingir tarifa.
- No mezclar workspaces `adb-bigdata-*`, `databricksAI` ni `databricks_capacitacion` en el pool de referencia salvo que el usuario lo pida.
- Si MCP falla: no estimar de memoria; reintentar PRD o pedir extracto de usage.
