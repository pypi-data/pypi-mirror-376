import json, unittest
from ultracompress_module import auto_compress, auto_decompress

class TestAutoDecompressFallback(unittest.TestCase):
    def test_text_blob_as_object(self):
        # Create a blob produced in text-preserve mode
        obj = {"a":1,"b":[1,2,3],"c":{"d":4}}
        text = json.dumps(obj, separators=(',',':'))
        meta = auto_compress(text, mode='fast')  # preserve_text=True inside auto
        # Ask for object recovery (return_text=False) -> should fallback gracefully
        recovered = auto_decompress(meta.blob, return_text=False)
        self.assertEqual(recovered, obj)

if __name__ == '__main__':
    unittest.main()
