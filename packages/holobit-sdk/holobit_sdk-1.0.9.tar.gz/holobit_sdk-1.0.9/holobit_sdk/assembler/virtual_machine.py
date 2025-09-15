from pathlib import Path
import os

from holobit_sdk.assembler.parser import AssemblerParser
from holobit_sdk.assembler.executor import AssemblerExecutor
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.utils.safe_eval import safe_eval
from . import macros


class InstructionLimitExceeded(RuntimeError):
    """Se lanza cuando se supera el número máximo de instrucciones."""

    pass


class HolocronInstruction:
    """Representa una instrucción básica del ensamblador holográfico."""

    def __init__(self, name, func):
        self.name = name
        self.func = func

    def execute(self, parser, *args):
        return self.func(parser, *args)


def _crear(parser, nombre, *coords):
    line = f"CREAR {nombre} ({', '.join(coords)})"
    parser.parse_line(line)


def _crear_holobit(parser, nombre, refs):
    line = f"CREAR {nombre} {{{refs}}}"
    parser.parse_line(line)


def _rotar(parser, nombre, eje, angulo):
    line = f"ROT {nombre} {eje} {angulo}"
    parser.parse_line(line)


def _entrelazar(parser, h1, h2):
    """Registra el entrelazamiento entre dos Holobits."""
    line = f"ENTR {h1} {h2}"
    parser.parse_line(line)


def _superpos(parser, *holobits):
    line = "SUPERPOS " + " ".join(holobits)
    parser.parse_line(line)


def _medir(parser, *holobits):
    line = "MEDIR " + " ".join(holobits)
    parser.parse_line(line)


def _sincronizar(parser, *grupos):
    line = "SINCRONIZAR " + " ".join(grupos)
    parser.parse_line(line)


def _entangle(parser, *holobits):
    line = "ENTANGLE " + " ".join(holobits)
    parser.parse_line(line)


def _aplicar(parser, operacion, *grupos):
    op = macros.resolve_alias(operacion)
    if not grupos:
        raise ValueError("Se requiere al menos un grupo")
    if len(grupos) == 1:
        line = f"APLICAR {op} {grupos[0]}"
    else:
        line = f"APLICAR {op} {{{', '.join(grupos)}}}"
    parser.parse_line(line)


def _crear_grupo(parser, holocron, nombre, *holobits):
    line = f"GRUPO {nombre} = {{{', '.join(holobits)}}}"
    parser.parse_line(line)
    holocron.create_group(nombre, list(holobits))


DEFAULT_INSTRUCTIONS = {
    "CREAR": HolocronInstruction("CREAR", _crear),
    "CREAR_HOLOBIT": HolocronInstruction("CREAR_HOLOBIT", _crear_holobit),
    "ROT": HolocronInstruction("ROT", _rotar),
    "ENTR": HolocronInstruction("ENTR", _entrelazar),
    "SUPERPOS": HolocronInstruction("SUPERPOS", _superpos),
    "MEDIR": HolocronInstruction("MEDIR", _medir),
    "SINCRONIZAR": HolocronInstruction("SINCRONIZAR", _sincronizar),
    "ENTANGLE": HolocronInstruction("ENTANGLE", _entangle),
    "APLICAR": HolocronInstruction("APLICAR", _aplicar),
    "GRUPO": HolocronInstruction("GRUPO", _crear_grupo),
}


