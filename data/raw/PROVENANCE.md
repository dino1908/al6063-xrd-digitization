# Source data

The five TIFF files are copies of the Al6063 research plots retained from 2015. The numerical text file is the original Bruker XRD Commander export for the solution-treated sample, acquired 8 June 2015. The instrument file contains a header and a `[Data]` section; it is intentionally retained without rewriting or cleaning it.

- `tiff/XRD_ST_2015.tif`: solution treated
- `tiff/XRD_CR40_2015.tif`: 40% cold rolled, according to the archive label
- `tiff/XRD_CR40_annealed_2015.tif`: 40% cold rolled and annealed, according to the archive label
- `tiff/XRD_UDR85_2015.tif`: 85% unidirectional rolling, according to the archive label
- `tiff/XRD_UDR85_annealed_2015.tif`: unidirectional rolling and annealed, according to the archive label
- `instrument/XRD_Al6063_ST_2015_06_08_ASCII.txt`: surviving ST instrument export

These filenames describe how the source archive was labeled, not independently verified processing histories. See `analysis/source_sha256_manifest.csv` for the bytes and hashes of all six originals. The archive does not include matching detector exports for the other four plots.

To reduce repository size, the unchanged TIFF bytes are distributed in `original_tiffs_lossless.zip`; run `python scripts/unpack_tiffs.py` after cloning. Each TIFF is restored and checked against the recorded SHA-256 digest.
