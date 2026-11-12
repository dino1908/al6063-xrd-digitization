"""V4: skeleton centerline with refined calibration and peak-tip correction."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import find_peaks
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "01_original_data" / "XRD_ST_2015.tif"
OUTPUT = Path(__file__).with_name("ST_reconstructed_v4.csv")
ANGLES = np.round(np.arange(35.0, 81.85 + 1e-6, 0.05), 2)


def main():
    pixels = np.asarray(Image.open(INPUT).convert("L"))
    x = np.arange(798, 2605)
    dark = pixels[250:1890, 798:2605] < 140
    skeleton = skeletonize(dark)
    upper = np.full(x.size, np.nan)
    middle = np.full(x.size, np.nan)
    for column in range(x.size):
        rows = np.flatnonzero(dark[:, column])
        center_rows = np.flatnonzero(skeleton[:, column])
        if rows.size:
            upper[column] = 250 + rows.min()
        if center_rows.size:
            middle[column] = 250 + np.median(center_rows)
    for values in (upper, middle):
        good = np.isfinite(values)
        values[~good] = np.interp(x[~good], x[good], values[good])
    widths = dark.sum(axis=0)
    flat_widths = widths[(widths >= 2) & (widths <= 8)]
    sigma = max(2.0, float(np.median(flat_widths)))
    corrected = middle.copy()
    tips, _ = find_peaks(-upper, prominence=30, distance=30)
    indices = np.arange(x.size)
    for tip in tips:
        correction = max(0.0, middle[tip] - upper[tip])
        corrected -= correction * np.exp(-0.5 * ((indices - tip) / sigma) ** 2)
    angle = 30 + 60 * (x - 606.0) / (2918.0 - 606.0)
    intensity = (1870.0 - corrected) * 3500.0 / (1870.0 - 276.0)
    recovered = np.maximum(0, np.interp(ANGLES, angle, intensity))
    np.savetxt(OUTPUT, np.column_stack([ANGLES, recovered]), delimiter=",",
               header="angle_degrees,intensity_estimated", comments="",
               fmt=["%.2f", "%.4f"])


if __name__ == "__main__":
    main()
