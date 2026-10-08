"""Pruebas de caracterización agregadas durante el reto.

Se escribieron ANTES de refactorizar, contra el código original, para fijar el
comportamiento observable que la suite base no cubría (textos exactos, mensajes
de error, límites de descuento, empates). Los archivos de prueba originales no
se modificaron.
"""

import json

import pytest

import almacen
import gestor
import reportes


def _alta(codigo="A1", nombre="Café", precio=100.0, stock=50):
    assert gestor.agregarProducto(codigo, nombre, precio, stock)


# ---------------------------------------------------------------- descuentos


@pytest.mark.parametrize(
    ("precio", "cantidad", "total"),
    [
        (99.99, 5, 579.94),  # subtotal $499.95: justo debajo del 5 %
        (100.0, 5, 551.0),  # subtotal $500 exacto: 5 %
        (99.99, 10, 1101.89),  # subtotal $999.90: sigue en 5 %
        (100.0, 10, 1044.0),  # subtotal $1000 exacto: 10 %
    ],
)
def test_limites_de_descuento_por_volumen(precio, cantidad, total):
    _alta(precio=precio)
    assert gestor.registrar_venta("A1", cantidad)["total"] == total
    assert gestor.cotizar("A1", cantidad) == total


def test_vip_sin_monto_minimo_no_recibe_extra():
    # $20 de compra: no pasa de $200, el prefijo VIP no cambia nada
    _alta(precio=10.0)
    assert gestor.registrar_venta("A1", 2, "VIP001")["descuento"] == 0


def test_vip_aplica_extra_sin_descuento_por_volumen():
    # 3 x $100 = $300 > $200 -> 2 % VIP = $6 -> $294 + IVA = $341.04
    _alta()
    venta = gestor.registrar_venta("A1", 3, "VIP001")
    assert venta["descuento"] == 6.0
    assert venta["total"] == 341.04


@pytest.mark.parametrize("cliente", ["", None, "VI", "vip001", "XVIP"])
def test_clientes_no_vip(cliente):
    _alta()
    venta = gestor.registrar_venta("A1", 3, cliente)
    assert venta["descuento"] == 0
    assert venta["total"] == 348.0
    assert venta["cliente"] == cliente


def test_cotizar_no_aplica_descuento_vip():
    _alta()
    assert gestor.cotizar("A1", 6) == 661.2
    assert gestor.registrar_venta("A1", 6, "VIP007")["total"] == 647.28


# ---------------------------------------------------------- mensajes de error


@pytest.mark.parametrize(
    ("codigo", "cantidad", "mensaje"),
    [
        ("", 1, "codigo vacio"),
        (None, 1, "codigo vacio"),
        ("ZZZ", 1, "producto no existe"),
        ("A1", 0, "cantidad invalida"),
        ("A1", None, "cantidad invalida"),
        ("A1", 51, "stock insuficiente"),
    ],
)
def test_registrar_venta_mensajes_de_error(codigo, cantidad, mensaje):
    _alta()
    assert gestor.registrar_venta(codigo, cantidad) is None
    assert gestor.ultimo_error == mensaje
    assert gestor.VENTAS == []


@pytest.mark.parametrize(
    ("codigo", "cantidad", "mensaje"),
    [
        ("", 1, "producto no existe"),
        ("ZZZ", 1, "producto no existe"),
        ("A1", 0, "cantidad invalida"),
        ("A1", None, "cantidad invalida"),
    ],
)
def test_cotizar_mensajes_de_error(codigo, cantidad, mensaje):
    _alta()
    assert gestor.cotizar(codigo, cantidad) is None
    assert gestor.ultimo_error == mensaje


def test_cotizar_no_valida_stock_ni_lo_modifica():
    _alta(stock=1)
    assert gestor.cotizar("A1", 10) == 1044.0
    assert gestor.INVENTARIO["A1"]["stock"] == 1


@pytest.mark.parametrize(
    ("codigo", "precio", "stock", "mensaje"),
    [
        ("", 10.0, 1, "codigo vacio"),
        (None, 10.0, 1, "codigo vacio"),
        ("A1", 10.0, 1, "el producto ya existe"),
        ("B1", 0, 1, "precio invalido"),
        ("B1", 10.0, -1, "stock invalido"),
    ],
)
def test_agregar_producto_mensajes_de_error(codigo, precio, stock, mensaje):
    _alta()
    assert gestor.agregarProducto(codigo, "X", precio, stock) is False
    assert gestor.ultimo_error == mensaje


def test_eliminar_y_actualizar_inexistente():
    assert gestor.eliminar_producto("ZZZ") is False
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.actualizar_stock("ZZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"
    _alta(stock=1)
    assert gestor.actualizar_stock("A1", -2) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"


def test_buscar_texto_vacio_regresa_todo():
    _alta("A1")
    _alta("A2", nombre="Azúcar")
    assert [p["codigo"] for p in gestor.buscarProducto("")] == ["A1", "A2"]


# -------------------------------------------------------------------- ticket


def test_ticket_con_descuento_texto_exacto():
    _alta(nombre="Café")
    venta = gestor.registrar_venta("A1", 6)
    assert venta["ticket"] == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Café x6\n"
        "Subtotal: $600.0\n"
        "Descuento: -$30.0\n"
        "IVA: $91.2\n"
        "TOTAL: $661.2\n"
    )


def test_ticket_sin_descuento_omite_la_linea():
    _alta(precio=10.0)
    venta = gestor.registrar_venta("A1", 2)
    assert "Descuento" not in venta["ticket"]
    assert venta["ticket"].endswith("Subtotal: $20.0\nIVA: $3.2\nTOTAL: $23.2\n")


