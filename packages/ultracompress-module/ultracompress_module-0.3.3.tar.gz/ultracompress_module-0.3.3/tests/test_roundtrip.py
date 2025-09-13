import json
import unittest
from ultracompress_module import compress_object, decompress_bytes, compress_text

CASES_STRUCT = [
    {"name": "simple", "obj": {"a":1,"b":[1,2,3,4],"c":"hello"}},
    {"name": "numeric_long", "obj": {"nums": list(range(0,2000))}},
    {"name": "zigzag_signed", "obj": {"vals": [(-1)**i * (i//3) for i in range(2500)]}},
    {"name": "strings_prefix", "obj": {"words": [f"alpha_beta_gamma_{i}" for i in range(600)]}},
    {"name": "columns_like", "obj": {"rows": [{"id":i,"cat":"c"+str(i%5),"val":(i%11)-5} for i in range(800)]}},
]

class TestRoundTrip(unittest.TestCase):
    def test_structured_modes(self):
        for case in CASES_STRUCT:
            obj = case['obj']
            blobs = {}
            for mode in ('fast','aggressive','ultra'):
                b = compress_object(obj, mode=mode)
                r = decompress_bytes(b, preserve_text=False)
                self.assertEqual(r, obj, f"Mismatch in {case['name']} mode={mode}")
                blobs[mode] = len(b)
            # sanity: ultra should not exceed fast
            self.assertLessEqual(blobs['ultra'], blobs['fast'])

    def test_text_preserve(self):
        text = json.dumps({"arr": list(range(500))})
        for mode in ('fast','aggressive','ultra'):
            b = compress_text(text, preserve_text=True, mode=mode)
            r = decompress_bytes(b, preserve_text=True)
            self.assertEqual(r, text)

if __name__ == '__main__':
    unittest.main()
