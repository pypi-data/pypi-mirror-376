import unittest
from holobit_sdk.asiic_holographic.interpreter import ASIICInterpreter
from holobit_sdk.asiic_holographic.translator import ASIICTranslator
from holobit_sdk.assembler.virtual_machine import AssemblerVM



class TestASIIC(unittest.TestCase):
    """
    Pruebas unitarias para el ASIIC Holográfico.
    """

    def setUp(self):
        """ Configuración inicial para las pruebas. """
        self.vm = AssemblerVM()
        self.interpreter = ASIICInterpreter(self.vm)
        self.translator = ASIICTranslator()

    def test_interpretar_rotar(self):
        """Verifica que ROTAR modifica el estado de la VM."""
        # Crear quarks y holobit necesarios
        for i in range(1, 7):
            self.vm.execute_instruction("CREAR", f"Q{i}", f"{i * 0.1}", f"{i * 0.2}", f"{i * 0.3}")
        refs = ", ".join(f"Q{i}" for i in range(1, 7))
        self.vm.execute_instruction("CREAR_HOLOBIT", "H1", refs)

        # Ejecutar ROTAR mediante el intérprete
        resultado = self.interpreter.interpretar("ROTAR H1 z 90")

        self.assertIn("H1", self.vm.parser.holobits)
        self.assertEqual(resultado, "ROT H1 z 90")

    def test_interpretar_entrelazar(self):
        """Verifica el registro de entrelazamiento entre Holobits."""
        # Crear quarks y holobits necesarios
        for i in range(1, 13):
            self.vm.execute_instruction("CREAR", f"Q{i}", f"{i * 0.1}", f"{i * 0.2}", f"{i * 0.3}")
        refs1 = ", ".join(f"Q{i}" for i in range(1, 7))
        refs2 = ", ".join(f"Q{i}" for i in range(7, 13))
        self.vm.execute_instruction("CREAR_HOLOBIT", "H1", refs1)
        self.vm.execute_instruction("CREAR_HOLOBIT", "H2", refs2)

        resultado = self.interpreter.interpretar("ENTRELAZAR H1 H2")

        self.assertEqual(resultado, "ENTR H1 H2")
        self.assertIn(("H1", "H2"), self.vm.parser.entanglements)

    def test_traducir_rotar(self):
        """ Verifica que la instrucción ROTAR se traduce correctamente a ensamblador. """
        resultado = self.translator.traducir("ROTAR H1 z 90")
        self.assertEqual(resultado, "ROT H1 z 90")

    def test_traducir_rotar_mayus_minus(self):
        """Verifica que 'rotar' y 'ROTAR' generan el mismo ensamblador."""
        resultado_mayus = self.translator.traducir("ROTAR H1 z 90")
        resultado_minus = self.translator.traducir("rotar H1 z 90")
        self.assertEqual(resultado_mayus, "ROT H1 z 90")
        self.assertEqual(resultado_minus, "ROT H1 z 90")
        self.assertEqual(resultado_mayus, resultado_minus)

    def test_traducir_entrelazar(self):
        """ Verifica que la instrucción ENTRELAZAR se traduce correctamente a ensamblador. """
        resultado = self.translator.traducir("ENTRELAZAR H1 H2")
        self.assertEqual(resultado, "ENTR H1 H2")

    def test_instruccion_desconocida(self):
        """ Verifica que una instrucción desconocida sea manejada correctamente. """
        resultado = self.translator.traducir("DESCONOCIDO X Y Z")
        self.assertEqual(resultado, "Instrucción desconocida: DESCONOCIDO")

    def test_ejecutar_comando_traducido_rotar(self):
        """Comprueba que un comando traducido se ejecuta en la VM."""
        for i in range(1, 7):
            cmd = self.translator.traducir(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")
            self.vm.executor.execute(cmd)
        refs = ", ".join(f"Q{i}" for i in range(1, 7))
        self.vm.execute_instruction("CREAR_HOLOBIT", "H1", refs)

        cmd = self.translator.traducir("ROTAR H1 z 90")
        self.vm.executor.execute(cmd)

        holobit = self.vm.parser.holobits["H1"]
        self.assertAlmostEqual(holobit.quarks[0].posicion[0], -0.2, places=6)
        self.assertAlmostEqual(holobit.quarks[0].posicion[1], 0.1, places=6)

    def test_ejecutar_comando_traducido_entrelazar(self):
        """Comprueba el registro de entrelazamiento ejecutando comandos traducidos."""
        for i in range(1, 13):
            cmd = self.translator.traducir(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")
            self.vm.executor.execute(cmd)
        refs1 = ", ".join(f"Q{i}" for i in range(1, 7))
        refs2 = ", ".join(f"Q{i}" for i in range(7, 13))
        self.vm.execute_instruction("CREAR_HOLOBIT", "H1", refs1)
        self.vm.execute_instruction("CREAR_HOLOBIT", "H2", refs2)

        self.vm.executor.execute(self.translator.traducir("ENTRELAZAR H1 H2"))

        self.assertIn(("H1", "H2"), self.vm.parser.entanglements)


if __name__ == "__main__":
    unittest.main()
