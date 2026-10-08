# Bitácora de refactorización

**Nombre:** Eber Silva García
**Fecha:** 2026-10-08
**Herramienta:** Claude Code (CLI), modelo Claude Opus 5.5, en modo agente con permisos de edición y terminal.
**Rama:** `refactorizacion` (13 commits sobre `main`, uno por paso)

> **Cómo se trabajó.** La sesión de Claude Code arrancó con una petición
> general ("ayúdame con este reto", más los documentos del reto y el ZIP del
> proyecto). A partir de ahí el agente leyó el código, propuso el plan y
> ejecutó cada refactorización. La columna **Prompt** registra la instrucción
> concreta con la que se ejecutó cada paso: está redactada para que cualquiera
> pueda repetir el paso pegándola en Claude Code con este mismo `CLAUDE.md`.

## Resumen

| Métrica | Antes | Después |
|---|---|---|
| Errores de `ruff check src` | 20 | **0** |
| Pruebas | 20 (suite original) | **70** (20 originales intactas + 50 nuevas) |
| `mypy --strict` | no aplica (sin hints) | **sin errores** |
| Complejidad máxima (McCabe) | 17 (`menu`), 12 (`registrar_venta`) | 7 (`menu`), 5 (`registrar_venta`) |
| Sentencias `global` | 6 | 3 (solo en las funciones dueñas del estado) |
| Funciones | 20 | 36 (más pequeñas, una responsabilidad cada una) |
| Código muerto | 3 funciones + 1 bloque comentado + 1 variable | 0 |

Cada paso se validó con `pytest` y `ruff check src`. La salida completa de
cada corrida está en [`docs/evidencia/`](evidencia/), con un log por commit.
Desde R6, además, se comparó el programa interactivo original contra el
refactorizado con la **misma sesión scriptada** de 40 entradas (todas las
opciones del menú y casos de error): la salida (155 líneas) y el JSON guardado
fueron idénticos en cada paso.

## Tabla de refactorizaciones

| # | Prompt usado (resumen) | Cambio realizado | Justificación | Tests OK |
|---|---|---|---|---|
| 0 | "Antes de refactorizar, escribe pruebas de caracterización en un archivo nuevo para lo que la suite no cubre…" | `tests/test_casos_borde.py`: 43 pruebas contra el código **original** | Red de seguridad: la suite base no verificaba tickets, mensajes de error, límites ni empates | ✅ 63/63 |
| 1 | "Elimina código muerto y comentarios obsoletos…" | Fuera `calcular_descuento_viejo`, `reporteViejoCSV`, `exportar_txt` comentado, `MODO_DEBUG`, `import os`, cabeceras `coding` | Código que nadie llama confunde y hay que mantenerlo | ✅ 63/63 · ruff 20→13 |
| 2 | "Reemplaza los números mágicos por constantes con nombre…" | `TASA_IVA`, `UMBRAL_/TASA_DESCUENTO_*`, reglas VIP, `STOCK_MINIMO`, etc. | Las reglas de negocio quedan documentadas y en un solo lugar | ✅ 63/63 · ruff 13 |
| 3 | "registrar_venta y cotizar duplican el cálculo de precio; extráelo…" | `calcular_descuento_por_volumen`, `calcular_descuento_vip`, `calcular_importes` → `Importes` | Elimina duplicación: cotización y venta ya no pueden divergir | ✅ 63/63 · ruff 13→11 |
| 4 | "Aplana los if anidados con cláusulas de guarda conservando el orden…" | Guardas en `registrar_venta`, `startswith` para VIP, `return` directo en `hayArchivo` | De 4 niveles de anidamiento a 1; se lee de arriba abajo | ❌→✅ 64/64 · ruff 11→7 |
| 5 | "Separa el armado del ticket de la lógica de la venta…" | `formatear_ticket(venta)` con f-strings; venta como literal de dict | `registrar_venta` dejaba de "hacer de todo"; presentación aparte | ✅ 64/64 · ruff 7 |
| 6 | "Divide menu() en una función por opción con tabla de despacho…" | `opcion_*()` + diccionario `ACCIONES`; nombres `codigo/cantidad/cliente` | Complejidad 17→3, cada opción se puede leer y probar sola | ✅ 64/64 · ruff 7→5 |
| 7 | "Mejora el manejo de errores en almacen; primero escribe los tests…" | `with`, `JSONDecodeError`/`OSError`, validación de estructura antes de tocar el estado | Un JSON incompleto borraba el inventario y luego tronaba | ✅ 70/70 · ruff 5→2 |
| 8 | "Renombra identificadores crípticos y unifica snake_case…" | `contador_ventas`, `existe_archivo`, `formatear_dinero`, `producto`, `nuevo_stock`… | Los nombres dicen qué contienen; cumple PEP 8 | ✅ 70/70 · ruff 2→**0** |
| 9 | "Reescribe reportes.py de forma idiomática sin cambiar ni un carácter de salida…" | Burbuja → `Counter`+`sorted`; `sum`, `join`, f-strings; `tiene_stock_bajo()` | Código O(n log n), sin reglas duplicadas, sin `s/t/v/aux` | ✅ 70/70 · ruff 0 |
| 10 | "Agrega type hints a todo src/ con TypedDict y verifica con mypy --strict" | `Producto`, `DatosVenta`, `Venta`; firmas tipadas | La forma de los datos queda documentada y verificable | ✅ 70/70 · mypy OK |
| 11 | "almacen escribe variables internas de gestor; encapsula el estado…" | `exportar_estado`, `restaurar_estado`, `registrar_error` | Un solo módulo es dueño de su estado; `global` 6→3 | ❌→✅ 70/70 · mypy OK |
| — | Pulido final | Docstring obsoleto de `gestor`, `TypeGuard` en `almacen` | Comentario que ya no describía el código | ✅ 70/70 · ruff 0 · mypy OK |

