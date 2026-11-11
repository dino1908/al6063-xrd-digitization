# ST experiment log

The original ST TIFF is the image input for all four versions. The Bruker text export is reserved for the validation script and never read by the extraction routines.

1. **V1:** For each x-pixel column, record the topmost dark pixel. This biases steep shoulders upward and inflates their apparent width.
2. **V2:** Replace the upper edge with the median position of dark ink pixels. This better approximates the plotted line's middle.
3. **V3:** Apply a narrow local peak-tip correction on top of V2. It helps recover peak height but not overall RMSE.
4. **V4:** Thin the image stroke to a skeleton, refine the axis calibration from TIFF ticks, and apply a measured-stroke-width tip correction.

The corresponding `ST_v1.csv` through `ST_v4.csv` are kept as direct reproducibility artifacts. `pointwise_errors.csv` stores all 938 original counts, four sets of digitized estimates and their differences. Figures compare the same original intensity scale. See the README and `analysis/st_validation_metrics.csv` for quantitative results.
