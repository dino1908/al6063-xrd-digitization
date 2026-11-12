# Al6063 lattice-parameter results

The batch notebook fitted the FCC (200), (220) and (311) reflections in all five V4 profiles using the Cu Kα₁ wavelength of 1.5406 Å. The values below are in Å.

| Sample | Arithmetic mean | Nelson–Riley | Cohen-style LS with N–R |
|---|---:|---:|---:|
| ST | 4.054361 | 4.053861 | 4.053963 |
| CR40 | 4.052420 | 4.052331 | 4.052622 |
| CR40 annealed | 4.053312 | 4.052320 | 4.052584 |
| UDR85 | 4.051311 | 4.050562 | 4.051404 |
| UDR85 annealed | 4.054511 | 4.053298 | 4.053074 |

The spread across methods was 0.00029–0.00144 Å within each sample. UDR85 gave the lowest estimate by all three methods. After annealing, its estimate increased by 0.00167–0.00320 Å. The apparent change for CR40 depended on the method, ranging from −0.00004 to +0.00089 Å.

## ST reference comparison

The original and reconstructed ST scans were fitted separately with the same peak model and reflections. The largest difference in fitted 2θ was 0.00503° for (220).

| Method | Original TXT (Å) | V4 CSV (Å) | V4 minus original (Å) | Absolute relative difference |
|---|---:|---:|---:|---:|
| Arithmetic mean | 4.054448 | 4.054361 | −0.000087 | 0.00215% |
| Nelson–Riley | 4.054048 | 4.053861 | −0.000187 | 0.00461% |
| Cohen-style LS with N–R | 4.053939 | 4.053963 | +0.000024 | 0.00058% |

The ST comparison measures how well the reconstruction preserves the lattice estimate for the sample used to develop V4. The other four samples have no original numerical reference. Both extrapolations use three reflections and extend from a highest Bragg angle of about 39° to 90°. The method spread measures agreement among estimates derived from the same peaks. Instrument calibration and fitting uncertainty would be needed to assess the significance of the processing-condition differences.

## Files

- [Batch lattice parameters](all_samples_lattice_parameters.csv), [fitted peaks](all_samples_fitted_peaks.csv) and [Bragg calculations](all_samples_indexed_bragg.csv)
- [ST validation notebook](ST_reference_validation.ipynb), [lattice-parameter differences](st_reference_lattice_comparison.csv) and [fitted peak-position differences](st_reference_peak_comparison.csv)
