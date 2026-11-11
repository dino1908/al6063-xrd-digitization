"""Reproduce all four solution-treated reconstruction experiments."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.st_versions import ANGLES, reconstruct_st


def main():
    tiff = ROOT / 'data/raw/tiff/XRD_ST_2015.tif'
    out = ROOT / 'experiments/st_versions'
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    for version in (1, 2, 3, 4):
        y = reconstruct_st(tiff, version)
        path = out / f'ST_v{version}.csv'
        np.savetxt(path, np.column_stack([ANGLES, y]), delimiter=',',
                   header='angle_degrees,intensity_estimated', comments='', fmt=['%.2f', '%.4f'])
        ax.plot(ANGLES, y, label=f'V{version}', linewidth=1)
        print(f'V{version}: {len(y)} points -> {path.relative_to(ROOT)}')
    ax.set(xlabel='2θ (degrees)', ylabel='Estimated intensity', title='ST TIFF reconstructions, V1–V4')
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
    fig.savefig(out / 'ST_all_versions.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    main()

