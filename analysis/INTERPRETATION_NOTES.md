# Reading the validation files

The numerical comparisons use the *same angles* for the original ST scan and each reconstructed ST CSV. MAE measures the average absolute count difference; RMSE gives larger residuals more weight; correlation describes curve-shape similarity. A high correlation can coexist with substantial errors in faint features or individual points.

`st_peak_validation.csv` evaluates maxima, half-prominence FWHM and background-subtracted areas in fixed windows. These are descriptive metrics on the existing scan—not refined instrumental line profiles or physical crystallite-size estimates. The (200), (220) and (311) labels refer to likely FCC Al assignments and are not intended as an exhaustive phase-identification exercise. The weak ~58° feature is intentionally not assigned a Miller index.

`all_samples_image_qa.csv` measures each reconstructed sample point's distance back to the black ink in the source TIFF. This catches some tracing artifacts, notably one UDR85 point near 78.25° at about 21 pixels, but *cannot* certify recovery of the original detector counts. A point lying directly on the rasterized ink may still be a biased estimate of an experimental measurement.

The raw ST scan was used to compare and choose extraction methods. Its strong final agreement should therefore not be treated as an independent generalization experiment. In particular, the ~0.61% whole-scan intensity difference should not be extrapolated to the other four plots.

`drive_reproduction_check.csv` records the exact rerun match against the separately saved Google Drive CSVs and manifest. SHA-256 equality verifies reproducibility of those files only.
