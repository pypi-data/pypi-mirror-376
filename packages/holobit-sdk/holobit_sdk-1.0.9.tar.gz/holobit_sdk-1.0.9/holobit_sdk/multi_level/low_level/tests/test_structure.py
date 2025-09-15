import unittest
from holobit_sdk.multi_level.low_level.low_level_api import LowLevelAPI

class TestHoloStructure(unittest.TestCase):
    def setUp(self):
        self.api = LowLevelAPI()

    def test_create_and_translate(self):
        self.api.ejecutar_comando("ALLOCATE", "H1", 0.1, 0.1, 0.1)
        self.api.ejecutar_comando("ALLOCATE", "H2", 0.2, 0.2, 0.2)
        res = self.api.ejecutar_comando("CREATE_STRUCT", "S1", "H1", "H2")
        self.assertIn("Estructura S1 creada", res)
        self.api.ejecutar_comando("TRANSFORM_STRUCT", "S1", "TRANSLATE", "0.1", "0.1", "0.1")
        pos1 = self.api.memory.get_position("H1")
        pos2 = self.api.memory.get_position("H2")
        self.assertEqual(pos1, (0.2, 0.2, 0.2))
        self.assertEqual(pos2, (0.30000000000000004, 0.30000000000000004, 0.30000000000000004))

    def test_rotate_structure(self):
        self.api.ejecutar_comando("ALLOCATE", "H3", 0.2, 0, 0)
        self.api.ejecutar_comando("ALLOCATE", "H4", 0.4, 0, 0)
        self.api.ejecutar_comando("CREATE_STRUCT", "S2", "H3", "H4")
        self.api.ejecutar_comando("TRANSFORM_STRUCT", "S2", "ROTATE", "z", "90")
        pos3 = self.api.memory.get_position("H3")
        pos4 = self.api.memory.get_position("H4")
        self.assertAlmostEqual(pos3[0], 0.0, places=6)
        self.assertAlmostEqual(pos3[1], 0.2, places=6)
        self.assertAlmostEqual(pos4[0], 0.0, places=6)
        self.assertAlmostEqual(pos4[1], 0.4, places=6)

    def test_scale_structure(self):
        self.api.ejecutar_comando("ALLOCATE", "H5", 0.1, 0.1, 0.1)
        self.api.ejecutar_comando("ALLOCATE", "H6", 0.2, 0.2, 0.2)
        self.api.ejecutar_comando("CREATE_STRUCT", "S3", "H5", "H6")
        self.api.ejecutar_comando("TRANSFORM_STRUCT", "S3", "SCALE", "2")
        pos5 = self.api.memory.get_position("H5")
        pos6 = self.api.memory.get_position("H6")
        self.assertEqual(pos5, (0.2, 0.2, 0.2))
        self.assertEqual(pos6, (0.4, 0.4, 0.4))


if __name__ == "__main__":
    unittest.main()
