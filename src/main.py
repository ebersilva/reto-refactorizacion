"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

from collections.abc import Callable

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"

OPCIONES_MENU = [
    "1) Agregar producto",
    "2) Registrar venta",
    "3) Cotizar",
    "4) Reporte de inventario",
    "5) Resumen de ventas",
    "6) Mas vendidos",
    "7) Alertas de stock bajo",
    "8) Guardar y salir",
]


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def mostrar_error() -> None:
    print("Error:", gestor.ultimo_error)


def opcion_agregar_producto() -> None:
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        mostrar_error()


def opcion_registrar_venta() -> None:
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        mostrar_error()


def opcion_cotizar() -> None:
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        mostrar_error()


def opcion_mas_vendidos() -> None:
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def opcion_stock_bajo() -> None:
    bajos = reportes.productos_stock_bajo()
    if not bajos:
        print("No hay productos con stock bajo.")
        return
    for producto in bajos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


ACCIONES: dict[str, Callable[[], object]] = {
    "1": opcion_agregar_producto,
    "2": opcion_registrar_venta,
    "3": opcion_cotizar,
    "4": reportes.reporte_inventario,
    "5": reportes.resumen_ventas,
    "6": opcion_mas_vendidos,
    "7": opcion_stock_bajo,
}
OPCION_SALIR = "8"


def menu() -> None:
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.existe_archivo(ARCHIVO):
        if almacen.cargar_datos(ARCHIVO):
            print("Datos cargados de", ARCHIVO)
        else:
            mostrar_error()
    while True:
        print("")
        print("\n".join(OPCIONES_MENU))
        opcion = input("Opcion: ")
        if opcion == OPCION_SALIR:
            if almacen.guardar_datos(ARCHIVO):
                print("Datos guardados. Hasta luego.")
                break
            mostrar_error()
            continue
        accion = ACCIONES.get(opcion)
        if accion is None:
            print("Opcion no valida.")
        else:
            accion()


if __name__ == "__main__":
    menu()