❌→✅ = hubo un intento fallido detectado por las pruebas y corregido antes del commit (ver detalle).

---

## Detalle por paso

### Paso previo — Configuración y diagnóstico

**Configuración.** Se creó `CLAUDE.md` con:
- qué hace la app;
- los comandos de prueba y linter;
- las reglas inquebrantables: no tocar `tests/` ni `pyproject.toml`, y la lista de la API pública que los tests usan;
- las reglas de negocio exactas, que el agente no debe "arreglar";
- convenciones con un ejemplo de antes y después.

`.claudeignore` excluye el entorno virtual, las cachés, la basura de macOS, `.git`, los logs de evidencia y los JSON generados por la app (conserva `datos_ejemplo.json`).

**Prompt de diagnóstico** (modo chat, solo lectura):

> Lee todo el proyecto (src, tests, pyproject.toml, README). No modifiques nada.
> Dame: 1) qué hace cada módulo, 2) la lista de *code smells* con archivo y línea,
> 3) qué partes del comportamiento NO cubre la suite de pruebas, 4) un orden
> de refactorización priorizado por riesgo, y 5) qué restricciones imponen los
> tests sobre el diseño (por ejemplo, qué nombres globales leen).

**Code smells encontrados** (20 los marca ruff; los demás se encontraron leyendo el código):

| Smell | Dónde | ¿Lo detecta ruff? |
|---|---|---|
| Función gigante (complejidad 17) | `main.menu` | Sí (C901) |
| Función que "hace de todo" (complejidad 12) | `gestor.registrar_venta` | Sí (C901) |
| Lógica de precios duplicada | `registrar_venta` / `cotizar` | No |
| `if` anidados en 4 niveles | `registrar_venta`, regla VIP | Parcial (SIM102) |
| Números mágicos (0.16, 1000, 500, 0.10, 0.05, 200, 0.02, 5) | `gestor`, `reportes` | No |
| Nombres crípticos (`aux`, `temp2`, `x`, `d`, `t`, `hacer_cosa`) | todos | No |
| camelCase mezclado | `contadorVentas`, `hayArchivo`, `reporteViejoCSV` | Sí (N802/N816) |
| Código muerto | `calcular_descuento_viejo`, `reporteViejoCSV`, `exportar_txt`, `MODO_DEBUG`, `import os` | Parcial (F401) |
| `open()` sin `with` y `except Exception` genérico | `almacen` | Parcial (SIM115) |
| Ordenamiento de burbuja con TODO | `reportes.mas_vendidos` | No |
| Estado global mutado desde otro módulo | `almacen` → `gestor.*` | No |
| Concatenación repetida de strings | ticket y reportes | No |
| Mezcla de lógica y presentación | ticket dentro de `registrar_venta` | No |

