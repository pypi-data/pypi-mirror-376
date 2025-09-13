import json, subprocess, sys, os, tempfile, pathlib
from ultracompress_module import compress_object

PY = sys.executable

def test_cli_inspect_structured():
    data = {"a":1, "b":[1,2,3], "c": {"k": "v"}}
    blob = compress_object(data, mode='fast')
    with tempfile.TemporaryDirectory() as td:
        uc_path = os.path.join(td, 'sample.uc')
        with open(uc_path, 'wb') as f:
            f.write(blob)
        # Run CLI inspect
        proc = subprocess.run([PY, '-m', 'ultracompress_module.ultrajson_pro', 'inspect', uc_path], capture_output=True, text=True, timeout=10)
        assert proc.returncode == 0, proc.stderr
        out = proc.stdout
        assert 'Total bytes:' in out
        assert 'Structured decode: OK' in out or 'Text decode: OK' in out
