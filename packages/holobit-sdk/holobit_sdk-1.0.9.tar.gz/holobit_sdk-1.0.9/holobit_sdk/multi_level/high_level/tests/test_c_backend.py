import textwrap
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


def test_c_backend_generates_if_else():
    compiler = HoloLangCompiler("c")
    program = textwrap.dedent(
        """
        SI 1 {
            IMPRIMIR A
        } SINO {
            IMPRIMIR B
        }
        """
    )
    output = compiler.compilar_y_ejecutar(program)
    assert "#include <stdio.h>" in output
    assert "if (1)" in output
    assert "// IMPRIMIR A" in output
    assert "// IMPRIMIR B" in output


def test_c_backend_for_loop():
    compiler = HoloLangCompiler("c")
    program = "PARA i = 0..2 { IMPRIMIR i }"
    output = compiler.compilar_y_ejecutar(program)
    assert "for (int i = 0; i <= 2; ++i)" in output


def test_cpp_backend_header():
    compiler = HoloLangCompiler("cpp")
    program = "IMPRIMIR X"
    output = compiler.compilar_y_ejecutar(program)
    assert "#include <iostream>" in output
