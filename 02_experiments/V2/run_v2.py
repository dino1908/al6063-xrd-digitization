"""V2: trace the median position of the plotted ST curve."""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "01_original_data" / "XRD_ST_2015.tif"
OUTPUT = Path(__file__).with_name("ST_reconstructed_v2.csv")
ANGLES = np.round(np.arange(35.0, 81.85 + 1e-6, 0.05), 2)


def main():
    image = Image.open(INPUT).convert("RGB")
    pixels = np.asarray(image)
    x = np.arange(798, 2605)
    dark = np.max(pixels[250:1890, 798:2605], axis=2) < 140
    y = np.full(x.size, np.nan)
    for column in range(x.size):
        rows = np.flatnonzero(dark[:, column])
        if rows.size:
            y[column] = 250 + np.median(rows)
    good = np.isfinite(y)
    y = np.interp(x, x[good], y[good])
    angle = 30 + 60 * (x - 605.5) / (2917.0 - 605.5)
    intensity = (1869.0 - y) * 3500.0 / (1869.0 - 276.0)
    recovered = np.interp(ANGLES, angle, intensity)
    np.savetxt(OUTPUT, np.column_stack([ANGLES, recovered]), delimiter=",",
               header="angle_degrees,intensity_estimated", comments="",
               fmt=["%.4f", "%.4f"])


if __name__ == "__main__":
    main()
