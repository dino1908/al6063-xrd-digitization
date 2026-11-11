"""Restore the five original TIFFs byte-for-byte from the lossless archive.

The archive is kept in Git because the uncompressed TIFFs are nearly 40 MB,
while the lossless ZIP is under 200 kB. No image data are altered.
"""
from pathlib import Path
import hashlib
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / 'data/raw/original_tiffs_lossless.zip'
destination = ROOT / 'data/raw/tiff'
destination.mkdir(parents=True, exist_ok=True)
expected = pd.read_csv(ROOT/'analysis/source_sha256_manifest.csv')
checks = dict(zip(expected.path, expected.sha256))
with zipfile.ZipFile(archive) as z:
    for filename in z.namelist():
        if '/' in filename or filename.startswith('.') or not filename.endswith('.tif'):
            raise ValueError(f'Unexpected archive member: {filename}')
        output = destination / filename
        if not output.exists():
            output.write_bytes(z.read(filename))
        actual = hashlib.sha256(output.read_bytes()).hexdigest()
        rel = f'data/raw/tiff/{filename}'
        assert checks.get(rel) == actual, f'Source TIFF hash mismatch: {filename}'
        print('Verified:', filename)
