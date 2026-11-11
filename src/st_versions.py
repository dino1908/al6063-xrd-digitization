"""Historical ST digitization experiments, versions 1–4.

These methods are deliberately kept separate so the progression can be reproduced.
The only input to reconstruction is the ST TIFF. The Bruker export is reserved
for evaluation; it is not used to set any recovered intensity values.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import find_peaks
from skimage.morphology import skeletonize

ANGLES = np.round(np.arange(35, 81.85 + 1e-6, 0.05), 2)


def _fill(x, y):
    ok = np.isfinite(y)
    if ok.mean() < 0.95:
        raise ValueError(f"Line detection covers only {ok.mean():.1%} of columns")
    return np.interp(x, x[ok], y[ok])


def reconstruct_st(tiff_path: str | Path, version: int) -> np.ndarray:
    """Return 938 TIFF-derived intensities on the ST scan's angle grid.

    V1: top edge of black ink, original axis calibration.
    V2: median ink pixel in each column, same calibration.
    V3: V2 plus local peak-tip restoration.
    V4: adjusted calibration, skeleton centerline, broader tip restoration.
    """
    if version not in (1, 2, 3, 4):
        raise ValueError("Expected version 1, 2, 3 or 4")
    path = Path(tiff_path)
    image = Image.open(path)
    if image.size != (3390, 2379):
        raise ValueError(f"Unexpected TIFF resolution: {image.size}")

    x_left, x_right = 798, 2604
    y_top, y_bottom = 250, 1890
    x = np.arange(x_left, x_right + 1)
    if version == 4:
        gray = np.asarray(image.convert('L'))
        dark = gray[y_top:y_bottom, x_left:x_right + 1] < 140
    else:
        rgb = np.asarray(image.convert('RGB'))
        dark = np.max(rgb[y_top:y_bottom, x_left:x_right + 1], axis=2) < 140

    top = np.full(x.size, np.nan)
    middle = np.full(x.size, np.nan)
    skeleton = skeletonize(dark) if version == 4 else None
    for i in range(x.size):
        ink_rows = np.flatnonzero(dark[:, i])
        if not ink_rows.size:
            continue
        top[i] = y_top + ink_rows.min()
        if version == 4:
            sk_rows = np.flatnonzero(skeleton[:, i])
            if sk_rows.size:
                middle[i] = y_top + np.median(sk_rows)
        else:
            middle[i] = y_top + np.median(ink_rows)

    top = _fill(x, top)
    middle = _fill(x, middle)

    if version == 1:
        y = top
    elif version == 2:
        y = middle
    else:
        y = middle.copy()
        tips, _ = find_peaks(-top, prominence=30, distance=30)
        if version == 3:
            sigma = 2.0
        else:
            widths = dark.sum(axis=0)
            flat_widths = widths[(widths >= 2) & (widths <= 8)]
            sigma = max(2.0, float(np.median(flat_widths)) if flat_widths.size else 4.0)
        indices = np.arange(x.size)
        for p in tips:
            delta = middle[p] - top[p] if version == 3 else max(0.0, middle[p] - top[p])
            y -= delta * np.exp(-0.5 * ((indices - p) / sigma) ** 2)

    if version == 4:
        x30, x90, y0, y3500 = 606.0, 2918.0, 1870.0, 276.0
    else:
        x30, x90, y0, y3500 = 605.5, 2917.0, 1869.0, 276.0
    angle = 30 + 60 * (x - x30) / (x90 - x30)
    intensity = (y0 - y) * 3500.0 / (y0 - y3500)
    recovered = np.interp(ANGLES, angle, intensity)
    return np.maximum(0, recovered) if version == 4 else recovered
