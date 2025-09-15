"""Gestor simple de macros para el ensamblador holográfico."""

from collections import defaultdict
from typing import Iterable, List

from holobit_sdk.utils.safe_eval import safe_eval

# ``macros`` almacena las macros separadas por espacio de nombres.
# Cada entrada es ``{namespace: {nombre: (parametros, lineas)}}`` donde
# ``parametros`` es un diccionario ``{param: valor_por_defecto}``.
macros = defaultdict(dict)

# ``aliases`` guarda los alias por espacio de nombres.
# El formato es ``{namespace: {alias: objetivo}}``. Un namespace vacío
# representa los alias globales para mantener compatibilidad.
aliases = defaultdict(dict)


def _eval_expr(expr: str, holocron) -> bool:
    """Evalúa una expresión en un contexto dado.

    Este helper se utiliza tanto por el preprocesador como por el
    ensamblador para interpretar expresiones simples. Para mantener la
    compatibilidad con versiones anteriores se exponen únicamente
    campos específicos del Holocron:

    ``holocron``
        Referencia directa al objeto completo para quienes necesiten
        inspeccionarlo.
    ``holobits``
        Diccionario de Holobits disponibles para permitir expresiones
        como ``'HB1' in holobits``.
    ``groups``
        Mapeo de grupos de Holobits, útil para validar su existencia.

    Limitar el contexto evita filtrar atributos internos o métodos
    sensibles del Holocron. Si ``holocron`` es un diccionario (por
    ejemplo, un mapeo de mediciones), sus entradas se inyectan
    directamente en el contexto de evaluación permitiendo referenciarlas
    por nombre.
    """

    if isinstance(holocron, dict):
        context = dict(holocron)
    else:
        context = {"holocron": holocron}
        for attr in ("holobits", "groups"):
            context[attr] = getattr(holocron, attr, {})
    return bool(safe_eval(expr, context))


def preprocess_lines(lines: Iterable[str], holocron) -> List[str]:
    """Procesa directivas ``#if``, ``#else`` y ``#endif`` en las líneas.

    Las condiciones se evalúan usando las variables presentes en el Holocron.
    """

    result: List[str] = []
    stack: List[dict] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#if "):
            expr = stripped[4:].strip()
            parent_active = stack[-1]["active"] if stack else True
            cond = _eval_expr(expr, holocron) if parent_active else False
            stack.append(
                {
                    "cond": cond,
                    "active": parent_active and cond,
                    "parent": parent_active,
                    "else": False,
                }
            )
        elif stripped == "#else":
            if not stack:
                raise ValueError("#else sin #if")
            frame = stack[-1]
            if frame["else"]:
                raise ValueError("Múltiples #else")
            frame["else"] = True
            frame["active"] = frame["parent"] and not frame["cond"]
        elif stripped == "#endif":
            if not stack:
                raise ValueError("#endif sin #if")
            stack.pop()
        else:
            if not stack or stack[-1]["active"]:
                result.append(line)
    if stack:
        raise ValueError("Directivas #if sin cerrar")
    return result


def _split_namespace(name):
    """Divide un nombre en ``(namespace, nombre)``."""

    if "::" in name:
        return tuple(name.split("::", 1))
    return "", name


def register_macro(name, params, lines):
    """Registra una macro con parámetros opcionales.

    Args:
        name: Nombre de la macro, opcionalmente con ``namespace``.
        params: Diccionario de parámetros y sus valores por defecto.
        lines: Lista de líneas que forman la plantilla.
    """

    namespace, macro_name = _split_namespace(name)
    macros[namespace][macro_name] = (params, lines)


def is_macro(name):
    """Verifica si una macro está registrada."""

    namespace, macro_name = _split_namespace(name)
    return macro_name in macros.get(namespace, {})


def expand_macro(name, args, holocron=None):
    """Expande una macro reemplazando parámetros por argumentos.

    Los argumentos faltantes se rellenan con los valores por defecto
    definidos al registrar la macro. Si se proporciona un ``holocron``,
    también se procesan las directivas de preprocesador.
    """

    namespace, macro_name = _split_namespace(name)
    params, lines = macros[namespace][macro_name]
    param_names = list(params.keys())
    if len(args) > len(param_names):
        raise ValueError("Demasiados argumentos para la macro")
    mapping = params.copy()
    for param, arg in zip(param_names, args):
        mapping[param] = arg
    expanded = [line.format(**mapping) for line in lines]
    if holocron is not None:
        expanded = preprocess_lines(expanded, holocron)
    return expanded


def remove_macro(name):
    namespace, macro_name = _split_namespace(name)
    if namespace in macros:
        macros[namespace].pop(macro_name, None)


def register_alias(alias, target):
    """Registra un alias opcionalmente namespaced."""

    namespace, alias_name = _split_namespace(alias)
    aliases[namespace][alias_name] = target


def resolve_alias(name):
    """Resuelve un alias considerando su espacio de nombres."""

    namespace, alias_name = _split_namespace(name)
    if alias_name in aliases.get(namespace, {}):
        return aliases[namespace][alias_name]
    if namespace == "":
        return aliases.get("", {}).get(alias_name, alias_name)
    return name


def load_defaults():
    """Registra alias básicos disponibles por defecto."""

    register_alias("ROTAR", "ROT")
    register_alias("INTERCAMBIAR", "SWAP")
    register_alias("ENTRELACE", "ENTR")
    register_alias("MEASURE", "MEDIR")
    register_alias("ENTRELAZAR", "ENTANGLE")
    register_alias("SUPERPOSICION", "SUPERPOS")
    register_alias("DESENTRELAZAR", "DESENTANGLE")

