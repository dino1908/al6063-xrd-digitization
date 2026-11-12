"""Compare V1-V4 with the original ST numerical scan and with each other."""
from pathlib import Path
import csv
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import peak_widths

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
RAW_PATH = ROOT / "01_original_data" / "XRD_Al6063_ST_2015_06_08_ASCII.txt"
VERSION_PATHS = {
    version: ROOT / "02_experiments" / f"V{version}" / f"ST_reconstructed_v{version}.csv"
    for version in range(1, 5)
}


def load_raw(path):
    text = path.read_text(errors="replace")
    rows = []
    for line in text.split("[Data]", 1)[1].splitlines():
        match = re.fullmatch(r"\s*([\d.]+)\s*,\s*([\d.]+)\s*,?\s*", line)
        if match:
            rows.append((float(match.group(1)), float(match.group(2))))
    return np.asarray(rows)


def peak_values(angles, intensity, center, left, right):
    near = (angles >= center - 0.35) & (angles <= center + 0.35)
    index = np.where(near)[0][np.argmax(intensity[near])]
    fwhm = peak_widths(intensity, [index], rel_height=0.5)[0][0] * np.median(np.diff(angles))
    within = (angles >= left) & (angles <= right)
    x, y = angles[within], intensity[within]
    background = np.interp(x, [x[0], x[-1]],
                           [np.median(y[:3]), np.median(y[-3:])])
    area = np.trapezoid(np.maximum(y - background, 0), x)
    return angles[index], intensity[index], fwhm, area


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    raw = load_raw(RAW_PATH)
    angles, original = raw.T
    versions = {
        version: np.loadtxt(path, delimiter=",", skiprows=1)
        for version, path in VERSION_PATHS.items()
    }

    metric_rows = []
    for version, values in versions.items():
        error = values[:, 1] - original
        metric_rows.append({
            "version": f"V{version}",
            "points": len(error),
            "mae": f"{np.mean(np.abs(error)):.8f}",
            "rmse": f"{np.sqrt(np.mean(error ** 2)):.8f}",
            "correlation": f"{np.corrcoef(original, values[:, 1])[0, 1]:.8f}",
            "r2": f"{1 - np.sum(error ** 2) / np.sum((original - original.mean()) ** 2):.8f}",
            "intensity_sum_error_pct": f"{100 * (values[:, 1].sum() / original.sum() - 1):.8f}",
        })
    write_csv(HERE / "validation_metrics.csv", list(metric_rows[0]), metric_rows)

    peaks = [("200", 44.70, 44.1, 45.3), ("220", 65.05, 64.3, 65.8),
             ("311", 78.20, 77.5, 78.95), ("weak_58", 58.05, 57.5, 58.6)]
    peak_rows = []
    for name, center, left, right in peaks:
        reference = peak_values(angles, original, center, left, right)
        for version, values in versions.items():
            estimated = peak_values(values[:, 0], values[:, 1], center, left, right)
            peak_rows.append({
                "peak": name,
                "version": f"V{version}",
                "original_angle": f"{reference[0]:.7f}",
                "estimated_angle": f"{estimated[0]:.7f}",
                "angle_error_degrees": f"{estimated[0] - reference[0]:.7f}",
                "height_error_pct": f"{100 * (estimated[1] / reference[1] - 1):.7f}",
                "fwhm_error_pct": f"{100 * (estimated[2] / reference[2] - 1):.7f}",
                "area_error_pct": f"{100 * (estimated[3] / reference[3] - 1):.7f}",
            })
    write_csv(HERE / "peak_validation.csv", list(peak_rows[0]), peak_rows)

    pointwise_fields = ["angle_degrees", "original_intensity"]
    pointwise_fields += [f"v{version}_estimated" for version in versions]
    pointwise_fields += [f"v{version}_error" for version in versions]
    pointwise_rows = []
    for index, angle in enumerate(angles):
        row = {"angle_degrees": f"{angle:.2f}",
               "original_intensity": f"{original[index]:.4f}"}
        for version, values in versions.items():
            row[f"v{version}_estimated"] = f"{values[index, 1]:.4f}"
            row[f"v{version}_error"] = f"{values[index, 1] - original[index]:.4f}"
        pointwise_rows.append(row)
    write_csv(HERE / "pointwise_comparison.csv", pointwise_fields, pointwise_rows)

    figure, axis = plt.subplots(figsize=(11, 4.5))
    axis.plot(angles, original, color="black", linewidth=1.4, label="Original TXT")
    for version, values in versions.items():
        axis.plot(values[:, 0], values[:, 1], linestyle="--", linewidth=0.9,
                  label=f"V{version}")
    axis.set(xlabel="2θ (degrees)", ylabel="Intensity",
             title="ST reconstruction methods compared with original numerical data")
    axis.grid(alpha=0.2)
    axis.legend(ncol=3)
    figure.tight_layout()
    figure.savefig(HERE / "versions_vs_original.png", dpi=170)
    plt.close(figure)

    zoom = (angles >= 64.55) & (angles <= 65.55)
    figure, axis = plt.subplots(figsize=(10, 4.5))
    axis.plot(angles[zoom], original[zoom], color="black", marker=".",
              linewidth=1.4, label="Original TXT")
    for version, values in versions.items():
        axis.plot(values[:, 0][zoom], values[:, 1][zoom], linestyle="--",
                  marker=".", markersize=2, label=f"V{version}")
    axis.set(xlabel="2θ (degrees)", ylabel="Intensity",
             title="V1-V4 comparison around the 65° peak")
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(HERE / "peak_65_comparison.png", dpi=170)
    plt.close(figure)

    for version, values in versions.items():
        folder = VERSION_PATHS[version].parent
        write_csv(folder / "validation_metrics.csv", list(metric_rows[0]),
                  [metric_rows[version - 1]])
        selected = [row for row in peak_rows if row["version"] == f"V{version}"]
        write_csv(folder / "peak_validation.csv", list(peak_rows[0]), selected)
        figure, axis = plt.subplots(figsize=(10, 4.3))
        axis.plot(angles, original, color="black", linewidth=1.3, label="Original TXT")
        axis.plot(values[:, 0], values[:, 1], color="#00727a", linestyle="--",
                  linewidth=1.0, label=f"V{version}")
        axis.set(xlabel="2θ (degrees)", ylabel="Intensity",
                 title=f"V{version} reconstruction compared with original ST data")
        axis.grid(alpha=0.2)
        axis.legend()
        figure.tight_layout()
        figure.savefig(folder / "comparison_with_original.png", dpi=160)
        plt.close(figure)


if __name__ == "__main__":
    main()