**Hallazgo clave del diagnóstico:** la suite original es de caja negra, pero
**no verifica el texto de los tickets ni de los reportes, los mensajes de
`ultimo_error`, los límites exactos de descuento ni el orden en empates**.
Una refactorización podía cambiar todo eso y seguir "en verde". Por eso el
primer paso fue escribir pruebas de caracterización.

### Paso 0 — Pruebas de caracterización

**Prompt:**

> Antes de refactorizar, escribe pruebas de caracterización en un archivo NUEVO
> `tests/test_casos_borde.py` (no toques los existentes) para todo lo que la
> suite no cubre: texto exacto del ticket con y sin descuento, texto exacto de
> los reportes, cada mensaje de `ultimo_error`, los límites $500/$1000, la regla
> VIP con montos bajo y sobre $200, clientes `None`/`"VI"`/`"vip"`, empates en
> `mas_vendidos`, archivo corrupto/inexistente y que `INVENTARIO`/`VENTAS` sigan
> siendo el mismo objeto tras cargar. Deben pasar contra el código ACTUAL.

**Resultado:** 43 pruebas nuevas, todas en verde contra el original (63/63).
Log: `evidencia/01_tests_caracterizacion.log`.
**Por qué:** convierte comportamiento implícito en explícito. En R4 y R11 estas
pruebas atraparon regresiones que la suite original dejaba pasar.

### R1 — Eliminar código muerto y comentarios obsoletos

**Prompt:**

> Elimina el código muerto: funciones que nadie llama (verifica con búsqueda en
> src y tests antes de borrar), código comentado, variables nunca leídas,
> imports sin usar y las cabeceras `# -*- coding: utf-8 -*-`. No toques nada más.

**Cambio:** se borraron `calcular_descuento_viejo` (fórmula de 2023),
`reporteViejoCSV` (además abría el archivo sin `with`), el bloque comentado
`exportar_txt`, `MODO_DEBUG` (nunca se leía), `import os` sin usar y las 4
cabeceras de encoding (UTF-8 es el default en Python 3).
**Justificación:** "por si acaso" está para eso git. Ese código se lee, se
mantiene y confunde: ¿cuál es la fórmula de descuento vigente?
**Tests:** 63 passed · ruff 20 → 13. Log: `evidencia/02_r1_codigo_muerto.log`.

### R2 — Números mágicos → constantes

**Prompt:**

> Reemplaza los números mágicos de gestor.py y reportes.py por constantes con
> nombre al inicio de cada módulo (IVA, umbrales y tasas de descuento, reglas
> VIP, stock mínimo, nombre de la tienda, formato de fecha). Solo sustitución:
> no cambies la estructura todavía.

**Cambio:** 11 constantes en `gestor`, `STOCK_MINIMO` en `reportes`. Los
comentarios aclaran dos sutilezas de la regla VIP: el umbral se compara contra el
subtotal *ya con descuento*, pero el 2 % se calcula sobre el subtotal *original*.
**Justificación:** si cambia el IVA, se toca una sola línea. Antes `0.16`
aparecía dos veces y `5` dos veces en lugares distintos.
**Decisión:** se pidió explícitamente "solo sustitución" para que el diff fuera
fácil de revisar y no mezclar propósitos (regla 4 de `CLAUDE.md`).
**Tests:** 63 passed · ruff 13. Log: `evidencia/03_r2_constantes.log`.

### R3 — Extraer el cálculo de importes duplicado

**Prompt:**

> `registrar_venta` y `cotizar` duplican el cálculo de descuentos e IVA.
> Extrae funciones puras: `calcular_descuento_por_volumen(subtotal)`,
> `calcular_descuento_vip(subtotal, descuento_volumen, cliente)` y
> `calcular_importes(subtotal, cliente="")` que regrese un NamedTuple con
> subtotal, descuento, impuesto y total. Ojo: `cotizar` NO aplica VIP y los
> resultados en punto flotante deben ser idénticos (mismo orden de operaciones).

