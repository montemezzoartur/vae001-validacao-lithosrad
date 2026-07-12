# VAE-001 - Fase 0: Inventario do dataset

Dataset: ct-uroliths-freiburg - DOI 10.6084/m9.figshare.21992264
Kellner E, Neubauer J. 2023-02-08. Licenca: CC BY 4.0.

## 1. Arquivos e integridade

| Arquivo | Tamanho | SHA-256 |
|---|---|---|
| `ct-uroliths_matlab.mat` | 18,175,283 B | `d8184b37eb6a8fa4aa4affd249787068d5e77f19388323b8e99736c99313ec87` |
| `ct-uroliths_table.csv` | 2,030 B | `f31e53f8c126e6a9f4713748c18ee3acb1f0febd4dc71eff886498d797b183c6` |

## 2. Tabela de referencia (CSV)

### `ct-uroliths_table.csv`

- Separador: `;`   Separador decimal: `.`
- Linhas: **101**   Colunas: **4**

| Coluna | dtype | n nao-nulo | n unicos | min | max |
|---|---|---|---|---|---|
| `ID` | int64 | 101 | 101 | 1 | 101 |
| `Volume` | float64 | 101 | 49 | 0.01 | 20 |
| `Diameter` | float64 | 101 | 97 | 5.26 | 46.58 |
| `StoneType` | str | 59 | 8 | - | - |

**Niveis de `StoneType`:**

```
StoneType
NaN                           42
cystine                       23
brushite                      17
uric acid                      8
calciumoxalate-dihydrate       6
struvite                       2
cacliumoxalate-monohydrate     1
calciumoxalate-monohydrate     1
Cystine                        1
```

**Distribuicao da referencia** (caracteristica basal, nao e desfecho):

```
               ID      Volume    Diameter
count  101.000000  101.000000  101.000000
mean    51.000000    1.221485   13.344356
std     29.300171    2.890682    8.140109
min      1.000000    0.010000    5.260000
25%     26.000000    0.090000    7.320000
50%     51.000000    0.190000   11.520000
75%     76.000000    0.830000   15.670000
max    101.000000   20.000000   46.580000
```

**Populacao dos estratos do protocolo** (via `Diameter`):

| Estrato | n |
|---|---|
| < 5 mm | 0 |
| 5-10 mm | 44 |
| 10-20 mm | 40 |
| > 20 mm | 17 |

> O estrato >= 10 mm e o desfecho primario. Se estiver pouco povoado,
> o estudo perde poder - registrar como limitacao ANTES de rodar.

**ACHADOS CRITICOS DO CSV:**

- Medicoes individuais dos 3 avaliadores: **NAO**
- Coluna de origem (humano/canino): **NAO**
- Se ambas forem NAO aqui, verificar no `.mat` (secao 3). Se nao estiverem
  la tampouco, o protocolo precisa de emenda (Secoes 5 e 8) e provavelmente
  de contato com os autores.

## 3. Dados de imagem (MATLAB)

### `ct-uroliths_matlab.mat`

- Formato: MAT v7 ou anterior (scipy.io.loadmat)

- `stones`: STRUCT  shape=(1, 101)  campos=['gt_diam', 'gt_vol', 'imgdata', 'voxsiz', 'voxvol_mL']
  - `gt_diam`: array  shape=(1, 1)  dtype=float64  valores=[5.263333333333334]
  - `gt_vol`: array  shape=(1, 1)  dtype=float64  valores=[0.01]
  - `imgdata`: *** VOLUME 3D ***  shape=(83, 83, 83)  dtype=float64
      min=0.0  max=759.0  mean=0.1
  - `voxsiz`: array  shape=(1, 3)  dtype=float64  valores=[0.7363, 0.7363, 0.7]
  - `voxvol_mL`: array  shape=(1, 1)  dtype=float64  valores=[0.0003795253689029323]

## 4. Perguntas que viram emenda ao protocolo

1. Espacamento do voxel esta no arquivo? Se nao, assumimos 0,7 x 0,7 x 0,7 mm do artigo - e isso vira premissa documentada, nao dado verificado.

2. Os volumes 3D sao VOIs recortados ou exames inteiros? (ver shape) Se recortados, o criterio de exclusao por VAZAMENTO (Secao 11) e inaplicavel.

3. Um calculo por volume, ou varios? Define se ha logica de semente.

4. As medicoes individuais dos 3 avaliadores existem? Se nao, a Secao 5 cai.

5. Ha informacao de origem (humano/canino)? Se nao, a Secao 8 e inexequivel.

6. Unidades da referencia: Volume em mL ou mm3? Diameter em mm?

7. Os dados ja vem em UH, ou ha escala a aplicar? (ver min/max dos volumes 3D)

