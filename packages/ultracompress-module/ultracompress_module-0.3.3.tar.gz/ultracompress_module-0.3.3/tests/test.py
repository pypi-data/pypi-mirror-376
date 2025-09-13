from ultracompress_module import auto_compress, auto_decompress, describe_blob
import json

data = {"users": [{"id": i, "name": f"u{i}"} for i in range(10)]}

print("=== OBJECT MODE ===")
meta = auto_compress(data, mode='aggressive')
print("Original -> Compressed:", meta.original_len, "->", meta.compressed_len)
print("Blob preview:", describe_blob(meta.blob))
restored = auto_decompress(meta.blob, return_text=False)
print("Restored object:", restored)
assert restored == data

print("\n=== TEXT MODE ===")
json_text = '{"a":1,"b":[1,2,3]}'
meta_text = auto_compress(json_text, mode='fast')
print("Original -> Compressed:", meta_text.original_len, "->", meta_text.compressed_len)
print("Blob preview:", describe_blob(meta_text.blob))
restored_txt = auto_decompress(meta_text.blob, return_text=True)
print("Restored text:", restored_txt)
assert restored_txt == json_text

# Si tu veux voir l’objet décodé depuis le blob texte:
parsed_obj = auto_decompress(meta_text.blob, return_text=False)
print("Parsed object from text blob:", parsed_obj)