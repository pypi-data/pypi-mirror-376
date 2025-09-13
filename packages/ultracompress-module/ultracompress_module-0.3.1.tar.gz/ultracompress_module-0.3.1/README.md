# UltraCompress Module

Compression JSON multi-mode (fast / aggressive / ultra) avec chaînes de transformations réversibles (maps, delta, MTF, RLE, internage + BPE, front-coding, packing / bit-packing d'entiers, zigzag, GCD scaling, affine / décimal normalisation, segmentation numérique, déduplication de sous-arbres, colonnes améliorées...) et sélection automatique du meilleur backend (multi-niveaux Zstandard, Brotli, LZMA) pour obtenir des réductions >95% (souvent >99%) sur des structures répétitives complexes — tout en garantissant un round‑trip exact et l'ordre original.

## Installation

```bash
pip install ultracompress_module
````

## Modes

| Mode | Objectif | Vitesse | Recherche backend | Transformations explorées |
|------|----------|---------|-------------------|---------------------------|
| `fast` (défaut) | Bonne compression rapide | ⚡ | zstd (niveau unique ou choisi), fallback lzma/brotli si meilleur | Sous-ensemble sûr (maps, delta, mtf, rle, int pack basique) |
| `aggressive` | Ratio plus élevé | ⚡➜🐢 | zstd multi-niveaux + brotli (9/11) + lzma extrême | Ajoute exploration large int packing, colonnes simples, internage chaîne |
| `ultra` | Maximum de réduction | 🐢 | Large panel zstd (niveaux étendus + dict si dispo) + brotli + lzma | Active recherche combinatoire (intern+BPE, front-coding, subtree dedup robuste, colonnes améliorées, bit/zigzag pack, GCD/affine/decimal/segbit cascade, variantes pipelines >100) |

Tous les pipelines sont strictement **lossless** et l'ordre des éléments est préservé. Le moteur évalue plusieurs variantes et conserve le plus petit résultat final.

## Utilisation basique (fichiers)

```python
from ultracompress_module import compress, decompress

# Compresser un fichier JSON (mode rapide: compresse le texte brut)
compress("input.json", "output.uc", preserve_text=True)

# Mode structuré (transformations maps/delta/mtf/rle pour meilleur ratio)
compress("input.json", "output_struct.uc", preserve_text=False, preproc_opts={
	'maps': True, 'delta': True, 'mtf': True, 'rle': True
})

"""Fast (défaut) vs aggressive vs ultra"""
# Mode agressif (plus de recherche backend + transformations)
compress("input.json", "output_aggr.uc", preserve_text=False, preproc_opts={
    'maps': True, 'delta': True, 'mtf': True, 'rle': True
}, mode='aggressive')

# Mode ultra (exploration maximale, meilleur ratio, plus lent sur gros fichiers)
compress("input.json", "output_ultra.uc", preserve_text=False, preproc_opts={
    'maps': True, 'delta': True, 'mtf': True, 'rle': True
}, mode='ultra')

# Décompresser
decompress("output.uc", "reconstruit.json", preserve_text=True)
```

## Utilisation en mémoire (aucun fichier intermédiaire)

```python
from ultracompress_module import compress_text, decompress_bytes

json_text = '{"hello": "world", "nums": [1,1,1,2,2,3,3,3,3], "nested": {"a":1,"b":1}}'

# Texte brut (fast) -> idéal si on veut exactement la chaîne identique (espaces, ordre etc.)
blob_fast = compress_text(json_text, preserve_text=True)  # bytes .uc
restored_text = decompress_bytes(blob_fast)  # str identique

# Structuré agressif (objet Python à la restauration) :
blob_aggr = compress_text(json_text, preserve_text=False, preproc_opts={'maps': True}, mode='aggressive')
obj = decompress_bytes(blob_aggr, preserve_text=False)  # objet Python identique

# Structuré ultra (max ratio) :
blob_ultra = compress_text(json_text, preserve_text=False, preproc_opts={'maps': True}, mode='ultra')
obj_ultra = decompress_bytes(blob_ultra, preserve_text=False)
```

## CLI

Après installation, une commande `ultracompress` est disponible :

```bash
ultracompress compress input.json output.uc  # fast par défaut
ultracompress compress --mode aggressive input.json output_aggr.uc
ultracompress compress --mode ultra input.json output_ultra.uc

ultracompress decompress output_ultra.uc restored.json --mode ultra  # (mode requis pour hints quand structuré)

# Compression texte brut (préserver format exact)
ultracompress compress --mode fast --preserve-text input.json out_text.uc

# Optimisation automatique (essaie plusieurs entrées / pipelines internes)
ultracompress optimize input.json best.uc
```

Sous-commandes additionnelles :

- `build-maps` : génère `maps_keys.json` / `maps_values.json` depuis un corpus.
- `train-dict` : entraîne un dictionnaire Zstandard (placé dans `zstd_dict`).
- `optimize` : essaie plusieurs stratégies de pipeline complètes.
- `fast-optimize` : sous-ensemble plus rapide.
- `inspect` : affiche un aperçu (taille, hex, base64, tentative de décodage structuré/texte) d'un fichier `.uc`.

Exemple :

```bash
ultracompress inspect sample.uc --max-bytes 96
```

Afficher l'aide :

```bash
ultracompress --help
```

## Bench (exemple indicatif)

Sur un jeu mixte (structures imbriquées, listes d'entiers, chaînes répétitives) :

| Dataset | Taille JSON | fast | aggressive | ultra | Gain ultra |
|---------|------------:|-----:|-----------:|------:|-----------:|
| nested_medium | 120 KB | 18.2 KB | 9.7 KB | 5.3 KB | 95.6% |
| numeric_arrays | 200 KB | 21.5 KB | 8.4 KB | 3.1 KB | 98.4% |
| repetitive_strings | 85 KB | 9.1 KB | 4.0 KB | 0.6 KB | 99.3% |

(Les chiffres fluctuent selon contenu / machine; lancer vos propres mesures via un script bench.)

## Exemples complets

Voir `examples/example_usage.py` pour un script autonome qui montre :

- Compression en mémoire (texte vs structuré) sur les trois modes.
- Compression de fichiers (fast/aggressive/ultra) et restauration.
- Utilisation de `benchmark_ratio` pour comparer rapidement les tailles.

Exécution :

```bash
python examples/example_usage.py
```

### API auto-détection rapide

Pour simplifier selon le type passé (texte JSON, objet Python ou chemin de fichier) :

```python
from ultracompress_module import auto_compress, auto_decompress

data = {"users": [{"id": i, "name": f"u{i}"} for i in range(10)]}
meta = auto_compress(data, mode='aggressive')  # retourne AutoCompressed
print(meta.original_len, '->', meta.compressed_len)
restored = auto_decompress(meta.blob, return_text=False)
assert restored == data

json_text = '{"a":1,"b":[1,2,3]}'
meta_text = auto_compress(json_text, mode='fast')
restored_txt = auto_decompress(meta_text.blob, return_text=True)
assert restored_txt == json_text
```

## Garantie d'intégrité

Chaque transformation est entièrement réversible. Une suite de tests valide le round‑trip (fast/aggressive/ultra, texte & structuré). Si une variante ne réduit pas la taille ou échoue à valider sa reconstruction intermédiaire, elle est écartée.

## Limites / Conseils

- Pour de très petits fichiers (<200 octets) le surcoût d'entête peut réduire l'intérêt : rester en `fast`.
- `ultra` peut explorer >100 pipelines; sur de gros JSON (multi-MB) prévoir plus de temps CPU.
- Fournir un dictionnaire Zstandard entraîné (`train-dict`) peut encore améliorer les ratios.
- `preserve_text=True` désactive les optimisations structurelles (on compresse la chaîne brute après éventuel mapping minimal) afin de garantir l'exactitude byte‑à‑byte.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---
Notes version 0.3.0:

- Nouveau mode `ultra` : exploration combinatoire étendue (internage + BPE, front-coding, subtree dedup robuste, colonnes avancées, cascades numériques GCD/affine/decimal/segbit, bit/zigzag pack, multi-niveaux zstd élargis) → gains >95% fréquents.
- Sélection dynamique du meilleur pipeline parmi >100 variantes lorsque pertinent.
- Ajout des transforms numériques avancées (mise à l'échelle GCD, détection affine, normalisation décimale, bit-packing segmenté) et amélioration de la réversibilité.
- CLI : option `--mode {fast,aggressive,ultra}` pour `compress` & `decompress`.
- Documentation enrichie (table de modes, benchs, conseils).

Notes version 0.2.0:

- Ajout du mode `aggressive` : essaie plusieurs niveaux Zstandard (3,6,9,15,19), Brotli (9/11), LZMA extrême et choisit le meilleur ratio.
- Transformation optionnelle d'emballage d'entiers (`int packing`) pour grandes listes d'entiers (>=8) non négatifs.
- Décompression des conteneurs structurés : auto-détection zstd -> lzma -> brotli (si installé) sans champ de méthode stocké (compat rétro).
- API fonctionnelle en mémoire stable (`compress_text`, `compress_object`, etc.).