class AssemblerVM:
    """Pequeña máquina virtual para ejecutar instrucciones holográficas."""

    def __init__(self):
        macros.load_defaults()
        self.parser = AssemblerParser()
        self.executor = AssemblerExecutor(self.parser)
        self.instructions = DEFAULT_INSTRUCTIONS
        self.holocron = Holocron()

    def execute_instruction(self, name, *args):
        name = macros.resolve_alias(name)
        if name not in self.instructions:
            raise ValueError(f"Instrucción desconocida: {name}")
        instr = self.instructions[name]
        if name == "GRUPO":
            instr.execute(self.parser, self.holocron, *args)
        else:
            instr.execute(self.parser, *args)

    def run_program(self, lines, max_instructions=None, _counter=None):
        pc = 0
        stack = []
        total = len(lines)
        if _counter is None:
            _counter = {"count": 0}
        while pc < total:
            line = lines[pc].strip()
            if not line:
                pc += 1
                continue
            if max_instructions is not None:
                _counter["count"] += 1
                if _counter["count"] > max_instructions:
                    raise InstructionLimitExceeded("Límite de instrucciones excedido")
            parts = line.split()
            command = parts[0]
            if command == "FUNC":
                name = parts[1]
                end = self._jump_to_endfunc(lines, pc + 1)
                self.parser.functions[name] = [ln.strip() for ln in lines[pc + 1 : end]]
                pc = end + 1
                continue
            elif command == "CALL":
                name = parts[1]
                if name not in self.parser.functions:
                    raise KeyError(f"Función desconocida: {name}")
                self.run_program(self.parser.functions[name], max_instructions, _counter)
                pc += 1
                continue
            elif command == "ENDFUNC":
                pc += 1
                continue
            if command == "SI":
                var = parts[1]
                value = self.parser.measurements.get(var, 0)
                if value == True:
                    pc += 1
                else:
                    pc = self._jump_to_else_or_end(lines, pc + 1, "SINO")
            elif command == "SINO":
                pc = self._jump_to_end(lines, pc + 1)
            elif command == "SIQ":
                expr = line[len("SIQ") :].strip()
                try:
                    val = safe_eval(expr, self.parser.measurements)
                except Exception:
                    val = False
                if val == True:
                    pc += 1
                else:
                    pc = self._jump_to_else_or_end(lines, pc + 1, "ELSEQ")
            elif command == "ELSEQ":
                pc = self._jump_to_end(lines, pc + 1)
            elif command == "MIENTRAS":
                var = parts[1]
                value = self.parser.measurements.get(var, 0)
                if stack and stack[-1].get("type") == "MIENTRAS" and stack[-1]["start"] == pc:
                    if value == True:
                        pc += 1
                    else:
                        stack.pop()
                        pc = self._jump_to_end(lines, pc + 1)
                else:
                    if value == True:
                        stack.append({"type": "MIENTRAS", "start": pc})
                        pc += 1
                    else:
                        pc = self._jump_to_end(lines, pc + 1)
            elif command == "PARA":
                count = int(parts[1])
                if count <= 0:
                    pc = self._jump_to_end(lines, pc + 1)
                else:
                    stack.append({"type": "PARA", "start": pc, "remaining": count})
                    pc += 1
            elif command == "PARAG":
                group_id = parts[1]
                group = self.parser.holocron.groups.get(group_id, [])
                end = self._jump_to_end(lines, pc + 1)
                if not group:
                    pc = end
                else:
                    name_map = {
                        hb: name
                        for name, hb in self.parser.holocron.holobits.items()
                    }
                    block = lines[pc + 1 : end]
                    for hb in group:
                        nombre = name_map.get(hb)
                        if not nombre:
                            continue
                        replaced = [ln.replace("$", nombre) for ln in block]
                        self.run_program(replaced, max_instructions, _counter)
                    pc = end
            elif command == "FIN":
                if stack:
                    top = stack[-1]
                    if top["type"] == "MIENTRAS":
                        pc = top["start"]
                    elif top["type"] == "PARA":
                        top["remaining"] -= 1
                        if top["remaining"] > 0:
                            pc = top["start"] + 1
                        else:
                            stack.pop()
                            pc += 1
                    else:
                        pc += 1
                else:
                    pc += 1
            elif command == "CASO":
                expr = parts[1]
                try:
                    value = int(expr)
                except ValueError:
                    value = self.parser.measurements.get(expr, 0)
                pc = self._execute_caso(lines, pc, value, max_instructions, _counter)
            elif command in {"CUANDO", "OTRO", "FINCASO"}:
                # Procesados dentro de _execute_caso
                pc += 1
            else:
                self.executor.execute(line)
                pc += 1

    def _jump_to_else_or_end(self, lines, start, else_token):
        depth = 0
        for i in range(start, len(lines)):
            tokens = lines[i].strip().split()
            if not tokens:
                continue
            cmd = tokens[0]
            if cmd in {"SI", "SIQ", "MIENTRAS", "PARA", "PARAG", "CASO"}:
                depth += 1
            elif cmd == "FIN":
                if depth == 0:
                    return i + 1
                depth -= 1
            elif cmd == "FINCASO":
                if depth > 0:
                    depth -= 1
            elif cmd == else_token and depth == 0:
                return i + 1
        return len(lines)

    def _jump_to_end(self, lines, start):
        depth = 0
        for i in range(start, len(lines)):
            tokens = lines[i].strip().split()
            if not tokens:
                continue
            cmd = tokens[0]
            if cmd in {"SI", "SIQ", "MIENTRAS", "PARA", "PARAG", "CASO"}:
                depth += 1
            elif cmd == "FIN":
                if depth == 0:
                    return i + 1
                depth -= 1
            elif cmd == "FINCASO" and depth > 0:
                depth -= 1
        return len(lines)

    def _execute_caso(self, lines, start, value, max_instructions, _counter):
        i = start + 1
        total = len(lines)
        cases = []
        default = None
        current_match = None
        block_start = None
        depth = 0
        fin = total
        while i < total:
            tokens = lines[i].strip().split()
            if not tokens:
                i += 1
                continue
            cmd = tokens[0]
            if cmd in {"SI", "SIQ", "MIENTRAS", "PARA", "PARAG", "CASO"}:
                depth += 1
            elif cmd == "FIN":
                if depth > 0:
                    depth -= 1
            elif cmd == "FINCASO" and depth == 0:
                if current_match is not None:
                    cases.append((current_match, block_start, i))
                fin = i
                break
            elif depth == 0 and cmd in {"CUANDO", "OTRO"}:
                if current_match is not None:
                    cases.append((current_match, block_start, i))
                current_match = tokens[1] if cmd == "CUANDO" else "DEFAULT"
                block_start = i + 1
            i += 1
        for match, start_block, end_block in cases:
            if match == "DEFAULT":
                default = (start_block, end_block)
            elif str(value) == match:
                self.run_program(lines[start_block:end_block], max_instructions, _counter)
                return fin + 1
        if default:
            self.run_program(lines[default[0]:default[1]], max_instructions, _counter)
        return fin + 1

    def _jump_to_endfunc(self, lines, start):
        depth = 0
        for i in range(start, len(lines)):
            tokens = lines[i].strip().split()
            if not tokens:
                continue
            cmd = tokens[0]
            if cmd == "FUNC":
                depth += 1
            elif cmd == "ENDFUNC":
                if depth == 0:
                    return i
                depth -= 1
        return len(lines)

    def run_file(self, filepath, max_instructions=None):
        path = Path(filepath)
        root_dir = Path(os.getenv("HOLOBIT_VM_ROOT", Path.cwd())).resolve()

        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Archivo no encontrado: {path}") from exc
        except OSError as exc:
            raise PermissionError(f"No se puede leer el archivo: {path}") from exc

        real_path = Path(os.path.realpath(f"/proc/self/fd/{fd}"))
        try:
            real_path.relative_to(root_dir)
        except ValueError as exc:
            os.close(fd)
            raise PermissionError("Ruta fuera del directorio permitido") from exc

        with os.fdopen(fd, "r", encoding="utf-8") as f:
            self.run_program(f.readlines(), max_instructions=max_instructions)
