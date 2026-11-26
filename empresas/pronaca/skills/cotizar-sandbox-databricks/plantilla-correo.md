# Plantilla de correo (cotización sandbox)

Sustituir lo que va entre corchetes. Correo corto y atemporal: sin años ni partidas específicas, sin nombrar el área del sandbox de referencia, sin párrafos de metodología. Los importes salen del flujo de la skill, no de este ejemplo.

---

Estimado/a [Nombre]

Conforme a tu solicitud, comparto la estimación de costos del entorno Databricks (sandbox) para [ÁREA], como insumo para su planificación presupuestaria.

**Resumen del estimado**

Para un equipo de [N] personas, con un cómputo de propósito general y un SQL Warehouse compartidos:

| Escenario | Mensual (USD) | Anual (USD) | Uso |
|-----------|---------------|-------------|-----|
| Bajo | [ ] | [ ] | Adopción gradual y control estricto de apagado |
| Base | [ ] | [ ] | [N] personas, patrón comparable al sandbox de referencia |
| Alto | [ ] | [ ] | Crecimiento de uso + contingencia 15% |
| Solicitud recomendada | [ ] | [ ] | Redondeo del escenario alto |

El estimado se construyó sobre el consumo real de un sandbox equivalente que ya opera en nuestro ecosistema, escalado al tamaño y ritmo de trabajo del equipo de [ÁREA]. Sugerimos presupuestar el escenario alto, ya que el consumo depende directamente de las horas de sesión activa del equipo.

**Alcance**

Los valores corresponden al consumo de la plataforma Databricks a precio de lista en dólares e incorporan la infraestructura Azure asociada al ambiente. No incluyen descuentos contractuales que puedan aplicar a nivel corporativo ni licenciamiento de herramientas de visualización u otros servicios fuera de Databricks.

**Control del gasto**

- **Apagado automático de recursos** tras un período de inactividad; es el control con mayor impacto en el costo.
- **Etiquetado y política de presupuesto** asociados a la cuenta y dimensión de [ÁREA] desde el primer día, para que la facturación sea trazable.
- **Un responsable designado del área** que reciba el reporte mensual de consumo y canalice novedades a Soporte de TI.

**Siguientes pasos**

Para configurar el entorno con la atribución de costos correcta, necesitamos que [ÁREA] nos confirme:

- Número de cuenta contable desde el cual se pagarán los consumos de Databricks.
- Número de dimensión asociado al área.

Con esa definición, por favor ayúdennos generando el ticket en la mesa de servicios asignado al área de Datos con la solicitud formal del espacio.

Quedo atento a cualquier consulta.

Saludos cordiales,

---

## Frases prohibidas

No usar: "presupuesto [año]", "durante [año]", el nombre del área del sandbox de referencia, "medido entre [mes] y [mes]", "es considerablemente más sencillo no ejecutar un presupuesto aprobado", "con gusto revisamos el detalle en una reunión", ni desgloses del monto Azure tipo "aprox. USD X/mes" (el monto Azure va integrado en los escenarios).
