"""Reportes de la tienda: inventario, ventas y mas vendidos."""

from collections import Counter

import gestor

STOCK_MINIMO = 5  # por debajo de esta cantidad se considera stock bajo


def formatear_dinero(monto):
    """Formatea un monto como dinero: $ seguido del valor redondeado a 2."""
    return "$" + str(round(monto, 2))


def tiene_stock_bajo(producto):
    return producto["stock"] < STOCK_MINIMO


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [p for p in gestor.INVENTARIO.values() if tiene_stock_bajo(p)]


def _linea_inventario(producto):
    linea = (
        f"{producto['codigo']} | {producto['nombre']} | "
        f"{formatear_dinero(producto['precio'])} | stock: {producto['stock']}"
    )
    if tiene_stock_bajo(producto):
        linea += "  <-- STOCK BAJO"
    return linea


def reporte_inventario():
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    productos = gestor.INVENTARIO.values()
    valor_total = sum(p["precio"] * p["stock"] for p in productos)
    lineas = [
        "===== INVENTARIO =====",
        *(_linea_inventario(p) for p in productos),
        f"Valor total del inventario: {formatear_dinero(valor_total)}",
    ]
    reporte = "\n".join(lineas) + "\n"
    print(reporte)
    return reporte


def _suma_de_totales():
    return sum(venta["total"] for venta in gestor.VENTAS)


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    return round(_suma_de_totales(), 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades).

    En empate se conserva el orden en que el producto se vendio por primera vez.
    """
    unidades_por_codigo = Counter()
    for venta in gestor.VENTAS:
        unidades_por_codigo[venta["codigo"]] += venta["cantidad"]
    # sorted es estable: los empates mantienen el orden de aparicion.
    # No se usa Counter.most_common(n) porque con n negativo no equivale a [:n].
    ranking = sorted(
        unidades_por_codigo.items(), key=lambda par: par[1], reverse=True
    )
    return ranking[:n]


def resumen_ventas():
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    lineas = ["===== RESUMEN DE VENTAS ====="]
    lineas += [
        f"Folio {venta['folio']}: {venta['nombre']} x{venta['cantidad']}"
        f" = {formatear_dinero(venta['total'])}"
        for venta in gestor.VENTAS
    ]
    lineas.append(f"Numero de ventas: {len(gestor.VENTAS)}")
    lineas.append(f"Total del dia: {formatear_dinero(_suma_de_totales())}")
    resumen = "\n".join(lineas) + "\n"
    print(resumen)
    return resumen
