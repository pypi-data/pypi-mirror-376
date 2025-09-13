import unittest, json
from ultracompress_module import compress_object, decompress_bytes, benchmark_ratio

OBJ = {
    'numbers': list(range(200)),
    'repeat': ['x']*50 + ['y']*40 + ['z']*30,
    'nested': {'a': [1,2,3,4,5], 'b': list(range(10,30))},
}

class TestDeltaAndBenchmark(unittest.TestCase):
    def test_roundtrip_structured(self):
        blob = compress_object(OBJ, preproc_opts={'maps': False, 'delta': True, 'mtf': False, 'rle': True})
        restored = decompress_bytes(blob, preserve_text=False)
        self.assertEqual(restored, OBJ)

    def test_benchmark_improvement(self):
        ratios = benchmark_ratio(OBJ, structured=True)
        self.assertLessEqual(ratios['aggressive_bytes'], ratios['fast_bytes'])

if __name__ == '__main__':
    unittest.main()
