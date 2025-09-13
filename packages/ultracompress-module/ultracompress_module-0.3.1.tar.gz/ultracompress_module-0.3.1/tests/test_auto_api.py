import json, os, tempfile
import unittest
from ultracompress_module import auto_compress, auto_decompress

SAMPLE_OBJ = {"a":1,"b":[1,2,3],"c":{"x":10,"y":"hello"}}
SAMPLE_TEXT = json.dumps(SAMPLE_OBJ, separators=(",",":"))

class TestAutoAPI(unittest.TestCase):
    def test_auto_object(self):
        meta = auto_compress(SAMPLE_OBJ, mode='fast')
        self.assertTrue(meta.compressed_len < meta.original_len)
        restored = auto_decompress(meta.blob, return_text=False)
        self.assertEqual(restored, SAMPLE_OBJ)

    def test_auto_text(self):
        meta = auto_compress(SAMPLE_TEXT, mode='fast')
        restored_text = auto_decompress(meta.blob, return_text=True)
        self.assertEqual(restored_text, SAMPLE_TEXT)

    def test_auto_file_structured(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, 'data.json')
            with open(p,'w',encoding='utf-8') as f: f.write(SAMPLE_TEXT)
            meta = auto_compress(p, mode='fast')  # default force_structured True
            restored = auto_decompress(meta.blob, return_text=False)
            self.assertEqual(restored, SAMPLE_OBJ)

if __name__ == '__main__':
    unittest.main()
