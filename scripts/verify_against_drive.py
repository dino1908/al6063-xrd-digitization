"""Optional verification of a downloaded Drive results directory.

Usage: python scripts/verify_against_drive.py /path/to/drive-results-folder
"""
from pathlib import Path
import argparse
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT/'results/batch_v4'

def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('drive_folder', type=Path)
args=p.parse_args()
rows=[]
for local in sorted(EXPECTED.glob('*.csv')):
    other=args.drive_folder / local.name
    if not other.exists():
        print(f'MISSING in Drive results: {local.name}')
        rows.append({'file':local.name,'status':'missing','max_abs_numeric_difference':None})
        continue
    exact=digest(local)==digest(other)
    if local.name=='QA_summary.csv':
        # Compare the manifest bytewise; mixed text and numeric columns.
        numeric_diff=None
    else:
        a=np.loadtxt(local,delimiter=',',skiprows=1)
        b=np.loadtxt(other,delimiter=',',skiprows=1)
        numeric_diff=float(np.max(np.abs(a-b))) if a.shape==b.shape else float('inf')
    rows.append({'file':local.name,'status':'byte-identical' if exact else 'different',
                 'max_abs_numeric_difference':numeric_diff})
print(pd.DataFrame(rows).to_string(index=False))
assert all(r['status']=='byte-identical' for r in rows), 'Some files differ from Drive results'
