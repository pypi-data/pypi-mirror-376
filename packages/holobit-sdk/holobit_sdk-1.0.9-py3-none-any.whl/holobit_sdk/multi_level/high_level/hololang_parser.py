import re
import math
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.utils.safe_eval import safe_eval
from holobit_sdk.quantum_holocron.entanglement import ENTANGLE, DESENTANGLE
from holobit_sdk.quantum_holocron.quantum_algorithm import (
    SUPERPOSICION,
    MEDIR,
    TELETRANSPORTAR,
    COLAPSAR,
    FUSIONAR,
    DECOHERENCIA,
)
from holobit_sdk.quantum_holocron.fractal import Fractal
from holobit_sdk.visualization.fractal_plot import visualizar_fractal


class HoloLangParser:
    """Analizador sintáctico para el lenguaje de programación holográfico."""

    def __init__(self):
        self.variables = {}
        self.structures = {}
        self.groups = {}
        self.measurements = {}
        self.holocron = Holocron()
        self.entanglements = {}
        self.functions = {}
        self.constants = {
            "PI": math.pi,
            "TAU": math.tau,
            "E": math.e,
        }
        self.fractals = {}

    def _remove_comments(self, line: str) -> str:
        """Elimina comentarios de una línea de código."""
        return re.split(r"//|#", line)[0]

    # ------------------------------------------------------------------
    # Nuevas reglas de análisis para estructuras de control
    # ------------------------------------------------------------------
    def parse_program(self, codigo):
        """Genera un árbol de instrucciones a partir de un programa.

        Esta función soporta las construcciones ``FUNCION``, ``SI``, ``SINO``,
        ``SIQ``, ``ELSEQ``, ``PARA``, ``MIENTRAS`` y ``CASO`` empleando llaves ``{`` y ``}`` para
        delimitar bloques.

        Parameters
        ----------
        codigo:
            Cadena con el programa en HoloLang.

        Returns
        -------
        list
            Árbol de instrucciones representado como una lista anidada de
            diccionarios.
        """

        lines = []
        for l in codigo.strip().splitlines():
            l = self._remove_comments(l).strip()
            if l:
                lines.append(l)
        root = []
        stack = [root]
        for line in lines:
            if re.match(r"FUNCION\s+\w+\s*\(.*\)\s*\{", line):
                nombre, params = re.findall(r"FUNCION\s+(\w+)\s*\((.*?)\)", line)[0]
                parametros = [p.strip() for p in params.split(",") if p.strip()]
                node = {"params": parametros, "body": []}
                self.functions[nombre] = node
                stack.append(node["body"])
            elif re.match(r"SI\s+.*\{", line):
                condition = re.sub(r"SI\s+|\{", "", line).strip()
                node = {"type": "IF", "condition": condition, "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"SIQ\s+.*\{", line):
                condition = re.sub(r"SIQ\s+|\{", "", line).strip()
                node = {"type": "QIF", "condition": condition, "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"SINO\s*\{", line):
                if stack[-1] and stack[-1][-1].get("type") == "IF" and "else" not in stack[-1][-1]:
                    node = stack[-1][-1]
                    node["else"] = []
                    stack.append(node["else"])
            elif re.match(r"ELSEQ\s*\{", line):
                if stack[-1] and stack[-1][-1].get("type") == "QIF" and "else" not in stack[-1][-1]:
                    node = stack[-1][-1]
                    node["else"] = []
                    stack.append(node["else"])
            elif re.match(r"PARA\s+\w+\s*=.*\.\..*\{", line):
                m = re.match(r"PARA\s+(\w+)\s*=\s*(.*?)\.\.\s*(.*?)\s*\{", line)
                var, start, end = m.groups()
                node = {"type": "FOR", "var": var, "start": start.strip(), "end": end.strip(), "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"PARA\s+.*\{", line):
                count = re.sub(r"PARA\s+|\{", "", line).strip()
                node = {"type": "FOR", "count": count, "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"MIENTRAS\s+.*\{", line):
                condition = re.sub(r"MIENTRAS\s+|\{", "", line).strip()
                node = {"type": "WHILE", "condition": condition, "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"CASO\s+.*\{", line):
                expr = re.sub(r"CASO\s+|\{", "", line).strip()
                node = {"type": "SWITCH", "expr": expr, "cases": []}
                stack[-1].append(node)
                stack.append(node["cases"])
            elif re.match(r"CUANDO\s+.*\{", line):
                value = re.sub(r"CUANDO\s+|\{", "", line).strip()
                node = {"type": "CASE", "match": value, "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"OTRO\s*\{", line):
                node = {"type": "CASE", "match": "DEFAULT", "body": []}
                stack[-1].append(node)
                stack.append(node["body"])
            elif re.match(r"(CREAR_FRACTAL_ND|DINAMICA_FRACTAL|DENSIDAD_MORFO)\s+\w+", line):
                stack[-1].append({"type": "INSTR", "code": line})
            elif line == "FINCASO":
                if len(stack) > 1:
                    stack.pop()
            elif line == "}":
                if len(stack) > 1:
                    stack.pop()
            else:
                stack[-1].append({"type": "INSTR", "code": line})
        return root

    def interpretar(self, codigo):
        """
        Interpreta una línea de código en HoloLang.

        Args:
            codigo (str): Línea de código en HoloLang.

        Returns:
            str: Resultado de la ejecución de la línea de código.
        """
        codigo = self._remove_comments(codigo).strip()

        if not codigo:
            return ""

        if re.match(r'CREAR\s+(?:QUARK\s+|HOLOBIT\s+)?\w+\s*(?:\(.*\)|\{.*\})', codigo):
            return self._crear_variable(codigo)
        elif re.match(r'CONSTANTE\s+\w+\s*=\s*.+', codigo):
            return self._definir_constante(codigo)
        elif re.match(r'IMPRIMIR\s+\w+', codigo):
            return self._imprimir_variable(codigo)
        elif re.match(r'CREAR_ESTRUCTURA\s+\w+\s+\{.*\}', codigo):
            return self._crear_estructura(codigo)
        elif re.match(r'TRANSFORMAR_ESTRUCTURA\s+\w+\s+\w+', codigo):
            return self._transformar_estructura(codigo)
        elif re.match(r'CREAR_GRUPO\s+\w+\s+\(.*\)', codigo):
            return self._crear_grupo(codigo)
        elif re.match(r'APLICAR_GRUPO\s+\w+\s+\w+(\s+\w+)*', codigo):
            return self._aplicar_grupo(codigo)
        elif re.match(r'CANALIZAR\s+\{[^}]+\}\s+\w+', codigo):
            return self._canalizar(codigo)
        elif re.match(r'FUSIONAR_GRUPO\s+\w+\s+\(.*\)', codigo):
            return self._fusionar_grupo(codigo)
        elif re.match(r'DIVIDIR_GRUPO\s+\w+\s+\w+\s+\(.*\)', codigo):
            return self._dividir_grupo(codigo)
        elif re.match(r'ENTRELAZAR\s+\w+(\s+\w+)+', codigo):
            return self._entrelazar(codigo)
        elif re.match(r'(DESENTANGLE|DESENTRELAZAR)\s+\w+(\s+\w+)+', codigo):
            return self._desentrelazar(codigo)
        elif re.match(r'SUPERPOSICION\s+\w+', codigo):
            return self._superposicion(codigo)
        elif re.match(r'MEDIR\s+\w+', codigo):
            return self._medir(codigo)
        elif re.match(r'SINCRONIZAR\s+\w+(\s+\w+)+', codigo):
            return self._sincronizar_mediciones(codigo)
        elif re.match(r'TELETRANSPORTAR\s+\w+', codigo):
            return self._teletransportar(codigo)
        elif re.match(r'COLAPSAR\s+\w+', codigo):
            return self._colapsar(codigo)
        elif re.match(r'FUSIONAR\s+\w+(\s+\w+)*', codigo):
            return self._fusionar(codigo)
        elif re.match(r'GUARDAR_ESTADO\s+\w+', codigo):
            return self._guardar_estado(codigo)
        elif re.match(r'RESTABLECER_ESTADO\s+\w+', codigo):
            return self._restaurar_estado(codigo)
        elif re.match(r'DECOHERENCIA\s+\w+', codigo):
            return self._decoherencia(codigo)
        elif re.match(r'CREAR_FRACTAL\s+\w+(?:\s*\([^)]*\))?', codigo):
            return self._crear_fractal(codigo)
        elif re.match(r'CREAR_FRACTAL_ND\s+\w+\s*\([^)]*\)', codigo):
            return self._crear_fractal_nd(codigo)
        elif re.match(r'DINAMICA_FRACTAL\s+\w+\s*\([^)]*\)', codigo):
            return self._dinamica_fractal(codigo)
        elif re.match(r'DENSIDAD_MORFO\s+\w+\s+\d+', codigo):
            return self._densidad_morfo(codigo)
        elif re.match(r'GRAFICAR_FRACTAL\s+\w+', codigo):
            return self._graficar_fractal(codigo)
        elif re.match(r'FRACTAL_ALT\s+\w+\s+\d+', codigo):
            return self._fractal_alt(codigo)
        else:
            return "Error de sintaxis."

    def _crear_variable(self, codigo):
        """
        Crea una variable en HoloLang.

        Args:
            codigo (str): Línea de código que define la variable.

        Returns:
            str: Confirmación de la creación de la variable.
        """
        partes = re.findall(r'\w+', codigo)
        if len(partes) < 2:
            return "Error de sintaxis en la declaración de la variable."

        tipo = "QUARK"
        if partes[1] in {"QUARK", "HOLOBIT"}:
            tipo = partes[1]
            if len(partes) < 3:
                return "Error de sintaxis en la declaración de la variable."
            nombre = partes[2]
        else:
            nombre = partes[1]

        if tipo == "HOLOBIT":
            valores_match = re.search(r'\{(.*?)\}', codigo)
            if valores_match:
                referencias = [v.strip() for v in valores_match.group(1).split(',') if v.strip()]
                if not referencias:
                    return "Error de sintaxis en la declaración de la variable."
                self.variables[nombre] = referencias
                self.holocron.add_holobit(nombre, referencias)
                self.holocron.create_group(nombre, referencias)
                return f"Holobit {nombre} creado con referencias {referencias}"
            return "Error de sintaxis en la declaración de la variable."

        # Por defecto o tipo QUARK
        valores_match = re.search(r'\((.*?)\)', codigo)
        if valores_match:
            valores_crudos = [v.strip() for v in valores_match.group(1).split(',')]
            try:
                valores = tuple(self._eval_value(v) for v in valores_crudos)
            except Exception:
                return "Error de sintaxis en la declaración de la variable."
            self.variables[nombre] = valores
            self.holocron.add_holobit(nombre, valores)
            self.holocron.create_group(nombre, [nombre])
            return f"Variable {nombre} creada con valores {valores}"

        return "Error de sintaxis en la declaración de la variable."

    def _eval_value(self, expr):
        expr = expr.replace("i", "j")
        allowed = {**self.constants, **self.variables}
        value = safe_eval(expr, allowed)
        if isinstance(value, (int, float, complex)):
            return value
        raise ValueError("Expresión inválida")

    def _definir_constante(self, codigo):
        match = re.match(r"CONSTANTE\s+(\w+)\s*=\s*(.+)", codigo)
        if not match:
            return "Error de sintaxis en la definición de la constante."
        nombre, expr = match.groups()
        try:
            valor = self._eval_value(expr)
        except Exception:
            return "Error de sintaxis en la definición de la constante."
        self.constants[nombre] = valor
        return f"Constante {nombre} definida con valor {valor}"

    def _imprimir_variable(self, codigo):
        """
        Imprime el valor de una variable en HoloLang.

        Args:
            codigo (str): Línea de código que solicita la impresión.

        Returns:
            str: Valor de la variable o mensaje de error.
        """
        nombre = codigo.split()[1]
        if nombre in self.variables:
            return f"{nombre} = {self.variables[nombre]}"
        return f"Error: Variable {nombre} no definida."

    def _crear_estructura(self, codigo):
        partes = re.findall(r'\w+', codigo)
        nombre = partes[1]
        holobits = partes[2:]
        self.structures[nombre] = holobits
        for hb in holobits:
            if hb not in self.holocron.holobits:
                self.holocron.add_holobit(hb, hb)
        self.holocron.create_group(nombre, holobits)
        return f"Estructura {nombre} creada con {len(holobits)} holobits"

    def _transformar_estructura(self, codigo):
        partes = codigo.split()
        nombre = partes[1]
        operacion = partes[2]
        parametros = " ".join(partes[3:])
        if nombre not in self.structures:
            return f"Error: Estructura {nombre} no definida"
        return f"Estructura {nombre} operacion {operacion} {parametros}"

    def _crear_grupo(self, codigo):
        partes = re.findall(r'\w+', codigo)
        nombre = partes[1]
        holobits = partes[2:]
        self.groups[nombre] = holobits
        self.holocron.create_group(nombre, holobits)
        return f"Grupo {nombre} creado con {len(holobits)} holobits"

    def _fusionar_grupo(self, codigo):
        partes = re.findall(r'\w+', codigo)
        nuevo = partes[1]
        grupos = partes[2:]
        self.holocron.merge_groups(nuevo, grupos)
        holobits = []
        for g in grupos:
            holobits.extend(self.groups.pop(g, []))
        self.groups[nuevo] = holobits
        return f"Grupo {nuevo} fusionado a partir de {', '.join(grupos)}"

    def _dividir_grupo(self, codigo):
        partes = re.findall(r'\w+', codigo)
        origen = partes[1]
        nuevo = partes[2]
        holobits = partes[3:]
        self.holocron.split_group(origen, nuevo, holobits)
        self.groups[nuevo] = holobits
        self.groups[origen] = [hb for hb in self.groups.get(origen, []) if hb not in holobits]
        return f"Grupo {origen} dividido en {nuevo}"

    def _aplicar_grupo(self, codigo):
        partes = codigo.split()
        operacion = partes[1]
        grupos = partes[2:]
        operaciones = {
            "ENTRELAZAR": ENTANGLE,
            "DESENTRELAZAR": DESENTANGLE,
            "DESENTANGLE": DESENTANGLE,
            "SUPERPOSICION": SUPERPOSICION,
            "MEDIR": MEDIR,
            "DECOHERENCIA": DECOHERENCIA,
            "TELETRANSPORTAR": TELETRANSPORTAR,
            "COLAPSAR": COLAPSAR,
            "FUSIONAR": FUSIONAR,
        }
        if operacion not in operaciones:
            return f"Error: Operación {operacion} no reconocida"
        op = operaciones[operacion]
        objetivo = grupos if len(grupos) > 1 else grupos[0]
        return self.holocron.execute_quantum_operation(op, objetivo)

    def _entrelazar(self, codigo):
        partes = codigo.split()
        grupos = partes[1:]
        resultado = self.holocron.execute_quantum_operation(ENTANGLE, grupos)
        self.entanglements[tuple(grupos)] = resultado
        return resultado

    def _desentrelazar(self, codigo):
        partes = codigo.split()
        grupos = partes[1:]
        key = tuple(grupos)
        estado = self.entanglements.get(key, [])
        resultado = DESENTANGLE.apply(estado)
        self.entanglements[key] = resultado
        return resultado

    def _superposicion(self, codigo):
        partes = codigo.split()
        grupo = partes[1]
        resultado = self.holocron.execute_quantum_operation(SUPERPOSICION, grupo)
        self.measurements[grupo] = resultado
        return resultado

    def _medir(self, codigo):
        partes = codigo.split()
        grupo = partes[1]
        resultado = self.holocron.execute_quantum_operation(MEDIR, grupo)
        self.measurements[grupo] = resultado
        return resultado

    def _decoherencia(self, codigo):
        partes = codigo.split()
        grupo = partes[1]
        resultado = self.holocron.execute_quantum_operation(DECOHERENCIA, grupo)
        self.measurements[grupo] = resultado
        return resultado

    def _sincronizar_mediciones(self, codigo):
        partes = codigo.split()
        grupos = partes[1:]
        resultados = self.holocron.synchronize_measurements(grupos)
        for nombre, resultado in resultados.items():
            self.measurements[nombre] = resultado
        return resultados

    def _teletransportar(self, codigo):
        partes = codigo.split()
        grupo = partes[1]
        resultado = self.holocron.execute_quantum_operation(TELETRANSPORTAR, grupo)
        self.measurements[grupo] = resultado
        return resultado

    def _colapsar(self, codigo):
        partes = codigo.split()
        grupo = partes[1]
        resultado = self.holocron.execute_quantum_operation(COLAPSAR, grupo)
        self.measurements[grupo] = resultado
        return resultado

    def _fusionar(self, codigo):
        partes = codigo.split()
        grupos = partes[1:]
        objetivo = grupos if len(grupos) > 1 else grupos[0]
        resultado = self.holocron.execute_quantum_operation(FUSIONAR, objetivo)
        return resultado

    def _guardar_estado(self, codigo):
        partes = codigo.split()
        nombre = partes[1]
        self.holocron.save_state(nombre)
        return f"Estado {nombre} guardado"

    def _restaurar_estado(self, codigo):
        partes = codigo.split()
        nombre = partes[1]
        try:
            self.holocron.restore_state(nombre)
            self.variables = dict(self.holocron.holobits)
            self.groups = {
                gid: [
                    name
                    for name, hb in self.holocron.holobits.items()
                    if hb in grupo
                ]
                for gid, grupo in self.holocron.groups.items()
            }
            return f"Estado {nombre} restablecido"
        except KeyError:
            return f"Error: Estado {nombre} no existe"

    def _crear_fractal(self, codigo):
        match = re.match(
            r"CREAR_FRACTAL\s+(\w+)(?:\s*\(\s*densidad_max\s*=\s*(\d+)\s*\))?",
            codigo,
        )
        if not match:
            return "Error de sintaxis en CREAR_FRACTAL"
        nombre, densidad = match.groups()
        fractal = Fractal(self.holocron)
        if densidad:
            fractal.hierarquia_superior = int(densidad)
        fractal.generar()
        self.fractals[nombre] = fractal
        return f"Fractal {nombre} creado con densidad_max={fractal.hierarquia_superior}"

    def _crear_fractal_nd(self, codigo):
        match = re.match(
            r"CREAR_FRACTAL_ND\s+(\w+)\s*\(([^)]*)\)",
            codigo,
        )
        if not match:
            return "Error de sintaxis en CREAR_FRACTAL_ND"
        nombre, params = match.groups()
        valores = dict(re.findall(r"(\w+)\s*=\s*([\w\.]+)", params))
        dimension = int(valores.get("dimension", 3))
        densidad = valores.get("densidad_max")
        fractal = Fractal(self.holocron, dimension=dimension)
        if densidad is not None:
            fractal.hierarquia_superior = int(densidad)
        fractal.generar()
        self.fractals[nombre] = fractal
        return (
            f"Fractal {nombre} creado con dimension={dimension} "
            f"y densidad_max={fractal.hierarquia_superior}"
        )

    def _dinamica_fractal(self, codigo):
        match = re.match(
            r"DINAMICA_FRACTAL\s+(\w+)\s*\(([^)]*)\)",
            codigo,
        )
        if not match:
            return "Error de sintaxis en DINAMICA_FRACTAL"
        nombre, params = match.groups()
        valores = dict(re.findall(r"(\w+)\s*=\s*([\w\.]+)", params))
        pasos = int(valores.get("pasos", 0))
        dt = float(valores.get("dt", 1.0))
        fractal = self.fractals.get(nombre)
        if fractal is None:
            return f"Error: Fractal {nombre} no definido"
        fractal.simular_dinamica(pasos, dt)
        return f"Dinámica de fractal {nombre} simulada ({pasos} pasos, dt={dt})"

    def _densidad_morfo(self, codigo):
        match = re.match(r"DENSIDAD_MORFO\s+(\w+)\s+(\d+)", codigo)
        if not match:
            return "Error de sintaxis en DENSIDAD_MORFO"
        nombre, dimension = match.groups()
        fractal = self.fractals.get(nombre)
        if fractal is None:
            return f"Error: Fractal {nombre} no definido"
        return fractal.densidad(int(dimension))

    def _graficar_fractal(self, codigo):
        partes = codigo.split()
        nombre = partes[1] if len(partes) > 1 else None
        fractal = self.fractals.get(nombre)
        if fractal is None:
            return f"Error: Fractal {nombre} no definido"
        import numpy as np

        datos = np.array(list(fractal.densidades.values()))
        lado = int(math.sqrt(len(datos))) or 1
        matriz = datos.reshape(lado, lado)
        fig, axes = visualizar_fractal(matriz)
        return fig, axes

    def _fractal_alt(self, codigo):
        match = re.match(r"FRACTAL_ALT\s+(\w+)\s+(\d+)", codigo)
        if not match:
            return "Error de sintaxis en FRACTAL_ALT"
        nombre, semilla = match.groups()
        fractal = self.fractals.get(nombre)
        if fractal is None:
            return f"Error: Fractal {nombre} no definido"
        import numpy as np

        datos = np.array(list(fractal.densidades.values()))
        lado = int(math.sqrt(len(datos))) or 1
        matriz = datos.reshape(lado, lado)
        fig, axes = visualizar_fractal(lambda seed=None, density=None: matriz, semillas=[int(semilla)])
        return fig, axes

    def _canalizar(self, codigo):
        match = re.match(r'CANALIZAR\s+\{([^}]*)\}\s+(\w+)', codigo)
        if not match:
            return "Error de sintaxis en CANALIZAR"
        ops_txt, grupo = match.groups()
        operaciones = [op.strip() for op in ops_txt.split(',') if op.strip()]
        if not operaciones:
            return "Error de sintaxis en CANALIZAR"
        from holobit_sdk.quantum_holocron.instructions import AVAILABLE_OPERATIONS
        resultado = None
        for op_name in operaciones:
            if op_name not in AVAILABLE_OPERATIONS:
                raise KeyError(f"La operación cuántica '{op_name}' no está definida.")
            operation = AVAILABLE_OPERATIONS[op_name]
            resultado = self.holocron.execute_quantum_operation(operation, grupo)
            self.holocron.groups[grupo] = resultado
        return resultado


# Ejemplo de uso
if __name__ == "__main__":
    parser = HoloLangParser()
    print(parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)"))
    print(parser.interpretar("IMPRIMIR H1"))

