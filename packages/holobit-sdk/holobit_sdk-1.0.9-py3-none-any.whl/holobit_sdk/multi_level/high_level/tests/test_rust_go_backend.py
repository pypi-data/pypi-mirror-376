import textwrap
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


def test_rust_backend_if_else():
    compiler = HoloLangCompiler("rust")
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
    assert "fn main()" in output
    assert "if 1" in output
    assert "// IMPRIMIR A" in output
    assert "// IMPRIMIR B" in output


def test_go_backend_header():
    compiler = HoloLangCompiler("go")
    program = "IMPRIMIR X"
    output = compiler.compilar_y_ejecutar(program)
    assert "package main" in output
    assert "func main()" in output
    assert "// IMPRIMIR X" in output
