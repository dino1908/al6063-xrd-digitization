"""Basic integrity and reproducibility checks for the supplied ST TIFF."""
from pathlib import Path
import numpy as np
import pytest
from src.st_versions import ANGLES, reconstruct_st

ROOT = Path(__file__).resolve().parents[1]
TIFF = ROOT/'data/raw/tiff/XRD_ST_2015.tif'

@pytest.mark.parametrize('v', [1,2,3,4])
def test_versions_reproduce_saved_curves(v):
    expected = np.loadtxt(ROOT/f'experiments/st_versions/ST_v{v}.csv',
                          delimiter=',',skiprows=1)
    actual = reconstruct_st(TIFF,v)
    assert expected.shape==(938,2)
    np.testing.assert_allclose(ANGLES, expected[:,0],rtol=0,atol=1e-10)
    np.testing.assert_allclose(actual,expected[:,1],rtol=0,atol=0.00005)

def test_v4_reconstruction_near_reference_accuracy():
    original_path=ROOT/'data/raw/instrument/XRD_Al6063_ST_2015_06_08_ASCII.txt'
    data_part=original_path.read_text().split('[Data]',1)[1]
    rows=[]
    for line in data_part.splitlines():
        items=[x.strip() for x in line.split(',') if x.strip()]
        if len(items)==2:
            try: rows.append(tuple(map(float,items)))
            except ValueError: continue
    original=np.asarray(rows)
    estimated=reconstruct_st(TIFF,4)
    assert original.shape==(938,2)
    np.testing.assert_allclose(original[:,0],ANGLES,rtol=0,atol=1e-10)
    mae=np.mean(np.abs(estimated-original[:,1]))
    assert mae<3.3, f'V4 ST MAE unexpectedly large: {mae}'
