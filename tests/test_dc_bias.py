import unittest
from dc_bias import analyze_dc_bias, BiasError

REF = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)


class TestReferenceValues(unittest.TestCase):
    def test_reference_operating_point(self):
        r = analyze_dc_bias(**REF)
        self.assertAlmostEqual(r["vth"], 2.1639, places=3)
        self.assertAlmostEqual(r["rth"], 18032.79, places=1)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.2986, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.2422, places=3)
        self.assertAlmostEqual(r["vb"], 1.9422, places=3)
        self.assertAlmostEqual(r["ve"], 1.2422, places=3)
        self.assertAlmostEqual(r["vc"], 9.2943, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)
        self.assertEqual(r["region"], "forward-active")
        self.assertEqual(r["warnings"], [])

    def test_cutoff_region(self):
        r = analyze_dc_bias(**{**REF, "r2": 1_000.0})   # VTH = 0.1188 V <= VBE
        self.assertEqual(r["region"], "cutoff")
        self.assertEqual((r["ib"], r["ic"], r["ie"]), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(r["vc"], 12.0, places=6)
        self.assertTrue(any("Cutoff" in w for w in r["warnings"]))

    def test_saturation_region(self):
        r = analyze_dc_bias(**{**REF, "rc": 47_000.0})   # VCE goes very negative
        self.assertEqual(r["region"], "saturation")
        self.assertTrue(any("Saturation" in w for w in r["warnings"]))

    def test_vth_equals_vbe_boundary_is_cutoff(self):
        r = analyze_dc_bias(vcc=7.0, r1=90_000.0, r2=10_000.0, rc=2_200.0,
                            re=1_000.0, beta=100.0, vbe=0.70)  # VTH = 0.7 exactly
        self.assertEqual(r["region"], "cutoff")

    def test_large_beta_computes(self):
        r = analyze_dc_bias(**{**REF, "beta": 10_000.0})
        self.assertEqual(r["region"], "forward-active")
        self.assertGreater(r["vce"], 0.2)


class TestValidation(unittest.TestCase):
    def test_non_positive_inputs_raise(self):
        for field, value in [("vcc", 0.0), ("vcc", -5.0), ("r1", 0.0), ("r2", -1.0),
                             ("rc", 0.0), ("re", -2.0), ("beta", 0.0), ("beta", -3.0)]:
            with self.assertRaises(BiasError, msg=field):
                analyze_dc_bias(**{**REF, field: value})

    def test_non_numeric_raises(self):
        with self.assertRaises(BiasError):
            analyze_dc_bias(**{**REF, "vcc": "twelve"})


if __name__ == "__main__":
    unittest.main()
