# Reflexión final

**Eber Silva García** — 8 de octubre de 2026

## ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?

Muy útil. En mi trabajo diario desarrollo en Java con Spring y bases de datos
PostgreSQL y Oracle, y ya uso Claude Code en esos proyectos, pero este reto me
obligó a usarlo de forma más disciplinada: con un `CLAUDE.md` que funciona como
contrato, una refactorización por commit y validación después de cada cambio.
En pocos minutos tuve el mapa del proyecto, la lista de *code smells* con
archivo y línea y un plan ordenado por riesgo. Lo que más me sirvió fue que
no se quedó en "los tests pasan": comparó el menú original contra el nuevo con
la misma entrada, hizo una prueba diferencial de 14 000 casos para
`mas_vendidos` y usó `mypy --strict` para que los type hints no fueran
decorativos.

## ¿Qué propuso la IA que yo no había notado?

Que **la suite original era débil**. Daba verde aunque cambiara el texto del
ticket, los mensajes de error o el orden de los empates. Si hubiera
refactorizado confiando solo en esos 20 tests, habría podido romper cosas sin
enterarme. Escribir primero 43 pruebas de caracterización contra el código
original fue la decisión que más pagó: en R11 un error que borraba todos los
mensajes de error pasó la suite original 20 de 20, y solo lo atraparon las
pruebas nuevas. También encontró un bug real que la consigna no mencionaba:
cargar un JSON sin la llave `"ventas"` vaciaba el inventario antes de tronar.

## ¿En qué casos hubo que corregir o rechazar sugerencias?

En tres momentos el cambio parecía equivalente y no lo era:

- **R4:** `if not codigo` parece una simplificación inocente, pero cambia el
  caso de un código `0`. Pasó todos los tests; se detectó al revisar el diff.
- **R9:** `Counter.most_common(n)` era la opción idiomática, pero no es
  equivalente cuando `n` es negativo; se usó `sorted` con un corte de lista.
- **R11:** un reemplazo masivo quitó un `global` que sí hacía falta.

Las tres correcciones salieron de las pruebas y de la revisión del diff, no de
la intuición. Me quedo con el patrón: **"simplificar" e "idiomático" invitan a
cambios que se ven iguales pero no lo son en los casos límite.**

## ¿Qué aprendí sobre refactorizar con apoyo de IA?

1. **Primero la red de seguridad, después los cambios.** Unas buenas pruebas
   de caracterización valen más que cualquier prompt bien escrito.
2. **Un buen prompt lleva tres cosas:** el objetivo, la restricción de
   comportamiento ("conserva la semántica exacta", "la salida no debe cambiar
   ni un carácter") y cómo se va a verificar (qué test, qué comando).
3. **`CLAUDE.md` es un contrato.** Dejar por escrito la API que usan los
   tests, las reglas de negocio y "una refactorización por commit" evitó que
   el agente renombrara `agregarProducto` o mezclara cambios. Es la misma
   lógica que aplico en el trabajo cuando una base de datos se comparte con
   producción: se escribe qué no se toca antes de empezar.
4. **Que los tests pasen no prueba que el cambio sea correcto**; prueba que no
   se rompió lo que los tests miran. La revisión sigue siendo responsabilidad
   de quien entrega.
5. **Los commits pequeños abaratan los errores.** El propio agente se
   equivocó al armar el commit base; se notó porque el diff de R1 traía
   archivos completos y se corrigió antes de seguir.

## ¿Qué haría distinto?

- Convertir la comparación del menú en pruebas de pytest con `monkeypatch`
  sobre `input`, en lugar de un script externo.
- Eliminar el estado global por completo con una clase `Tienda`, acordando
  antes si se puede ajustar el contrato de los tests.
- Agregar `mypy` y `ruff format --check` a la configuración del proyecto para
  que no dependan de que alguien se acuerde de correrlos.