**Cambio:** tres funciones puras y `Importes` (NamedTuple). `cotizar` pasó de
19 a 7 líneas.
**Justificación:** la duplicación ya había divergido: `cotizar` no tenía el
`else: desc = 0`, ni el bloque VIP. Con una fuente única, la prueba
`test_cotizar_coincide_con_el_total_de_la_venta` queda garantizada por diseño.
**Por qué se mencionó el punto flotante en el prompt:** `base + base * 0.16`
y `base * 1.16` no siempre dan el mismo float. Pedir "mismo orden de
operaciones" evitó que la IA "simplificara" la fórmula.
**Tests:** 63 passed · ruff 13 → 11 (desaparece el C901 de `registrar_venta`).
Log: `evidencia/04_r3_extraer_importes.log`.

### R4 — Simplificar condicionales (con intento fallido)

**Prompt (1.ª versión):**

> Aplana los if anidados de registrar_venta con cláusulas de guarda, simplifica
> la regla VIP y el if/else que regresa True/False en hayArchivo.

**Intento fallido:** la primera versión usó `if not codigo:` como guarda. Todos
los tests pasaron (63/63), pero en la revisión del diff se detectó que **no es
equivalente** a `codigo is None or codigo == ""`: con un código numérico `0`
el original lo aceptaba y la nueva versión respondía "codigo vacio". Se escribió
`test_codigo_numerico_cero_no_se_trata_como_vacio` y se confirmó que **pasaba
con el código anterior y fallaba con el nuevo**. Log:
`evidencia/05a_r4_intento_fallido.log`.

**Prompt (2.ª versión, la que funcionó):**

> Las guardas deben conservar la semántica EXACTA y el orden de validación del
> original. Compara con `None` y `""` explícitamente; no uses truthiness.

**Cambio final:** `if codigo in (None, ""):`; 4 guardas en el mismo orden que
el original (vacío → no existe → cantidad → stock); la regla VIP pasa de 4 `if`
anidados a `startswith`; `hayArchivo` regresa `os.path.exists(ruta)` directo.
**Justificación:** de 4 niveles de indentación a 1. Cada error se lee junto a
su condición, no 15 líneas después en un `else`.
**Aprendizaje:** "simplifica" invita a la IA a usar idioms (`not x`) que cambian
casos límite. Conviene pedir "semántica exacta".
**Tests:** 64 passed · ruff 11 → 7. Log: `evidencia/05_r4_condicionales.log`.

### R5 — Separar el ticket de la lógica de venta

**Prompt:**

> Extrae el armado del ticket de registrar_venta a `formatear_ticket(venta)`.
> Usa f-strings y una lista de líneas unida con "\n". El texto debe ser idéntico
> byte a byte (hay un test que lo verifica); `str(20.0)` es "20.0", no "20.00".

**Cambio:** `formatear_ticket` y la venta construida como literal de diccionario.
El docstring de `registrar_venta` ya no dice "esta función hace de todo".
**Revisión manual:** el original decidía si mostrar la línea de descuento con
el valor **sin redondear** y el nuevo usa el redondeado. Solo diferirían con un
descuento entre 0 y $0.005, lo cual es imposible con estas reglas (mínimo $25
por volumen o $4 por VIP). Se aceptó y se documenta aquí.
**Tests:** 64 passed · ruff 7. Log: `evidencia/06_r5_separar_ticket.log`.

### R6 — Dividir `menu()` (complejidad 17)

**Prompt:**

> Divide menu() de main.py: una función por opción (`opcion_agregar_producto`,
> etc.) y un diccionario de despacho tecla → función. Renombra c/n/p/s/cant/cli.
> Todos los textos que ve el usuario deben quedar idénticos. Como no hay tests
> de main.py, compara la salida del menú original y el nuevo con la misma
> entrada scriptada.

**Cambio:** 6 funciones `opcion_*` y `mostrar_error`, más `OPCIONES_MENU`,
`ACCIONES` y `OPCION_SALIR`. Las opciones 4 y 5 apuntan directo a
`reportes.reporte_inventario` y `resumen_ventas`, que ya imprimen.
**Validación extra:** `scripts/comparar_menu.sh` corre el `main.py` original (de `main`) y el
nuevo con una sesión de 40 entradas: todas las opciones, un número inválido,
un producto duplicado, stock insuficiente, un producto inexistente, una opción
inválida y salir. Resultado: `MENU IDENTICO (155 lineas de salida, JSON guardado igual)`.
**Justificación:** agregar una opción ya no implica tocar un `if/elif` de 60
líneas.
**Tests:** 64 passed · ruff 7 → 5. Log: `evidencia/07_r6_menu.log`.

