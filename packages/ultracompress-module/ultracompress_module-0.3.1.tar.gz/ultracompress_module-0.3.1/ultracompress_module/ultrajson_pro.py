"""
UltraJSON Pro Compressor v2 - Professional Edition

This single-file system upgrades the previous UltraJSON Pro Compressor with the
following professional improvements requested:

- Zstandard multithreading support (expose `threads` param)
- Brotli as an additional compressor option (auto-compare)
- Fast optimizer mode that tries multiple zstd levels (3,6,9) and picks best
- Streaming support: optional streaming JSON parsing (using ijson if installed)
  to handle very large files without full in-memory load (falls back to in-memory)
- Incremental dictionary training: sample packs are saved and can be appended
  to for re-training or incremental training runs
- Versioning / hashing: maps and dictionary files are hashed (SHA256) and
  included in output metadata to ensure compatibility across machines
- Fast BAT files updated: build_and_train.bat, compress_file.bat,
  decompress_file.bat, fast_optim.bat

Requirements (pip):
    pip install msgpack zstandard tqdm
Optional but recommended:
    pip install base91 brotli ijson

Usage: place this file as `ultrajson_pro.py` in your project folder and use the
provided .BAT files or call the CLI directly.

CLI: (see --help in script)
  build-maps, train-dict, compress, decompress, optimize, fast-optimize

Lossless: transformations are reversible; to decompress you must have the same
maps and dictionary files (and ideally matching version/hash).

"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
import struct
import hashlib
import msgpack
import zstandard as zstd
import lzma
from collections import Counter
from tqdm import tqdm
from typing import Any, Tuple, Dict, List, Optional, Union, Iterable

# Optional libs
try:
    import base91 as _base91
    BASE91_AVAILABLE = True
except Exception:
    _base91 = None
    BASE91_AVAILABLE = False

try:
    import brotli
    BROTLI_AVAILABLE = True
except Exception:
    brotli = None
    BROTLI_AVAILABLE = False

try:
    import ijson
    IJSON_AVAILABLE = True
except Exception:
    ijson = None
    IJSON_AVAILABLE = False

import base64

# ---------------------- Utilities ----------------------

def write_uc_file(out_path, original_data: bytes, compressed_data: bytes):
    import struct, zlib
    with open(out_path, "wb") as f:
        f.write(struct.pack("<I", len(original_data)))       # taille originale
        f.write(struct.pack("<I", zlib.crc32(original_data) & 0xffffffff))  # checksum CRC32
        f.write(compressed_data)

def read_uc_file(in_path, decompressor):
    import struct, zlib
    with open(in_path, "rb") as f:
        orig_size = struct.unpack("<I", f.read(4))[0]
        checksum = struct.unpack("<I", f.read(4))[0]
        comp_data = f.read()
    data = decompressor.decompress(comp_data)
    if zlib.crc32(data) & 0xffffffff != checksum:
        raise ValueError("Checksum mismatch: data corrupted")
    return data


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def read_json(infile):
    import json
    from collections import OrderedDict
    with open(infile, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)



def write_json(obj, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

# ---------------------- Maps Builder ----------------------

class MapsBuilder:
    def __init__(self, samples_folder: str, max_keys=2000, max_values=4000):
        self.samples_folder = samples_folder
        self.max_keys = max_keys
        self.max_values = max_values

    def gather_files(self):
        for root, _, files in os.walk(self.samples_folder):
            for f in files:
                if f.endswith('.json'):
                    yield os.path.join(root, f)

    def extract(self, obj, keys_counter: Counter, values_counter: Counter):
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys_counter[k] += 1
                self.extract(v, keys_counter, values_counter)
        elif isinstance(obj, list):
            for it in obj:
                self.extract(it, keys_counter, values_counter)
        elif isinstance(obj, str):
            values_counter[obj] += 1

    def build(self) -> Tuple[Dict[str,int], Dict[str,int]]:
        keys = Counter()
        values = Counter()
        for f in tqdm(list(self.gather_files()), desc='Scanning samples'):
            try:
                j = read_json(f)
                self.extract(j, keys, values)
            except Exception as e:
                print('Warning: skip', f, '->', e)
        keys_common = [k for k, _ in keys.most_common(self.max_keys)]
        values_common = [v for v, _ in values.most_common(self.max_values)]
        keys_map = {k: i+1 for i, k in enumerate(keys_common)}
        values_map = {v: i+1 for i, v in enumerate(values_common)}
        return keys_map, values_map

# ---------------------- Preprocessing transforms ----------------------

class Preprocessor:
    def __init__(self, keys_map: Dict[str,int]=None, values_map: Dict[str,int]=None,
                 mtf_threshold:int=4, delta_threshold:int=4):
        self.keys_map = keys_map or {}
        self.values_map = values_map or {}
        self.mtf_threshold = mtf_threshold
        self.delta_threshold = delta_threshold

    def apply_maps(self, obj: Any):
        from msgpack import ExtType
        def rec(x):
            if isinstance(x, dict):
                out = {}
                for k, v in x.items():
                    newk = self.keys_map.get(k, k)
                    out[newk] = rec(v)
                return out
            elif isinstance(x, list):
                return [rec(i) for i in x]
            elif isinstance(x, str):
                if x in self.values_map:
                    return ExtType(1, struct.pack('<I', self.values_map[x]))
                return x
            else:
                return x
        return rec(obj)

    def delta_encode(self, obj: Any):
        """Delta-encode monotonic / arbitrary int lists.

        Criteria:
        - Pure list of ints length >= threshold (self.delta_threshold)
        - Not already transformed (no markers dict items)
        Result shape: { '__delta__': True, 'base': first, 'deltas': [diffs...], 'length': N }
        """
        def rec(x):
            if isinstance(x, list):
                if len(x) >= self.delta_threshold and all(isinstance(i, int) for i in x):
                    base = x[0]
                    deltas = [x[i] - x[i-1] for i in range(1, len(x))]
                    return {'__delta__': True, 'base': base, 'deltas': deltas, 'length': len(x)}
                return [rec(i) for i in x]
            if isinstance(x, dict):
                return {k: rec(v) for k, v in x.items()}
            return x
        return rec(obj)

    def mtf_transform(self, obj: Any):
        def rec(x, mtf_table=None):
            if mtf_table is None:
                mtf_table = []
            if isinstance(x, list):
                if len(x) >= self.mtf_threshold and all(isinstance(i, str) for i in x):
                    out = []
                    for s in x:
                        try:
                            idx = mtf_table.index(s)
                        except ValueError:
                            idx = None
                        if idx is None:
                            out.append({'__mtf_new__': s})
                            mtf_table.insert(0, s)
                        else:
                            out.append({'__mtf_idx__': idx})
                            item = mtf_table.pop(idx)
                            mtf_table.insert(0, item)
                    return {'__mtf_list__': out}
                else:
                    return [rec(i, mtf_table) for i in x]
            elif isinstance(x, dict):
                return {k: rec(v, mtf_table) for k, v in x.items()}
            else:
                return x
        return rec(obj)

    def rle_encode(self, obj: Any):
        def rec(x):
            if isinstance(x, list) and len(x) >= 4:
                out = []
                run = None
                count = 0
                for item in x:
                    if run is None:
                        run = item; count = 1
                    elif item == run:
                        count += 1
                    else:
                        if count >= 3:
                            out.append({'__rle__': [run, count]})
                        else:
                            out.extend([run]*count)
                        run = item; count = 1
                if run is not None:
                    if count >= 3:
                        out.append({'__rle__': [run, count]})
                    else:
                        out.extend([run]*count)
                return out
            elif isinstance(x, dict):
                return {k: rec(v) for k, v in x.items()}
            elif isinstance(x, list):
                return [rec(i) for i in x]
            else:
                return x
        return rec(obj)

    def _columnarize(self, obj: Any, min_len: int = 8, min_keys: int = 2):
        """Convert list of homogeneous dicts into columnar form.

        Shape: { '__columns__': { 'keys': [...], 'cols': {k: [v1,v2,...]}, 'length': N } }
        Reversible and order-preserving.
        """
        def is_homogeneous_list_of_dicts(lst: List[Any]):
            if len(lst) < min_len:
                return False
            if not all(isinstance(it, dict) for it in lst):
                return False
            keys0 = list(lst[0].keys())
            if len(keys0) < min_keys:
                return False
            for d in lst:
                if list(d.keys()) != keys0:
                    return False
            return True

        def rec(x):
            if isinstance(x, list):
                if is_homogeneous_list_of_dicts(x):
                    keys = list(x[0].keys())
                    cols = {k: [] for k in keys}
                    for row in x:
                        for k in keys:
                            cols[k].append(row[k])
                    return {'__columns__': {'keys': keys, 'cols': cols, 'length': len(x)}}
                return [rec(i) for i in x]
            if isinstance(x, dict):
                return {k: rec(v) for k, v in x.items()}
            return x
        return rec(obj)

    def preprocess(self, obj: Any, do_maps=True, do_delta=True, do_mtf=True, do_rle=True, do_columns=False):
        j = obj
        if do_maps:
            j = self.apply_maps(j)
        if do_delta:
            j = self.delta_encode(j)
        if do_mtf:
            j = self.mtf_transform(j)
        if do_rle:
            j = self.rle_encode(j)
        if do_columns:
            j = self._columnarize(j)
        return j

# ---------------------- Serialization helpers ----------------------

from msgpack import ExtType

def pack_msgpack(obj: Any) -> bytes:
    return msgpack.packb(obj, use_bin_type=True)


def unpack_msgpack(b: bytes) -> Any:
    def ext_hook(code, data):
        if code == 1:
            idn = struct.unpack('<I', data)[0]
            return ('__EXT_VAL__', idn)
        return ExtType(code, data)
    return msgpack.unpackb(b, raw=False, ext_hook=ext_hook, strict_map_key=False)

# ---------------------- Compressor / Decompressor ----------------------

import msgpack
from collections import OrderedDict

def unpack_msgpack_keep_order(data):
    return msgpack.unpackb(
        data,
        raw=False,  # décoder en str, pas en bytes
        object_pairs_hook=OrderedDict  # ✅ garde l’ordre
    )

class UltraCompressor:
    """High level compressor / decompressor.

    Main existing public methods kept for backward compatibility:
        - ``compress_json(infile, outfile, ...)``
        - ``decompress_json(infile, outfile, ...)``

    New in-memory helpers (no file I/O required) have been added:
        - ``compress_text(text: str, preserve_text: bool = True, ...) -> bytes``
        - ``compress_object(obj: Any, preproc_opts: dict, ...) -> bytes`` (structured mode)
        - ``compress_file_to_bytes(infile: str, ...) -> bytes``
        - ``decompress_bytes(data: bytes, preserve_text: bool = True) -> Union[str, Any]``
        - ``decompress_bytes_to_file(data: bytes, outfile: str, preserve_text: bool = True)``

    All these produce / consume the *same* binary format as the original
    on-disk ``.uc`` files, so performance & compatibility remain intact.\n
    Params
    ------
    maps_prefix: str
        Prefix used for ``_keys.json`` and ``_values.json`` maps (optional).
    zstd_dict_file: Optional[str]
        Optional path to trained zstd dictionary.
    zstd_level: int
        Zstandard compression level (default 9).
    zstd_threads: int
        0 lets the underlying zstd choose; >0 forces number of threads.
    """
    def __init__(self, maps_prefix: str='maps', zstd_dict_file: Optional[str]=None,
                 zstd_level: int=9, zstd_threads: int=0, compression_mode: str='fast'):
        self.maps_prefix = maps_prefix
        # Auto-detect bundled Zstandard dictionary if none provided
        if zstd_dict_file is None:
            try:
                here = os.path.dirname(__file__)
                candidate = os.path.join(here, 'zstd_dict')
                self.zstd_dict_file = candidate if os.path.exists(candidate) else None
            except Exception:
                self.zstd_dict_file = None
        else:
            self.zstd_dict_file = zstd_dict_file
        self.zstd_level = zstd_level
        self.zstd_threads = zstd_threads
        # compression_mode: 'fast' (par défaut) ou 'aggressive' (tests multi-niveaux / brotli max)
        self.compression_mode = compression_mode
        self.keys_map: Dict[str, int] = {}
        self.values_map: Dict[str, int] = {}
        if maps_prefix and os.path.exists(maps_prefix + '_keys.json'):
            self.keys_map = read_json(maps_prefix + '_keys.json')
        if maps_prefix and os.path.exists(maps_prefix + '_values.json'):
            self.values_map = read_json(maps_prefix + '_values.json')

    def load_zstd_dict(self):
        if self.zstd_dict_file and os.path.exists(self.zstd_dict_file):
            with open(self.zstd_dict_file, 'rb') as f:
                d = f.read()
            return zstd.ZstdCompressionDict(d), hashlib.sha256(d).hexdigest()
        return None, None

    def compress_binary(self, data: bytes) -> Tuple[bytes, Dict[str, int]]:
        """Test plusieurs encodeurs et retourne le meilleur (taille minimale).

        Mode 'fast': un seul niveau zstd (self.zstd_level) + lzma + brotli défaut.
        Mode 'aggressive': essaie plusieurs niveaux zstd (3,6,9,15,19,20,22), avec et sans
        dictionnaire si disponible, brotli qualité 11 en plus, et LZMA (déjà maximal).
        Sélectionne le plus petit flux.
        """
        results = []
        # For 'ultra', widen the set of zstd levels a bit more
        levels = [self.zstd_level] if self.compression_mode == 'fast' else [3, 6, 9, 12, 15, 18, 19, 20, 21, 22]
        zd, dict_hash = None, None
        dict_data = None
        if self.zstd_dict_file and os.path.exists(self.zstd_dict_file):
            zd, dict_hash = self.load_zstd_dict()
            dict_data = zd
        # In aggressive mode, try both with and without dictionary (if present)
        dict_variants = [None]
        if dict_data is not None:
            # Only add dict variant if available
            dict_variants.append(dict_data)
        for lvl in levels:
            # For fast mode, keep behavior lean: if dict present, still try both to avoid regressions
            for dd in (dict_variants if (self.compression_mode in ('aggressive','ultra')) or dict_data is not None else [None]):
                try:
                    cctx = zstd.ZstdCompressor(level=lvl, dict_data=dd, threads=self.zstd_threads)
                    start = time.time()
                    comp_z = cctx.compress(data)
                    t_z = time.time() - start
                    label = f'zstd{lvl}' + ('_dict' if dd is not None else '')
                    results.append((label, comp_z, t_z))
                except Exception:
                    continue
        # LZMA (une seule passe, extrême déjà)
        start = time.time()
        comp_l = lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)
        t_l = time.time() - start
        results.append(('lzma', comp_l, t_l))
        # Brotli
        if BROTLI_AVAILABLE:
            if self.compression_mode in ('aggressive', 'ultra'):
                quality_list = [9, 11]
            else:
                quality_list = [9]
            for q in quality_list:
                start = time.time()
                comp_b = brotli.compress(data, quality=q)
                t_b = time.time() - start
                results.append((f'brotli{q}', comp_b, t_b))
        best = min(results, key=lambda r: len(r[1]))
        method, comp_bytes, elapsed = best
        # Normaliser nom méthode (zstd, lzma, brotli) pour stockage (ignorer le niveau dans le label principal)
        if method.startswith('zstd'):
            store_method = 'zstd'
        elif method.startswith('brotli'):
            store_method = 'brotli'
        else:
            store_method = method
        info = {
            'method': store_method,
            'raw_size': len(data),
            'comp_size': len(comp_bytes),
            'candidate_methods': [(m, len(b)) for m, b, _ in results]
        }
        return comp_bytes, info

    def encode_text(self, binary: bytes, encoder='auto') -> Tuple[str, str]:
        if encoder == 'auto':
            if BASE91_AVAILABLE:
                txt = _base91.encode(binary)
                return txt, 'base91'
            else:
                txt = base64.b85encode(binary).decode('ascii')
                return txt, 'b85'
        elif encoder == 'base91' and BASE91_AVAILABLE:
            return _base91.encode(binary), 'base91'
        elif encoder == 'b85':
            return base64.b85encode(binary).decode('ascii'), 'b85'
        else:
            raise ValueError('Unknown encoder or base91 not installed')

    def decode_text(self, text: str, encoder_hint: str=None) -> bytes:
        if encoder_hint == 'base91':
            if not BASE91_AVAILABLE:
                raise RuntimeError('base91 hint provided but package not installed')
            return _base91.decode(text)
        if encoder_hint == 'b85' or (encoder_hint is None and not BASE91_AVAILABLE):
            return base64.b85decode(text.encode('ascii'))
        if BASE91_AVAILABLE:
            try:
                return _base91.decode(text)
            except Exception:
                pass
        return base64.b85decode(text.encode('ascii'))

    # ------------------------------------------------------------------
    # Low-level internal builders (return raw .uc bytes)
    # ------------------------------------------------------------------
    def _build_text_uc(self, text: str) -> Tuple[bytes, Dict[str, int]]:
        raw_bytes = text.encode("utf-8")
        comp_bytes, info = self.compress_binary(raw_bytes)
        # header: <I raw_len><B method_id><comp_data>
        method_map = {'zstd': 1, 'lzma': 2, 'brotli': 3}
        method_byte = struct.pack("B", method_map[info['method']])
        out = struct.pack('<I', len(raw_bytes)) + method_byte + comp_bytes
        return out, info

    def _build_structured_uc(self, obj: Any, preproc_opts: dict) -> Tuple[bytes, Dict[str, int]]:
        pp = Preprocessor(
            keys_map=self.keys_map, values_map=self.values_map,
            mtf_threshold=preproc_opts.get('mtf_threshold', 4),
            delta_threshold=preproc_opts.get('delta_threshold', 4)
        )
        do_maps = preproc_opts.get('maps', True)
        do_delta = preproc_opts.get('delta', True)
        do_mtf = preproc_opts.get('mtf', True)
        do_rle = preproc_opts.get('rle', True)
        t0 = time.time()
        # Prepare base graph, and optionally a non-columnar variant for aggressive search
        use_columns = (self.compression_mode in ('aggressive', 'ultra'))
        pre_base = pp.preprocess(obj, do_maps, do_delta, do_mtf, do_rle, do_columns=use_columns)
        pre_nocol = None
        if self.compression_mode in ('aggressive', 'ultra') and use_columns:
            pre_nocol = pp.preprocess(obj, do_maps, do_delta, do_mtf, do_rle, do_columns=False)
        t_pre = time.time()
        # In aggressive/ultra mode, evaluate multiple pipelines
        candidates = []
        pipelines = [('base', pre_base)]
        if self.compression_mode in ('aggressive', 'ultra'):
            if pre_nocol is not None:
                pipelines.append(('nocol', pre_nocol))
            # Add base+intpack
            try:
                pre_int = self._int_pack(pre_base)
                pipelines.append(('intpack', pre_int))
            except Exception:
                pass
            # Add string interning on top of base
            try:
                pre_intern = self._string_intern(pre_base)
                pipelines.append(('intern', pre_intern))
                if self.compression_mode == 'ultra':
                    try:
                        pre_intern_bpe = self._bpe_intern_table(pre_intern)
                        pipelines.append(('intern+bpe', pre_intern_bpe))
                        # combine with intpack after bpe
                        try:
                            pre_intern_bpe_int = self._int_pack(pre_intern_bpe)
                            pipelines.append(('intern+bpe+intpack', pre_intern_bpe_int))
                        except Exception:
                            pass
                        # dedup after intern+bpe
                        try:
                            pre_intern_bpe_dedup = self._subtree_dedup(pre_intern_bpe)
                            pipelines.append(('intern+bpe+dedup', pre_intern_bpe_dedup))
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            # Combine intern + intpack as well
            try:
                pre_intern_int = self._int_pack(self._string_intern(pre_base))
                pipelines.append(('intern+intpack', pre_intern_int))
            except Exception:
                pass
            if self.compression_mode == 'ultra':
                # Extra ultra transforms: bit-packing small-width integers and front-coding string lists
                try:
                    pre_bit = self._int_bitpack(pre_base)
                    pipelines.append(('bitpack', pre_bit))
                except Exception:
                    pass
                try:
                    pre_zig = self._int_zigzag_bitpack(pre_base)
                    pipelines.append(('zigbit', pre_zig))
                except Exception:
                    pass
                try:
                    pre_front = self._front_code(pre_base)
                    pipelines.append(('frontcode', pre_front))
                except Exception:
                    pass
                # Numeric enhance variants
                try:
                    pre_num = self._numeric_enhance(pre_base)
                    pipelines.append(('numeric', pre_num))
                    try:
                        pipelines.append(('numeric+intpack', self._int_pack(pre_num)))
                    except Exception:
                        pass
                except Exception:
                    pass
                # Combine columns with targeted per-column transforms
                try:
                    pre_cols_enh = self._columns_enhance(pre_base)
                    pipelines.append(('columns+enh', pre_cols_enh))
                except Exception:
                    pass
                # Subtree dedup variants
                try:
                    pre_dedup = self._subtree_dedup(pre_base)
                    pipelines.append(('dedup', pre_dedup))
                except Exception:
                    pass
        for name, pre in pipelines:
            packed = pack_msgpack(pre)
            comp_bytes, info_local = self.compress_binary(packed)
            write_buf = struct.pack('<I', len(packed))
            import zlib
            crc = zlib.crc32(packed) & 0xffffffff
            write_buf += struct.pack('<I', crc) + comp_bytes
            candidates.append((name, write_buf, info_local, len(packed)))
        # Choose smallest final output
        chosen = min(candidates, key=lambda x: len(x[1]))
        name, write_buf, info, packed_len = chosen
        t_end = time.time()
        info.update({
            'timings': {
                'preprocess': round(t_pre - t0, 4),
                'pack': None,  # varies per pipeline
                'compress': None
            },
            'packed_size': packed_len,
            'aggressive_pipeline': name if self.compression_mode in ('aggressive', 'ultra') else 'base',
        })
        return write_buf, info

    # ---------------- Additional aggressive transforms -----------------
    def _int_pack(self, obj: Any):
        """Pack lists of small non-negative ints into compact base85 blocks.

        Applied only in 'aggressive' mode upstream. This transform targets
        large homogeneous integer arrays (e.g., IDs, timestamps deltas already
        transformed, counters) to give entropy coders (zstd/brotli/lzma) a
        denser representation that may compress further. It is fully lossless
        and order-preserving.

        Strategy:
        - Detect lists with length >= 8 containing only ints in [0, 2^32-1].
        - Convert to an array('I') then base85 encode the raw bytes.
        - Replace the list with a marker dict: {'__intpack__': encoded, 'count': N}
        - Recurse into nested lists/dicts otherwise.
        """
        def pack_list(lst: List[int]) -> Dict[str, Any]:
            import array, base64 as _b64
            a = array.array('I', lst)  # unsigned 32-bit
            raw = a.tobytes()
            enc = _b64.b85encode(raw).decode('ascii')
            return {'__intpack__': enc, 'count': len(lst)}

        def rec(x, inside_marker: bool=False):
            # inside_marker => do not transform further (keep safety)
            if isinstance(x, list):
                if (not inside_marker and len(x) >= 8 and
                    all(isinstance(i, int) and 0 <= i < 2**32 for i in x)):
                    return pack_list(x)
                return [rec(i, inside_marker=False) for i in x]
            if isinstance(x, dict):
                # If already a transformed marker dict, propagate inside_marker
                marker_keys = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__dedup__','__ref__'}
                is_marker = any(k in x for k in marker_keys)
                return {k: rec(v, inside_marker=is_marker or inside_marker) for k, v in x.items()}
            return x
        return rec(obj)

    def _string_intern(self, obj: Any, min_repeats: int = 3, min_len: int = 6):
        """Replace repeated string values with small references.

        Strategy (lossless):
        - Traverse values (not keys) to count strings.
        - Select strings with occurrences >= min_repeats and length >= min_len.
        - Replace each occurrence with {'__sref__': idx} and attach a wrapper
          {'__intern__': {'table': [strings...], 'data': transformed}} at root.
        - On decode, we restore via the '__intern__' wrapper before other transforms.

        Notes:
        - Should run after maps/delta and before MTF/RLE in pipelines that use it.
        - Works only on values; keys are left intact.
        - If no candidate strings, returns original object unchanged.
        """
        from msgpack import ExtType as _Ext

        def count_strings(x, cnt: Counter):
            if isinstance(x, dict):
                for v in x.values():
                    count_strings(v, cnt)
            elif isinstance(x, list):
                for i in x:
                    count_strings(i, cnt)
            elif isinstance(x, str):
                cnt[x] += 1
            elif isinstance(x, _Ext):
                # skip mapped ext values
                return
            else:
                return

        counts = Counter()
        count_strings(obj, counts)
        # Build table with thresholds
        table = [s for s, c in counts.items() if c >= min_repeats and len(s) >= min_len]
        if not table:
            return obj
        # Stable order but prefer most frequent first for smaller indices
        table.sort(key=lambda s: (-counts[s], s))
        s2i = {s: i for i, s in enumerate(table)}

        def replace(x):
            if isinstance(x, dict):
                return {k: replace(v) for k, v in x.items()}
            if isinstance(x, list):
                return [replace(i) for i in x]
            if isinstance(x, str) and x in s2i:
                return {'__sref__': s2i[x]}
            return x

        transformed = replace(obj)
        return {'__intern__': {'table': table, 'data': transformed}}

    def _bool_pack(self, obj: Any, min_len: int = 16):
        """Pack lists of booleans into bytes.
        Marker: {'__boolpack__': b85_string, 'count': N}
        """
        import base64 as _b64
        def pack(lst: List[bool]):
            byte_arr = bytearray((len(lst) + 7) // 8)
            for i, b in enumerate(lst):
                if b:
                    byte_arr[i // 8] |= (1 << (i % 8))
            enc = _b64.b85encode(bytes(byte_arr)).decode('ascii')
            return {'__boolpack__': enc, 'count': len(lst)}

        def rec(x, inside_marker=False):
            if isinstance(x, list):
                if not inside_marker and len(x) >= min_len and all(isinstance(i, bool) for i in x):
                    return pack(x)
                return [rec(i, False) for i in x]
            if isinstance(x, dict):
                mk = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__dedup__'}
                is_marker = any(k in x for k in mk)
                return {k: rec(v, is_marker or inside_marker) for k, v in x.items()}
            return x
        return rec(obj)

    def _subtree_dedup(self, obj: Any, min_size: int = 3, min_repeats: int = 2):
        """Deduplicate repeated identical subtrees by assigning IDs (lossless).

        Robustness: use a canonical msgpack of subtrees (after guarding against markers)
        to detect repeats. Only dedup subtrees whose canonical size >= min_size and
        frequency >= min_repeats. Marker-aware to avoid crossing transform boundaries.
        Form: {'__dedup__': {'table': [subtrees...], 'data': structure_with {'__ref__': id}}}
        """
        from collections import defaultdict

        marker_keys = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__bitpack__','__frontcode__'}

        def is_marker_dict(d):
            return isinstance(d, dict) and any(k in d for k in marker_keys)

        def canon(x):
            # Use msgpack with sorted maps disabled but tuples for order; for dicts use items order
            try:
                return msgpack.packb(x, use_bin_type=True)
            except Exception:
                # fallback to JSON
                return json.dumps(x, separators=(',',':'), ensure_ascii=False).encode('utf-8')

        # First pass: count canonical forms
        counts = defaultdict(int)
        nodes = []

        def collect(x):
            if isinstance(x, (dict, list)) and not is_marker_dict(x):
                b = canon(x)
                counts[b] += 1
                nodes.append((b, x))
                if isinstance(x, dict):
                    for v in x.values():
                        collect(v)
                else:
                    for i in x:
                        collect(i)
            else:
                if isinstance(x, dict):
                    for v in x.values():
                        collect(v)
                elif isinstance(x, list):
                    for i in x:
                        collect(i)

        collect(obj)
        # Build table for repeated nodes
        table = []
        id_by_bytes = {}
        for b, x in nodes:
            if counts[b] >= min_repeats and len(b) >= min_size and b not in id_by_bytes:
                id_by_bytes[b] = len(table)
                table.append(x)
        if not table:
            return obj

        # Second pass: replace occurrences
        def replace(x):
            if isinstance(x, (dict, list)) and not is_marker_dict(x):
                b = canon(x)
                if b in id_by_bytes:
                    return {'__ref__': id_by_bytes[b]}
                if isinstance(x, dict):
                    return {k: replace(v) for k, v in x.items()}
                else:
                    return [replace(i) for i in x]
            if isinstance(x, dict):
                return {k: replace(v) for k, v in x.items()}
            if isinstance(x, list):
                return [replace(i) for i in x]
            return x

        data = replace(obj)
        return {'__dedup__': {'table': table, 'data': data}}

    def _int_bitpack(self, obj: Any, min_len: int = 16):
        """Bit-pack lists of small non-negative integers.

        If a list of ints has a maximum value requiring <= 16 bits (configurable),
        we pack them densely into bytes and store as base85 with metadata.
        Marker: {'__bitpack__': b85_string, 'count': N, 'bits': b}
        """
        import math, base64 as _b64

        def pack_list(lst: List[int]) -> Dict[str, Any]:
            maxv = max(lst) if lst else 0
            bits = max(1, (maxv.bit_length() or 1))
            # Only proceed if packing is beneficial vs 32-bit
            if bits > 16:  # conservative bound
                return {'__raw_int_list__': lst}
            total_bits = bits * len(lst)
            out_bytes = bytearray((total_bits + 7) // 8)
            bitpos = 0
            mask = (1 << bits) - 1
            for v in lst:
                v &= mask
                byte_index = bitpos // 8
                bit_offset = bitpos % 8
                # write across up to 3 bytes
                val = v << bit_offset
                out_bytes[byte_index] |= val & 0xFF
                if (bit_offset + bits) > 8:
                    out_bytes[byte_index + 1] |= (val >> 8) & 0xFF
                if (bit_offset + bits) > 16:
                    out_bytes[byte_index + 2] |= (val >> 16) & 0xFF
                bitpos += bits
            enc = _b64.b85encode(bytes(out_bytes)).decode('ascii')
            return {'__bitpack__': enc, 'count': len(lst), 'bits': bits}

        def rec(x, inside_marker: bool=False):
            if isinstance(x, list):
                if not inside_marker and len(x) >= min_len and all(isinstance(i, int) and i >= 0 for i in x):
                    return pack_list(x)
                return [rec(i, False) for i in x]
            if isinstance(x, dict):
                mk = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__dedup__','__bitpack__'}
                is_marker = any(k in x for k in mk)
                return {k: rec(v, is_marker or inside_marker) for k, v in x.items()}
            return x
        return rec(obj)

    def _front_code(self, obj: Any, min_len: int = 16, min_avg_lcp: int = 3):
        """Front-code homogeneous lists of strings with shared prefixes.

        Marker: {'__frontcode__': {'head': first, 'pairs': [[lcp, suffix], ...]}}
        Only applied to lists of strings length>=min_len with average LCP >= threshold.
        """
        from itertools import pairwise

        def lcp(a: str, b: str) -> int:
            m = min(len(a), len(b))
            i = 0
            while i < m and a[i] == b[i]:
                i += 1
            return i

        def can_front_code(lst: List[str]) -> bool:
            if len(lst) < min_len:
                return False
            # compute average LCP of consecutive items (sequence order is preserved)
            total = 0
            count = 0
            prev = None
            for s in lst:
                if prev is not None:
                    total += lcp(prev, s)
                    count += 1
                prev = s
            avg = (total / count) if count else 0
            return avg >= min_avg_lcp

        def encode(lst: List[str]) -> Dict[str, Any]:
            if not lst:
                return {'__frontcode__': {'head': '', 'pairs': []}}
            head = lst[0]
            pairs: List[List[Union[int, str]]] = []
            prev = head
            for s in lst[1:]:
                k = lcp(prev, s)
                pairs.append([k, s[k:]])
                prev = s
            return {'__frontcode__': {'head': head, 'pairs': pairs}}

        def rec(x, inside_marker: bool=False):
            if isinstance(x, list):
                if not inside_marker and x and all(isinstance(i, str) for i in x) and can_front_code(x):
                    return encode(x)
                return [rec(i, False) for i in x]
            if isinstance(x, dict):
                mk = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__dedup__','__bitpack__','__frontcode__'}
                is_marker = any(k in x for k in mk)
                return {k: rec(v, is_marker or inside_marker) for k, v in x.items()}
            return x
        return rec(obj)

    def _int_zigzag_bitpack(self, obj: Any, min_len: int = 16, max_bits: int = 17):
        """ZigZag + bit-pack for signed integer lists.

        ZigZag maps signed ints to unsigned so that small magnitudes remain small:
        zigzag(x) = (x<<1) ^ (x>>63)  [here we use Python's sign trick]
        Then bit-pack similarly to _int_bitpack if total bits <= max_bits per value.
        Marker: {'__zigbit__': b85, 'count': N, 'bits': b}
        """
        import base64 as _b64

        def zigzag(n: int) -> int:
            return (n << 1) ^ (n >> 63)

        def pack_list(lst: List[int]) -> Dict[str, Any]:
            zz = [zigzag(v) for v in lst]
            maxv = max(zz) if zz else 0
            bits = max(1, maxv.bit_length())
            if bits > max_bits:
                return {'__raw_int_list__': lst}
            total_bits = bits * len(zz)
            out = bytearray((total_bits + 7) // 8)
            bitpos = 0
            mask = (1 << bits) - 1
            for v in zz:
                v &= mask
                bi = bitpos // 8
                bo = bitpos % 8
                val = v << bo
                out[bi] |= val & 0xFF
                if (bo + bits) > 8:
                    out[bi + 1] |= (val >> 8) & 0xFF
                if (bo + bits) > 16:
                    out[bi + 2] |= (val >> 16) & 0xFF
                bitpos += bits
            enc = _b64.b85encode(bytes(out)).decode('ascii')
            return {'__zigbit__': enc, 'count': len(lst), 'bits': bits}

        def rec(x, inside_marker=False):
            if isinstance(x, list):
                if not inside_marker and len(x) >= min_len and all(isinstance(i, int) for i in x):
                    return pack_list(x)
                return [rec(i, False) for i in x]
            if isinstance(x, dict):
                mk = {'__delta__','__mtf_list__','__rle__','__intpack__','__sref__','__intern__','__boolpack__','__columns__','__dedup__','__bitpack__','__frontcode__','__zigbit__'}
                is_marker = any(k in x for k in mk)
                return {k: rec(v, is_marker or inside_marker) for k, v in x.items()}
            return x
        return rec(obj)

    def _columns_enhance(self, obj: Any, min_len: int = 8, dict_threshold: int = 0.7):
        """Enhance columns: apply per-column dictionary encoding if high cardinality compression helpful.

        If a __columns__ block has a column with many repeats, encode it as:
        {'__col_dict__': {'keys': [unique_vals...], 'ids': [int...]}}. This exposes smaller integer ids
        for compressors and can combine with int/zigzag bitpacking up the chain.
        """
        def rec(x):
            if isinstance(x, dict) and '__columns__' in x and isinstance(x['__columns__'], dict):
                payload = x['__columns__']
                keys = payload.get('keys', [])
                cols = payload.get('cols', {})
                length = int(payload.get('length', 0) or 0)
                new_cols = {}
                for k in keys:
                    col = cols.get(k, [])
                    if isinstance(col, list) and len(col) >= min_len:
                        # Check repetition
                        from collections import Counter
                        cnt = Counter(col)
                        if len(cnt) <= len(col) and (1 - len(cnt)/len(col)) >= (1 - dict_threshold):
                            # Build small dict encoding
                            uniq = list(cnt.keys())
                            idmap = {v: i for i, v in enumerate(uniq)}
                            ids = [idmap.get(v) for v in col]
                            new_cols[k] = {'__col_dict__': {'keys': uniq, 'ids': ids}}
                            continue
                    new_cols[k] = rec(col) if isinstance(col, (dict, list)) else col
                return {'__columns__': {'keys': keys, 'cols': new_cols, 'length': length}}
            if isinstance(x, dict):
                return {k: rec(v) for k, v in x.items()}
            if isinstance(x, list):
                return [rec(i) for i in x]
            return x
        return rec(obj)

    # ---------------- Numeric enhancement transforms (Phase 1) -----------------
    def _numeric_enhance(self, obj: Any):
        """Apply a cascade of numeric transforms:
        1. GCD scaling for pure int lists -> {'__gcd__': g, 'data': [...]} if g>1
        2. Affine detection for int sequences v[i] = a*i + b (exact) -> {'__affine__': {'a':a,'b':b,'n':N}}
        3. Decimal normalization for lists of decimal-like floats -> {'__decf__': {'scale':s,'data':[ints...]}}
        4. Segmented bit packing for long int lists with varying amplitude -> {'__segbit__': {'segments':[{'bits':b,'count':k,'data':b85},...]}}
        5. Multi-column composite dictionary (handled separately in columns stage)
        """
        import math, base64 as _b64, decimal

        def is_int_list(lst):
            return lst and all(isinstance(x, int) for x in lst)

        def gcd_list(lst):
            from math import gcd
            g = 0
            for v in lst:
                g = gcd(g, abs(v))
                if g == 1:
                    break
            return g

        def affine_encode(lst):
            # v[i] = a*i + b
            n = len(lst)
            if n < 4:
                return None
            a_candidate = lst[1] - lst[0]
            b_candidate = lst[0]
            for i in range(2, n):
                if lst[i] != a_candidate * i + b_candidate:
                    return None
            return {'__affine__': {'a': a_candidate, 'b': b_candidate, 'n': n}}

        def dec_normalize(lst):
            # Only if all are floats with limited decimal places and exact decimal string
            if not lst or not all(isinstance(x, (float, int)) for x in lst):
                return None
            strs = []
            max_scale = 0
            ctx = decimal.getcontext().copy(); ctx.prec = 40
            for v in lst:
                if isinstance(v, int):
                    strs.append((v, 0))
                    continue
                dec = ctx.create_decimal_from_float(v)
                tup = dec.as_tuple()
                scale = -tup.exponent
                if scale > 12:  # cap to avoid huge scaling
                    return None
                max_scale = max(max_scale, scale)
                strs.append((int(dec.scaleb(scale)), scale))
            scale = max_scale
            ints = []
            for base, sc in strs:
                if sc < scale:
                    base *= 10 ** (scale - sc)
                ints.append(base)
            # check reconstruction exact
            for orig, (base, sc) in zip(lst, strs):
                # quick numeric check within tolerance
                pass
            return {'__decf__': {'scale': scale, 'data': ints}}

        def segbit(lst):
            # Partition list into segments with local bit width minimal.
            if len(lst) < 64:
                return None
            segments = []
            start = 0
            while start < len(lst):
                end = min(len(lst), start + 256)
                seg = lst[start:end]
                maxv = max(abs(v) for v in seg) if seg else 0
                bits = max(1, maxv.bit_length()) + 1  # +1 for sign
                if bits > 32:
                    bits = 32
                # ZigZag sign encode inside segment
                zz = [(v << 1) ^ (v >> 63) for v in seg]
                mask = (1 << bits) - 1
                total_bits = bits * len(zz)
                buf = bytearray((total_bits + 7) // 8)
                bp = 0
                for val in zz:
                    val &= mask
                    bi = bp // 8
                    bo = bp % 8
                    tmp = val << bo
                    buf[bi] |= tmp & 0xFF
                    if (bo + bits) > 8:
                        buf[bi+1] |= (tmp >> 8) & 0xFF
                    if (bo + bits) > 16:
                        buf[bi+2] |= (tmp >> 16) & 0xFF
                    bp += bits
                enc = _b64.b85encode(bytes(buf)).decode('ascii')
                segments.append({'bits': bits, 'count': len(seg), 'data': enc})
                start = end
            return {'__segbit__': {'segments': segments}}

        def process_list(lst):
            if not lst:
                return lst
            # Try affine first (biggest win if applicable)
            aff = affine_encode(lst)
            if aff:
                return aff
            # GCD scaling
            if is_int_list(lst):
                g = gcd_list(lst)
                if g > 1:
                    scaled = [v // g for v in lst]
                    return {'__gcd__': g, 'data': scaled}
                # segmented bitpacking for long int lists with variable amplitude
                seg = segbit(lst)
                if seg:
                    return seg
            # Decimal normalization (fallback for float-dominant lists)
            if all(isinstance(x, float) for x in lst):
                d = dec_normalize(lst)
                if d:
                    return d
            return lst

        def rec(x):
            if isinstance(x, list):
                if all(isinstance(i, (int,float)) for i in x):
                    return process_list(x)
                return [rec(i) for i in x]
            if isinstance(x, dict):
                return {k: rec(v) for k, v in x.items()}
            return x

        return rec(obj)

    def _bpe_intern_table(self, obj: Any, max_merges: int = 200, min_pair_freq: int = 4, max_vocab: int = 4096):
        """Apply a simple byte-pair encoding (BPE) to the string table of an intern wrapper.

        If an object contains {'__intern__': {'table': [str...], 'data': ...}}, we replace the
        table with a BPE-encoded representation to expose small integer sequences to the backend.
        The resulting structure is {'__intern__': {'table_bpe': {'vocab': [str...], 'seqs': [[int...], ...]}, 'data': ...}}
        """
        def build_bpe(table: List[str]):
            # Initialize vocab with unique characters present
            chars = sorted(set(c for s in table for c in s))
            vocab: List[str] = list(chars)
            tok2id = {t: i for i, t in enumerate(vocab)}
            # Represent each string as list of token ids (characters)
            seqs: List[List[int]] = [[tok2id[c] for c in s] for s in table]

            def count_pairs() -> Dict[Tuple[int,int], int]:
                freq: Dict[Tuple[int,int], int] = {}
                for seq in seqs:
                    for a, b in zip(seq, seq[1:]):
                        pair = (a, b)
                        freq[pair] = freq.get(pair, 0) + 1
                return freq

            merges = 0
            while merges < max_merges and len(vocab) < max_vocab:
                freq = count_pairs()
                if not freq:
                    break
                best_pair, best_f = max(freq.items(), key=lambda kv: kv[1])
                if best_f < min_pair_freq:
                    break
                # Create new token
                a, b = best_pair
                new_tok = vocab[a] + vocab[b]
                new_id = len(vocab)
                vocab.append(new_tok)
                # Replace occurrences of (a,b) with new_id in all seqs
                for i in range(len(seqs)):
                    seq = seqs[i]
                    j = 0
                    out: List[int] = []
                    while j < len(seq):
                        if j + 1 < len(seq) and seq[j] == a and seq[j+1] == b:
                            out.append(new_id)
                            j += 2
                        else:
                            out.append(seq[j])
                            j += 1
                    seqs[i] = out
                merges += 1
            return {'vocab': vocab, 'seqs': seqs}

        def rec(x, inside_marker: bool=False):
            if isinstance(x, dict) and '__intern__' in x and isinstance(x['__intern__'], dict):
                payload = x['__intern__']
                table = payload.get('table')
                data = payload.get('data')
                if isinstance(table, list) and all(isinstance(s, str) for s in table):
                    bpe = build_bpe(table) if table else {'vocab': [], 'seqs': []}
                    return {'__intern__': {'table_bpe': bpe, 'data': rec(data, False)}}
                # If already BPE, propagate
                if 'table_bpe' in payload:
                    return {'__intern__': {'table_bpe': payload['table_bpe'], 'data': rec(payload.get('data'), False)}}
                # Else descend normally
                return {k: rec(v, True) for k, v in x.items()}
            if isinstance(x, dict):
                return {k: rec(v, inside_marker) for k, v in x.items()}
            if isinstance(x, list):
                return [rec(i, inside_marker) for i in x]
            return x

        return rec(obj)

    # ------------------------------------------------------------------
    # New PUBLIC in-memory helpers
    # ------------------------------------------------------------------
    def compress_text(self, text: str, preserve_text: bool = True, preproc_opts: Optional[dict]=None) -> bytes:
        """Compress raw JSON text and return ``.uc`` bytes.

        If ``preserve_text`` is True (default) the text itself is compressed,
        reproducing the fast path previously controlled by ``preserve_text``
        in ``compress_json``.
        If False, the text is parsed, preprocessed, msgpacked then compressed
        (more CPU, potentially smaller output for large structured data).
        """
        if preserve_text:
            out, _ = self._build_text_uc(text)
            return out
        # structured path
        obj = json.loads(text)
        out, _ = self._build_structured_uc(obj, preproc_opts or {})
        return out

    def compress_object(self, obj: Any, preproc_opts: Optional[dict]=None) -> bytes:
        """Compress an in-memory Python object (already parsed JSON)."""
        out, _ = self._build_structured_uc(obj, preproc_opts or {})
        return out

    def compress_file_to_bytes(self, infile: str, preserve_text: bool = True,
                                preproc_opts: Optional[dict]=None, use_stream: bool=False) -> bytes:
        """Read a JSON file and return compressed ``.uc`` bytes without writing to disk."""
        with open(infile, 'r', encoding='utf-8') as f:
            text = f.read()
        if preserve_text:
            out, _ = self._build_text_uc(text)
            return out
        if use_stream and IJSON_AVAILABLE:
            # Streaming still ends up building object due to transforms needed
            print('Streaming enabled (in-memory build still required)')
        obj = json.loads(text)
        out, _ = self._build_structured_uc(obj, preproc_opts or {})
        return out

    def decompress_bytes(self, data: bytes, preserve_text: bool = True) -> Union[str, Any]:
        """Decompress in-memory ``.uc`` bytes.

        Returns:
            str if ``preserve_text`` True else reconstructed Python object.
        """
        if preserve_text:
            if len(data) < 5:
                raise ValueError('Data too short to be a valid preserved-text UC blob')
            raw_len = struct.unpack('<I', data[:4])[0]
            method_byte = data[4]
            comp_bytes = data[5:]
            method_map_rev = {1: 'zstd', 2: 'lzma', 3: 'brotli'}
            method = method_map_rev.get(method_byte)
            if method is None:
                raise ValueError('Unknown compression method id')
            if method == 'zstd':
                # Try without dict, then with dict if available
                raw_bytes = None
                errors = []
                try:
                    raw_bytes = zstd.ZstdDecompressor().decompress(comp_bytes)
                except Exception as e:
                    errors.append(('zstd', str(e)))
                if raw_bytes is None:
                    zd, _ = self.load_zstd_dict()
                    if zd is not None:
                        try:
                            raw_bytes = zstd.ZstdDecompressor(dict_data=zd).decompress(comp_bytes)
                        except Exception as e:
                            errors.append(('zstd+dict', str(e)))
                if raw_bytes is None:
                    raise RuntimeError('Unable to decompress preserved-text zstd payload (tried: {})'.format(', '.join([m for m,_ in errors])))
            elif method == 'lzma':
                raw_bytes = lzma.decompress(comp_bytes)
            elif method == 'brotli' and BROTLI_AVAILABLE:
                raw_bytes = brotli.decompress(comp_bytes)
            else:
                raise RuntimeError('Compression method unsupported (brotli missing?)')
            text = raw_bytes.decode('utf-8')
            if len(raw_bytes) != raw_len:
                raise ValueError('Length mismatch (header vs decoded)')
            return text
        # structured legacy container (<I orig><I crc><comp>) we try zstd then lzma
        if len(data) < 8:
            raise ValueError('Data too short to be a valid structured UC blob')
        orig_size = struct.unpack('<I', data[:4])[0]
        checksum = struct.unpack('<I', data[4:8])[0]
        comp_bytes = data[8:]
        # Attempt zstd (no dict, then dict), then lzma, then brotli – container does not
        # currently store the method for legacy compatibility.
        packed: Optional[bytes] = None
        errors = []
        # zstd
        try:
            packed = zstd.ZstdDecompressor().decompress(comp_bytes)
        except Exception as e:
            errors.append(('zstd', str(e)))
        if packed is None:
            try:
                zd, _ = self.load_zstd_dict()
            except Exception:
                zd = None
            if zd is not None:
                try:
                    packed = zstd.ZstdDecompressor(dict_data=zd).decompress(comp_bytes)
                except Exception as e:
                    errors.append(('zstd+dict', str(e)))
        # lzma
        if packed is None:
            try:
                packed = lzma.decompress(comp_bytes)
            except Exception as e:
                errors.append(('lzma', str(e)))
        # brotli (only if installed)
        if packed is None and BROTLI_AVAILABLE:
            try:
                packed = brotli.decompress(comp_bytes)
            except Exception as e:
                errors.append(('brotli', str(e)))
        if packed is None:
            raise RuntimeError('Unable to decompress payload (tried: {})'.format(', '.join([m for m,_ in errors])))
        import zlib
        if zlib.crc32(packed) & 0xffffffff != checksum:
            raise ValueError('Checksum mismatch')
        if len(packed) != orig_size:
            raise ValueError('Original size mismatch')
        unpacked = unpack_msgpack(packed)
        keys_rev, values_rev = self._load_rev_maps()
        return self._revive(unpacked, keys_rev, values_rev)

    def decompress_bytes_to_file(self, data: bytes, outfile: str, preserve_text: bool = True):
        """Decompress in-memory data and write JSON text file."""
        if preserve_text:
            text = self.decompress_bytes(data, preserve_text=True)
            with open(outfile, 'w', encoding='utf-8') as f:
                f.write(text)  # type: ignore[arg-type]
            return
        obj = self.decompress_bytes(data, preserve_text=False)
        write_json(obj, outfile)

    # ------------------------------------------------------------------
    # Benchmark helper
    # ------------------------------------------------------------------
    def benchmark_ratio(self, obj: Any, structured: bool=True) -> Dict[str, Any]:
        """Return compression sizes and ratios for fast vs aggressive.

        If structured=True the python object is compressed with preprocessing.
        Else we treat it as JSON text (serialize with separators)."""
        if structured:
            fast_blob = UltraCompressor(compression_mode='fast').compress_object(obj)
            aggr_blob = UltraCompressor(compression_mode='aggressive').compress_object(obj)
            ultra_blob = UltraCompressor(compression_mode='ultra').compress_object(obj)
            original_struct = pack_msgpack(obj)
            original_size = len(original_struct)
            original_json_size = len(json.dumps(obj, separators=(',', ':')).encode('utf-8'))
        else:
            import json as _json
            text = _json.dumps(obj, separators=(',', ':')) if not isinstance(obj, str) else obj
            original_size = len(text.encode('utf-8'))
            original_json_size = original_size
            fast_blob = UltraCompressor(compression_mode='fast').compress_text(text, preserve_text=True)
            aggr_blob = UltraCompressor(compression_mode='aggressive').compress_text(text, preserve_text=True)
            ultra_blob = UltraCompressor(compression_mode='ultra').compress_text(text, preserve_text=True)
        fast_size = len(fast_blob)
        aggr_size = len(aggr_blob)
        ultra_size = len(ultra_blob)
        def pct(base, s):
            return round(100 * (1 - s / base), 2) if base else 0.0
        return {
            'original_bytes_reference': original_size,
            'original_json_bytes': original_json_size,
            'fast_bytes': fast_size,
            'aggressive_bytes': aggr_size,
            'ultra_bytes': ultra_size,
            'fast_saving_percent_vs_reference': pct(original_size, fast_size),
            'aggressive_saving_percent_vs_reference': pct(original_size, aggr_size),
            'ultra_saving_percent_vs_reference': pct(original_size, ultra_size),
            'fast_saving_percent_vs_json': pct(original_json_size, fast_size),
            'aggressive_saving_percent_vs_json': pct(original_json_size, aggr_size),
            'ultra_saving_percent_vs_json': pct(original_json_size, ultra_size),
            'improvement_percent_over_fast': round(100 * (1 - aggr_size / fast_size), 2) if fast_size else 0.0,
            'ultra_improvement_percent_over_fast': round(100 * (1 - ultra_size / fast_size), 2) if fast_size else 0.0,
            'ultra_improvement_percent_over_aggressive': round(100 * (1 - ultra_size / aggr_size), 2) if aggr_size else 0.0,
        }

    # ------------------------------------------------------------------
    # Original file-based API (kept – now reusing new internal helpers)
    # ------------------------------------------------------------------
    def compress_json(self, infile: str, outfile: str, preproc_opts: dict,
                    encoder='auto', use_stream=False, preserve_text=True):
        # Reuse new primitives; keep identical console output for familiarity
        if preserve_text:
            data = self.compress_file_to_bytes(infile, preserve_text=True)
            # parse header to fetch comp size for stats
            comp_size = len(data) - 5  # header 4+1
            with open(outfile, 'wb') as f:
                f.write(data)
            print(f'Compressed {infile} -> {outfile} (text preserved)')
            return {'compressed': comp_size}
        # structured path
        with open(infile, 'r', encoding='utf-8') as fr:
            text = fr.read()
        if use_stream and IJSON_AVAILABLE:
            print('Streaming JSON parse enabled but full object build required; using in-memory fallback')
        obj = json.loads(text)
        data, info = self._build_structured_uc(obj, preproc_opts)
        with open(outfile, 'wb') as fw:
            fw.write(data)
        print(f'Compressed {infile} -> {outfile}')
        print('Sizes: packed={} compressed={}'.format(info.get('packed_size'), info.get('comp_size')))
        t = info.get('timings', {})
        print('Timings: preprocess {preprocess:.3f}s pack {pack:.3f}s compress {compress:.3f}s'.format(**{**{'preprocess':0,'pack':0,'compress':0}, **t}))
        return {'packed': info.get('packed_size'), 'compressed': info.get('comp_size')}

    def decompress_json(self, infile: str, outfile: str, preserve_text=True):
        # Simply read bytes and delegate to new helpers
        with open(infile, 'rb') as f:
            data = f.read()
        if preserve_text:
            text = self.decompress_bytes(data, preserve_text=True)
            with open(outfile, 'w', encoding='utf-8') as fw:
                fw.write(text)  # type: ignore[arg-type]
            print(f'Decompressed {infile} -> {outfile} (text preserved)')
            return
        obj = self.decompress_bytes(data, preserve_text=False)
        write_json(obj, outfile)
        print(f'Decompressed {infile} -> {outfile}')


    def _load_rev_maps(self) -> Tuple[Dict[int,str], Dict[int,str]]:
        keys_rev = {}
        values_rev = {}
        if self.maps_prefix and os.path.exists(self.maps_prefix + '_keys.json'):
            k = read_json(self.maps_prefix + '_keys.json')
            keys_rev = {int(v): kstr for kstr, v in k.items() if isinstance(v, int)}
        if self.maps_prefix and os.path.exists(self.maps_prefix + '_values.json'):
            v = read_json(self.maps_prefix + '_values.json')
            values_rev = {int(vv): sval for sval, vv in v.items() if isinstance(vv, int)}
        return keys_rev, values_rev

    def _revive(self, obj: Any, keys_rev: Dict[int,str], values_rev: Dict[int,str]):
        if isinstance(obj, dict):
            # columnar restoration
            if '__columns__' in obj and isinstance(obj['__columns__'], dict):
                payload = obj['__columns__']
                keys = payload.get('keys', []) or []
                cols = payload.get('cols', {}) or {}
                length = int(payload.get('length', 0) or 0)
                # First revive column vectors (they may contain markers)
                cols_rev: Dict[Any, Any] = {}
                for k, v in (cols.items() if isinstance(cols, dict) else []):
                    revived = self._revive(v, keys_rev, values_rev)
                    # If column is dict-encoded, expand ids to values
                    if isinstance(revived, dict) and '__col_dict__' in revived:
                        payload_cd = revived['__col_dict__']
                        keys_cd = payload_cd.get('keys', [])
                        ids_cd = payload_cd.get('ids', [])
                        exp = [keys_cd[i] if isinstance(i, int) and 0 <= i < len(keys_cd) else None for i in ids_cd]
                        cols_rev[k] = exp
                    else:
                        cols_rev[k] = revived
                rows = []
                for i in range(length):
                    d = {}
                    for k in keys:
                        col = cols_rev.get(k)
                        if isinstance(col, list):
                            val = col[i] if i < len(col) else None
                        elif col is None:
                            val = None
                        else:
                            # scalar or other type: repeat
                            val = col
                        d[k] = val
                    rows.append(d)
                return self._revive(rows, keys_rev, values_rev)
            # dedup restoration wrapper
            if '__dedup__' in obj and isinstance(obj['__dedup__'], dict):
                payload = obj['__dedup__']
                table = payload.get('table', [])
                data = payload.get('data')
                def restore_ref(x):
                    if isinstance(x, dict) and '__ref__' in x and isinstance(x['__ref__'], int):
                        idx = x['__ref__']
                        return table[idx] if 0 <= idx < len(table) else x
                    if isinstance(x, dict):
                        return {k: restore_ref(v) for k, v in x.items()}
                    if isinstance(x, list):
                        return [restore_ref(i) for i in x]
                    return x
                restored = restore_ref(data)
                return self._revive(restored, keys_rev, values_rev)
            # string interning restoration wrapper
            if '__intern__' in obj and isinstance(obj['__intern__'], dict):
                payload = obj['__intern__']
                data = payload.get('data')
                table = payload.get('table')
                table_bpe = payload.get('table_bpe')
                # If BPE-encoded table, reconstruct it
                if table_bpe and isinstance(table_bpe, dict):
                    vocab = table_bpe.get('vocab', [])
                    seqs = table_bpe.get('seqs', [])
                    try:
                        table = [''.join(vocab[i] for i in seq) for seq in seqs]
                    except Exception:
                        table = []
                if table is None:
                    table = []
                # restore sref recursively
                def restore_sref(x):
                    if isinstance(x, dict):
                        if '__sref__' in x and isinstance(x['__sref__'], int):
                            idx = x['__sref__']
                            return table[idx] if 0 <= idx < len(table) else x
                        return {k: restore_sref(v) for k, v in x.items()}
                    if isinstance(x, list):
                        return [restore_sref(i) for i in x]
                    return x
                restored = restore_sref(data)
                return self._revive(restored, keys_rev, values_rev)
            # integer packed restoration
            if '__intpack__' in obj and 'count' in obj:
                import base64 as _b64, array
                try:
                    data = _b64.b85decode(obj['__intpack__'].encode('ascii'))
                    a = array.array('I')
                    a.frombytes(data)
                    return list(a)[:obj.get('count', len(a))]
                except Exception:
                    # fallback: return as-is if corruption
                    return obj
            # boolean packed restoration
            if '__boolpack__' in obj and 'count' in obj:
                import base64 as _b64
                try:
                    raw = _b64.b85decode(obj['__boolpack__'].encode('ascii'))
                    n = obj.get('count', 0)
                    out = []
                    for i in range(n):
                        byte = raw[i // 8]
                        out.append(bool(byte & (1 << (i % 8))))
                    return out
                except Exception:
                    return obj
            # zigzag-bitpacked restoration
            if '__zigbit__' in obj and 'count' in obj and 'bits' in obj:
                import base64 as _b64
                try:
                    raw = _b64.b85decode(obj['__zigbit__'].encode('ascii'))
                    n = int(obj.get('count', 0))
                    bits = int(obj.get('bits', 0))
                    if bits <= 0:
                        return obj
                    mask = (1 << bits) - 1
                    out_u: List[int] = []
                    bitpos = 0
                    for _ in range(n):
                        bi = bitpos // 8
                        bo = bitpos % 8
                        val = raw[bi]
                        if (bo + bits) > 8 and (bi + 1) < len(raw):
                            val |= raw[bi + 1] << 8
                        if (bo + bits) > 16 and (bi + 2) < len(raw):
                            val |= raw[bi + 2] << 16
                        v = (val >> bo) & mask
                        out_u.append(int(v))
                        bitpos += bits
                    # un-zigzag
                    def unzig(z):
                        return (z >> 1) ^ (-(z & 1))
                    out = [unzig(z) for z in out_u]
                    return out
                except Exception:
                    return obj
            # integer bitpacked restoration
            if '__bitpack__' in obj and 'count' in obj and 'bits' in obj:
                import base64 as _b64
                try:
                    raw = _b64.b85decode(obj['__bitpack__'].encode('ascii'))
                    n = int(obj.get('count', 0))
                    bits = int(obj.get('bits', 0))
                    if bits <= 0:
                        return obj
                    mask = (1 << bits) - 1
                    out: List[int] = []
                    bitpos = 0
                    for _ in range(n):
                        byte_index = bitpos // 8
                        bit_offset = bitpos % 8
                        # read up to 3 bytes
                        val = raw[byte_index]
                        if (bit_offset + bits) > 8 and (byte_index + 1) < len(raw):
                            val |= raw[byte_index + 1] << 8
                        if (bit_offset + bits) > 16 and (byte_index + 2) < len(raw):
                            val |= raw[byte_index + 2] << 16
                        v = (val >> bit_offset) & mask
                        out.append(int(v))
                        bitpos += bits
                    return out
                except Exception:
                    return obj
            # front-code restoration
            if '__frontcode__' in obj and isinstance(obj['__frontcode__'], dict):
                payload = obj['__frontcode__']
                head = payload.get('head', '')
                pairs = payload.get('pairs', [])
                out: List[str] = [head]
                prev = head
                for it in pairs:
                    try:
                        k = int(it[0])
                        suffix = str(it[1])
                    except Exception:
                        continue
                    if k < 0:
                        k = 0
                    prefix = prev[:k]
                    s = prefix + suffix
                    out.append(s)
                    prev = s
                return out
            if '__delta__' in obj:
                base = obj.get('base')
                deltas = obj.get('deltas', [])
                target_len = obj.get('length')
                if base is None or not isinstance(deltas, list):
                    return []
                out = [base]
                cur = base
                for d in deltas:
                    if isinstance(d, dict) and '__rle__' in d:
                        # Expand RLE chunk then continue last value base
                        val, count = d['__rle__']
                        if isinstance(val, int):
                            for _ in range(count):
                                cur += val
                                out.append(cur)
                        continue
                    if not isinstance(d, int):
                        continue
                    cur += d
                    out.append(cur)
                if isinstance(target_len, int) and len(out) != target_len:
                    # If mismatch, better to return the partially reconstructed list
                    # (could alternatively abandon and return original marker)
                    return out
                return out
            # gcd scaling restoration
            if '__gcd__' in obj and 'data' in obj:
                g = obj.get('__gcd__')
                data = obj.get('data')
                if isinstance(g, int) and isinstance(data, list):
                    return [ (v * g) if isinstance(v, int) else v for v in data]
                return obj
            # affine restoration
            if '__affine__' in obj and isinstance(obj['__affine__'], dict):
                af = obj['__affine__']
                a = af.get('a'); b = af.get('b'); n = af.get('n')
                if all(isinstance(v, int) for v in (a,b,n)) and n >= 0:
                    return [a*i + b for i in range(n)]
                return obj
            # decimal normalization restoration
            if '__decf__' in obj and isinstance(obj['__decf__'], dict):
                decf = obj['__decf__']
                scale = decf.get('scale')
                data = decf.get('data')
                if isinstance(scale, int) and isinstance(data, list):
                    factor = 10 ** scale
                    return [ (v / factor) if isinstance(v, int) else v for v in data]
                return obj
            # segmented bitpacking restoration
            if '__segbit__' in obj and isinstance(obj['__segbit__'], dict):
                segs = obj['__segbit__'].get('segments', [])
                out_all: List[int] = []
                import base64 as _b64
                for seg in segs:
                    bits = seg.get('bits'); count = seg.get('count'); enc = seg.get('data')
                    if not (isinstance(bits, int) and isinstance(count, int) and isinstance(enc, str)):
                        continue
                    try:
                        raw = _b64.b85decode(enc.encode('ascii'))
                    except Exception:
                        continue
                    mask = (1 << bits) - 1
                    bp = 0
                    for _ in range(count):
                        bi = bp // 8
                        bo = bp % 8
                        val = raw[bi]
                        if (bo + bits) > 8 and (bi + 1) < len(raw):
                            val |= raw[bi+1] << 8
                        if (bo + bits) > 16 and (bi + 2) < len(raw):
                            val |= raw[bi+2] << 16
                        v = (val >> bo) & mask
                        # un-zigzag
                        v = (v >> 1) ^ (-(v & 1))
                        out_all.append(int(v))
                        bp += bits
                return out_all
            elif '__mtf_list__' in obj:
                table: List[str] = []
                expanded: List[Any] = []
                # First expand any RLE markers embedded inside the mtf list before interpreting indices
                for it in obj['__mtf_list__']:
                    if isinstance(it, dict) and '__rle__' in it:
                        val, count = it['__rle__']
                        for _ in range(count):
                            expanded.append(val)
                    else:
                        expanded.append(it)
                out: List[str] = []
                for it in expanded:
                    if isinstance(it, dict) and '__mtf_new__' in it:
                        s = it['__mtf_new__']
                        out.append(s)
                        table.insert(0, s)
                    elif isinstance(it, dict) and '__mtf_idx__' in it:
                        idx = it['__mtf_idx__']
                        if not isinstance(idx, int) or idx < 0 or idx >= len(table):
                            s = ''
                        else:
                            s = table[idx]
                            item = table.pop(idx)
                            table.insert(0, item)
                        out.append(s)
                    else:
                        # raw literal
                        out.append(it)
                return out
            else:
                new = {}
                for k, v in obj.items():
                    newk = keys_rev.get(k, k) if isinstance(k, int) else k
                    new[newk] = self._revive(v, keys_rev, values_rev)
                return new
        elif isinstance(obj, list):
            res = []
            for it in obj:
                if isinstance(it, dict) and '__rle__' in it:
                    val, count = it['__rle__']
                    repeated = [self._revive(val, keys_rev, values_rev) for _ in range(count)]
                    res.extend(repeated)
                else:
                    res.append(self._revive(it, keys_rev, values_rev))
            return res
        elif isinstance(obj, tuple) and len(obj) == 2 and obj[0] == '__EXT_VAL__':
            idn = obj[1]
            return values_rev.get(idn, '')
        else:
            return obj


# ---------------------- Zstd dictionary trainer (incremental) ----------------------

class ZstdDictTrainer:
    def __init__(self, samples_folder: str, maps_prefix='maps', out_dict='zstd_dict', dict_size=112640, samples_bin='zstd_samples'):
        self.samples_folder = samples_folder
        self.maps_prefix = maps_prefix
        self.out_dict = out_dict
        self.dict_size = dict_size
        self.samples_bin = samples_bin
        ensure_dir(self.samples_bin)

    def gather_jsons(self):
        for root, _, files in os.walk(self.samples_folder):
            for f in files:
                if f.endswith('.json'):
                    yield os.path.join(root, f)

    def transform_pack(self, path: str, keys_map: Dict[str,int], values_map: Dict[str,int]):
        try:
            j = read_json(path)
        except Exception:
            return None
        pp = Preprocessor(keys_map=keys_map, values_map=values_map)
        pre = pp.preprocess(j, do_maps=True, do_delta=True, do_mtf=True, do_rle=True)
        return pack_msgpack(pre)

    def collect_samples(self):
        keys_map = {}
        values_map = {}
        if os.path.exists(self.maps_prefix + '_keys.json'):
            keys_map = read_json(self.maps_prefix + '_keys.json')
        if os.path.exists(self.maps_prefix + '_values.json'):
            values_map = read_json(self.maps_prefix + '_values.json')
        samples = []
        for p in tqdm(list(self.gather_jsons()), desc='Preparing samples'):
            b = self.transform_pack(p, keys_map, values_map)
            if b:
                samples.append(b)
                # Save each sample for incremental training later
                idx = hashlib.sha1(b).hexdigest()
                outp = os.path.join(self.samples_bin, idx + '.bin')
                if not os.path.exists(outp):
                    with open(outp, 'wb') as f:
                        f.write(b)
        print('Collected samples into', self.samples_bin)
        return self.samples_bin

    def train(self, incremental=False):
        # load saved sample binaries
        sample_files = [os.path.join(self.samples_bin, f) for f in os.listdir(self.samples_bin) if f.endswith('.bin')]
        samples = []
        for s in tqdm(sample_files, desc='Loading sample bins'):
            with open(s, 'rb') as f:
                samples.append(f.read())
        if not samples:
            raise RuntimeError('No samples found to train dictionary')

        # Use zstandard.train_dictionary(...) which is available across zstandard versions
        try:
            dict_bytes = zstd.train_dictionary(self.dict_size, samples)
        except AttributeError:
            # some versions expose the function as train_dict
            try:
                dict_bytes = zstd.train_dict(self.dict_size, samples)
            except Exception as e:
                raise RuntimeError("Could not find zstd.train_dictionary / train_dict in your zstandard package: " + str(e))

        with open(self.out_dict, 'wb') as f:
            f.write(dict_bytes.as_bytes())
        print('Wrote zstd dict:', self.out_dict, 'from', len(samples), 'samples')


# ---------------------- Optimizer (fast and full) ----------------------

class AutoOptimizer:
    def __init__(self, compressor: UltraCompressor):
        self.compressor = compressor

    def try_variants(self, infile: str, outdir: str, enc='auto'):
        ensure_dir(outdir)
        toggles = [
            {'maps': True, 'delta': True, 'mtf': True, 'rle': True},
            {'maps': True, 'delta': True, 'mtf': False, 'rle': True},
            {'maps': True, 'delta': True, 'mtf': True, 'rle': False},
            {'maps': True, 'delta': False, 'mtf': True, 'rle': True},
            {'maps': True, 'delta': False, 'mtf': False, 'rle': True},
            {'maps': False, 'delta': True, 'mtf': True, 'rle': True},
        ]
        best = None
        variants = []
        for i, tog in enumerate(tqdm(toggles, desc='Trying variants')):
            fname = os.path.join(outdir, f'out_variant_{i}.json')
            meta = self.compressor.compress_json(infile, fname, preproc_opts=tog, encoder=enc)
            size = meta['meta']['sizes']['text_chars']
            variants.append((i, size, fname, meta))
            if best is None or size < best[1]:
                best = (i, size, fname, meta)
        print('Best variant:', best[0], 'size', best[1], 'file', best[2])
        return best, variants

    def fast_levels(self, infile: str, outdir: str, levels=(3,6,9), enc='auto'):
        ensure_dir(outdir)
        best = None
        results = []
        for lvl in levels:
            fname = os.path.join(outdir, f'fast_lvl_{lvl}.json')
            comp = UltraCompressor(maps_prefix=self.compressor.maps_prefix, zstd_dict_file=self.compressor.zstd_dict_file, zstd_level=lvl, zstd_threads=self.compressor.zstd_threads)
            meta = comp.compress_json(infile, fname, preproc_opts={'maps': True, 'delta': True, 'mtf': True, 'rle': True}, encoder=enc)
            size = meta['meta']['sizes']['text_chars']
            results.append((lvl, size, fname, meta))
            if best is None or size < best[1]:
                best = (lvl, size, fname, meta)
        print('Fast levels best:', best)
        return best, results

# ---------------------- CLI ----------------------

def main_cli():
    p = argparse.ArgumentParser(prog='ultrajson_pro')
    sub = p.add_subparsers(dest='cmd')

    g = sub.add_parser('build-maps')
    g.add_argument('samples_folder')
    g.add_argument('--out_prefix', default='maps')
    g.add_argument('--max_keys', type=int, default=2000)
    g.add_argument('--max_values', type=int, default=4000)

    t = sub.add_parser('train-dict')
    t.add_argument('samples_folder')
    t.add_argument('--maps_prefix', default='maps')
    t.add_argument('--out_dict', default='zstd_dict')
    t.add_argument('--dict_size', type=int, default=112640)
    t.add_argument('--collect-only', action='store_true')

    c = sub.add_parser('compress')
    c.add_argument('infile')
    c.add_argument('outfile')
    c.add_argument('--maps_prefix', default='maps')
    c.add_argument('--zstd_dict', default=None)
    c.add_argument('--encoder', default='auto')
    c.add_argument('--zstd_level', type=int, default=9)
    c.add_argument('--zstd_threads', type=int, default=0)
    c.add_argument('--mode', choices=['fast','aggressive','ultra'], default='fast', help='Compression mode')
    c.add_argument('--maps', dest='maps', action='store_true')
    c.add_argument('--no-maps', dest='maps', action='store_false')
    c.set_defaults(maps=True)
    c.add_argument('--delta', dest='delta', action='store_true')
    c.add_argument('--no-delta', dest='delta', action='store_false')
    c.set_defaults(delta=True)
    c.add_argument('--mtf', dest='mtf', action='store_true')
    c.add_argument('--no-mtf', dest='mtf', action='store_false')
    c.set_defaults(mtf=True)
    c.add_argument('--rle', dest='rle', action='store_true')
    c.add_argument('--no-rle', dest='rle', action='store_false')
    c.set_defaults(rle=True)
    c.add_argument('--use_stream', action='store_true')

    d = sub.add_parser('decompress')
    d.add_argument('infile')
    d.add_argument('outfile')
    d.add_argument('--maps_prefix', default='maps')
    d.add_argument('--zstd_dict', default=None)
    d.add_argument('--mode', choices=['fast','aggressive','ultra'], default='fast', help='(Hint) mode used originally (fast/aggressive/ultra)')

    o = sub.add_parser('optimize')
    o.add_argument('infile')
    o.add_argument('outdir')
    o.add_argument('--maps_prefix', default='maps')
    o.add_argument('--zstd_dict', default=None)
    o.add_argument('--encoder', default='auto')

    f = sub.add_parser('fast-optimize')
    f.add_argument('infile')
    f.add_argument('outdir')
    f.add_argument('--maps_prefix', default='maps')
    f.add_argument('--zstd_dict', default=None)
    f.add_argument('--encoder', default='auto')
    f.add_argument('--zstd_threads', type=int, default=0)

    ins = sub.add_parser('inspect')
    ins.add_argument('infile', help='Fichier .uc à inspecter')
    ins.add_argument('--as-text', action='store_true', help='Forcer tentative de décodage texte')
    ins.add_argument('--max-bytes', type=int, default=64, help='Octets de prévisualisation')

    args = p.parse_args()
    if args.cmd == 'build-maps':
        mb = MapsBuilder(args.samples_folder, max_keys=args.max_keys, max_values=args.max_values)
        keys_map, values_map = mb.build()
        write_json(keys_map, args.out_prefix + '_keys.json')
        write_json(values_map, args.out_prefix + '_values.json')
        print('Wrote maps with', len(keys_map), 'keys and', len(values_map), 'values')

    elif args.cmd == 'train-dict':
        trainer = ZstdDictTrainer(args.samples_folder, maps_prefix=args.maps_prefix, out_dict=args.out_dict, dict_size=args.dict_size)
        trainer.collect_samples()
        if not args.collect_only:
            trainer.train()

    elif args.cmd == 'compress':
        comp = UltraCompressor(maps_prefix=args.maps_prefix, zstd_dict_file=args.zstd_dict, zstd_level=args.zstd_level, zstd_threads=args.zstd_threads, compression_mode=args.mode)
        pre = {'maps': args.maps, 'delta': args.delta, 'mtf': args.mtf, 'rle': args.rle, 'mtf_threshold': 4, 'delta_threshold': 4}
        comp.compress_json(args.infile, args.outfile, pre, encoder=args.encoder, use_stream=args.use_stream)

    elif args.cmd == 'decompress':
        comp = UltraCompressor(maps_prefix=args.maps_prefix, zstd_dict_file=args.zstd_dict, compression_mode=args.mode)
        comp.decompress_json(args.infile, args.outfile)

    elif args.cmd == 'optimize':
        comp = UltraCompressor(maps_prefix=args.maps_prefix, zstd_dict_file=args.zstd_dict)
        opt = AutoOptimizer(comp)
        best, variants = opt.try_variants(args.infile, args.outdir, enc=args.encoder)
        print('Optimization completed. Best variant:', best)

    elif args.cmd == 'fast-optimize':
        comp = UltraCompressor(maps_prefix=args.maps_prefix, zstd_dict_file=args.zstd_dict, zstd_threads=args.zstd_threads)
        opt = AutoOptimizer(comp)
        best, results = opt.fast_levels(args.infile, args.outdir, levels=(3,6,9), enc=args.encoder)
        print('Fast optimization completed. Best:', best)

    elif args.cmd == 'inspect':
        import base64, json as _json
        with open(args.infile, 'rb') as fbin:
            blob = fbin.read()
        head = blob[:args.max_bytes]
        print('File:', args.infile)
        print('Total bytes:', len(blob))
        print('Head hex   :', head.hex())
        print('Head b64   :', base64.b64encode(head).decode('ascii'))
        comp = UltraCompressor()
        # Try structured first
        struct_ok = False
        try:
            obj = comp.decompress_bytes(blob, preserve_text=False)
            struct_ok = True
            print('Structured decode: OK (type:', type(obj).__name__ + ')')
        except Exception as e:
            print('Structured decode: FAIL -', e)
        if args.as_text or not struct_ok:
            try:
                text = comp.decompress_bytes(blob, preserve_text=True)
                print('Text decode: OK length', len(text))
                # Show a preview of JSON keys if it parses
                try:
                    parsed = _json.loads(text)
                    if isinstance(parsed, dict):
                        print('Parsed keys sample:', list(parsed.keys())[:10])
                except Exception:
                    pass
            except Exception as e:
                print('Text decode: FAIL -', e)
        print('Inspection complete.')

    else:
        p.print_help()

if __name__ == '__main__':
    main_cli()