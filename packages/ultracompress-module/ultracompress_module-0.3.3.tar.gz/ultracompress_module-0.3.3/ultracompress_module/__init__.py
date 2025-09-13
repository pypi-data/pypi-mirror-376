from pathlib import Path
from dataclasses import dataclass
from typing import Any, Union, Dict, List, Optional, Literal, overload
from .ultrajson_pro import UltraCompressor  # Import interne (non exposé dans __all__)

__version__ = "0.3.2"

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
    'auto_compress', 'auto_decompress', 'AutoCompressed', 'JSONType', 'describe_blob',
    'simple_compress', 'simple_decompress', '__version__'
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

# ---------------------------------------------------------------------------
# API ULTRA SIMPLIFIEE (une fonction pour produire un bloc copiable, une pour le décoder)
# ---------------------------------------------------------------------------

def simple_compress(data: Any, *, mode: str = 'fast', preserve_order: bool = True,
                    include_hex: bool = True, markers: bool = True, line_width: int = 0,
                    header: bool = True) -> str:
    """Compression ultra simple retournant un bloc prêt à copier-coller.

    Arguments:
      data: str (JSON brut) ou objet JSON (dict/list/etc.)
      mode: 'fast' | 'aggressive' | 'ultra'
      preserve_order: si True essaie de préserver EXACTEMENT le texte d'entrée (si str). Si objet -> sérialisation compacte.
      include_hex: ajoute en plus un bloc hex.
      markers: entoure les blocs avec B64_START/B64_END et HEX_START/HEX_END.
      line_width: si >0 coupe les lignes Base64/Hex.
      header: ajoute un petit en-tête commenté avec stats.

    Retourne une chaîne multi-lignes (str) contenant:
      - éventuellement un en-tête (# ...)
      - un bloc Base64 (toujours)
      - éventuellement un bloc Hex
    """
    import json, base64

    # Préparation du texte source & choix preserve_text
    if isinstance(data, str):
        text = data
        preserve_text = True  # On conserve exactement le texte
    else:
        # Objet Python -> soit on force mode structuré si preserve_order False, sinon on génère un JSON compact stable
        if preserve_order:
            # Génère une version compacte déterministe (Python >=3.7 préserve insertion order)
            text = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            preserve_text = True
        else:
            preserve_text = False
            text = None  # pas utilisé dans ce cas

    if preserve_text:
        blob = compress_text(text, preserve_text=True, mode=mode)  # type: ignore[arg-type]
        original_len = len(text.encode('utf-8'))
    else:
        blob = compress_object(data, mode=mode)
        # Taille « logique »: JSON compact
        compact = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        original_len = len(compact.encode('utf-8'))

    b64 = base64.b64encode(blob).decode('ascii')
    hx = blob.hex()

    def _wrap(s: str) -> str:
        if line_width and line_width > 0:
            return '\n'.join(s[i:i+line_width] for i in range(0, len(s), line_width))
        return s

    lines = []
    if header:
        ratio = (len(blob) / original_len) if original_len else 0.0
        lines.append(f"# ultracompress simple export | mode={mode} | preserve_order={preserve_order} | original={original_len} bytes | compressed={len(blob)} | ratio={ratio:.2%}")
    # Bloc Base64
    if markers:
        lines.append('B64_START')
    lines.append(_wrap(b64))
    if markers:
        lines.append('B64_END')
    # Bloc Hex (optionnel)
    if include_hex:
        if markers:
            lines.append('HEX_START')
        lines.append(_wrap(hx))
        if markers:
            lines.append('HEX_END')
    return '\n'.join(lines) + ('\n' if lines and not lines[-1].endswith('\n') else '')

def simple_decompress(block: str, *, return_text: Optional[bool] = None) -> Any:
    """Décode un bloc produit par simple_compress (Base64 obligatoire, Hex optionnel).

    - Tolère lignes supplémentaires, prompts '>>', espaces.
    - Détecte les marqueurs B64_START / B64_END sinon considère le bloc complet comme base64.
    - Si base64 échoue, tente un décodage Hex (si présent ou si seulement hex fourni).
    - Utilise auto_decompress si return_text est None.

    Arguments:
      block: chaîne contenant le bloc exporté.
      return_text: True => retourne toujours du texte JSON, False => objet Python (structuré), None => heuristique.
    """
    import re, base64, binascii

    def _extract(marker_start: str, marker_end: str, text: str) -> Optional[str]:
        if marker_start in text and marker_end in text:
            pattern = rf"{marker_start}\n?(.*?)\n?{marker_end}"
            m = re.search(pattern, text, flags=re.DOTALL)
            if m:
                return m.group(1).strip()
        return None

    # Cherche bloc base64 prioritaire
    raw_b64 = _extract('B64_START', 'B64_END', block)
    raw_hex = _extract('HEX_START', 'HEX_END', block)

    # Si pas de marqueurs, on devine
    if raw_b64 is None and raw_hex is None:
        # Supprime commentaires / lignes commençant par '#'
        candidate = '\n'.join(l for l in block.strip().splitlines() if not l.strip().startswith('#'))
        # Nettoie prompts
        candidate = '\n'.join(l.lstrip('> ').strip() for l in candidate.splitlines() if l.strip())
        # Heuristique: si caractères hors 0-9a-f => probablement base64
        if re.search(r"[^0-9A-Fa-f\s]", candidate):
            raw_b64 = candidate.replace('\n', '')
        else:
            raw_hex = candidate.replace('\n', '')

    blob: Optional[bytes] = None
    errors = []

    if raw_b64:
        # Sanitize base64
        b64_clean = re.sub(r"[^A-Za-z0-9+/=]", "", raw_b64)
        try:
            blob = base64.b64decode(b64_clean)
        except Exception as e:
            errors.append(f"base64:{e}")

    if blob is None and raw_hex:
        hx_clean = re.sub(r"[^0-9A-Fa-f]", "", raw_hex)
        try:
            blob = bytes.fromhex(hx_clean)
        except ValueError as e:
            errors.append(f"hex:{e}")

    if blob is None:
        raise ValueError(f"Impossible de décoder base64/hex. Détails: {errors}")

    # Décompression
    if return_text is True:
        return decompress_bytes(blob, preserve_text=True)
    if return_text is False:
        # Tente d'abord structuré
        try:
            return decompress_bytes(blob, preserve_text=False)
        except Exception:
            # Fallback: texte puis tentative de json.loads
            try:
                txt = decompress_bytes(blob, preserve_text=True)
                import json
                return json.loads(txt)
            except Exception:
                # Dernier recours: retourner texte brut
                return txt  # type: ignore[name-defined]
    # Heuristique auto
    try:
        return decompress_bytes(blob, preserve_text=False)
    except Exception:
        # Fallback text; si parse JSON ok on retourne objet sinon texte
        txt = decompress_bytes(blob, preserve_text=True)
        try:
            import json
            return json.loads(txt)
        except Exception:
            return txt