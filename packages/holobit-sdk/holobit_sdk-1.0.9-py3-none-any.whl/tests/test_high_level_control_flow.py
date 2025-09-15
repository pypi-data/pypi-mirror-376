import unittest
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestHighLevelControlFlow(unittest.TestCase):
    def setUp(self):
        self.compiler = HoloLangCompiler()

    def test_if_without_else(self):
        programa = """
        SI 1 {
            CREAR QUARK A (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("A", self.compiler.parser.variables)

    def test_if_with_else(self):
        programa = """
        SI 0 {
            CREAR QUARK A (1)
        }
        SINO {
            CREAR QUARK B (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("B", self.compiler.parser.variables)
        self.assertNotIn("A", self.compiler.parser.variables)

    def test_switch_case(self):
        programa = """
        CASO 2 {
            CUANDO 1 {
                CREAR QUARK A (1)
            }
            CUANDO 2 {
                CREAR QUARK B (1)
            }
            OTRO {
                CREAR QUARK C (1)
            }
        } FINCASO
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("B", self.compiler.parser.variables)
        self.assertNotIn("A", self.compiler.parser.variables)
        self.assertNotIn("C", self.compiler.parser.variables)

    def test_siq_executes_then(self):
        self.compiler.parser.measurements["G1"] = 1
        programa = """
        SIQ G1 == 1 {
            CREAR QUARK A (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("A", self.compiler.parser.variables)
        self.assertNotIn("B", self.compiler.parser.variables)

    def test_siq_with_elseq(self):
        self.compiler.parser.measurements["G1"] = 0
        programa = """
        SIQ G1 == 1 {
            CREAR QUARK A (1)
        }
        ELSEQ {
            CREAR QUARK B (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("B", self.compiler.parser.variables)
        self.assertNotIn("A", self.compiler.parser.variables)

    def test_for_range_variable_usage(self):
        programa = """
        PARA i = 1..3 {
            IMPRIMIR i
        }
        """
        resultado = self.compiler.compilar_y_ejecutar(programa)
        self.assertEqual(resultado, ["i = 1", "i = 2", "i = 3"])
        self.assertEqual(self.compiler.parser.variables.get("i"), 4)

    def test_siq_comparisons(self):
        self.compiler.parser.measurements["G1"] = 1
        casos = [
            ("!= 2", "A"),
            ("< 2", "B"),
            ("> 0", "C"),
            ("<= 1", "D"),
            (">= 1", "E"),
        ]
        for expr, var in casos:
            programa = f"""
            SIQ G1 {expr} {{
                CREAR QUARK {var} (1)
            }}
            """
            self.compiler.compilar_y_ejecutar(programa)
            self.assertIn(var, self.compiler.parser.variables)
            self.compiler.parser.variables.clear()

    def test_siq_compound_expression(self):
        self.compiler.parser.measurements["G1"] = 1
        self.compiler.parser.measurements["G2"] = 1
        programa = """
        SIQ (G1 + G2) > 1 {
            CREAR QUARK A (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("A", self.compiler.parser.variables)

    def test_constant_malicious_expression(self):
        resultado = self.compiler.parser.interpretar(
            "CONSTANTE X = __import__('os').system('1')"
        )
        self.assertEqual(
            resultado,
            "Error de sintaxis en la definición de la constante.",
        )

    def test_siq_rejects_malicious_expression(self):
        programa = """
        SIQ __import__('os').system('1') {
            CREAR QUARK A (1)
        }
        ELSEQ {
            CREAR QUARK B (1)
        }
        """
        self.compiler.compilar_y_ejecutar(programa)
        self.assertIn("B", self.compiler.parser.variables)
        self.assertNotIn("A", self.compiler.parser.variables)


if __name__ == "__main__":
    unittest.main()
