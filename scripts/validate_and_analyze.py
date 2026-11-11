"""Rebuild validation tables and figures from the original ST scan and digitized TIFFs.

The instrument data are used here only, never by the reconstruction scripts.
We report image-tracing agreement separately from experimental accuracy.
"""
from pathlib import Path
import csv
import hashlib
import re
import sys

import numpy as np
import pandas as pd
from PIL import Image
from scipy.signal import peak_widths
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'analysis'
EXPERIMENTS = ROOT / 'experiments' / 'st_versions'
BATCH = ROOT / 'results' / 'batch_v4'
RAW = ROOT / 'data' / 'raw'
ANALYSIS.mkdir(parents=True, exist_ok=True)

# Keep the method independent of the historical raw-file parser version.
def load_bruker(path):
    content = Path(path).read_text(errors='replace')
    if '[Data]' not in content:
        raise ValueError('Instrument export has no [Data] section')
    rows = []
    for line in content.split('[Data]', 1)[1].splitlines():
        match = re.fullmatch(r'\s*([\d.]+)\s*,\s*([\d.]+)\s*,?\s*', line)
        if match:
            rows.append((float(match.group(1)), float(match.group(2))))
    if len(rows) != 938:
        raise ValueError(f'Expected 938 ST measurements; found {len(rows)}')
    return np.asarray(rows)


def load_csv(path):
    arr = np.loadtxt(path, delimiter=',', skiprows=1)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError(f'Expected two CSV columns in {path}')
    return arr


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def metric_row(name, x, y, reference):
    if len(x) != len(reference) or not np.allclose(x, reference[:, 0], atol=1e-7, rtol=0):
        raise ValueError(f'{name}: reconstruction and raw scan grids differ')
    truth = reference[:, 1]
    err = y - truth
    return dict(version=name, points=len(x), mae=float(np.mean(np.abs(err))),
                rmse=float(np.sqrt(np.mean(err**2))),
                correlation=float(np.corrcoef(truth, y)[0, 1]),
                r2=float(1-np.sum(err**2)/np.sum((truth-np.mean(truth))**2)),
                intensity_sum_error_pct=float(100 * (np.sum(y)/np.sum(truth)-1)),
                mean_signed_error=float(np.mean(err)))


def peak_attributes(angles, intensities, center, left, right):
    # Max among measured values in a small fixed window around the nominal peak.
    near = (angles >= center - .35) & (angles <= center + .35)
    loc = np.where(near)[0][np.argmax(intensities[near])]
    fwhm = peak_widths(intensities, [loc], rel_height=.5)[0][0] * np.median(np.diff(angles))
    within = (angles >= left) & (angles <= right)
    xx, yy = angles[within], intensities[within]
    # Approximate linearly varying background between the window endpoints.
    bg = np.interp(xx, [xx[0], xx[-1]],
                   [np.median(yy[:3]), np.median(yy[-3:])])
    area = float(np.trapezoid(np.maximum(yy-bg, 0), xx))
    return float(angles[loc]), float(intensities[loc]), float(fwhm), area


raw = load_bruker(RAW/'instrument/XRD_Al6063_ST_2015_06_08_ASCII.txt')
x = raw[:, 0]
versions = {k: load_csv(EXPERIMENTS / f'ST_v{k}.csv') for k in range(1, 5)}
versions['batch_V4'] = load_csv(BATCH/'XRD_ST_2015_reconstructed_v4.csv')
metric_rows = [metric_row(f'V{key}' if isinstance(key, int) else key,
                          arr[:, 0], arr[:, 1], raw)
               for key, arr in versions.items()]
metrics = pd.DataFrame(metric_rows)
metrics.to_csv(ANALYSIS/'st_validation_metrics.csv', index=False, float_format='%.8f')

differences = pd.DataFrame({'angle_degrees':x, 'original_counts':raw[:, 1]})
for k, arr in versions.items():
    name = f'v{k}' if isinstance(k, int) else k.lower()
    differences[name+'_estimated'] = arr[:, 1]
    differences[name+'_error'] = arr[:, 1]-raw[:, 1]
differences.to_csv(EXPERIMENTS/'pointwise_errors.csv', index=False, float_format='%.4f')

# All versions have the same fixed peak definitions and background windows.
peaks = [('200',44.70,44.1,45.3),('220',65.05,64.3,65.8),
         ('311',78.20,77.5,78.95),('weak_58',58.05,57.5,58.6)]
peak_rows=[]
for name, center, lo, hi in peaks:
    orig = peak_attributes(x, raw[:, 1], center, lo, hi)
    for key, arr in versions.items():
        p = peak_attributes(arr[:, 0], arr[:, 1], center, lo, hi)
        peak_rows.append(dict(peak=name, version=f'V{key}' if isinstance(key,int) else key,
                              orig_angle=orig[0], estimated_angle=p[0],
                              angle_error_degrees=p[0]-orig[0],
                              orig_height=orig[1], estimated_height=p[1],
                              height_error_pct=(p[1]/orig[1]-1)*100,
                              orig_fwhm_degrees=orig[2], estimated_fwhm_degrees=p[2],
                              fwhm_error_pct=(p[2]/orig[2]-1)*100,
                              orig_integrated_area=orig[3], estimated_integrated_area=p[3],
                              area_error_pct=(p[3]/orig[3]-1)*100))
pd.DataFrame(peak_rows).to_csv(ANALYSIS/'st_peak_validation.csv',index=False,float_format='%.7f')

# Separate high-intensity peak regions from the rest of the curve.
peak_region = np.zeros(len(x), dtype=bool)
for _, _, lo, hi in peaks[:3]:
    peak_region |= (x>=lo)&(x<=hi)
