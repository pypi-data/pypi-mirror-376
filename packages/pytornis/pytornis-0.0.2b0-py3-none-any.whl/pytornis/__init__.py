# pytornis/__init__.py
"""
Pytornis: Industrial Deep Learning Library
Init mejorado (carga lazy, expositor automático de símbolos y generador de imports estáticos).
No importa todo el núcleo en import time: se carga bajo demanda para evitar warnings/efectos.
"""

from __future__ import annotations

# Silenciar el warning conocido que aparece con python -m y runpy
import warnings
warnings.filterwarnings(
    "ignore",
    message=r".*found in sys\.modules after import of package .* but prior to execution of .*; this may result in unpredictable behaviour.*",
    category=RuntimeWarning,
)

# Módulos estándar usados por utilidades (pocos y seguros)
import importlib
import inspect
import sys
import types
import os
import io
import re
from typing import Iterable, List, Optional

# ------------------------------------------------------------------
# Helper para carga perezosa (lazy) del núcleo pytornis.pytornis
# ------------------------------------------------------------------
_SRC_CACHE: Optional[types.ModuleType] = None

def _lazy_load_src() -> types.ModuleType:
    """
    Carga (y cachea) el módulo `.pytornis` sólo cuando sea necesario.
    Usa importlib.import_module(".pytornis", __package__) para que
    funcione tanto con import normal como con import -m.
    """
    global _SRC_CACHE
    if _SRC_CACHE is not None:
        return _SRC_CACHE
    # Importar el módulo núcleo; puede lanzar errores si el módulo tiene errores internos.
    _SRC_CACHE = importlib.import_module(".pytornis", __package__)
    return _SRC_CACHE

# ------------------------------------------------------------------
# Clase proxy para acceso estilo objeto (user: pytornis.<attr>)
# ------------------------------------------------------------------
class pytornis_module:
    """
    Proxy ligero que delega atributos en el núcleo `pytornis.pytornis`.
    Evita importar todo en el tiempo de import del paquete.
    """
    def __init__(self):
        # No cargar el src aquí; se hará a demanda en __getattr__
        object.__setattr__(self, "_loaded", False)
        object.__setattr__(self, "_src", None)

    def _ensure_loaded(self):
        if not object.__getattribute__(self, "_loaded"):
            src = _lazy_load_src()
            object.__setattr__(self, "_src", src)
            object.__setattr__(self, "_loaded", True)

    def __getattr__(self, name: str):
        # Delegar a src si existe
        self._ensure_loaded()
        src = object.__getattribute__(self, "_src")
        # Preferir atributos ya en la instancia (si los hay)
        if name in self.__dict__:
            return self.__dict__[name]
        if hasattr(src, name):
            return getattr(src, name)
        raise AttributeError(f"'pytornis' no tiene el atributo '{name}'")

    def __dir__(self) -> List[str]:
        # Unir los nombres públicos del proxy y del núcleo (si cargado)
        self._ensure_loaded()
        src = object.__getattribute__(self, "_src")
        names = set(dir(type(self)))
        names.update(name for name in dir(self.__class__) if not name.startswith("_"))
        if src is not None:
            names.update(n for n in dir(src) if not n.startswith("_"))
        return sorted(names)

    def __repr__(self):
        if object.__getattribute__(self, "_loaded"):
            return f"<pytornis proxy (loaded)>"
        return f"<pytornis proxy (lazy)>"

# Instancia que el usuario importará: `import pytornis as pt; pt.Tensor ...`
pytornis = pytornis_module()

# ------------------------------------------------------------------
# Module-level helpers: permitir accesso `from pytornis import X` y `pt.X`
# Usamos PEP-562: module-level __getattr__/__dir__ (Python 3.7+).
# ------------------------------------------------------------------
def __getattr__(name: str):
    """
    Si alguien hace `import pytornis; pytornis.FOO`, Python llamará aquí si FOO
    no está en el namespace del módulo. Delegamos al proxy.
    """
    # delegamos a la instancia proxy
    return getattr(pytornis, name)

def __dir__():
    # combinar nombres del módulo y del proxy/núcleo
    names = set(globals().keys())
    try:
        names.update(dir(pytornis))
    except Exception:
        pass
    return sorted(names)

