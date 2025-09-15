import unittest
import math
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestMathFunctions(unittest.TestCase):
    def setUp(self):
        self.compiler = HoloLangCompiler()

    def test_eval_trigonometric_functions(self):
        res_sin = self.compiler._eval_expr("sin(PI / 2)")
        res_cos = self.compiler._eval_expr("cos(PI)")
        self.assertAlmostEqual(res_sin, math.sin(math.pi / 2))
        self.assertAlmostEqual(res_cos, math.cos(math.pi))


if __name__ == "__main__":
    unittest.main()
