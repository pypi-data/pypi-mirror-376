from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core.quark import Quark
from . import macros
import re

# Importación del Holocron para gestionar Holobits y grupos
try:  # pragma: no cover - compatibilidad con diferentes puntos de entrada
    from quantum_holocron.core.holocron import Holocron
except ModuleNotFoundError:  # Fallback cuando el paquete no está expuesto a nivel superior
    from holobit_sdk.quantum_holocron.core.holocron import Holocron


class AssemblerParser:
    def __init__(self):
        """
        Inicializa el parser del ensamblador.
        """
        self.holobits = {}  # Tabla de símbolos para almacenar quarks y holobits
        self.entanglements = {}  # Registro de entrelazamientos entre Holobits
        self.measurements = {}  # Resultados de mediciones cuánticas
        # Holocron centralizado para gestionar Holobits y agrupaciones
        self.holocron = Holocron()
        # Alias para mantener compatibilidad con código existente
        self.groups = self.holocron.groups
        self.control_tokens = {
            "SI",
            "SINO",
            "SIQ",
            "ELSEQ",
            "MIENTRAS",
            "PARA",
            "PARAG",
            "CASO",
            "CUANDO",
            "OTRO",
            "FIN",
            "FINCASO",
            "CANALIZAR",
            "CANALIZAR_PARALELO",
            "DESENTANGLE",
            "FUNC",
            "ENDFUNC",
            "CALL",
        }
        self._current_macro = None  # Estado para definición de macros
        self._current_function = None  # Estado para definición de funciones
        self._if_stack = []  # Pila de estados del preprocesador
        self.functions = {}  # Almacén de funciones definidas

    def analyze_blocks(self, lines):
        """Pequeño analizador para estructuras de control.

        Verifica que los bloques iniciados con ``SI``, ``MIENTRAS``, ``PARA``
        o ``CASO`` sean cerrados correctamente. ``SI``, ``MIENTRAS`` y ``PARA``
        se cierran con ``FIN``, mientras que ``CASO`` utiliza ``FINCASO``. Los
        tokens ``CUANDO`` y ``OTRO`` solo son válidos dentro de un bloque
        ``CASO``. No interpreta el contenido, únicamente asegura la validez
        estructural.
        """
        stack = []
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            token = stripped.split()[0]
            if token in {"SI", "SIQ", "MIENTRAS", "PARA", "PARAG", "CASO", "FUNC"}:
                stack.append(token)
            elif token == "FIN":
                if not stack or stack[-1] not in {"SI", "SIQ", "MIENTRAS", "PARA", "PARAG"}:
                    raise ValueError(f"FIN sin bloque en línea {idx}")
                stack.pop()
            elif token == "ENDFUNC":
                if not stack or stack[-1] != "FUNC":
                    raise ValueError(f"ENDFUNC sin FUNC en línea {idx}")
                stack.pop()
            elif token == "FINCASO":
                if not stack or stack[-1] != "CASO":
                    raise ValueError(f"FINCASO sin CASO en línea {idx}")
                stack.pop()
            elif token in {"CUANDO", "OTRO"}:
                if not stack or stack[-1] != "CASO":
                    raise ValueError(f"{token} fuera de CASO en línea {idx}")
        if stack:
            raise ValueError("Bloques sin cerrar: " + ", ".join(stack))
        return True

    def parse_line(self, line):
        """
        Interpreta una línea de código ensamblador.

        Args:
            line: Línea en lenguaje ensamblador.
        """
        # Eliminar comentarios y limpiar espacios adicionales
        raw = line.strip()

        # Manejo de definición de macros
        if self._current_macro is not None:
            if raw == "#endmacro":
                macros.register_macro(
                    self._current_macro["name"],
                    self._current_macro["params"],
                    self._current_macro["lines"],
                )
                self._current_macro = None
            else:
                if raw and not raw.startswith(";"):
                    self._current_macro["lines"].append(raw)
            return

        # Directivas del preprocesador
        if raw.startswith("#if "):
            expr = raw[4:].strip()
            parent_active = self._if_stack[-1]["active"] if self._if_stack else True
            cond = macros._eval_expr(expr, self.holocron) if parent_active else False
            self._if_stack.append(
                {
                    "cond": cond,
                    "active": parent_active and cond,
                    "parent": parent_active,
                    "else": False,
                }
            )
            return
        if raw == "#else":
            if not self._if_stack:
                raise ValueError("#else sin #if")
            frame = self._if_stack[-1]
            if frame["else"]:
                raise ValueError("Múltiples #else")
            frame["else"] = True
            frame["active"] = frame["parent"] and not frame["cond"]
            return
        if raw == "#endif":
            if not self._if_stack:
                raise ValueError("#endif sin #if")
            self._if_stack.pop()
            return
        if self._if_stack and not self._if_stack[-1]["active"]:
            return

        if raw.startswith("#macro"):
            parts = raw.split()
            nombre = parts[1]
            params = {}
            for p in parts[2:]:
                if "=" in p:
                    key, default = p.split("=", 1)
                else:
                    key, default = p, None
                params[key] = default
            self._current_macro = {"name": nombre, "params": params, "lines": []}
            return

        clean = raw.split(";")[0].strip()
        if not clean:
            return  # Saltar líneas vacías o comentarios

        if self._current_function is not None:
            if clean == "ENDFUNC":
                self._current_function = None
            else:
                self.functions[self._current_function].append(clean)
            return

        if clean.startswith("FUNC "):
            nombre = clean.split()[1]
            self.functions[nombre] = []
            self._current_function = nombre
            return

        line = clean

        tokens = line.split()  # Dividir por espacios
        command = macros.resolve_alias(tokens[0])
        tokens[0] = command

        if macros.is_macro(command):
            expanded = macros.expand_macro(command, tokens[1:], self.holocron)
            for exp_line in expanded:
                self.parse_line(exp_line)
            return

        if command == "CALL":
            if len(tokens) != 2:
                raise ValueError(
                    f"Formato inválido para la instrucción CALL: '{line}'"
                )
            nombre = tokens[1]
            if nombre not in self.functions:
                raise KeyError(f"La función '{nombre}' no está definida")
            for func_line in self.functions[nombre]:
                self.parse_line(func_line)
            return

        if command in self.control_tokens:
            if command == "SIQ":
                expr = line[len("SIQ") :].strip()
                if not expr:
                    raise ValueError(
                        f"Formato inválido para la instrucción {command}: '{line}'"
                    )
                condicion = macros._eval_expr(expr, self.measurements)
                return {"command": command, "condition": condicion}
            if command in {"SI", "MIENTRAS", "PARA", "PARAG", "CASO"} and len(tokens) != 2:
                raise ValueError(
                    f"Formato inválido para la instrucción {command}: '{line}'"
                )
            if command in {"SINO", "ELSEQ", "FIN", "OTRO", "FINCASO"} and len(tokens) != 1:
                raise ValueError(
                    f"Formato inválido para la instrucción {command}: '{line}'"
                )
            if command == "CUANDO" and len(tokens) != 2:
                raise ValueError(
                    f"Formato inválido para la instrucción {command}: '{line}'"
                )
            if command == "CANALIZAR":
                from holobit_sdk.quantum_holocron.instructions import (
                    AVAILABLE_OPERATIONS,
                )
                # Sintaxis extendida: CANALIZAR {OP1, OP2, ...} G1
                if "{" in line and "}" in line:
                    match = re.match(r"CANALIZAR\s+\{([^}]*)\}\s+(\w+)", line)
                    if not match:
                        raise ValueError(
                            f"Formato inválido para la instrucción {command}: '{line}'"
                        )
                    ops_txt, group = match.groups()
                    operaciones = [
                        macros.resolve_alias(op.strip())
                        for op in ops_txt.split(",")
                        if op.strip()
                    ]
                    if not operaciones:
                        raise ValueError(
                            f"No se especificaron operaciones en {command}: '{line}'"
                        )
                    resultado = None
                    for op_name in operaciones:
                        if op_name not in AVAILABLE_OPERATIONS:
                            raise KeyError(
                                f"La operación cuántica '{op_name}' no está definida."
                            )
                        operation = AVAILABLE_OPERATIONS[op_name]
                        resultado = self.holocron.execute_quantum_operation(
                            operation, group
                        )
                        self.holocron.groups[group] = resultado
                    return resultado
                # Sintaxis original: CANALIZAR OP G1 [G2 ...]
                if len(tokens) < 3:
                    raise ValueError(
                        f"Formato inválido para la instrucción {command}: '{line}'"
                    )
                operation_name = macros.resolve_alias(tokens[1])
                grupos = tokens[2:]
                if operation_name not in AVAILABLE_OPERATIONS:
                    raise KeyError(
                        f"La operación cuántica '{operation_name}' no está definida."
                    )
                operation = AVAILABLE_OPERATIONS[operation_name]
                target = grupos[0] if len(grupos) == 1 else grupos
                resultado = self.holocron.execute_quantum_operation(operation, target)
                if isinstance(target, str):
                    self.holocron.groups[target] = resultado
                return resultado
            if command == "CANALIZAR_PARALELO":
                from holobit_sdk.quantum_holocron.instructions import (
                    AVAILABLE_OPERATIONS,
                )
                match = re.match(r"CANALIZAR_PARALELO\s+\{([^}]*)\}\s*$", line)
                if not match:
                    raise ValueError(
                        f"Formato inválido para la instrucción {command}: '{line}'"
                    )
                contenido = match.group(1).strip()
                if not contenido:
                    raise ValueError(
                        f"No se especificaron operaciones en {command}: '{line}'"
                    )
                pares = [p.strip() for p in contenido.split(",") if p.strip()]
                mapping = {}
                for par in pares:
                    if ":" not in par:
                        raise ValueError(
                            f"Par inválido '{par}' en {command}: '{line}'"
                        )
                    op_txt, grupo = par.split(":", 1)
                    op_name = macros.resolve_alias(op_txt.strip())
                    grupo = grupo.strip()
                    if op_name not in AVAILABLE_OPERATIONS:
                        raise KeyError(
                            f"La operación cuántica '{op_name}' no está definida."
                        )
                    mapping[AVAILABLE_OPERATIONS[op_name]] = grupo
                resultados = self.holocron.execute_parallel_operations(mapping)
                for gid, res in resultados.items():
                    self.holocron.groups[gid] = res
                return resultados
            if command == "DESENTANGLE":
                pass  # Se procesa en bloques posteriores
            else:
                return {"command": command, "args": tokens[1:]}

        if len(tokens) < 2:
            raise ValueError(f"Línea inválida: '{line}'")

        if command == "CREAR":
            if len(tokens) < 3:
                raise ValueError(f"Formato inválido para la instrucción CREAR: '{line}'")

            # Soporte para sintaxis tipada: CREAR QUARK Q1 (...) o CREAR HOLOBIT H1 {...}
            tipo = None
            if tokens[1] in {"QUARK", "HOLOBIT"}:
                tipo = tokens[1]
                if len(tokens) < 4:
                    raise ValueError(
                        f"Formato inválido para la instrucción CREAR: '{line}'"
                    )
                nombre = tokens[2]
                contenido = " ".join(tokens[3:]).strip()
            else:
                nombre = tokens[1]
                contenido = " ".join(tokens[2:]).strip()

            # Determinar tipo si no se especifica
            if tipo is None:
                if contenido.startswith("{") and contenido.endswith("}"):
                    tipo = "HOLOBIT"
                elif contenido.startswith("(") and contenido.endswith(")"):
                    tipo = "QUARK"
                else:
                    raise ValueError(f"Formato inválido para CREAR: '{line}'")

            if tipo == "HOLOBIT":
                if not (contenido.startswith("{") and contenido.endswith("}")):
                    raise ValueError(
                        f"Se esperaban referencias entre llaves para HOLOBIT: '{line}'"
                    )
                referencias = contenido[1:-1].split(",")
                referencias = [ref.strip() for ref in referencias if ref.strip()]
                if len(referencias) != 6:
                    raise ValueError(
                        f"Un Holobit requiere exactamente 6 referencias, pero se encontraron {len(referencias)}: '{contenido}'"
                    )

                quarks = []
                for ref in referencias:
                    if ref in self.holobits:
                        quarks.append(self.holobits[ref])
                    else:
                        raise KeyError(
                            f"El quark '{ref}' no existe en la tabla de símbolos."
                        )

                self.holobits[nombre] = Holobit(
                    quarks, [self._crear_antiquark(q) for q in quarks]
                )
                # Registrar el Holobit en el Holocron
                self.holocron.add_holobit(nombre, self.holobits[nombre])
            elif tipo == "QUARK":
                if not (contenido.startswith("(") and contenido.endswith(")")):
                    raise ValueError(
                        f"Se esperaban coordenadas entre paréntesis para QUARK: '{line}'"
                    )
                coords = self._parse_coordinates(contenido)
                self.holobits[nombre] = Quark(*coords)
            else:
                raise ValueError(f"Tipo desconocido para CREAR: '{tipo}'")
        elif command == "ROT":
            if len(tokens) != 4:
                raise ValueError(f"Formato inválido para la instrucción ROT: '{line}'")
            holobit_name, axis, angle = tokens[1], tokens[2].lower(), tokens[3]
            if holobit_name not in self.holobits:
                raise KeyError(f"El Holobit '{holobit_name}' no existe en la tabla de símbolos.")
            if axis not in ["x", "y", "z"]:
                raise ValueError(f"Eje inválido para rotación: '{axis}'. Debe ser 'x', 'y' o 'z'.")
            try:
                angle = float(angle)
            except ValueError:
                raise ValueError(f"Ángulo inválido para rotación: '{angle}'. Debe ser un número válido.")

            holobit = self.holobits[holobit_name]
            holobit.rotar(axis, angle)
        elif command == "ENTR":
            if len(tokens) != 3:
                raise ValueError(f"Formato inválido para la instrucción ENTR: '{line}'")
            h1, h2 = tokens[1], tokens[2]
            if h1 not in self.holobits or h2 not in self.holobits:
                raise KeyError("Uno de los Holobits no existe en la tabla de símbolos.")
            from ..core.operations import entrelazar
            hb1 = self.holobits[h1]
            hb2 = self.holobits[h2]
            estado = entrelazar(hb1.quarks[0], hb2.quarks[0])
            self.entanglements[(h1, h2)] = estado
        elif command == "SUPERPOS":
            if len(tokens) < 2:
                raise ValueError(f"Formato inválido para la instrucción SUPERPOS: '{line}'")
            nombres = tokens[1:]
            holobits = []
            for n in nombres:
                if n not in self.holobits:
                    raise KeyError(f"El Holobit '{n}' no existe en la tabla de símbolos.")
                holobits.append(self.holobits[n])
            from holobit_sdk.quantum_holocron.quantum_algorithm import superposicion_y_medicion
            resultados = superposicion_y_medicion(holobits)
            for nombre, resultado in zip(nombres, resultados):
                self.measurements[nombre] = resultado
            return resultados
        elif command == "MEDIR":
            if len(tokens) < 2:
                raise ValueError(f"Formato inválido para la instrucción MEDIR: '{line}'")
            nombres = tokens[1:]
            holobits = []
            for n in nombres:
                if n not in self.holobits:
                    raise KeyError(f"El Holobit '{n}' no existe en la tabla de símbolos.")
                holobits.append(self.holobits[n])
            from holobit_sdk.quantum_holocron.quantum_algorithm import superposicion_y_medicion
            resultados = superposicion_y_medicion(holobits)
            for nombre, resultado in zip(nombres, resultados):
                self.measurements[nombre] = resultado
            return resultados
        elif command == "SINCRONIZAR":
            if len(tokens) < 3:
                raise ValueError(
                    f"Formato inválido para la instrucción SINCRONIZAR: '{line}'"
                )
            grupos = tokens[1:]
            resultados = self.holocron.synchronize_measurements(grupos)
            for nombre, resultado in resultados.items():
                self.measurements[nombre] = resultado
            return resultados
        elif command == "ENTANGLE":
            if len(tokens) < 3:
                raise ValueError(f"Formato inválido para la instrucción ENTANGLE: '{line}'")
            nombres = tokens[1:]
            holobits = []
            for n in nombres:
                if n not in self.holobits:
                    raise KeyError(f"El Holobit '{n}' no existe en la tabla de símbolos.")
                holobits.append(self.holobits[n])
            from holobit_sdk.quantum_holocron.entanglement import entangle_holobits
            resultado = entangle_holobits(holobits)
            self.entanglements[tuple(nombres)] = resultado
            return resultado
        elif command == "DESENTANGLE":
            if len(tokens) < 3:
                raise ValueError(
                    f"Formato inválido para la instrucción DESENTANGLE: '{line}'"
                )
            nombres = tokens[1:]
            key = tuple(nombres)
            estado = self.entanglements.get(key, [])
            from holobit_sdk.quantum_holocron.entanglement import desentangle_holobits
            resultado = desentangle_holobits(estado)
            self.entanglements[key] = resultado
            return resultado
        elif command == "GRUPO":
            # Sintaxis: GRUPO G1 = {H1, H2}
            if "=" not in line:
                raise ValueError(
                    f"Formato inválido para la instrucción GRUPO: '{line}'"
                )
            nombre, contenido = line[len("GRUPO") :].split("=", 1)
            nombre = nombre.strip()
            contenido = contenido.strip()
            if not (contenido.startswith("{") and contenido.endswith("}")):
                raise ValueError(f"Formato inválido para GRUPO: '{line}'")
            referencias = [
                ref.strip() for ref in contenido[1:-1].split(",") if ref.strip()
            ]
            if not referencias:
                raise ValueError(
                    f"Se requiere al menos un Holobit para formar un grupo: '{line}'"
                )
            for ref in referencias:
                if ref not in self.holobits:
                    raise KeyError(
                        f"El Holobit '{ref}' no existe en la tabla de símbolos."
                    )
                # Asegurar que el Holocron conozca al Holobit
                if ref not in self.holocron.holobits:
                    self.holocron.add_holobit(ref, self.holobits[ref])
            # Crear el grupo a través del Holocron
            self.holocron.create_group(nombre, referencias)
        elif command == "AGRUPAR":
            # Sintaxis: AGRUPAR G1 /patron/
            if len(tokens) < 3:
                raise ValueError(
                    f"Formato inválido para la instrucción AGRUPAR: '{line}'"
                )
            nombre = tokens[1]
            patron_txt = line.split(None, 2)[2].strip()
            if not (patron_txt.startswith("/") and patron_txt.endswith("/")):
                raise ValueError(f"Patrón inválido para AGRUPAR: '{line}'")
            patron = patron_txt[1:-1]
            self.holocron.create_group_from_pattern(nombre, patron)
        elif command == "FUSIONAR":
            # Sintaxis: FUSIONAR G3 = {G1, G2}
            if "=" not in line:
                raise ValueError(
                    f"Formato inválido para la instrucción FUSIONAR: '{line}'"
                )
            nombre, contenido = line[len("FUSIONAR") :].split("=", 1)
            nombre = nombre.strip()
            contenido = contenido.strip()
            if not (contenido.startswith("{") and contenido.endswith("}")):
                raise ValueError(f"Formato inválido para FUSIONAR: '{line}'")
            grupos = [g.strip() for g in contenido[1:-1].split(",") if g.strip()]
            if len(grupos) < 2:
                raise ValueError(
                    f"Se requieren al menos dos grupos para fusionar: '{line}'"
                )
            self.holocron.merge_groups(nombre, grupos)
        elif command == "DIVIDIR":
            # Sintaxis: DIVIDIR G1 G2 = {H3, H4}
            if "=" not in line:
                raise ValueError(
                    f"Formato inválido para la instrucción DIVIDIR: '{line}'"
                )
            left, contenido = line[len("DIVIDIR") :].split("=", 1)
            left = left.strip()
            partes = left.split()
            if len(partes) != 2:
                raise ValueError(
                    f"Formato inválido para DIVIDIR, se esperaba 'DIVIDIR origen nuevo = {{...}}': '{line}'"
                )
            origen, nuevo = partes
            contenido = contenido.strip()
            if not (contenido.startswith("{") and contenido.endswith("}")):
                raise ValueError(f"Formato inválido para DIVIDIR: '{line}'")
            holobits_ids = [
                ref.strip() for ref in contenido[1:-1].split(",") if ref.strip()
            ]
            if not holobits_ids:
                raise ValueError(
                    f"Se requiere al menos un Holobit para dividir: '{line}'"
                )
            self.holocron.split_group(origen, nuevo, holobits_ids)
        elif command == "APLICAR":
            # Sintaxis: APLICAR OPERACION G1 o APLICAR OPERACION {G1, G2}
            if len(tokens) < 3:
                raise ValueError(
                    f"Formato inválido para la instrucción APLICAR: '{line}'"
                )
            operation_name = macros.resolve_alias(tokens[1])
            if len(tokens) == 3:
                grupos_txt = tokens[2]
                if grupos_txt.startswith("{") and grupos_txt.endswith("}"):
                    grupos = [g.strip() for g in grupos_txt[1:-1].split(",") if g.strip()]
                else:
                    grupos = grupos_txt
            else:
                grupos_txt = " ".join(tokens[2:]).strip()
                if grupos_txt.startswith("{") and grupos_txt.endswith("}"):
                    grupos = [g.strip() for g in grupos_txt[1:-1].split(",") if g.strip()]
                else:
                    grupos = [g.strip() for g in tokens[2:]]

            if operation_name == "SWAP" and isinstance(grupos, list) and len(grupos) > 2:
                raise ValueError("SWAP requiere uno o dos grupos")

            from holobit_sdk.quantum_holocron.instructions import assembler_instructions

            if not hasattr(assembler_instructions, operation_name):
                raise KeyError(
                    f"La operación cuántica '{operation_name}' no está definida."
                )
            operation = getattr(assembler_instructions, operation_name)
            return self.holocron.execute_quantum_operation(operation, grupos)
        elif command == "COMPARAR_ESTADO":
            if len(tokens) != 4:
                raise ValueError(
                    f"Formato inválido para la instrucción COMPARAR_ESTADO: '{line}'"
                )
            clave, estado_a, estado_b = tokens[1:4]
            resultado = self.holocron.compare_states(estado_a, estado_b)
            self.measurements[clave] = resultado
            return resultado
        elif command == "REGISTRAR":
            if len(tokens) != 2:
                raise ValueError(
                    f"Formato inválido para la instrucción REGISTRAR: '{line}'"
                )
            self.holocron.save_state(tokens[1])
        elif command == "RECUPERAR":
            if len(tokens) != 2:
                raise ValueError(
                    f"Formato inválido para la instrucción RECUPERAR: '{line}'"
                )
            self.holocron.restore_state(tokens[1])
        else:
            raise ValueError(f"Comando desconocido: '{command}'")

    def _parse_coordinates(self, coords_string):
        coords_string = coords_string.strip()

        # Validar paréntesis inicial y final
        if not (coords_string.startswith("(") and coords_string.endswith(")")):
            raise ValueError(f"Las coordenadas deben estar entre paréntesis: '{coords_string}'")

        # Quitar paréntesis y procesar el contenido interno
        coords_content = coords_string[1:-1].strip()
        if not coords_content:
            raise ValueError(f"Las coordenadas están vacías: '{coords_string}'")

        # Procesar coordenadas y convertir a flotantes
        try:
            coords = [float(coord.strip()) for coord in coords_content.split(",")]
            if len(coords) != 3:
                raise ValueError(
                    f"Se requieren exactamente 3 coordenadas, pero se encontraron {len(coords)}: '{coords_string}'")
        except ValueError as e:
            raise ValueError(f"Error al procesar las coordenadas '{coords_string}': {e}")

        return tuple(coords)

    def _crear_antiquark(self, quark):
        """
        Crea un antiquark con posición opuesta.

        Args:
            quark: Objeto Quark.
        """
        return Quark(-quark.posicion[0], -quark.posicion[1], -quark.posicion[2], quark.estado)
