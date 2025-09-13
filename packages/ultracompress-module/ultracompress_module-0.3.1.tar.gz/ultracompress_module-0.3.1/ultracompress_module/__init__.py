from pathlib import Path
from dataclasses import dataclass
from typing import Any, Union, Dict, List, Optional, Literal, overload
from .ultrajson_pro import UltraCompressor  # Import interne (non exposé dans __all__)

# ---------------------------------------------------------------------------
# API FONCTIONNELLE PUBLIQUE
# ---------------------------------------------------------------------------
def compress(infile: str, outfile: str, preserve_text: bool = True, preproc_opts=None, mode: str='fast'):
    """Compresse un fichier JSON vers un fichier `.uc`.

    Arguments:
        infile: chemin du JSON source.
        outfile: chemin de sortie `.uc`.
        preserve_text: si True (défaut) compresse directement le texte JSON.
        preproc_opts: dict d'options (maps/delta/mtf/rle) utilisé si preserve_text=False.
    """
    infile, outfile = Path(infile), Path(outfile)
    comp = UltraCompressor(compression_mode=mode)
    comp.compress_json(str(infile), str(outfile), preproc_opts=preproc_opts or {}, preserve_text=preserve_text)
    return outfile

def decompress(infile: str, outfile: str, preserve_text: bool = True, mode: str='fast'):
    """Décompresse un fichier `.uc` en JSON (écrit `outfile`)."""
    infile, outfile = Path(infile), Path(outfile)
    comp = UltraCompressor(compression_mode=mode)
    comp.decompress_json(str(infile), str(outfile), preserve_text=preserve_text)
    return outfile

# ------------------------------ In-memory ----------------------------------
def compress_text(text: str, preserve_text: bool = True, preproc_opts=None, mode: str='fast') -> bytes:
    """Compresse une chaîne JSON et retourne les bytes `.uc`."""
    comp = UltraCompressor(compression_mode=mode)
    return comp.compress_text(text, preserve_text=preserve_text, preproc_opts=preproc_opts)

def compress_object(obj, preproc_opts=None, mode: str='fast') -> bytes:
    """Compresse un objet Python (dict/list) déjà parsé en bytes `.uc` (mode structuré)."""
    comp = UltraCompressor(compression_mode=mode)
    return comp.compress_object(obj, preproc_opts=preproc_opts or {})

def compress_file_to_bytes(infile: str, preserve_text: bool = True, preproc_opts=None, use_stream: bool=False, mode: str='fast') -> bytes:
    """Lit un fichier JSON et renvoie les bytes `.uc` sans créer de fichier."""
    comp = UltraCompressor(compression_mode=mode)
    return comp.compress_file_to_bytes(infile, preserve_text=preserve_text, preproc_opts=preproc_opts or {}, use_stream=use_stream)

def decompress_bytes(data: bytes, preserve_text: bool = True):
    """Décompresse des bytes `.uc` en texte JSON (preserve_text=True) ou objet Python (False)."""
    comp = UltraCompressor()
    return comp.decompress_bytes(data, preserve_text=preserve_text)

def decompress_bytes_to_file(data: bytes, outfile: str, preserve_text: bool = True):
    """Décompresse des bytes `.uc` directement vers un fichier JSON."""
    comp = UltraCompressor()
    comp.decompress_bytes_to_file(data, outfile, preserve_text=preserve_text)
    return outfile

def decompress_file_to_text(infile: str) -> str:
    """Décompresse un fichier `.uc` (mode texte) et retourne la chaîne JSON sans écrire un nouveau fichier."""
    comp = UltraCompressor()
    with open(infile, 'rb') as f:
        data = f.read()
    return comp.decompress_bytes(data, preserve_text=True)  # type: ignore[return-value]

def decompress_file_to_object(infile: str):
    """Décompresse un fichier `.uc` structuré (préproc) et retourne l'objet Python."""
    comp = UltraCompressor()
    with open(infile, 'rb') as f:
        data = f.read()
    return comp.decompress_bytes(data, preserve_text=False)

def benchmark_ratio(obj, structured: bool=True):
    """Compare les tailles fast vs aggressive et retourne un dict de ratios.

    structured=True : utilise le pipeline prétraité (compress_object)
    structured=False : traite comme texte JSON (ou chaîne si déjà str)"""
    comp = UltraCompressor()
    return comp.benchmark_ratio(obj, structured=structured)

# ---------------------------------------------------------------------------
# Convenience auto-detection API
# ---------------------------------------------------------------------------
JSONPrimitive = Union[str, int, float, bool, None]
JSONType = Union[JSONPrimitive, Dict[str, 'JSONType'], List['JSONType']]

@dataclass
class AutoCompressed:
    source_type: Literal['text','object','file_text','file_object']
    mode: str
    preserve_text: bool
    original_len: int
    compressed_len: int
    blob: bytes

def _is_json_like(value: Any) -> bool:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_json_like(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_json_like(v) for k,v in value.items())
    return False

