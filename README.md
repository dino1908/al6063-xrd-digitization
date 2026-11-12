# Al6063 XRD TIFF digitization

This repository reconstructs numerical XRD profiles from five archived Al6063 TIFF plots. The solution-treated sample also has an original numerical TXT export, which is used to compare four experimental extraction methods.

## Repository structure

- `01_original_data` contains the original TXT export and five TIFF plots.
- `02_experiments` contains the code, reconstructed CSV, and validation outputs for V1, V2, V3, and V4.
- `03_version_comparison` compares V1-V4 with the original TXT data and with each other.
- `04_batch_v4_code` contains the V4 script scaled to process all five TIFF plots.
- `05_batch_v4_outputs` contains the batch results copied from the archived Drive folder.

## Run the project

```bash
python -m pip install -r requirements.txt

python 02_experiments/V1/run_v1.py
python 02_experiments/V2/run_v2.py
python 02_experiments/V3/run_v3.py
python 02_experiments/V4/run_v4.py

python 03_version_comparison/compare_versions.py
python 04_batch_v4_code/reconstruct_all_tiffs_v4.py
```

The original TXT file is used for validation only. The reconstruction scripts use the TIFF plots as their data source.
