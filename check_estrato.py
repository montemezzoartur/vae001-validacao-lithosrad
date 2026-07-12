from scipy.io import loadmat
import numpy as np, pandas as pd

s = loadmat('data/raw/ct-uroliths_matlab.mat')['stones'].ravel()
md = np.array([float(np.asarray(x['gt_diam']).ravel()[0]) for x in s])
c = pd.read_csv('data/raw/ct-uroliths_table.csv', sep=';')

bins, labs = [0, 5, 10, 20, np.inf], ['<5', '5-10', '10-20', '>20']
e_mat = pd.cut(md, bins, labels=labs, right=False)
e_csv = pd.cut(c.Diameter, bins, labels=labs, right=False)

print('ESTRATOS pelo .mat (correto):')
print(e_mat.value_counts().reindex(labs).to_string())
print('\nESTRATOS pelo CSV (usado na divisao):')
print(e_csv.value_counts().reindex(labs).to_string())
print('\nCalculos que MUDAM de estrato:', (e_mat != e_csv).sum())
print('Estrato primario (>=10mm) pelo .mat:', (md >= 10).sum())