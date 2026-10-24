import unittest
from scripts.ufc_market_residual_audit import residual_audit

class TestResidual(unittest.TestCase):
    def test_small_sample_rejected(self):
        with self.assertRaises(ValueError):
            residual_audit([])

if __name__ == '__main__':
    unittest.main()
