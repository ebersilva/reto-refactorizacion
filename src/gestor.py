"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import NamedTuple, TypedDict

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
SEPARADOR_TICKET = "-" * 28
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class Producto(TypedDict):
    codigo: str
    nombre: str
    precio: float
    stock: int


class DatosVenta(TypedDict):
    """Registro de una venta sin el ticket (lo que se necesita para armarlo)."""

    folio: int
    codigo: str
    nombre: str
    cantidad: int
    subtotal: float
    descuento: float
    impuesto: float
    total: float
    cliente: str | None
    fecha: str


class Venta(DatosVenta):
    ticket: str


# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO: dict[str, Producto] = {}
VENTAS: list[Venta] = []
contador_ventas: int = 0
ultimo_error: str = ""


def reiniciar_sistema() -> None:
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contador_ventas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contador_ventas = 0
    ultimo_error = ""


def agregarProducto(codigo: str, nombre: str, precio: float, stock: int) -> bool:
    """Valida los datos y da de alta un producto en el inventario.

    Conserva el nombre camelCase porque es API publica usada por los tests.
    """
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
    INVENTARIO[codigo] = {
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio,
        "stock": stock,
    }
    return True


def eliminar_producto(codigo: str) -> bool:
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo: str, cantidad: int) -> bool:
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    nuevo_stock = INVENTARIO[codigo]["stock"] + cantidad
    if nuevo_stock < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = nuevo_stock
    return True


def buscarProducto(texto: str) -> list[Producto]:
    """Productos cuyo nombre contiene el texto, sin distinguir mayusculas.

    Conserva el nombre camelCase porque es API publica usada por los tests.
    """
    texto_buscado = texto.lower()
    return [
        producto
        for producto in INVENTARIO.values()
        if texto_buscado in producto["nombre"].lower()
    ]


class Importes(NamedTuple):
    """Desglose de una compra: subtotal, descuento, IVA y total redondeado."""

    subtotal: float
    descuento: float
    impuesto: float
    total: float


def calcular_descuento_por_volumen(subtotal: float) -> float:
    """Descuento según el monto de la compra (antes de IVA)."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def calcular_descuento_vip(
    subtotal: float, descuento_volumen: float, cliente: str | None
) -> float:
    """Descuento extra para clientes VIP con compras arriba del monto minimo."""
    es_vip = cliente is not None and cliente.startswith(PREFIJO_CLIENTE_VIP)
    if es_vip and subtotal - descuento_volumen > MONTO_MINIMO_VIP:
        return subtotal * TASA_DESCUENTO_VIP
    return 0


def calcular_importes(subtotal: float, cliente: str | None = "") -> Importes:
    """Aplica descuentos e IVA a un subtotal. Fuente unica de las reglas de precio.

    Lo usan tanto registrar_venta como cotizar, asi que la cotizacion siempre
    coincide con la venta real (salvo el extra VIP, que cotizar no recibe).
    """
    descuento = calcular_descuento_por_volumen(subtotal)
    descuento = descuento + calcular_descuento_vip(subtotal, descuento, cliente)
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    return Importes(subtotal, descuento, impuesto, round(base + impuesto, 2))


def formatear_ticket(venta: DatosVenta) -> str:
    """Arma el ticket de texto plano de una venta ya registrada."""
    lineas = [
        NOMBRE_TIENDA,
        SEPARADOR_TICKET,
        f"Folio: {venta['folio']}",
        f"{venta['nombre']} x{venta['cantidad']}",
        f"Subtotal: ${venta['subtotal']}",
    ]
    if venta["descuento"] > 0:
        lineas.append(f"Descuento: -${venta['descuento']}")
    lineas.append(f"IVA: ${venta['impuesto']}")
    lineas.append(f"TOTAL: ${venta['total']}")
    return "\n".join(lineas) + "\n"


def registrar_venta(
    codigo: str, cantidad: int | None, cliente: str | None = ""
) -> Venta | None:
    """Valida y registra una venta: descuenta stock, asigna folio y arma el ticket.

    Regresa el registro de la venta, o None si los datos no son validos
    (el motivo queda en ultimo_error).
    """
    global contador_ventas, ultimo_error
    if codigo in (None, ""):
        ultimo_error = "codigo vacio"
        return None
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    producto = INVENTARIO[codigo]
    if producto["stock"] < cantidad:
        ultimo_error = "stock insuficiente"
        return None
    importes = calcular_importes(producto["precio"] * cantidad, cliente)
    producto["stock"] -= cantidad
    contador_ventas += 1
    datos: DatosVenta = {
        "folio": contador_ventas,
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "subtotal": round(importes.subtotal, 2),
        "descuento": round(importes.descuento, 2),
        "impuesto": round(importes.impuesto, 2),
        "total": importes.total,
        "cliente": cliente,
        "fecha": datetime.now().strftime(FORMATO_FECHA),
    }
    venta: Venta = {**datos, "ticket": formatear_ticket(datos)}
    VENTAS.append(venta)
    return venta


def cotizar(codigo: str, cantidad: int | None) -> float | None:
    """Calcula cuanto costaria una compra sin registrar la venta."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    return calcular_importes(INVENTARIO[codigo]["precio"] * cantidad).total
