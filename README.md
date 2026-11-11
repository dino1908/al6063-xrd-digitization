# Al6063 XRD profile reconstruction from TIFF plots

Five archived diffraction plots were digitized. The surviving Bruker export for the solution-treated (ST) specimen provides a numerical reference for four reconstruction methods. V4 reduced ST intensity RMSE from 48.884 to 9.244 counts and reproduced the grid locations of the three principal maxima. The other four profiles were checked against their TIFFs. Their measurement-level errors are unknown.

The [technical report](report/Al6063_XRD_Technical_Report.pdf) presents the validation results, peak measurements, and limitations.

| Directory | Contents |
|---|---|
| `data/raw/` | Lossless archive of the original TIFF plots and the ST instrument export |
| `src/` | Four historical ST extraction algorithms |
| `scripts/` | Reconstruction, validation, sample comparison, and report generation |
| `experiments/st_versions/` | Four ST reconstructions, pointwise residuals, and overlay plots |
| `results/batch_v4/` | Five reconstructed CSVs and TIFF trace overlays |
| `analysis/` | Validation tables, image QA, sample descriptors, and source hashes |

## Reproduce the results

Run from the project directory with Python 3.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/unpack_tiffs.py
python scripts/reconstruct_st_versions.py
python scripts/reconstruct_batch_v4.py
python scripts/validate_and_analyze.py
python scripts/compare_samples.py
python scripts/build_report.py
```

The digitizers read only the TIFFs. Validation reads the original ST export and compares it to the reconstructions on the same 938-point grid. Start with [scan-level metrics](analysis/st_validation_metrics.csv), [peak-level errors](analysis/st_peak_validation.csv), and [image QA outliers](analysis/image_qa_outliers.csv).
