import unittest
from holobit_sdk.assembler.parser import AssemblerParser
from holobit_sdk.assembler import macros
from holobit_sdk.core.quark import Quark


class TestMacros(unittest.TestCase):
    def setUp(self):
        macros.macros.clear()
        macros.aliases.clear()
        macros.load_defaults()
        self.parser = AssemblerParser()

    def test_macro_creation_and_expansion(self):
        self.parser.parse_line("#macro CREARQ nombre x y z")
        self.parser.parse_line("CREAR {nombre} ({x}, {y}, {z})")
        self.parser.parse_line("#endmacro")
        self.parser.parse_line("CREARQ Q1 0.1 0.2 0.3")
        self.assertIn("Q1", self.parser.holobits)
        self.assertIsInstance(self.parser.holobits["Q1"], Quark)

    def test_macro_removal(self):
        self.parser.parse_line("#macro CREARQ nombre x y z")
        self.parser.parse_line("CREAR {nombre} ({x}, {y}, {z})")
        self.parser.parse_line("#endmacro")
        macros.remove_macro("CREARQ")
        with self.assertRaises(ValueError):
            self.parser.parse_line("CREARQ Q2 0.2 0.3 0.4")

    def _expand_all(self, name, args):
        """Expande recursivamente una macro y todas las macros anidadas."""

        lines = macros.expand_macro(name, args)
        result = []
        for line in lines:
            tokens = line.split()
            if tokens and macros.is_macro(tokens[0]):
                result.extend(self._expand_all(tokens[0], tokens[1:]))
            else:
                result.append(line)
        return result

    def test_optional_parameters(self):
        macros.register_macro(
            "SALUDAR",
            {"nombre": "Mundo", "signo": "!"},
            ["SAY Hola {nombre}{signo}"],
        )
        self.assertEqual(macros.expand_macro("SALUDAR", []), ["SAY Hola Mundo!"])
        self.assertEqual(
            macros.expand_macro("SALUDAR", ["Luis"]), ["SAY Hola Luis!"]
        )

    def test_namespaces(self):
        macros.register_macro(
            "math::DOBLE",
            {"x": "0"},
            ["ADD {x}, {x}"],
        )
        macros.register_macro(
            "texto::DOBLE",
            {"s": ""},
            ["CONCAT {s}, {s}"],
        )
        self.assertTrue(macros.is_macro("math::DOBLE"))
        self.assertTrue(macros.is_macro("texto::DOBLE"))
        self.assertFalse(macros.is_macro("DOBLE"))
        self.assertEqual(macros.expand_macro("math::DOBLE", ["2"]), ["ADD 2, 2"])
        self.assertEqual(
            macros.expand_macro("texto::DOBLE", ["hi"]), ["CONCAT hi, hi"]
        )

    def test_nested_macros(self):
        macros.register_macro("INC", {"x": "0"}, ["ADD {x}, 1"])
        macros.register_macro(
            "DOBLE_INC",
            {"x": "0"},
            ["INC {x}", "INC {x}"],
        )
        expanded = self._expand_all("DOBLE_INC", ["5"])
        self.assertEqual(expanded, ["ADD 5, 1", "ADD 5, 1"])

    def test_macro_conditional_true(self):
        self.parser.holocron.holobits["HB1"] = object()
        macros.register_macro(
            "COND",
            {},
            [
                "#if 'HB1' in holobits",
                "CREAR QTRUE (0, 0, 0)",
                "#else",
                "CREAR QFALSE (0, 0, 0)",
                "#endif",
            ],
        )
        self.parser.parse_line("COND")
        self.assertIn("QTRUE", self.parser.holobits)
        self.assertNotIn("QFALSE", self.parser.holobits)

    def test_macro_conditional_false(self):
        macros.register_macro(
            "COND",
            {},
            [
                "#if 'HB1' in holobits",
                "CREAR QTRUE (0, 0, 0)",
                "#else",
                "CREAR QFALSE (0, 0, 0)",
                "#endif",
            ],
        )
        self.parser.parse_line("COND")
        self.assertIn("QFALSE", self.parser.holobits)
        self.assertNotIn("QTRUE", self.parser.holobits)

    def test_macro_malicious_expression(self):
        with self.assertRaises(ValueError):
            macros.preprocess_lines([
                "#if __import__('os').system('1')",
                "#endif",
            ], {})

    def test_macro_context_limited(self):
        """Las expresiones solo pueden acceder a atributos permitidos."""

        # ``custom`` no forma parte del contexto expuesto del Holocron
        self.parser.holocron.custom = True
        with self.assertRaises(ValueError):
            macros.preprocess_lines([
                "#if custom",
                "#endif",
            ], self.parser.holocron)


if __name__ == "__main__":
    unittest.main()