# ------------------------------------------------------------------
# Función para exponer estáticamente todos los símbolos públicos
# en este archivo (crea variables en este módulo para cada nombre).
# No se ejecuta automáticamente: usar manualmente si se quiere
# `from pytornis import Tensor` funcione sin carga adicional.
# ------------------------------------------------------------------
def expose_all_to_module(include_private: bool = False) -> int:
    """
    Importa dinámicamente el núcleo (si no cargado) y copia todos los símbolos
    públicos (o todos si include_private=True) al espacio del módulo.
    Devuelve el número de símbolos expuestos.
    """
    src = _lazy_load_src()
    exported = 0
    for name in dir(src):
        if not include_private and name.startswith("_"):
            continue
        # evitar sobrescribir nombres del propio init sensibles
        if name in ("__name__", "__file__", "__package__", "__spec__", "pytornis"):
            continue
        try:
            val = getattr(src, name)
            globals()[name] = val
            exported += 1
        except Exception:
            # seguridad: ignoramos símbolos problemáticos
            continue
    # actualizar __all__
    try:
        public = [n for n in globals().keys() if not n.startswith("_") and n != "pytornis"]
        globals()["__all__"] = sorted(public)
    except Exception:
        pass
    return exported

# ------------------------------------------------------------------
# Función que genera import statements estáticos dentro de este mismo archivo.
# Inserta líneas entre marcadores # BEGIN AUTOGEN IMPORTS / # END AUTOGEN IMPORTS.
# Útil si quieres convertir la carga lazy a imports físicos.
# ------------------------------------------------------------------
_AUTOGEN_START = "# BEGIN AUTOGEN IMPORTS"
_AUTOGEN_END   = "# END AUTOGEN IMPORTS"

def generate_static_imports(target_file: Optional[str] = None,
                            include_private: bool = False,
                            overwrite_marked_block: bool = True) -> str:
    """
    Genera (y escribe) líneas `from .pytornis import NAME` en target_file (por defecto este __init__.py).
    - No ejecuta los imports; solo escribe texto.
    - Si overwrite_marked_block==True, reemplaza el bloque entre marcadores; si los marcadores no existen los añade.
    - Devuelve la ruta del archivo modificado.
    Usar con precaución (mantener copia de seguridad).
    """
    if target_file is None:
        target_file = os.path.abspath(__file__)
    # cargar el módulo fuente para enumerar símbolos
    src = _lazy_load_src()
    names = []
    for name in dir(src):
        if not include_private and name.startswith("_"):
            continue
        # evitar nombres que no se deberían exportar
        if name in ("__name__", "__file__", "__package__", "__spec__"):
            continue
        names.append(name)
    # construir líneas de import
    imports = []
    imports.append(_AUTOGEN_START)
    imports.append("# Estas líneas fueron generadas automáticamente por pytornis.generate_static_imports()")
    imports.append("# Puedes borrar o editar este bloque si lo deseas")
    for nm in sorted(names):
        # generar safe import: from .pytornis import NAME as NAME
        # usar el alias `as` para evitar conflictos si se repite
        imports.append(f"from .pytornis import {nm} as {nm}")
    imports.append(_AUTOGEN_END)
    block_text = "\n".join(imports) + "\n"
    # leer archivo actual
    with open(target_file, "r", encoding="utf-8") as f:
        src_text = f.read()
    # si ya existen marcadores, reemplazar bloque entre ellos
    if _AUTOGEN_START in src_text and _AUTOGEN_END in src_text:
        if overwrite_marked_block:
            pattern = re.compile(re.escape(_AUTOGEN_START) + ".*?" + re.escape(_AUTOGEN_END), flags=re.DOTALL)
            new_text = pattern.sub(block_text.rstrip(), src_text)
        else:
            # no sobrescribir; adjuntar al final
            new_text = src_text + "\n\n" + block_text
    else:
        # agregar el bloque al final
        new_text = src_text + "\n\n" + block_text
    # escribir (hacer copia de seguridad primero)
    bak = target_file + ".bak"
    try:
        with open(bak, "w", encoding="utf-8") as f:
            f.write(src_text)
    except Exception:
        # si no se puede crear copia, continuar (pero no sobrescribir original sin precaución)
        pass
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_text)
    return target_file

# ------------------------------------------------------------------
# Función de ayuda: listar símbolos exportables (sin cargar todo si no quieres)
# ------------------------------------------------------------------
def list_exportable_symbols(include_private: bool = False) -> List[str]:
    """
    Devuelve la lista de nombres que podrían exportarse desde el núcleo.
    Carga el núcleo si es necesario.
    """
    src = _lazy_load_src()
    return [n for n in dir(src) if include_private or not n.startswith("_")]

# ------------------------------------------------------------------
# Valores por defecto y exposición mínima
# ------------------------------------------------------------------
# No cargamos src automáticamente ni hacemos expose_all_to_module() por defecto:
# el usuario controla cuándo materializar los imports.
__all__ = ["pytornis", "expose_all_to_module", "generate_static_imports", "list_exportable_symbols"]

# ------------------------------
# Nota:
# - Si quieres que todos los símbolos estén disponibles inmediatamente (por ejemplo para IDEs),
#   llama a pytornis.expose_all_to_module() tras la importación.
# - Si quieres generar imports estáticos en __init__.py (para eliminar la carga lazy),
#   usa pytornis.generate_static_imports() con precaución; el método hará un backup (.bak).
# ------------------------------
