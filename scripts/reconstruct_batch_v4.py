"""Digitize the five calibrated Al6063 diffraction plots."""
from pathlib import Path
import csv
import re
import numpy as np
from PIL import Image
from scipy.signal import find_peaks
from skimage.morphology import skeletonize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "raw" / "tiff"
OUTPUT_DIR = ROOT / "results" / "batch_v4"
STEP_DEGREES = 0.05

# Pixel calibrations verified from labels and tick marks in the five TIFFs.
# Each entry is (pixel_y_at_zero, pixel_y_at_reference, reference_intensity).
Y_CALIBRATION = {
    "XRD_ST_2015":              (1870.0, 276.0, 3500.0),
    "XRD_CR40_2015":            (1862.0, 398.0, 300.0),
    "XRD_CR40_annealed_2015":   (1828.0, 276.0, 1000.0),
    "XRD_UDR85_2015":           (1852.0, 276.0, 600.0),
    "XRD_UDR85_annealed_2015":  (1804.0, 366.0, 400.0),
}

# All five share this plotting template: 30° at pixel 606, 90° at pixel 2918.
X30, X90 = 606.0, 2918.0
Y_TOP, Y_BOTTOM = 250, 1890  # Exclude graph legend, axes and bottom horizontal axis.
INK_THRESHOLD = 140


def digitize_tiff(path, calibration):
    image = np.asarray(Image.open(path).convert("L"))
    if image.shape != (2379, 3390):
        raise ValueError(f"{path.name}: unexpected resolution {image.shape}; recalibration needed")
    y0, yref, ref_value = calibration
    if y0 == yref or ref_value <= 0:
        raise ValueError(f"{path.name}: invalid intensity-axis calibration")

    # Locate actual curve start/end, rather than assume every scan ends at 81.85°.
    search_left, search_right = int(X30) + 12, int(X90) - 12
    search = image[Y_TOP:Y_BOTTOM, search_left:search_right + 1] < INK_THRESHOLD
    occupied = np.flatnonzero(search.any(axis=0))
    if occupied.size < 400:
        raise ValueError(f"{path.name}: plotted line not found")
    x_start, x_end = int(occupied[0] + search_left), int(occupied[-1] + search_left)
    x_pixels = np.arange(x_start, x_end + 1)
    dark = image[Y_TOP:Y_BOTTOM, x_start:x_end + 1] < INK_THRESHOLD
    centerline = skeletonize(dark)

    center_y = np.full(len(x_pixels), np.nan)
    upper_y = np.full(len(x_pixels), np.nan)
    for i in range(len(x_pixels)):
        center_rows = np.flatnonzero(centerline[:, i])
        ink_rows = np.flatnonzero(dark[:, i])
        if center_rows.size:
            center_y[i] = Y_TOP + np.median(center_rows)
        if ink_rows.size:
            upper_y[i] = Y_TOP + ink_rows[0]

    completeness = float(np.isfinite(center_y).mean())
    if completeness < 0.95:
        raise ValueError(f"{path.name}: incomplete tracing ({completeness:.1%}); inspect source")
    for values in (center_y, upper_y):
        good = np.isfinite(values)
        values[~good] = np.interp(x_pixels[~good], x_pixels[good], values[good])

    # Original V4's centerline approach, with an adaptive tip prominence so
    # baseline noise is less likely to be mistaken for a true sharp peak.
    widths = dark.sum(axis=0)
    flat = widths[(widths >= 2) & (widths <= 8)]
    stroke_px = float(np.median(flat)) if flat.size else 4.0
    sigma = max(2.0, stroke_px)
    prominent_px = max(30.0, 0.035 * float(upper_y.max() - upper_y.min()))
    tip_peaks, _ = find_peaks(-upper_y, prominence=prominent_px, distance=30)
    corrected_y = center_y.copy()
    indices = np.arange(len(x_pixels))
    for p in tip_peaks:
        correction_px = max(0.0, center_y[p] - upper_y[p])
        corrected_y -= correction_px * np.exp(-0.5 * ((indices - p) / sigma) ** 2)

    angles = 30.0 + 60.0 * (x_pixels - X30) / (X90 - X30)
    intensities = (y0 - corrected_y) * ref_value / (y0 - yref)
    grid_start = np.ceil((angles.min() - 1e-7) / STEP_DEGREES) * STEP_DEGREES
    grid_end = np.floor((angles.max() + 1e-7) / STEP_DEGREES) * STEP_DEGREES
    grid = np.round(np.arange(grid_start, grid_end + 0.000001, STEP_DEGREES), 2)
    estimated = np.interp(grid, angles, intensities)
    clipped_fraction = float(np.mean(estimated < 0))
    estimated = np.maximum(estimated, 0.0)  # Detector counts cannot be negative.
    if len(grid) < 400 or not np.isfinite(estimated).all():
        raise ValueError(f"{path.name}: invalid reconstructed values")

    return {
        "angle": grid, "intensity": estimated, "x_pixels": x_pixels,
        "y_pixels": corrected_y, "coverage": completeness,
        "tip_count": len(tip_peaks), "stroke_px": stroke_px,
        "clipped_fraction": clipped_fraction,
        "visible_angle_range": (float(angles[0]), float(angles[-1]))
    }


