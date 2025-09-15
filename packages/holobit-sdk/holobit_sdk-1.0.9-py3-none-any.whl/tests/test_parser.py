import unittest
from holobit_sdk.assembler.parser import AssemblerParser
from holobit_sdk.core.quark import Quark

from holobit_sdk.quantum_holocron.instructions import assembler_instructions


class TestAssemblerParser(unittest.TestCase):
    def setUp(self):
        """
        Configuración inicial antes de cada prueba.
        """
        self.parser = AssemblerParser()

    def test_crear_quark(self):
        """
        Prueba la creación de un quark.
        """
        line = "CREAR Q1 (0.1, 0.2, 0.3)"
        self.parser.parse_line(line)
        self.assertIn("Q1", self.parser.holobits)
        self.assertIsInstance(self.parser.holobits["Q1"], Quark)

    def test_crear_quark_tipado(self):
        """Prueba la creación explícita de un quark utilizando tipado."""
        line = "CREAR QUARK Q1 (0.1, 0.2, 0.3)"
        self.parser.parse_line(line)
        self.assertIn("Q1", self.parser.holobits)
        self.assertIsInstance(self.parser.holobits["Q1"], Quark)

    def test_crear_quark_coordenadas_invalidas(self):
        invalid_coords = [
            "CREAR Q1 (0.1, 0.2)",  # Faltan coordenadas
            "CREAR Q1 (0.1, 0.2, texto)",  # Coordenada no numérica
            "CREAR Q1 (0.1,)",  # Coordenada incompleta
            "CREAR Q1 0.1, 0.2, 0.3",  # Sin paréntesis
            "CREAR Q1 ()",  # Vacío
            "CREAR Q1 (0.1 0.2, 0.3)"  # Falta coma
        ]
        for line in invalid_coords:
            with self.assertRaises(ValueError):
                self.parser.parse_line(line)

    def test_crear_holobit(self):
        for i in range(1, 7):
            self.parser.parse_line(f"CREAR Q{i} ({i * 0.1:.1f}, {i * 0.2:.1f}, {i * 0.3:.1f})")
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")

    def test_crear_holobit_tipado(self):
        for i in range(1, 7):
            self.parser.parse_line(
                f"CREAR QUARK Q{i} ({i * 0.1:.1f}, {i * 0.2:.1f}, {i * 0.3:.1f})"
            )
        self.parser.parse_line("CREAR HOLOBIT H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.assertIn("H1", self.parser.holobits)

    def test_crear_holobit_referencias_invalidas(self):
        """
        Prueba un Holobit con referencias inexistentes.
        """
        line = "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}"  # Sin crear los quarks
        with self.assertRaises(KeyError):
            self.parser.parse_line(line)

    def test_crear_tipado_invalido(self):
        """Verifica que se valide el tipo indicado en la instrucción CREAR."""
        with self.assertRaises(ValueError):
            self.parser.parse_line("CREAR QUARK Q1 {Q2}")
        with self.assertRaises(ValueError):
            self.parser.parse_line("CREAR HOLOBIT H1 (0.1,0.2,0.3)")

    def test_instruccion_invalida(self):
        """
        Prueba una instrucción no reconocida.
        """
        with self.assertRaises(ValueError):
            self.parser.parse_line("INVALID H1")

    def test_rotar_holobit(self):
        """
        Prueba la rotación de un Holobit.
        """
        # Crear quarks necesarios
        for i in range(1, 7):
            self.parser.parse_line(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")

        # Crear Holobit
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")

        # Rotar Holobit
        self.parser.parse_line("ROT H1 z 90")
        self.assertIn("H1", self.parser.holobits)

    def test_rotar_holobit_angulo_invalido(self):
        """
        Prueba la rotación de un Holobit con un ángulo inválido.
        """
        # Crear quarks necesarios
        for i in range(1, 7):
            self.parser.parse_line(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")

        # Crear Holobit
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")

        with self.assertRaises(ValueError):
            self.parser.parse_line("ROT H1 z texto")  # Ángulo no numérico

    def test_rotar_holobit_eje_invalido(self):
        """
        Prueba la rotación de un Holobit con un eje inválido.
        """
        # Crear quarks necesarios
        for i in range(1, 7):
            self.parser.parse_line(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")

        # Crear Holobit
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")

        with self.assertRaises(ValueError):
            self.parser.parse_line("ROT H1 invalid 90")  # Eje inválido

    def test_rotar_holobit_invalido(self):
        """
        Prueba la rotación de un Holobit inexistente.
        """
        line = "ROT H1 z 90"  # Holobit no creado
        with self.assertRaises(KeyError):
            self.parser.parse_line(line)

    def test_entrelazar(self):
        """Prueba el registro de entrelazamiento."""
        # Crear quarks para dos Holobits
        for i in range(1, 13):
            self.parser.parse_line(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")
        self.parser.parse_line("ENTR H1 H2")
        self.assertIn(("H1", "H2"), self.parser.entanglements)

    def test_fusionar_grupos(self):
        """Verifica la fusión de grupos mediante el Holocron."""
        # Crear holobits de prueba
        for i in range(1, 13):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")

        self.parser.parse_line("GRUPO G1 = {H1}")
        self.parser.parse_line("GRUPO G2 = {H2}")

        self.parser.parse_line("FUSIONAR G3 = {G1, G2}")
        self.assertIn("G3", self.parser.holocron.groups)
        self.assertNotIn("G1", self.parser.holocron.groups)
        self.assertNotIn("G2", self.parser.holocron.groups)
        self.assertEqual(len(self.parser.holocron.groups["G3"]), 2)

    def test_dividir_grupo(self):
        """Prueba la división de un grupo en dos."""
        for i in range(1, 13):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")

        self.parser.parse_line("GRUPO G1 = {H1, H2}")
        self.parser.parse_line("DIVIDIR G1 G2 = {H2}")

        self.assertEqual(self.parser.holocron.groups["G1"], [self.parser.holobits["H1"]])
        self.assertEqual(self.parser.holocron.groups["G2"], [self.parser.holobits["H2"]])

    def test_aplicar_operacion(self):
        """Comprueba la ejecución de una operación cuántica sobre un grupo."""
        # Definir una operación de identidad para la prueba
        assembler_instructions.IDENTIDAD = assembler_instructions.QuantumInstruction(
            "IDENTIDAD", lambda hbs: hbs
        )

        for i in range(1, 7):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("GRUPO G1 = {H1}")

        resultado = self.parser.parse_line("APLICAR IDENTIDAD G1")
        self.assertEqual(resultado, [self.parser.holobits["H1"]])

    def test_canalizar_operacion(self):
        """Verifica que CANALIZAR invoque la operación indicada."""
        self.parser.holocron.add_holobit("H1", 0b01)
        self.parser.holocron.create_group("G1", ["H1"])

        resultado = self.parser.parse_line("CANALIZAR FLIP G1")
        self.assertEqual(resultado, [~0b01])

    def test_canalizar_secuencial(self):
        """Ejecuta varias operaciones en secuencia sobre un grupo."""
        self.parser.holocron.add_holobit("H1", 0b01)
        self.parser.holocron.create_group("G1", ["H1"])

        resultado = self.parser.parse_line("CANALIZAR {FLIP, FLIP} G1")
        self.assertEqual(resultado, [0b01])
        self.assertEqual(self.parser.holocron.groups["G1"], [0b01])

        resultado2 = self.parser.parse_line("CANALIZAR {FLIP} G1")
        self.assertEqual(resultado2, [~0b01])
        self.assertEqual(self.parser.holocron.groups["G1"], [~0b01])

    def test_registrar_y_recuperar_estado(self):
        """Comprueba que REGISTRAR y RECUPERAR restauran el estado del Holocron."""

        for i in range(1, 7):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("GRUPO G1 = {H1}")

        self.parser.parse_line("REGISTRAR inicial")

        for i in range(7, 13):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")
        self.parser.parse_line("GRUPO G2 = {H2}")

        self.assertIn("H2", self.parser.holocron.holobits)
        self.assertIn("G2", self.parser.holocron.groups)

        self.parser.parse_line("RECUPERAR inicial")

        self.assertNotIn("H2", self.parser.holocron.holobits)
        self.assertNotIn("G2", self.parser.holocron.groups)
        self.assertIn("H1", self.parser.holocron.holobits)
        self.assertIn("G1", self.parser.holocron.groups)


if __name__ == "__main__":
    unittest.main()
