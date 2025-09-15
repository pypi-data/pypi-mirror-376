import ast
import operator
from typing import Any, Dict, Iterable, Optional

# Operadores binarios permitidos
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Operadores unarios permitidos
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

# Operadores lógicos permitidos
_BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}

# Operadores de comparación permitidos
_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: operator.contains(b, a),
    ast.NotIn: lambda a, b: not operator.contains(b, a),
}

# Tipos permitidos para acceso a atributos
_SAFE_ATTR_TYPES = (str, int, float, bool, dict, list)


class UnsafeExpression(ValueError):
    """Se lanza cuando la expresión contiene operaciones no permitidas."""


def safe_eval(
    expr: str,
    variables: Dict[str, Any],
    allowed_funcs: Optional[Iterable[Any]] = None,
    *,
    max_length: int = 1000,
    max_depth: int = 50,
) -> Any:
    """Evalúa de forma segura una expresión aritmética y lógica simple.

    Solo se permiten operaciones aritméticas básicas, comparaciones,
    operadores lógicos y acceso a las variables proporcionadas. Las
    llamadas a funciones se rechazan a menos que la función esté incluida
    en ``allowed_funcs``. También se rechaza el acceso a atributos que
    comiencen por ``__``.

    Parameters
    ----------
    expr: str
        Expresión a evaluar.
    variables: Dict[str, Any]
        Variables permitidas en la expresión.
    allowed_funcs: Optional[Iterable[Any]]
        Funciones explícitamente permitidas para ser llamadas. Si es
        ``None`` (por defecto), las llamadas a funciones están
        deshabilitadas.
    max_length: int
        Longitud máxima permitida para ``expr``. Si se supera, se lanza
        ``UnsafeExpression``. Por defecto es ``1000``.
    max_depth: int
        Profundidad máxima del AST a evaluar. Si se excede, se lanza
        ``UnsafeExpression``. Por defecto es ``50``.

    Returns
    -------
    Any
        Resultado de la evaluación.
    """

    if len(expr) > max_length:
        raise UnsafeExpression("Expresión demasiado larga")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpression("Expresión inválida") from exc

    def _eval(node, depth: int = 0):
        if depth > max_depth:
            raise UnsafeExpression("Expresión demasiado profunda")
        if isinstance(node, ast.Expression):
            return _eval(node.body, depth + 1)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex, bool, str)):
                return node.value
            raise UnsafeExpression("Constante no permitida")
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            raise UnsafeExpression(f"Variable no permitida: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](
                _eval(node.left, depth + 1), _eval(node.right, depth + 1)
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand, depth + 1))
        if isinstance(node, ast.BoolOp) and type(node.op) in _BOOL_OPS:
            vals = [_eval(v, depth + 1) for v in node.values]
            return _BOOL_OPS[type(node.op)](vals)
        if isinstance(node, ast.Compare):
            left = _eval(node.left, depth + 1)
            for op, comp in zip(node.ops, node.comparators):
                if type(op) not in _CMP_OPS:
                    raise UnsafeExpression("Comparación no permitida")
                right = _eval(comp, depth + 1)
                if not _CMP_OPS[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Attribute):
            value = _eval(node.value, depth + 1)
            attr = node.attr
            if attr.startswith("__"):
                raise UnsafeExpression("Atributo no permitido")
            if not isinstance(value, _SAFE_ATTR_TYPES):
                raise UnsafeExpression("Objeto no permitido para acceso a atributos")
            return getattr(value, attr)
        if isinstance(node, ast.Call):
            func = _eval(node.func, depth + 1)
            if not callable(func) or (
                allowed_funcs is None or func not in allowed_funcs
            ):
                raise UnsafeExpression("Llamada no permitida")
            args = [_eval(a, depth + 1) for a in node.args]
            return func(*args)
        raise UnsafeExpression("Operación no permitida")

    return _eval(tree.body)
