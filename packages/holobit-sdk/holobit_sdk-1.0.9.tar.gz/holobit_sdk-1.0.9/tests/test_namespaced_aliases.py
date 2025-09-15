import unittest
from holobit_sdk.assembler import macros


class TestNamespacedAliases(unittest.TestCase):
    def setUp(self):
        macros.aliases.clear()

    def test_namespaced_alias(self):
        macros.register_alias("alto::ROTAR", "ROT")
        self.assertEqual(macros.resolve_alias("alto::ROTAR"), "ROT")
        self.assertEqual(macros.resolve_alias("ROTAR"), "ROTAR")
        self.assertEqual(macros.resolve_alias("bajo::ROTAR"), "bajo::ROTAR")


if __name__ == "__main__":
    unittest.main()
