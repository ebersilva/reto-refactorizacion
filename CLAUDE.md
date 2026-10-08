# CLAUDE.md — Gestor de inventario y ventas "La Esquina"

Aplicación de consola en Python (3.10+) que administra inventario y ventas de una
tienda pequeña: alta de productos, ventas con descuento e IVA, cotizaciones,
alertas de stock bajo, reporte de más vendidos y persistencia en JSON.

Este repositorio es un **reto de refactorización**: el objetivo es mejorar la
calidad del código **sin cambiar su comportamiento observable**.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `src/gestor.py` | Lógica de negocio: productos, ventas, cotizaciones y estado global |
| `src/almacen.py` | Persistencia: guardar/cargar el estado en JSON |
| `src/reportes.py` | Reportes de texto e indicadores (stock bajo, más vendidos, totales) |
| `src/main.py` | Menú interactivo de consola (única capa con `input`/`print` de usuario) |
| `tests/` | Suite pytest de caja negra (**no se modifica**) |
| `docs/bitacora.md` | Bitácora de cada refactorización (prompt, cambio, justificación, tests) |

Los módulos se importan sin paquete (`import gestor`); `tests/conftest.py` agrega
`src/` al `sys.path`. Para correr la app: `cd src && python main.py`.

## Comandos

```bash
source .venv/bin/activate          # entorno virtual (crear con: python -m venv .venv)
pip install -r requirements.txt
pytest                             # TODAS las pruebas deben pasar
ruff check src                     # debe terminar sin errores
ruff check src --fix               # solo para correcciones triviales (imports, encoding)
```

**Después de cada cambio corre `pytest` y `ruff check src`.** No des una tarea
por terminada si alguno falla.

## Reglas inquebrantables

1. **No modificar** ningún archivo existente de `tests/` ni `pyproject.toml`.
   Se pueden **agregar** archivos de prueba nuevos (p. ej. `tests/test_casos_borde.py`).
2. **Comportamiento idéntico**: mismos valores de retorno, mismos textos de
   tickets/reportes, mismos mensajes en `ultimo_error`, mismo orden de validaciones.
3. **API pública que usan los tests** — conservar nombre y firma:
   - `gestor.agregarProducto`, `gestor.buscarProducto` (camelCase permitido por
     `pyproject.toml`), `eliminar_producto`, `actualizar_stock`, `registrar_venta`,
     `cotizar`, `reiniciar_sistema`.
   - `gestor.INVENTARIO` (dict) y `gestor.VENTAS` (list): los tests los leen
     directamente; deben seguir siendo **el mismo objeto** (mutar en sitio con
     `.clear()`, nunca reasignar).
   - `almacen.guardar_datos`, `almacen.cargar_datos`.
   - `reportes.productos_stock_bajo`, `total_vendido`, `mas_vendidos`,
     `reporte_inventario`, `resumen_ventas`.
4. **Una refactorización a la vez**: un cambio con un solo propósito, validado y
   con su propio commit. No mezclar renombrados con cambios de lógica.
5. No agregar dependencias fuera de la biblioteca estándar.

## Convenciones de código

- PEP 8, líneas de máximo 88 caracteres (lo valida ruff).
- Nombres en **español** y en `snake_case`; constantes en `MAYUSCULAS`.
  Nada de nombres genéricos (`aux`, `temp2`, `x`, `d`, `hacer_cosa`).
- Sin números mágicos: las reglas de negocio van como constantes al inicio del módulo.
- Funciones cortas con una sola responsabilidad; complejidad ciclomática ≤ 10.
- Cláusulas de guarda (`return` temprano) en lugar de `if` anidados.
- Type hints en todas las funciones; los diccionarios de dominio se describen con
  `TypedDict` (`Producto`, `Venta`).
- Archivos siempre con `with open(..., encoding="utf-8")`.
- Capturar excepciones **específicas** (`json.JSONDecodeError`, `OSError`,
  `KeyError`), nunca `except Exception` a secas.
- f-strings para armar texto. Ojo: `f"{x}"` equivale a `str(x)`; no cambies el
  formato de los números (p. ej. `str(20.0)` → `"20.0"`, no `"20.00"`).
- Docstrings en español; comentarios solo para explicar el *porqué*.

Ejemplo del estilo esperado:

```python
# Antes
if aux >= 1000:
    desc = aux * 0.10
else:
    if aux >= 500:
        desc = aux * 0.05

# Después
UMBRAL_DESCUENTO_ALTO = 1000
TASA_DESCUENTO_ALTO = 0.10


def calcular_descuento_por_volumen(subtotal: float) -> float:
    """Descuento por volumen según el subtotal de la compra."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0
```

## Reglas de negocio (no cambiarlas al refactorizar)

- Descuento por volumen sobre el subtotal: ≥ $1000 → 10 %; ≥ $500 → 5 %.
- Clientes cuyo código empieza con `VIP`: +2 % del subtotal **solo si** el
  subtotal ya con descuento es > $200. `cotizar` **no** aplica el extra VIP.
- IVA 16 % sobre (subtotal − descuento); el total se redondea a 2 decimales.
- Stock bajo: menos de 5 unidades.
- Los folios de venta son consecutivos y sobreviven a guardar/cargar.

## Cómo trabajar en este repo

- Antes de tocar código, explica el plan y qué *code smell* atiende.
- Si un test falla, la refactorización alteró el comportamiento: corrige el
  código, nunca el test.
- Al terminar cada refactorización, agrega la fila correspondiente en
  `docs/bitacora.md` y guarda la salida de pytest/ruff en `docs/evidencia/`.
