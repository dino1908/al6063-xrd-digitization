"""Build the technical report from the validation and batch results."""
import csv
from pathlib import Path
from textwrap import wrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
NAVY = "#163249"
INK = "#182732"
MUTED = "#4d6574"
TEAL = "#006d72"
RULE = "#d7e2e7"
COLORS = ["#a03e39", "#9b6321", "#6172a4", TEAL]
NAMES = ["ST", "CR40", "CR40 annealed", "UDR85", "UDR85 annealed"]
STEMS = ["ST", "CR40", "CR40_annealed", "UDR85", "UDR85_annealed"]


def read_rows(name):
    with (ROOT / "analysis" / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def page(number, section, title):
    fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
    fig.text(.08, .952, "AL6063  /  X-RAY DIFFRACTION", fontsize=9, weight="bold", color=TEAL)
    fig.text(.08, .899, title, fontsize=23, weight="bold", color=NAVY, linespacing=1.15, va="top")
    for y in (.934, .056):
        fig.add_artist(plt.Line2D([.08, .92], [y, y], transform=fig.transFigure, color=RULE))
    fig.text(.08, .031, section, color=MUTED, fontsize=9)
    fig.text(.92, .031, f"{number} / 3", ha="right", color=MUTED, fontsize=9)
    return fig


def paragraph(fig, y, value, *, size=10.5, width=90, color=INK):
    lines = wrap(value, width, break_long_words=False)
    fig.text(.08, y, "\n".join(lines), va="top", fontsize=size, color=color, linespacing=1.46)
    return y - len(lines) * .0185 - .023


def section(fig, y, title):
    fig.text(.08, y, title, fontsize=12, weight="bold", va="top", color=NAVY)
    return y - .031


def table(fig, top, headers, rows, widths):
    height = .032 * (len(rows) + 1)
    ax = fig.add_axes([.08, top - height, .84, height])
    ax.axis("off")
    grid = ax.table(cellText=rows, colLabels=headers, colWidths=widths, cellLoc="right",
                    bbox=[0, 0, 1, 1])
    grid.auto_set_font_size(False)
    grid.set_fontsize(9)
    for (row, col), cell in grid.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_facecolor(NAVY if row == 0 else ("#edf4f5" if row % 2 else "#f7f9fa"))
        cell.set_text_props(color="white" if row == 0 else INK,
                            weight="bold" if row == 0 else "normal",
                            ha="left" if col == 0 else "right")


def style_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color(RULE)
    ax.tick_params(labelsize=9, colors=INK)
    ax.grid(axis="y", color=RULE, linewidth=.55)
    ax.set_axisbelow(True)


def benchmark():
    rows = read_rows("st_validation_metrics.csv")
    fig = page(1, "Data and reconstruction", "Reconstructing Al6063 diffraction\nprofiles from archived TIFF plots")
    y = section(fig, .791, "Abstract")
    y = paragraph(fig, y, "Five archived Al6063 X-ray diffraction profiles were digitized from TIFF plots. Four tracing methods were evaluated against the original solution-treated (ST) scan. The skeleton-based method reduced the pointwise intensity RMSE from 48.884 to 9.244 counts and reproduced the grid positions of three principal maxima. The four rolled and annealed profiles could be checked against their TIFFs. Their numerical measurement errors remain unknown.")
    y = section(fig, y, "Source data and calibration")
    y = paragraph(fig, y, "The 2015 archive contains five 3390 × 2379 pixel TIFF plots and one Bruker RAW4.00 ASCII export. The ST export contains 938 readings from 35.00° to 81.85° in 0.05° 2θ steps. The header lists Cu Kα₁ at 1.5406 Å. The TIFFs provide the source traces. The export supplies the numerical comparison.")
    y = paragraph(fig, y, "The batch method maps horizontal pixels 606 and 2918 to 30° and 90° 2θ. Each image has its own two-point intensity calibration. The algorithm thresholds the cropped grayscale plot, skeletonizes the stroke, fills gaps by interpolation, and applies a local correction at prominent tips before resampling at 0.05°.")
    y = section(fig, y, "ST benchmark across 938 matched angles")
    methods = ["Upper ink edge", "Column median", "Median with tip correction", "Skeleton, new calibration and tip correction"]
    summary = [[f"{r['version']}  {method}", f"{float(r['mae']):.3f}",
                f"{float(r['rmse']):.3f}", f"{float(r['correlation']):.5f}",
                f"{float(r['intensity_sum_error_pct']):+.2f}%"]
               for r, method in zip(rows, methods)]
    table(fig, y, ["Tracing method", "MAE", "RMSE", "Pearson r", "Sum error"], summary,
          [.50, .105, .105, .135, .155])
    paragraph(fig, y - .146 - .038,
              "MAE and RMSE use the pointwise intensity residual in counts. Sum error is the signed difference in summed intensity divided by the reference sum. The ST scan informed method selection and is an in-sample benchmark. V3 recovered peak height at 65.05° but slightly increased scan-wide RMSE relative to V2.", size=9.2, width=105, color=MUTED)
    return fig


def peak_validation():
    fig = page(2, "Numerical validation", "Solution-treated reference scan")
    data = np.genfromtxt(ROOT / "experiments/st_versions/pointwise_errors.csv", delimiter=",", names=True)
    x = data["angle_degrees"]
    raw = data["original_counts"]
    overlay = fig.add_axes([.13, .665, .77, .165])
    overlay.plot(x, raw, color=INK, lw=1.3, label="Bruker ST")
    overlay.plot(x, data["v4_estimated"], color=TEAL, ls="--", lw=1.0, label="V4")
    overlay.set(xlabel="2θ (°)", ylabel="Intensity (counts)", xlim=(35, 82))
    overlay.legend(frameon=False, ncol=2, fontsize=9)
    style_axes(overlay)
    zoom = fig.add_axes([.13, .414, .77, .167])
    mask = (x >= 64.55) & (x <= 65.55)
    zoom.plot(x[mask], raw[mask], color=INK, lw=1.5, marker=".", label="Bruker ST")
    for i, color in enumerate(COLORS, 1):
        zoom.plot(x[mask], data[f"v{i}_estimated"][mask], color=color, lw=1, ls="--", label=f"V{i}")
    zoom.set(xlabel="2θ (°)", ylabel="Intensity (counts)")
    zoom.legend(frameon=False, ncol=5, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.005))
    style_axes(zoom)
    paragraph(fig, .626, "Figure 1. Original ST scan overlaid with the V4 reconstruction.", size=9.2, color=MUTED)
    paragraph(fig, .373, "Figure 2. Detail of the (220) reflection for all four tracing methods.", size=9.2, color=MUTED)
    rows = [r for r in read_rows("st_peak_validation.csv") if r["version"] == "V4" and r["peak"] != "weak_58"]
    values = [[f"({r['peak']})", f"{float(r['orig_angle']):.2f}°",
               f"{float(r['estimated_angle']):.2f}°",
               *[f"{float(r[k]):+.2f}%" for k in ("height_error_pct", "fwhm_error_pct", "area_error_pct")]]
              for r in rows]
    table(fig, .329, ["Al reflection", "Raw 2θ", "V4 2θ", "Height error", "Width error", "Area error"],
          values, [.20, .14, .14, .17, .18, .17])
    paragraph(fig, .176, "Al reflection assignments are tentative. Positions are grid maxima and widths are measured at half prominence. Areas use fixed windows and a linear background estimated from the median of three points at either end. V4 reproduced all three grid maxima, but the weak feature near 58° shifted by 0.05° and its area was 8.88% higher.", size=9.4, width=104)
    return fig


