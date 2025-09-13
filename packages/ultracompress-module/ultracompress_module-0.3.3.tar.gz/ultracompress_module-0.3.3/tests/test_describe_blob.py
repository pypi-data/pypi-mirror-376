import unittest, json
from ultracompress_module import auto_compress, describe_blob

class TestDescribeBlob(unittest.TestCase):
    def test_structured_blob(self):
        obj = {"k": [i for i in range(20)], "s": "hello"}
        meta = auto_compress(obj, mode='fast')
        info = describe_blob(meta.blob)
        self.assertIn('size', info)
        self.assertIn('head_hex', info)
        self.assertTrue(info['size'] > 0)
        self.assertIsNotNone(info['looks_structured'])

    def test_text_blob(self):
        text = json.dumps({"x":1,"y":[1,2,3]})
        meta = auto_compress(text, mode='fast')
        info = describe_blob(meta.blob)
        self.assertIn('base64', info)
        self.assertTrue(info['text_roundtrip_ok'])

if __name__ == '__main__':
    unittest.main()