zone_rows=[]
for key,arr in versions.items():
    for zone,mask in [('main_peak_windows',peak_region),('outside_main_peaks',~peak_region)]:
        delta = arr[:,1][mask]-raw[:,1][mask]
        zone_rows.append(dict(version=f'V{key}' if isinstance(key,int) else key,
                              zone=zone, points=int(mask.sum()),
                              mae=float(np.mean(np.abs(delta))),
                              rmse=float(np.sqrt(np.mean(delta**2)))))
pd.DataFrame(zone_rows).to_csv(ANALYSIS/'st_region_errors.csv',index=False,float_format='%.6f')

# The full overlay and a peak zoom make the residual shape easy to inspect.
fig, ax = plt.subplots(figsize=(11,4.4))
ax.plot(x,raw[:,1],label='Original Bruker ST',color='black',lw=1.4)
for k in (1,2,3,4):
    ax.plot(x,versions[k][:,1],lw=0.85,ls='--',alpha=.7,label=f'V{k}')
ax.set(xlabel='2θ (degrees)',ylabel='Intensity',title='Original ST scan and four TIFF reconstructions')
ax.legend(ncol=3);ax.grid(alpha=.2);fig.tight_layout()
fig.savefig(EXPERIMENTS/'st_versions_vs_raw.png',dpi=160);plt.close(fig)

zoom=(x>=64.55)&(x<=65.55)
fig,ax=plt.subplots(figsize=(10,4.5))
ax.plot(x[zoom],raw[:,1][zoom],color='black',marker='.',lw=1.5,label='Original Bruker ST')
for k in (1,2,3,4):
    ax.plot(x[zoom],versions[k][:,1][zoom],marker='.',markersize=2,ls='--',label=f'V{k}')
ax.set(xlabel='2θ (degrees)',ylabel='Intensity',title='Evolution of the 65° peak reconstruction')
ax.legend();ax.grid(alpha=.2);fig.tight_layout()
fig.savefig(EXPERIMENTS/'st_220_peak_comparison.png',dpi=170);plt.close(fig)

# Image-level consistency: project each CSV point back onto the plot, then
# measure its pixel distance to the nearest dark stroke. This is not raw-data validation.
cal = {
    'XRD_ST_2015':(1870.0,276.0,3500.0),
    'XRD_CR40_2015':(1862.0,398.0,300.0),
    'XRD_CR40_annealed_2015':(1828.0,276.0,1000.0),
    'XRD_UDR85_2015':(1852.0,276.0,600.0),
    'XRD_UDR85_annealed_2015':(1804.0,366.0,400.0),
}
sample_rows=[]
image_rows=[]
for stem,(y0,yref,scale) in cal.items():
    a=load_csv(BATCH/f'{stem}_reconstructed_v4.csv')
    img=np.asarray(Image.open(RAW/'tiff'/f'{stem}.tif').convert('L'))
    # The label-free graph area has the source stroke plus its curves.
    crop=img[250:1890,780:2750]
    dist=distance_transform_edt(crop>=140)
    px=606.0+(a[:,0]-30.0)*(2918.0-606.0)/60.0 - 780
    py=y0-a[:,1]*(y0-yref)/scale - 250
    xi=np.clip(np.rint(px).astype(int),0,dist.shape[1]-1)
    yi=np.clip(np.rint(py).astype(int),0,dist.shape[0]-1)
    distances=dist[yi,xi]
    sample_rows.append(dict(sample=stem,measurements=len(a),angle_min=a[0,0],angle_max=a[-1,0],
                            maximum_intensity=np.max(a[:,1]),angle_at_max=a[np.argmax(a[:,1]),0],
                            nearest_ink_median_px=np.median(distances),
                            nearest_ink_max_px=np.max(distances),
                            points_gt_3px=int(np.sum(distances>3))))
    for angle,intensity,d in zip(a[:,0],a[:,1],distances):
        if d>3:
            image_rows.append(dict(sample=stem,angle=float(angle),intensity=float(intensity),
                                   distance_to_nearest_ink_px=float(d)))
pd.DataFrame(sample_rows).to_csv(ANALYSIS/'all_samples_image_qa.csv',index=False,float_format='%.5f')
pd.DataFrame(image_rows, columns=['sample','angle','intensity','distance_to_nearest_ink_px']).to_csv(
    ANALYSIS/'image_qa_outliers.csv',index=False,float_format='%.5f')

# The Drive outputs were fetched independently for cross-run reproducibility.
DRIVE = Path('/mnt/data/projectA_drive_check')
drive_rows=[]
for path in sorted(BATCH.glob('*.csv')):
    counterpart=DRIVE/path.name
    if counterpart.exists():
        drive_rows.append(dict(filename=path.name,local_sha256=sha256(path),
                               archived_drive_sha256=sha256(counterpart),
                               byte_identical=path.read_bytes()==counterpart.read_bytes()))
if drive_rows:
    pd.DataFrame(drive_rows).to_csv(ANALYSIS/'drive_reproduction_check.csv',index=False)

hash_rows=[]
for path in sorted(RAW.glob('*/*')):
    hash_rows.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha256(path)))
pd.DataFrame(hash_rows).to_csv(ANALYSIS/'source_sha256_manifest.csv',index=False)

print('\nST validation metrics')
print(metrics.to_string(index=False,float_format=lambda v:f'{v:.5f}'))
print('\nImage QA')
print(pd.DataFrame(sample_rows).to_string(index=False,float_format=lambda v:f'{v:.3f}'))
if drive_rows:
    print('\nDrive agreement:',sum(v['byte_identical'] for v in drive_rows),'/',len(drive_rows),'CSV files')