def auto_compress(data: Union[str, bytes, JSONType, Path], *, mode: str='fast',
                  preproc_opts: Optional[dict]=None,
                  force_structured: Optional[bool]=None,
                  return_meta: bool=True) -> Union[bytes, AutoCompressed]:
    """Compression utilitaire unifiée.

    Accepte:
      - str contenant du JSON -> traité comme texte (preserve_text=True)
      - objet Python (dict/list) -> structuré (preserve_text=False)
      - Path / str chemin fichier .json -> auto choix selon force_structured

    Arguments:
      mode: fast/aggressive/ultra
      preproc_opts: options maps/delta/mtf/rle pour structuré
      force_structured: si True force parsing JSON et compression structurée
      return_meta: si True retourne AutoCompressed sinon bytes seules
    """
    comp = UltraCompressor(compression_mode=mode)
    preproc_opts = preproc_opts or {}

    # File path case
    if isinstance(data, (str, Path)) and Path(str(data)).exists():
        path = Path(str(data))
        text = path.read_text(encoding='utf-8')
        # Decide structured vs text
        do_struct = force_structured if force_structured is not None else True
        if do_struct:
            import json
            obj = json.loads(text)
            blob = comp.compress_object(obj, preproc_opts=preproc_opts)
            meta_type = 'file_object'
            original_len = len(text.encode('utf-8'))
            preserve_text = False
        else:
            blob = comp.compress_text(text, preserve_text=True, preproc_opts=None)
            meta_type = 'file_text'
            original_len = len(text.encode('utf-8'))
            preserve_text = True
        result = AutoCompressed(
            source_type=meta_type,
            mode=mode,
            preserve_text=preserve_text,
            original_len=original_len,
            compressed_len=len(blob),
            blob=blob
        )
        return result if return_meta else blob

    # Raw bytes: assume already compressed? We could raise.
    if isinstance(data, bytes):
        raise TypeError("bytes input not supported for auto_compress (ambiguous). Use decompress_bytes or explicit compress_*.")

    # String: treat as JSON text (avoid parse to keep exact formatting)
    if isinstance(data, str):
        blob = comp.compress_text(data, preserve_text=True, preproc_opts=None)
        result = AutoCompressed(
            source_type='text', mode=mode, preserve_text=True,
            original_len=len(data.encode('utf-8')), compressed_len=len(blob), blob=blob
        )
        return result if return_meta else blob

    # Object-like
    if _is_json_like(data):
        blob = comp.compress_object(data, preproc_opts=preproc_opts)
        import json
        original_len = len(json.dumps(data, separators=(',',':')).encode('utf-8'))
        result = AutoCompressed(
            source_type='object', mode=mode, preserve_text=False,
            original_len=original_len, compressed_len=len(blob), blob=blob
        )
        return result if return_meta else blob

    raise TypeError(f"Type non supporté pour auto_compress: {type(data)!r}")

def auto_decompress(blob: bytes, *, return_text: Optional[bool]=None):
    """Décompresse un blob .uc avec heuristique.

    Si return_text est True -> renvoie la chaîne JSON.
    Si return_text est False -> renvoie l'objet Python (structuré).
    Si None -> tente structuré puis fallback texte.
    """
    comp = UltraCompressor()
    if return_text is True:
        return comp.decompress_bytes(blob, preserve_text=True)
    if return_text is False:
        # Try structured first, fallback to text+json parse
        try:
            return comp.decompress_bytes(blob, preserve_text=False)
        except Exception:
            try:
                txt = comp.decompress_bytes(blob, preserve_text=True)
                import json
                return json.loads(txt)
            except Exception:
                raise
    # Heuristic (unspecified): try structured then fallback text
    try:
        return comp.decompress_bytes(blob, preserve_text=False)
    except Exception:
        return comp.decompress_bytes(blob, preserve_text=True)

__all__ = [
    'compress', 'decompress',
    'compress_text', 'compress_object', 'compress_file_to_bytes',
    'decompress_bytes', 'decompress_bytes_to_file',
    'decompress_file_to_text', 'decompress_file_to_object',
    'benchmark_ratio',
    'auto_compress', 'auto_decompress', 'AutoCompressed', 'JSONType', 'describe_blob'
]

def describe_blob(blob: bytes, max_preview: int = 48) -> dict:
    """Retourne un petit dictionnaire descriptif du blob compressé.

    Fournit:
      - size: taille en octets
      - head_hex: hex des premiers octets
      - base64: version base64 tronquée
      - looks_structured: bool heuristique (si décodage structuré possible)
      - text_roundtrip_ok: bool si décodage texte possible sans erreur
      - structured_type: type Python racine si structuré
    """
    import base64
    comp = UltraCompressor()
    info = {
        'size': len(blob),
        'head_hex': blob[:min(len(blob), max_preview)].hex(),
        'base64': base64.b64encode(blob[:min(len(blob), max_preview)]).decode('ascii'),
        'looks_structured': None,
        'text_roundtrip_ok': None,
        'structured_type': None,
    }
    # Try structured decode
    try:
        obj = comp.decompress_bytes(blob, preserve_text=False)
        info['looks_structured'] = True
        info['structured_type'] = type(obj).__name__
    except Exception:
        info['looks_structured'] = False
    # Try text decode
    try:
        text = comp.decompress_bytes(blob, preserve_text=True)
        info['text_roundtrip_ok'] = isinstance(text, str)
    except Exception:
        info['text_roundtrip_ok'] = False
    return info