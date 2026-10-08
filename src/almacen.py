"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os
from typing import Any

import gestor


def guardar_datos(ruta: str) -> bool:
    """Guarda el inventario, las ventas y el folio actual en un JSON.

    Regresa False si no se pudo escribir el archivo (motivo en ultimo_error).
    """
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(gestor.exportar_estado(), archivo, indent=2, ensure_ascii=False)
    except OSError as error:
        gestor.registrar_error(f"no se pudo guardar el archivo: {error}")
        return False
    return True


def _leer_json(ruta: str) -> dict[str, Any] | None:
    """Lee y valida el archivo. Regresa los datos o None (motivo en ultimo_error)."""
    if not os.path.exists(ruta):
        gestor.registrar_error("el archivo no existe")
        return None
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos: dict[str, Any] = json.load(archivo)
    except json.JSONDecodeError:
        gestor.registrar_error("archivo corrupto")
        return None
    except OSError as error:
        gestor.registrar_error(f"no se pudo leer el archivo: {error}")
        return None
    if not _tiene_estructura_valida(datos):
        gestor.registrar_error("archivo corrupto")
        return None
    return datos


def _tiene_estructura_valida(datos: Any) -> bool:
    return (
        isinstance(datos, dict)
        and isinstance(datos.get("inventario"), dict)
        and isinstance(datos.get("ventas"), list)
    )


def cargar_datos(ruta: str) -> bool:
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe, no se puede leer o esta corrupto;
    en ese caso el estado actual no se modifica.
    """
    datos = _leer_json(ruta)
    if datos is None:
        return False
    gestor.restaurar_estado(
        datos["inventario"], datos["ventas"], datos.get("contador", 0)
    )
    return True


def existe_archivo(ruta: str) -> bool:
    """Indica si ya existe el archivo de datos."""
    return os.path.exists(ruta)