def test_venta_registra_todos_los_campos():
    _alta()
    venta = gestor.registrar_venta("A1", 6, "VIP007")
    esperado = {
        "folio": 1,
        "codigo": "A1",
        "nombre": "Café",
        "cantidad": 6,
        "subtotal": 600.0,
        "descuento": 42.0,
        "impuesto": 89.28,
        "total": 647.28,
        "cliente": "VIP007",
    }
    assert {k: venta[k] for k in esperado} == esperado
    assert set(venta) == set(esperado) | {"fecha", "ticket"}
    assert gestor.VENTAS[-1] is venta


# ------------------------------------------------------------------ reportes


def test_reporte_inventario_texto_exacto(capsys):
    _alta("A1", "Leche", 26.0, 3)
    _alta("A2", "Azúcar", 32.5, 40)
    esperado = (
        "===== INVENTARIO =====\n"
        "A1 | Leche | $26.0 | stock: 3  <-- STOCK BAJO\n"
        "A2 | Azúcar | $32.5 | stock: 40\n"
        "Valor total del inventario: $1378.0\n"
    )
    assert reportes.reporte_inventario() == esperado
    assert capsys.readouterr().out == esperado + "\n"


def test_resumen_ventas_texto_exacto(capsys):
    _alta(precio=10.0)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("A1", 1)
    esperado = (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Café x2 = $23.2\n"
        "Folio 2: Café x1 = $11.6\n"
        "Numero de ventas: 2\n"
        "Total del dia: $34.8\n"
    )
    assert reportes.resumen_ventas() == esperado
    assert capsys.readouterr().out == esperado + "\n"


def test_stock_bajo_limite_es_cinco():
    _alta("A1", stock=4)
    _alta("A2", stock=5)
    assert [p["codigo"] for p in reportes.productos_stock_bajo()] == ["A1"]


def test_mas_vendidos_empates_conservan_orden_de_aparicion():
    for codigo in ("A1", "B1", "C1", "D1"):
        _alta(codigo)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("C1", 5)
    gestor.registrar_venta("D1", 1)
    assert reportes.mas_vendidos() == [("C1", 5), ("B1", 2), ("A1", 2)]
    assert reportes.mas_vendidos(10) == [("C1", 5), ("B1", 2), ("A1", 2), ("D1", 1)]
    assert reportes.mas_vendidos(0) == []


def test_mas_vendidos_sin_ventas():
    assert reportes.mas_vendidos() == []


# --------------------------------------------------------------- persistencia


def test_guardar_escribe_la_estructura_esperada(tmp_path):
    ruta = tmp_path / "datos.json"
    _alta()
    gestor.registrar_venta("A1", 1)
    assert almacen.guardar_datos(str(ruta)) is True
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert set(datos) == {"inventario", "ventas", "contador"}
    assert datos["contador"] == 1
    assert datos["inventario"]["A1"]["nombre"] == "Café"  # ensure_ascii=False


def test_cargar_archivo_corrupto(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    _alta()
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO  # el estado no se toca


def test_cargar_archivo_inexistente_deja_mensaje(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "nada.json")) is False
    assert gestor.ultimo_error == "el archivo no existe"


def test_cargar_sin_contador_inicia_en_cero(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text('{"inventario": {}, "ventas": []}', encoding="utf-8")
    assert almacen.cargar_datos(str(ruta)) is True
    _alta()
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


def test_cargar_conserva_identidad_de_las_colecciones(tmp_path):
    ruta = str(tmp_path / "datos.json")
    inventario, ventas = gestor.INVENTARIO, gestor.VENTAS
    _alta()
    almacen.guardar_datos(ruta)
    almacen.cargar_datos(ruta)
    assert gestor.INVENTARIO is inventario
    assert gestor.VENTAS is ventas


def test_codigo_numerico_cero_no_se_trata_como_vacio():
    # Agregado tras detectar en revisión que `if not codigo` cambiaba esto.
    assert gestor.agregarProducto(0, "Cero", 10.0, 5) is True
    assert gestor.registrar_venta(0, 1)["folio"] == 1
    assert gestor.registrar_venta(1, 1) is None
    assert gestor.ultimo_error == "producto no existe"


# ------------------------------------- manejo de errores (R7, cambio deliberado)
# Antes de R7 estos casos lanzaban excepciones sin capturar; dos de ellos
# además borraban el inventario antes de fallar.


@pytest.mark.parametrize(
    "contenido",
    ['{"inventario": {}}', '{"ventas": []}', "[]", '{"inventario": [], "ventas": []}'],
)
def test_cargar_estructura_invalida_no_toca_el_estado(tmp_path, contenido):
    ruta = tmp_path / "datos.json"
    ruta.write_text(contenido, encoding="utf-8")
    _alta()
    gestor.registrar_venta("A1", 1)
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO
    assert len(gestor.VENTAS) == 1


def test_cargar_ruta_ilegible(tmp_path):
    # un directorio "existe" pero no se puede leer como archivo
    assert almacen.cargar_datos(str(tmp_path)) is False
    assert gestor.ultimo_error.startswith("no se pudo leer el archivo")


def test_guardar_en_ruta_invalida_regresa_false(tmp_path):
    ruta = tmp_path / "no_existe" / "datos.json"
    assert almacen.guardar_datos(str(ruta)) is False
    assert gestor.ultimo_error.startswith("no se pudo guardar el archivo")
