import pytest
from holobit_sdk.transpiler.machine_code_transpiler import MachineCodeTranspiler

@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "ALLOCATE H1 0.1 0.2 0.3", "MOV H1 0.1 0.2 0.3"),
        ("ARM", "ALLOCATE H1 0.1 0.2 0.3", "LDR H1 0.1 0.2 0.3"),
        ("RISC-V", "ALLOCATE H1 0.1 0.2 0.3", "LW H1 0.1 0.2 0.3"),
    ],
)
def test_transpile_allocate(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,expected",
    [
        ("x86", "JMP LABEL1"),
        ("ARM", "B LABEL1"),
        ("RISC-V", "JAL LABEL1"),
    ],
)
def test_transpile_jump(architecture, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile("JUMP LABEL1") == expected


@pytest.mark.parametrize("architecture", ["x86", "ARM", "RISC-V"])
def test_transpile_unknown_instruction(architecture):
    transpiler = MachineCodeTranspiler(architecture)
    result = transpiler.transpile("UNKNOWN_CMD H1")
    assert result == f"Instrucción holográfica desconocida para {architecture}: UNKNOWN_CMD"


def test_compare_redundant():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("COMPARE H1 H1") == "NOP"


def test_push_pop_multi():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("PUSH H1 H2 H3") == "PUSH_MULTI H1 H2 H3"
    assert transpiler.transpile("POP H1 H2 H3") == "POP_MULTI H1 H2 H3"


def test_register_reuse():
    transpiler = MachineCodeTranspiler("x86")
    first = transpiler.transpile("ADD H1 H2")
    second = transpiler.transpile("ADD H1 H3")
    assert "; Registro registrado" in first
    assert "; Registro reutilizado" in second


def test_eliminate_mov_redundant():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("ALLOCATE H1 H1") == "NOP"


@pytest.mark.parametrize(
    "instruction,expected",
    [
        ("SI R1", "CMP R1"),
        ("SINO LABEL", "JMP LABEL"),
        ("MIENTRAS R1", "LOOP R1"),
    ],
)
def test_control_flow_new_tokens(instruction, expected):
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "TELETRANSPORTAR H1 H2", "TPORT H1 H2"),
        ("ARM", "TELETRANSPORTAR H1 H2", "TPORT_ARM H1 H2"),
        ("RISC-V", "TELETRANSPORTAR H1 H2", "TPORT_RV H1 H2"),
    ],
)
def test_transpile_teletransportar(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "COLAPSAR H1", "COLL H1"),
        ("ARM", "COLAPSAR H1", "COLL_ARM H1"),
        ("RISC-V", "COLAPSAR H1", "COLL_RV H1"),
    ],
)
def test_transpile_colapsar(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "FUSIONAR H1 H2", "FUSE H1 H2"),
        ("ARM", "FUSIONAR H1 H2", "FUSE_ARM H1 H2"),
        ("RISC-V", "FUSIONAR H1 H2", "FUSE_RV H1 H2"),
    ],
)
def test_transpile_fusionar(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


def test_teletransportar_redundant():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("TELETRANSPORTAR H1 H1") == "NOP"


def test_colapsar_redundant():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("COLAPSAR H1") == "COLL H1"
    assert transpiler.transpile("COLAPSAR H1") == "NOP"


def test_fusionar_redundant():
    transpiler = MachineCodeTranspiler("x86")
    assert transpiler.transpile("FUSIONAR H1 H1") == "NOP"


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "CREAR_FRACTAL_ND 3", "CFRACT_ND 3"),
        ("ARM", "CREAR_FRACTAL_ND 3", "CFRACT_ND_ARM 3"),
        ("RISC-V", "CREAR_FRACTAL_ND 3", "CFRACT_ND_RV 3"),
    ],
)
def test_transpile_crear_fractal_nd(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "DINAMICA_FRACTAL 3 10 0.01", "FRACT_DYN 3, 10, 0.01"),
        ("ARM", "DINAMICA_FRACTAL 3 10 0.01", "FRACT_DYN_ARM 3, 10, 0.01"),
        ("RISC-V", "DINAMICA_FRACTAL 3 10 0.01", "FRACT_DYN_RV 3, 10, 0.01"),
    ],
)
def test_transpile_dinamica_fractal(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected


@pytest.mark.parametrize(
    "architecture,instruction,expected",
    [
        ("x86", "DENSIDAD_MORFO 3", "MORPH_DENS 3"),
        ("ARM", "DENSIDAD_MORFO 3", "MORPH_DENS_ARM 3"),
        ("RISC-V", "DENSIDAD_MORFO 3", "MORPH_DENS_RV 3"),
    ],
)
def test_transpile_densidad_morfo(architecture, instruction, expected):
    transpiler = MachineCodeTranspiler(architecture)
    assert transpiler.transpile(instruction) == expected