def batch_results():
    fig = page(3, "Batch results and limitations", "Five reconstructed profiles")
    for i, (name, stem) in enumerate(zip(NAMES, STEMS)):
        ax = fig.add_axes([.13, .744 - i * .080, .77, .075])
        path = ROOT / "results/batch_v4" / f"XRD_{stem}_2015_reconstructed_v4.csv"
        x, y = np.loadtxt(path, delimiter=",", skiprows=1).T
        ax.plot(x, y / y.max(), color=TEAL, lw=1)
        ax.text(.985, .72, name, transform=ax.transAxes, color=NAVY, fontsize=9,
                weight="bold", ha="right")
        ax.set(xlim=(35, 85), ylim=(-.05, 1.10), yticks=[0, 1])
        ax.xaxis.set_major_locator(MaxNLocator(10))
        ax.tick_params(labelbottom=i == 4, bottom=i == 4)
        style_axes(ax)
    ax.set_xlabel("2θ (°)")
    fig.text(.075, .615, "Intensity / scan maximum", ha="center", va="center", rotation=90, fontsize=9)
    y = paragraph(fig, .378, "Figure 3. V4 profiles scaled to each scan's own maximum. The ST grid ends at 81.85°. The other four span 35.00° to 85.00° and contain 1,001 interpolated values each.", size=9.2, width=104, color=MUTED)
    y = section(fig, y, "Image agreement and scope")
    y = paragraph(fig, y, "The five batch CSVs reproduced the archived CSVs byte for byte. Mapping their points back to the source images flagged one UDR85 point at 78.25°, 21.10 pixels from the nearest dark stroke. The other samples had no points more than three pixels from the nearest dark stroke.", size=10, width=100)
    paragraph(fig, y, "The plotted profiles support comparison of prominent peak positions and shapes. ST was the only numerical reference. The 0.05° export interval for the four other plots gives no independent information about their acquisition step. Quantitative texture, microstrain and crystallite size require additional acquisition or calibration data.", size=10, width=100)
    return fig


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    output = ROOT / "report" / "Al6063_XRD_Technical_Report.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output, metadata={"Title": "Reconstructing Al6063 diffraction profiles from archived TIFF plots"}) as pdf:
        for i, build in enumerate((benchmark, peak_validation, batch_results), 1):
            fig = build()
            pdf.savefig(fig)
            if args.preview_dir:
                args.preview_dir.mkdir(parents=True, exist_ok=True)
                fig.savefig(args.preview_dir / f"page_{i}.png", dpi=115)
            plt.close(fig)


if __name__ == "__main__":
    main()