### R7 — Mejorar el manejo de errores (tests primero)

**Prompt:**

> Mejora el manejo de errores de almacen.py. Primero escribe tests que fallen
> para: JSON válido pero sin "ventas" o sin "inventario", JSON que es una lista,
> ruta que es un directorio, y guardar en una carpeta inexistente. En todos,
> la función debe regresar False con motivo en ultimo_error y NO tocar el
> estado. Luego usa `with`, captura excepciones específicas y valida la
> estructura antes de mutar. Ajusta main para que no diga "Datos cargados"
> si la carga falló.

**Problema real encontrado:** con `{"inventario": {}}` el original hacía
`INVENTARIO.clear()` y luego tronaba con `KeyError` al buscar `"ventas"`: la app
quedaba **sin inventario y con una excepción**.
**Cambio:** `with open(...)`; `json.JSONDecodeError` y `OSError` en lugar de
`except Exception`; `_tiene_estructura_valida` revisa todo antes de mutar;
`guardar_datos` regresa `False` ante un error de disco. En `main`, si la carga
falla se muestra el error, y si el guardado falla no se sale (para no perder
los datos).
**Ciclo rojo → verde:** 6 pruebas nuevas fallaron primero
(`6 failed, 64 passed`) y luego pasaron.
**Nota:** es el único paso que cambia comportamiento, y solo en rutas de error
que antes terminaban en excepción. El camino feliz del menú siguió idéntico.
**Tests:** 70 passed · ruff 5 → 2. Log: `evidencia/08_r7_manejo_errores.log`.

### R8 — Nombres descriptivos y snake_case

**Prompt:**

> Renombra identificadores crípticos en gestor, almacen y main (aux, temp2, x,
> k…) y pasa a snake_case contadorVentas y hayArchivo; hacer_cosa → formatear_dinero.
> NO renombres agregarProducto ni buscarProducto (los usan los tests); documenta
> en su docstring por qué conservan camelCase.

**Cambio:** `contador_ventas`, `existe_archivo`, `formatear_dinero`,
`producto`, `nuevo_stock`, `texto_buscado`. `buscarProducto` se volvió una
comprensión de lista y el alta de producto un literal de diccionario.
**Justificación:** `temp2` se usaba en 4 funciones con 4 significados distintos.
**Tests:** 70 passed · ruff 2 → **0** ("All checks passed!"). Log: `evidencia/09_r8_nombres.log`.

### R9 — `reportes.py` idiomático

**Prompt:**

> Reescribe reportes.py de forma idiomática: el TODO pide cambiar la burbuja
> por sorted, usa sum() en vez de acumuladores, join y f-strings en vez de
> concatenar, y saca la regla "stock < STOCK_MINIMO" a una función porque está
> duplicada. La salida no debe cambiar ni un carácter. En mas_vendidos, los
> empates deben conservar el orden de aparición, igual que la burbuja.

**Decisión técnica:** la opción obvia era `Counter.most_common(n)`, pero se
descartó al revisar el caso límite: `most_common(-1)` regresa `[]`, mientras que
el original con `temp[0:-1]` regresa todos menos el último. Se usó `sorted(...)[:n]`,
que es estable con `reverse=True` y respeta cualquier valor de `n`.
**Validación extra:** prueba diferencial contra el `reportes.py` original con
2000 escenarios aleatorios × 7 valores de `n` (−2, −1, 0, 1, 3, 5, `None`):
**14 000 casos idénticos**.
**Tests:** 70 passed · ruff 0. Log: `evidencia/10_r9_reportes.log`.

### R10 — Type hints con TypedDict

**Prompt:**

> Agrega type hints a todo src/ (Python 3.10: `X | None`, `list[...]`).
> Define TypedDict para Producto y Venta en vez de `dict[str, Any]`, y verifica
> con `mypy --strict`. Si mypy se queja, arregla el código, no uses `# type: ignore`.

**Por qué pedir mypy:** sin un verificador, los hints son solo comentarios. Con
los hints ya escritos y los tests en verde, `mypy --strict` todavía encontró
2 problemas:
1. `bool(cliente) and cliente.startswith(...)`: mypy no puede deducir que
   `cliente` no es `None`. Se cambió a `cliente is not None and ...`, que es
   equivalente para `str | None` y más explícito.