def main():
    paths = sorted(list(INPUT_DIR.glob("XRD_*.tif")) + list(INPUT_DIR.glob("XRD_*.tiff")))
    if not paths:
        raise FileNotFoundError(f"No XRD_*.tif images in {INPUT_DIR}. Set INPUT_DIR above.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in paths:
        name = re.sub(r"\(\d+\)$", "", path.stem).strip()
        if name not in Y_CALIBRATION:
            print(f"SKIPPED {path.name}: intensity axis is not calibrated. Add it to Y_CALIBRATION.")
            continue
        try:
            result = digitize_tiff(path, Y_CALIBRATION[name])
        except (ValueError, OSError) as exc:
            print(f"SKIPPED {path.name}: {exc}")
            continue
        # Avoid overwriting in case two files normalize to the same sample name.
        dest = OUTPUT_DIR / f"{path.stem}_reconstructed_v4.csv"
        np.savetxt(dest,
                   np.column_stack([result["angle"], result["intensity"]]),
                   delimiter=",", header="angle_degrees,intensity_estimated",
                   comments="", fmt=["%.2f", "%.4f"])
        # QA image: red trace should overlay the original ink accurately.
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.4))
        gray = np.asarray(Image.open(path).convert("L"))
        ax1.imshow(gray, cmap="gray", vmin=0, vmax=255)
        ax1.plot(result["x_pixels"], result["y_pixels"], color="red", lw=0.75)
        ax1.set(xlim=(730, 2790), ylim=(1930, 260), title="Red trace on original TIFF")
        ax2.plot(result["angle"], result["intensity"], color="black", lw=0.85)
        ax2.set(xlabel="2θ (degrees, inferred from graph)", ylabel="Estimated intensity",
                title="Reconstructed XRD curve")
        ax2.grid(alpha=0.2)
        fig.suptitle(path.name, fontsize=11)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"{path.stem}_QA.png", dpi=150)
        plt.close(fig)

        low, high = result["visible_angle_range"]
        manifest.append({
            "filename": path.name, "csv": dest.name, "data_points": len(result["angle"]),
            "angle_first": float(result["angle"][0]),
            "angle_last": float(result["angle"][-1]),
            "max_intensity": round(float(result["intensity"].max()), 2),
            "trace_coverage_pct": round(100 * result["coverage"], 2),
            "tip_corrections": result["tip_count"],
            "stroke_px": result["stroke_px"],
            "fraction_clipped_negative": round(result["clipped_fraction"], 5),
            "y_zero_pixel": Y_CALIBRATION[name][0],
            "y_reference_pixel": Y_CALIBRATION[name][1],
            "y_reference_intensity": Y_CALIBRATION[name][2],
            "reference_available": name == "XRD_ST_2015"
        })
        print(f"OK {path.name} → {dest.name} | {len(result['angle'])} points "
              f"| {low:.2f}–{high:.2f}° visible | trace {result['coverage']:.1%}")

    if manifest:
        with (OUTPUT_DIR / "QA_summary.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
            writer.writeheader()
            writer.writerows(manifest)
    print(f"\nFinished: {len(manifest)} TIFF(s) exported to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
