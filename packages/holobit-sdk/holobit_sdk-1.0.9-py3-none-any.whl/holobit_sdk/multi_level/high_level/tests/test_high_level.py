import unittest
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler
from holobit_sdk.multi_level.high_level.debugger import HoloLangDebugger
import random



class TestHighLevel(unittest.TestCase):
    """
    Pruebas unitarias para el Nivel Alto del SDK Holobit.
    """

    def setUp(self):
        self.parser = HoloLangParser()
        self.compiler = HoloLangCompiler()
        self.debugger = HoloLangDebugger()

    def test_crear_variable(self):
        """ Prueba la creación de variables en HoloLang. """
        resultado = self.parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)")
        self.assertEqual(resultado, "Variable H1 creada con valores (0.1, 0.2, 0.3)")

    def test_imprimir_variable(self):
        """ Prueba la impresión de variables en HoloLang. """
        self.parser.interpretar("CREAR H2 (0.4, 0.5, 0.6)")
        resultado = self.parser.interpretar("IMPRIMIR H2")
        self.assertEqual(resultado, "H2 = (0.4, 0.5, 0.6)")

    def test_compilar_y_ejecutar(self):
        """ Prueba la compilación y ejecución de código HoloLang. """
        resultado = self.compiler.compilar_y_ejecutar("CREAR H3 (0.7, 0.8, 0.9)")
        self.assertEqual(resultado, "Variable H3 creada con valores (0.7, 0.8, 0.9)")

    def test_parser_estructura(self):
        res = self.parser.interpretar("CREAR_ESTRUCTURA S1 {H1, H2}")
        self.assertIn("Estructura S1", res)
        self.assertIn("S1", self.parser.structures)

    def test_debugger_pausa(self):
        """ Prueba la adición de puntos de ruptura en el depurador. """
        self.debugger.agregar_punto_de_ruptura(2)
        self.assertIn(2, self.debugger.break_points)

    def test_instrucciones_cuanticas(self):
        self.parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)")
        self.parser.interpretar("CREAR H2 (0.4, 0.5, 0.6)")
        self.parser.interpretar("CREAR_ESTRUCTURA G1 {H1}")
        self.parser.interpretar("CREAR_ESTRUCTURA G2 {H2}")
        ent = self.parser.interpretar("ENTRELAZAR G1 G2")
        self.assertIn((self.parser.variables["H1"], self.parser.variables["H2"]), ent)
        random.seed(0)
        sup = self.parser.interpretar("SUPERPOSICION G1")
        self.assertIn(sup[0], [0, 1])
        random.seed(1)
        med = self.parser.interpretar("MEDIR G2")
        self.assertIn(med[0], [0, 1])

    def test_condicional_cuantico(self):
        """Evalúa la instrucción SI con una operación cuántica."""
        self.compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.compiler.compilar_y_ejecutar("CREAR H2 (0.4, 0.5, 0.6)")
        self.compiler.compilar_y_ejecutar("CREAR_ESTRUCTURA G1 {H1}")
        self.compiler.compilar_y_ejecutar("CREAR_ESTRUCTURA G2 {H2}")
        self.compiler.parser.variables["cond"] = 1
        programa = """
SI cond {
ENTRELAZAR G1 G2
}
"""
        resultado = self.compiler.compilar_y_ejecutar(programa)
        par = (
            self.compiler.parser.variables["H1"],
            self.compiler.parser.variables["H2"],
        )
        self.assertIn(par, resultado)

    def test_bucle_para_cuantico(self):
        """Evalúa la instrucción PARA ejecutando una operación varias veces."""
        self.compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.compiler.compilar_y_ejecutar("CREAR_ESTRUCTURA G1 {H1}")
        random.seed(0)
        programa = """
PARA 3 {
SUPERPOSICION G1
}
"""
        resultados = self.compiler.compilar_y_ejecutar(programa)
        self.assertEqual(len(resultados), 3)
        for r in resultados:
            self.assertIn(r, [0, 1])

    def test_bucle_mientras_cuantico(self):
        """Evalúa la instrucción MIENTRAS con operaciones cuánticas."""
        self.compiler.compilar_y_ejecutar("CREAR H2 (0.4, 0.5, 0.6)")
        self.compiler.compilar_y_ejecutar("CREAR_ESTRUCTURA G2 {H2}")
        random.seed(1)
        programa = """
MIENTRAS 2 {
MEDIR G2
}
"""
        resultados = self.compiler.compilar_y_ejecutar(programa)
        self.assertEqual(len(resultados), 2)
        for r in resultados:
            self.assertIn(r, [0, 1])

    def test_canalizar_secuencial(self):
        """Comprueba que CANALIZAR ejecute operaciones en orden."""
        self.parser.holocron.add_holobit("H1", 0b01)
        self.parser.holocron.create_group("G1", ["H1"])

        resultado = self.parser.interpretar("CANALIZAR {FLIP, FLIP} G1")
        self.assertEqual(resultado, [0b01])
        self.assertEqual(self.parser.holocron.groups["G1"], [0b01])

        resultado2 = self.parser.interpretar("CANALIZAR {FLIP} G1")
        self.assertEqual(resultado2, [~0b01])
        self.assertEqual(self.parser.holocron.groups["G1"], [~0b01])


if __name__ == "__main__":
    unittest.main()
