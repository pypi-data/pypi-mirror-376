import unittest

from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestStateManagement(unittest.TestCase):
    def test_parser_guardar_restaurar(self):
        parser = HoloLangParser()
        parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)")
        parser.interpretar("GUARDAR_ESTADO s1")
        parser.interpretar("CREAR H1 (0.4, 0.5, 0.6)")
        self.assertEqual(parser.variables["H1"], (0.4, 0.5, 0.6))
        parser.interpretar("RESTABLECER_ESTADO s1")
        self.assertEqual(parser.variables["H1"], (0.1, 0.2, 0.3))

    def test_compiler_guardar_restaurar(self):
        compiler = HoloLangCompiler()
        compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        compiler.compilar_y_ejecutar("GUARDAR_ESTADO s1")
        compiler.compilar_y_ejecutar("CREAR H1 (0.4, 0.5, 0.6)")
        self.assertEqual(compiler.parser.variables["H1"], (0.4, 0.5, 0.6))
        compiler.compilar_y_ejecutar("RESTABLECER_ESTADO s1")
        self.assertEqual(compiler.parser.variables["H1"], (0.1, 0.2, 0.3))


if __name__ == "__main__":
    unittest.main()

