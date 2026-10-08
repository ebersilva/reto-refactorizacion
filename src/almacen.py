"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON.

    Regresa False si no se pudo escribir el archivo (motivo en ultimo_error).
    """
    datos = {
        "inventario": gestor.INVENTARIO,
        "ventas": gestor.VENTAS,
        "contador": gestor.contadorVentas,
    }
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False)
    except OSError as error:
        gestor.ultimo_error = f"no se pudo guardar el archivo: {error}"
        return False
    return True


def _leer_json(ruta):
    """Lee y valida el archivo. Regresa los datos o None (motivo en ultimo_error)."""
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return None
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except json.JSONDecodeError:
        gestor.ultimo_error = "archivo corrupto"
        return None
    except OSError as error:
        gestor.ultimo_error = f"no se pudo leer el archivo: {error}"
        return None
    if not _tiene_estructura_valida(datos):
        gestor.ultimo_error = "archivo corrupto"
        return None
    return datos


def _tiene_estructura_valida(datos):
    return (
        isinstance(datos, dict)
        and isinstance(datos.get("inventario"), dict)
        and isinstance(datos.get("ventas"), list)
    )


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe, no se puede leer o esta corrupto;
    en ese caso el estado actual no se modifica.
    """
    datos = _leer_json(ruta)
    if datos is None:
        return False
    # se mutan en sitio: otros modulos (y los tests) guardan referencia a ellos
    gestor.INVENTARIO.clear()
    gestor.INVENTARIO.update(datos["inventario"])
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contadorVentas = datos.get("contador", 0)
    return True


def hayArchivo(ruta):
    # checa si ya existe el archivo de datos
    return os.path.exists(ruta)
