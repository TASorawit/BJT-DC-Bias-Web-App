import unittest
from app import app

VALID = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70"}


class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_shows_form(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"VCC", r.data)
        self.assertIn(b'name="r1"', r.data)

    def test_post_valid_returns_reference_results(self):
        r = self.client.post("/calculate", data=VALID)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"8.052", r.data)          # VCE
        self.assertIn(b"1.230", r.data)          # IC in mA
        self.assertIn(b"Forward-Active", r.data)

    def test_post_non_numeric_shows_error(self):
        r = self.client.post("/calculate", data={**VALID, "r1": "abc"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_blank_field_shows_error(self):
        r = self.client.post("/calculate", data={**VALID, "vcc": ""})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_omitted_field_shows_error(self):
        partial = dict(VALID); del partial["rc"]
        r = self.client.post("/calculate", data=partial)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"must be a number", r.data)

    def test_post_cutoff_shows_warning(self):
        r = self.client.post("/calculate", data={**VALID, "r2": "1"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Cutoff", r.data)


if __name__ == "__main__":
    unittest.main()
