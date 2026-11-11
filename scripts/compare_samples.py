"""Descriptive cross-sample plots. Relative intensities are not texture quantification."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'results/batch_v4'
OUT=ROOT/'analysis'
SAMPLES=[('ST','XRD_ST_2015'),('CR40','XRD_CR40_2015'),
         ('CR40 annealed','XRD_CR40_annealed_2015'),('UDR85','XRD_UDR85_2015'),
         ('UDR85 annealed','XRD_UDR85_annealed_2015')]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CURVES={name:np.loadtxt(SOURCE/f'{stem}_reconstructed_v4.csv',skiprows=1,delimiter=',') for name,stem in SAMPLES}

    fig,axes=plt.subplots(2,1,figsize=(11,8),sharex=True)
    for name,arr in CURVES.items():
        axes[0].plot(arr[:,0],arr[:,1],label=name,lw=1)
        axes[1].plot(arr[:,0],arr[:,1]/arr[:,1].max(),label=name,lw=1)
    axes[0].set(ylabel='Digitized intensity (plot units)',title='Al6063 XRD TIFF reconstructions')
    axes[1].set(xlabel='2θ (degrees)',ylabel='Intensity / within-scan maximum',
               title='Normalized for comparing peak patterns, not absolute amounts')
    for a in axes:
        a.legend(ncol=3,fontsize=8)
        a.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT/'five_sample_patterns.png',dpi=180)
    plt.close(fig)

    # Peak maxima in deliberately broad windows; weak/overlapping reflections may
    # not resolve into a unique measured peak on every plot.
    centers={'possible_111':38.45,'200':44.70,'220':65.05,'311':78.20}
    rows=[]
    for sample,values in CURVES.items():
        x,y=values.T
        record=dict(sample=sample,points=len(x),angle_start=x[0],angle_end=x[-1],max_intensity=y.max())
        for label,c in centers.items():
            win=(x>=c-.4)&(x<=c+.4)
            local_indices=np.where(win)[0]
            idx=local_indices[np.argmax(y[win])]
            record[f'{label}_max_angle']=x[idx]
            record[f'{label}_max_intensity']=y[idx]
        record['height_ratio_200_to_220']=(record['200_max_intensity']/record['220_max_intensity'])
        record['height_ratio_311_to_220']=(record['311_max_intensity']/record['220_max_intensity'])
        rows.append(record)
    pd.DataFrame(rows).to_csv(OUT/'sample_peak_descriptors.csv',index=False,float_format='%.5f')
    print(pd.DataFrame(rows)[['sample','max_intensity','200_max_intensity','220_max_intensity','height_ratio_200_to_220']].to_string(index=False))



if __name__ == "__main__":
    main()