2. `json.load` devuelve `Any`, lo cual se resolvió con `TypeGuard` en el pulido final.

**Cambio:** `Producto`, `DatosVenta` y `Venta(DatosVenta)` como TypedDict. La
venta se arma como `{**datos, "ticket": formatear_ticket(datos)}` para que el tipo
cierre sin claves opcionales. También se aplicó `ruff format`.
**Tests:** 70 passed · ruff 0 · mypy --strict sin errores. Log: `evidencia/11_r10_type_hints.log`.

### R11 — Reducir el acoplamiento al estado global (con intento fallido)

**Prompt:**

> almacen.py asigna directamente gestor.INVENTARIO, VENTAS, contador_ventas y
> ultimo_error. Haz que gestor sea el único dueño de su estado: expón
> exportar_estado(), restaurar_estado() y registrar_error(), y quita los
> `global ultimo_error` repetidos. INVENTARIO y VENTAS deben seguir siendo
> los mismos objetos (los tests los leen).

**Intento fallido:** el reemplazo masivo de `global ultimo_error` también quitó
la declaración **dentro de `registrar_error`**. Así, `ultimo_error = mensaje`
creaba una variable local y todos los mensajes de error se perdían.
- **La suite original pasó 20/20 con este bug.**
- Lo detectaron 25 pruebas de caracterización y la comparación del menú, que
  imprimía `Error: ` vacío.

Log: `evidencia/12a_r11_intento_fallido.log`.
**Corrección:** restaurar `global ultimo_error` solo en `registrar_error`.
**Cambio final:** `almacen` ya no escribe ninguna variable de `gestor`, y
`reiniciar_sistema` reutiliza `restaurar_estado`.
**Decisión consciente:** no se eliminó el estado global por completo (por
ejemplo, con una clase `Tienda`). Los tests originales leen `gestor.INVENTARIO`
y `gestor.VENTAS` como contrato, y ese cambio requeriría una capa de
compatibilidad con más riesgo que beneficio en este reto. Queda como trabajo
futuro.
**Tests:** 70 passed · ruff 0 · mypy OK. Log: `evidencia/12_r11_estado_global.log`.

---

## Variaciones de prompt: qué funcionó mejor

| Variación | Resultado |
|---|---|
| "Simplifica los condicionales" | Usó truthiness (`not codigo`) y cambió un caso límite |
| "…conservando la semántica EXACTA; compara con None y '' explícitamente" | Correcto a la primera |
| Hints escritos con tests en verde, sin verificador | Quedaban 2 inconsistencias de tipos invisibles para pytest |
| "…y verifica con mypy --strict; arregla el código, no uses type: ignore" | Las 2 se detectaron y corrigieron en el código |
| "Reescribe reportes de forma idiomática" (a secas) | La opción natural, `most_common(n)`, no es equivalente con `n<0` |
| "…los empates deben conservar el orden; la salida no debe cambiar ni un carácter" | `sorted` estable, más prueba diferencial de 14 000 casos |
| "Reemplaza todos los `global ultimo_error`" (reemplazo masivo) | Borró también el que sí hacía falta; lo atraparon los tests nuevos |
| "Primero escribe tests que fallen para X, Y, Z; luego…" | Ciclo rojo → verde claro y alcance acotado |

**Patrón:** los mejores prompts tuvieron **(1) el objetivo, (2) la restricción
de comportamiento explícita, (3) el criterio de verificación** (qué test, qué
comando o qué comparación). Los prompts de una sola línea funcionan, pero dejan
que la IA decida qué significa "equivalente".

## Herramientas de verificación usadas

- `pytest`: suite original (20) + caracterización y regresión (50).
- `ruff check src`: configuración del reto, sin modificar.
- `mypy --strict`: instalado solo en el entorno virtual como herramienta de
  revisión, no se agregó a `requirements.txt`.
- Comparación del menú: el `main.py` original contra el nuevo con la misma
  entrada; se comparan la salida estándar y el JSON guardado, ignorando la fecha.
- Prueba diferencial aleatoria de `mas_vendidos`/`total_vendido` contra el
  módulo original (R9).
