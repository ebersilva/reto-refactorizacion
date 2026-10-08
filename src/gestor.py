"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import NamedTuple

# ---------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------
TASA_IVA = 0.16
UMBRAL_DESCUENTO_ALTO = 1000
TASA_DESCUENTO_ALTO = 0.10
UMBRAL_DESCUENTO_MEDIO = 500
TASA_DESCUENTO_MEDIO = 0.05
PREFIJO_CLIENTE_VIP = "VIP"
MONTO_MINIMO_VIP = 200  # sobre el subtotal ya con descuento por volumen
TASA_DESCUENTO_VIP = 0.02  # se calcula sobre el subtotal original
NOMBRE_TIENDA = "TIENDA LA ESQUINA"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contadorVentas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contadorVentas = 0
    ultimo_error = ""


def agregarProducto(codigo, nombre, precio, stock):
    # valida los datos y da de alta un producto en el inventario
    global ultimo_error
    if codigo in (None, ""):
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    x = {}
    x["codigo"] = codigo
    x["nombre"] = nombre
    x["precio"] = precio
    x["stock"] = stock
    INVENTARIO[codigo] = x
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    aux = INVENTARIO[codigo]["stock"] + cantidad
    if aux < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = aux
    return True


def buscarProducto(texto):
    # busca productos cuyo nombre contenga el texto (sin importar mayusculas)
    temp2 = []
    for k in INVENTARIO:
        if texto.lower() in INVENTARIO[k]["nombre"].lower():
            temp2.append(INVENTARIO[k])
    return temp2


class Importes(NamedTuple):
    """Desglose de una compra: subtotal, descuento, IVA y total redondeado."""

    subtotal: float
    descuento: float
    impuesto: float
    total: float


def calcular_descuento_por_volumen(subtotal):
    """Descuento según el monto de la compra (antes de IVA)."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def calcular_descuento_vip(subtotal, descuento_volumen, cliente):
    """Descuento extra para clientes VIP con compras arriba del monto minimo."""
    es_vip = bool(cliente) and cliente.startswith(PREFIJO_CLIENTE_VIP)
    if es_vip and subtotal - descuento_volumen > MONTO_MINIMO_VIP:
        return subtotal * TASA_DESCUENTO_VIP
    return 0


def calcular_importes(subtotal, cliente=""):
    """Aplica descuentos e IVA a un subtotal. Fuente unica de las reglas de precio.

    Lo usan tanto registrar_venta como cotizar, asi que la cotizacion siempre
    coincide con la venta real (salvo el extra VIP, que cotizar no recibe).
    """
    descuento = calcular_descuento_por_volumen(subtotal)
    descuento = descuento + calcular_descuento_vip(subtotal, descuento, cliente)
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    return Importes(subtotal, descuento, impuesto, round(base + impuesto, 2))


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta completa.

    Esta funcion hace de todo: valida los datos, calcula descuentos e
    impuestos, descuenta el stock, genera el folio, arma el ticket en
    texto y guarda el registro en la lista de ventas. Si algo falla
    regresa None y deja el motivo en ultimo_error.
    """
    global contadorVentas, ultimo_error
    if codigo in (None, ""):
        ultimo_error = "codigo vacio"
        return None
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    temp2 = INVENTARIO[codigo]
    if temp2["stock"] < cantidad:
        ultimo_error = "stock insuficiente"
        return None
    importes = calcular_importes(temp2["precio"] * cantidad, cliente)
    # descontar del inventario
    temp2["stock"] = temp2["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {}
    venta["folio"] = contadorVentas
    venta["codigo"] = codigo
    venta["nombre"] = temp2["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(importes.subtotal, 2)
    venta["descuento"] = round(importes.descuento, 2)
    venta["impuesto"] = round(importes.impuesto, 2)
    venta["total"] = importes.total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime(FORMATO_FECHA)
    # armar el ticket en texto plano
    t = ""
    t = t + NOMBRE_TIENDA + "\n"
    t = t + "----------------------------\n"
    t = t + "Folio: " + str(venta["folio"]) + "\n"
    t = t + venta["nombre"] + " x" + str(cantidad) + "\n"
    t = t + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if importes.descuento > 0:
        t = t + "Descuento: -$" + str(venta["descuento"]) + "\n"
    t = t + "IVA: $" + str(venta["impuesto"]) + "\n"
    t = t + "TOTAL: $" + str(venta["total"]) + "\n"
    venta["ticket"] = t
    VENTAS.append(venta)
    return venta


def cotizar(codigo, cantidad):
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    return calcular_importes(INVENTARIO[codigo]["precio"] * cantidad).total
