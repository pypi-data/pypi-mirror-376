import re
from ultracompress_module import simple_compress, simple_decompress

SAMPLE_OBJ = {"hello": "world", "nums": [1,1,1,2,2,3,3,3], "nested": {"a":1, "b":2}}
SAMPLE_TEXT = '{"a":1,"b":[1,2,3]}'

def test_simple_roundtrip_object_markers_hex():
    block = simple_compress(SAMPLE_OBJ, mode='fast', preserve_order=True, include_hex=True, markers=True)
    assert 'B64_START' in block and 'HEX_START' in block
    restored = simple_decompress(block, return_text=False)
    assert restored == SAMPLE_OBJ


def test_simple_roundtrip_object_no_markers_no_hex():
    block = simple_compress(SAMPLE_OBJ, markers=False, include_hex=False, header=False)
    # Should be just base64 (single line)
    assert '\n' in block  # may end with newline
    b64_line = block.strip()
    assert re.match(r'^[A-Za-z0-9+/=]+$', b64_line)
    restored = simple_decompress(block, return_text=False)
    assert restored == SAMPLE_OBJ


def test_simple_roundtrip_wrapped_lines():
    block = simple_compress(SAMPLE_OBJ, markers=False, include_hex=False, line_width=8)
    # Multiple lines of base64
    lines = [l for l in block.splitlines() if l]
    assert len(lines) > 1
    restored = simple_decompress(block)
    assert restored == SAMPLE_OBJ


def test_simple_roundtrip_text_preserve():
    block = simple_compress(SAMPLE_TEXT, markers=False, include_hex=False, header=False)
    restored_text = simple_decompress(block, return_text=True)
    assert restored_text == SAMPLE_TEXT
    # object mode parse
    restored_obj = simple_decompress(block, return_text=False)
    import json
    assert restored_obj == json.loads(SAMPLE_TEXT)
