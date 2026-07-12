from scipy.io import loadmat
import numpy as np, pandas as pd

s = loadmat('data/raw/ct-uroliths_matlab.mat')['stones'].ravel()
mv = np.array([float(np.asarray(x['gt_vol']).ravel()[0]) for x in s])
md = np.array([float(np.asarray(x['gt_diam']).ravel()[0]) for x in s])

c = pd.read_csv('data/raw/ct-uroliths_table.csv', sep=';')
d = pd.DataFrame({'ID': range(1, 102), 'mat_vol': mv, 'mat_diam': md,
                  'csv_vol': c.Volume.values, 'csv_diam': c.Diameter.values})
d['dvol'] = (d.mat_vol - d.csv_vol).abs()
d['ddiam'] = (d.mat_diam - d.csv_diam).abs()

print('--- linhas com discrepancia de diametro > 0.01 mm ---')
print(d[d.ddiam > 0.01].to_string(index=False))
print()
print('n com ddiam > 0.01 :', (d.ddiam > 0.01).sum())
print('n com dvol  > 0.004:', (d.dvol  > 0.004).sum())