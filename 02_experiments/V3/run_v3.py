"""V3: median trace with a narrow correction at peak tips."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "01_original_data" / "XRD_ST_2015.tif"
OUTPUT = Path(__file__).with_name("ST_reconstructed_v3.csv")
ANGLES = np.round(np.arange(35.0, 81.85 + 1e-6, 0.05), 2)


def main():
    pixels = np.asarray(Image.open(INPUT).convert("RGB"))
    x = np.arange(798, 2605)
    dark = np.max(pixels[250:1890, 798:2605], axis=2) < 140
    upper = np.full(x.size, np.nan)
    middle = np.full(x.size, np.nan)
    for column in range(x.size):
        rows = np.flatnonzero(dark[:, column])
        if rows.size:
            upper[column] = 250 + rows.min()
            middle[column] = 250 + np.median(rows)
    for values in (upper, middle):
        good = np.isfinite(values)
        values[~good] = np.interp(x[~good], x[good], values[good])
    corrected = middle.copy()
    tips, _ = find_peaks(-upper, prominence=30, distance=30)
    indices = np.arange(x.size)
    for tip in tips:
        corrected -= (middle[tip] - upper[tip]) * np.exp(
            -0.5 * ((indices - tip) / 2.0) ** 2
        )
    angle = 30 + 60 * (x - 605.5) / (2917.0 - 605.5)
    intensity = (1869.0 - corrected) * 3500.0 / (1869.0 - 276.0)
    recovered = np.interp(ANGLES, angle, intensity)
    np.savetxt(OUTPUT, np.column_stack([ANGLES, recovered]), delimiter=",",
               header="angle_degrees,intensity_estimated", comments="",
               fmt=["%.4f", "%.4f"])


if __name__ == "__main__":
    main()
