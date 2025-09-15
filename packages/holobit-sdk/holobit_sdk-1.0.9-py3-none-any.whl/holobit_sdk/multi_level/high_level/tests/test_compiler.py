# Archivo: multi_level/high_level/tests/test_compiler.py

import unittest
import random
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestHoloLangCompiler(unittest.TestCase):
    """
    Pruebas unitarias para la integración del compilador con el transpilador.
    """

    def setUp(self):
        self.compiler_x86 = HoloLangCompiler("x86")
        self.compiler_arm = HoloLangCompiler("ARM")
        self.compiler_riscv = HoloLangCompiler("RISC-V")

    def test_crear_variable(self):
        """ Prueba la creación de variables en HoloLang. """
        resultado = self.compiler_x86.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.assertEqual(resultado, "Variable H1 creada con valores (0.1, 0.2, 0.3)")

    def test_imprimir_variable(self):
        """ Prueba la impresión de variables en HoloLang. """
        self.compiler_x86.compilar_y_ejecutar("CREAR H2 (0.4, 0.5, 0.6)")
        resultado = self.compiler_x86.compilar_y_ejecutar("IMPRIMIR H2")
        self.assertEqual(resultado, "H2 = (0.4, 0.5, 0.6)")

    def test_compilar_y_transpilar_x86(self):
        """ Prueba la compilación y transpilación en x86. """
        resultado = self.compiler_x86.compilar_y_ejecutar("EJECUTAR MULT H1 H2")
        self.assertEqual(resultado, "Código máquina generado: MUL H1 H2")

    def test_compilar_y_transpilar_arm(self):
        """ Prueba la compilación y transpilación en ARM. """
        resultado = self.compiler_arm.compilar_y_ejecutar("EJECUTAR DIV H1 H2")
        self.assertEqual(resultado, "Código máquina generado: DIV_ARM H1 H2")

    def test_compilar_y_transpilar_riscv(self):
        """ Prueba la compilación y transpilación en RISC-V. """
        resultado = self.compiler_riscv.compilar_y_ejecutar("EJECUTAR PUSH H1")
        self.assertEqual(resultado, "Código máquina generado: PUSH_RV H1")

    def test_crear_estructura(self):
        self.compiler_x86.compilar_y_ejecutar("EJECUTAR ALLOCATE H1 0.1 0.1 0.1")
        self.compiler_x86.compilar_y_ejecutar("EJECUTAR ALLOCATE H2 0.2 0.2 0.2")
        res = self.compiler_x86.compilar_y_ejecutar("CREAR_ESTRUCTURA S1 {H1, H2}")
        self.assertEqual(res, "Código máquina generado: CSTRUCT S1 H1 H2")
        self.assertIn("S1", self.compiler_x86.executor.api.structures)

    def test_transformar_estructura_translate(self):
        self.compiler_x86.compilar_y_ejecutar("EJECUTAR ALLOCATE H3 0.1 0.1 0.1")
        self.compiler_x86.compilar_y_ejecutar("EJECUTAR ALLOCATE H4 0.2 0.2 0.2")
        self.compiler_x86.compilar_y_ejecutar("CREAR_ESTRUCTURA S2 {H3, H4}")
        res = self.compiler_x86.compilar_y_ejecutar(
            "TRANSFORMAR_ESTRUCTURA S2 TRANSLATE 0.1 0.1 0.1"
        )
        self.assertEqual(res, "Código máquina generado: TSTRUCT S2 TRANSLATE 0.1 0.1 0.1")
        pos = self.compiler_x86.executor.api.memory.get_position("H3")
        self.assertEqual(pos, (0.2, 0.2, 0.2))

    def test_compiler_instrucciones_cuanticas(self):
        self.compiler_x86.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.compiler_x86.compilar_y_ejecutar("CREAR H2 (0.4, 0.5, 0.6)")
        self.compiler_x86.compilar_y_ejecutar("CREAR_ESTRUCTURA G1 {H1}")
        self.compiler_x86.compilar_y_ejecutar("CREAR_ESTRUCTURA G2 {H2}")
        ent = self.compiler_x86.compilar_y_ejecutar("ENTRELAZAR G1 G2")
        self.assertIn((self.compiler_x86.parser.variables["H1"], self.compiler_x86.parser.variables["H2"]), ent)
        random.seed(0)
        sup = self.compiler_x86.compilar_y_ejecutar("SUPERPOSICION G1")
        self.assertIn(sup[0], [0, 1])
        random.seed(1)
        med = self.compiler_x86.compilar_y_ejecutar("MEDIR G2")
        self.assertIn(med[0], [0, 1])


if __name__ == "__main__":
    unittest.main()
