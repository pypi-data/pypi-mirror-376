# Archivo: multi_level/high_level/compiler.py

import re
import math
from holobit_sdk.utils.safe_eval import safe_eval
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.low_level.execution_unit import ExecutionUnit
from holobit_sdk.transpiler.machine_code_transpiler import MachineCodeTranspiler
from holobit_sdk.multi_level.high_level.c_backend import CBackend
from holobit_sdk.multi_level.high_level.rust_backend import RustBackend
from holobit_sdk.multi_level.high_level.go_backend import GoBackend
from holobit_sdk.quantum_holocron.entanglement import ENTANGLE
from holobit_sdk.quantum_holocron.quantum_algorithm import (
    SUPERPOSICION,
    MEDIR,
    TELETRANSPORTAR,
    COLAPSAR,
    FUSIONAR,
    DECOHERENCIA,
)

class HoloLangCompiler:
    """
    Compilador para el lenguaje de programación holográfico, ahora integrado con el transpilador.
    """

    def __init__(self, architecture="x86"):
        self.parser = HoloLangParser()
        self.executor = ExecutionUnit()
        self.architecture = architecture
        if architecture in {"c", "cpp"}:
            self.backend = CBackend(architecture)
            self.transpiler = None
        elif architecture == "rust":
            self.backend = RustBackend()
            self.transpiler = None
        elif architecture == "go":
            self.backend = GoBackend()
            self.transpiler = None
        else:
            self.transpiler = MachineCodeTranspiler(architecture)
            self.backend = None

    # ------------------------------------------------------------------
    # Utilidades internas para ejecutar árboles de instrucciones
    # ------------------------------------------------------------------
    def _eval_expr(self, expr):
        """Evalúa una expresión aritmética sencilla."""
        expr = str(expr).strip()
        allowed = {**self.parser.constants, **self.parser.measurements}
        for k, v in self.parser.variables.items():
            if isinstance(v, (int, float, complex)):
                allowed[k] = v
        math_funcs = {
            name: getattr(math, name)
            for name in dir(math)
            if not name.startswith("_") and callable(getattr(math, name))
        }
        allowed.update(math_funcs)
        allowed["math"] = math
        try:
            value = safe_eval(expr, allowed, allowed_funcs=set(math_funcs.values()))
        except Exception:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float, complex)):
            return value
        return 0

    def _execute_ast(self, ast):
        resultados = []
        for node in ast:
            res = self._execute_node(node)
            if res is None:
                continue
            if isinstance(res, list):
                resultados.extend(res)
            else:
                resultados.append(res)
        return resultados

    def _execute_node(self, node):
        tipo = node.get("type")
        if tipo == "INSTR":
            return self.compilar_y_ejecutar(node["code"])
        if tipo == "IF":
            if self._eval_expr(node["condition"]):
                return self._execute_ast(node["body"])
            if "else" in node:
                return self._execute_ast(node["else"])
            return []
        if tipo == "QIF":
            if self._eval_expr(node["condition"]):
                return self._execute_ast(node["body"])
            if "else" in node:
                return self._execute_ast(node["else"])
            return []
        if tipo == "FOR":
            resultados = []
            if "count" in node:
                count = int(self._eval_expr(node["count"]))
                for _ in range(count):
                    resultados.extend(self._execute_ast(node["body"]))
                return resultados
            var = node.get("var")
            inicio = int(self._eval_expr(node.get("start")))
            fin = int(self._eval_expr(node.get("end")))
            paso = 1 if fin >= inicio else -1
            i = inicio
            while (paso > 0 and i <= fin) or (paso < 0 and i >= fin):
                self.parser.variables[var] = i
                resultados.extend(self._execute_ast(node["body"]))
                i += paso
            self.parser.variables[var] = i
            return resultados
        if tipo == "WHILE":
            condicion = int(self._eval_expr(node["condition"]))
            resultados = []
            while condicion > 0:
                resultados.extend(self._execute_ast(node["body"]))
                condicion -= 1
            return resultados
        if tipo == "SWITCH":
            valor = self._eval_expr(node["expr"])
            defecto = None
            for case in node.get("cases", []):
                match = case["match"]
                if match == "DEFAULT":
                    defecto = case
                elif self._eval_expr(match) == valor:
                    return self._execute_ast(case["body"])
            if defecto:
                return self._execute_ast(defecto["body"])
            return []
        return []

    def _execute_function(self, nombre, args):
        funcion = self.parser.functions.get(nombre)
        if not funcion:
            return [f"Error: Función {nombre} no definida"]
        params = funcion.get("params", [])
        if len(params) != len(args):
            return [f"Error: Argumentos inválidos para {nombre}"]
        mapping = dict(zip(params, args))

        def _substitute(node):
            nuevo = {}
            for clave, valor in node.items():
                if isinstance(valor, str):
                    for p, a in mapping.items():
                        valor = re.sub(rf"\b{p}\b", a, valor)
                    nuevo[clave] = valor
                elif isinstance(valor, list):
                    nuevo[clave] = [_substitute(n) if isinstance(n, dict) else n for n in valor]
                else:
                    nuevo[clave] = valor
            return nuevo

        ast = [_substitute(n) for n in funcion.get("body", [])]
        return self._execute_ast(ast)

    def compilar_y_ejecutar(self, codigo):
        """
        Compila y ejecuta una línea de código en HoloLang.

        Args:
            codigo (str): Código fuente en HoloLang.

        Returns:
            str: Resultado de la ejecución del código compilado o código máquina generado.
        """
        if self.backend:
            ast = self.parser.parse_program(codigo)
            return self.backend.translate(ast)

        if "\n" in codigo or re.match(r"^(SI|SIQ|PARA|MIENTRAS)\b", codigo.strip()):
            ast = self.parser.parse_program(codigo)
            return self._execute_ast(ast)

        partes = codigo.split()

        if not partes:
            return ""

        if partes[0] == "CONSTANTE":
            return self.parser.interpretar(codigo)

        if partes[0] in {"CREAR_FRACTAL", "GRAFICAR_FRACTAL", "FRACTAL_ALT"}:
            return self.parser.interpretar(codigo)

        if partes[0] == "LLAMAR":
            match = re.match(r"LLAMAR\s+(\w+)\s*\((.*?)\)", codigo)
            if match:
                nombre = match.group(1)
                args = [a.strip() for a in match.group(2).split(',') if a.strip()]
            else:
                nombre = partes[1]
                args = partes[2:]
            return self._execute_function(nombre, args)

        if partes[0] == "ENTRELAZAR":
            grupos = partes[1:]
            return self.parser.holocron.execute_quantum_operation(ENTANGLE, grupos)
        if partes[0] == "SUPERPOSICION":
            grupo = partes[1]
            return self.parser.holocron.execute_quantum_operation(SUPERPOSICION, grupo)
        if partes[0] == "MEDIR":
            grupo = partes[1]
            return self.parser.holocron.execute_quantum_operation(MEDIR, grupo)
        if partes[0] == "SINCRONIZAR":
            grupos = partes[1:]
            resultados = self.parser.holocron.synchronize_measurements(grupos)
            for nombre, resultado in resultados.items():
                self.parser.measurements[nombre] = resultado
            return resultados
        if partes[0] == "TELETRANSPORTAR":
            grupo = partes[1]
            return self.parser.holocron.execute_quantum_operation(TELETRANSPORTAR, grupo)
        if partes[0] == "DECOHERENCIA":
            grupo = partes[1]
            return self.parser.holocron.execute_quantum_operation(DECOHERENCIA, grupo)
        if partes[0] == "COLAPSAR":
            grupo = partes[1]
            return self.parser.holocron.execute_quantum_operation(COLAPSAR, grupo)
        if partes[0] == "FUSIONAR":
            grupos = partes[1:]
            objetivo = grupos if len(grupos) > 1 else grupos[0]
            return self.parser.holocron.execute_quantum_operation(FUSIONAR, objetivo)
        if partes[0] == "GUARDAR_ESTADO":
            estado = partes[1]
            self.parser.holocron.save_state(estado)
            return f"Estado {estado} guardado"
        if partes[0] == "RESTABLECER_ESTADO":
            estado = partes[1]
            self.parser.holocron.restore_state(estado)
            self.parser.variables = dict(self.parser.holocron.holobits)
            self.parser.groups = {
                gid: [
                    name
                    for name, hb in self.parser.holocron.holobits.items()
                    if hb in grupo
                ]
                for gid, grupo in self.parser.holocron.groups.items()
            }
            return f"Estado {estado} restablecido"
        if partes[0] == "CREAR_GRUPO":
            group_id = partes[1]
            holobits = [token.strip('(),') for token in partes[2:]]
            self.parser.holocron.create_group(group_id, holobits)
            return f"Grupo {group_id} creado con {len(holobits)} holobits"
        if partes[0] == "FUSIONAR_GRUPO":
            nuevo = partes[1]
            grupos = [token.strip('(),') for token in partes[2:]]
            self.parser.holocron.merge_groups(nuevo, grupos)
            holobits = []
            for g in grupos:
                holobits.extend(self.parser.groups.pop(g, []))
            self.parser.groups[nuevo] = holobits
            return f"Grupo {nuevo} fusionado a partir de {', '.join(grupos)}"
        if partes[0] == "DIVIDIR_GRUPO":
            origen = partes[1]
            nuevo = partes[2]
            holobits = [token.strip('(),') for token in partes[3:]]
            self.parser.holocron.split_group(origen, nuevo, holobits)
            self.parser.groups[nuevo] = holobits
            self.parser.groups[origen] = [
                hb for hb in self.parser.groups.get(origen, []) if hb not in holobits
            ]
            return f"Grupo {origen} dividido en {nuevo}"
        if partes[0] == "APLICAR_GRUPO":
            operacion = partes[1]
            grupos = partes[2:]
            operaciones = {
                "ENTRELAZAR": ENTANGLE,
                "SUPERPOSICION": SUPERPOSICION,
                "MEDIR": MEDIR,
                "DECOHERENCIA": DECOHERENCIA,
                "TELETRANSPORTAR": TELETRANSPORTAR,
                "COLAPSAR": COLAPSAR,
                "FUSIONAR": FUSIONAR,
            }
            if operacion not in operaciones:
                return "Error: Operación cuántica desconocida."
            op = operaciones[operacion]
            objetivo = grupos if len(grupos) > 1 else grupos[0]
            return self.parser.holocron.execute_quantum_operation(op, objetivo)

        resultado = self.parser.interpretar(codigo)
        if "Variable" in resultado:
            return resultado
        if "IMPRIMIR" in codigo:
            return resultado

        if partes[0] == "EJECUTAR":
            instruccion = " ".join(partes[1:])
            self.executor.ejecutar_instruccion(instruccion)
            codigo_maquina = self.transpiler.transpile(instruccion)
            codigo_limpio = codigo_maquina.split(" ;")[0].replace(",", "")
            return f"Código máquina generado: {codigo_limpio}"

        if partes[0] == "CREAR_ESTRUCTURA":
            struct_id = partes[1]
            holobits = [token.strip(',{}') for token in partes[2:]]
            instruccion = f"CREATE_STRUCT {struct_id} {' '.join(holobits)}"
            self.executor.ejecutar_instruccion(instruccion)
            codigo_maquina = self.transpiler.transpile(instruccion)
            codigo_limpio = codigo_maquina.split(" ;")[0].replace(",", "")
            return f"Código máquina generado: {codigo_limpio}"

        if partes[0] == "TRANSFORMAR_ESTRUCTURA":
            struct_id = partes[1]
            operacion = partes[2]
            argumentos = " ".join(partes[3:])
            instruccion = f"TRANSFORM_STRUCT {struct_id} {operacion} {argumentos}"
            self.executor.ejecutar_instruccion(instruccion)
            codigo_maquina = self.transpiler.transpile(instruccion)
            codigo_limpio = codigo_maquina.split(" ;")[0].replace(",", "")
            return f"Código máquina generado: {codigo_limpio}"

        return "Error: Comando no reconocido."


# Ejemplo de uso
if __name__ == "__main__":
    compiler = HoloLangCompiler("x86")
    print(compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)"))
    print(compiler.compilar_y_ejecutar("IMPRIMIR H1"))
    print(compiler.compilar_y_ejecutar("EJECUTAR MULT H1 H2"))  # Ahora genera código máquina

