# VAE-001, Adendo P, item 4: inspecao descritiva -- DESENVOLVIMENTO (2 calculos)

Entradas: `results/poshoc_casos_desenv.npz` (SHA-256 `822ee6eb723209d974aa995e77da4cabceb0eddd2d5cc409e91378fff8ff4bf1`) e `results/poshoc_prevoo_desenv.csv` (SHA-256 `fcf4259defe9b04349e66027fce011a7d59fb49023906c0c627fb3a780eb833b`), do pre-voo. O .mat nao e lido.
Script: `poshoc_item4.py` (SHA-256, fins de linha normalizados, `574f40fdc6295d09d105bb49a428802eb86f04b40d6e34ccb9b40ff7f31f10ff`).

Descricao apenas: numero e tamanho das componentes, posicao do diametro maximo e figura. Nenhuma estatistica e derivada destes calculos (Adendo P, item 4).

| Calculo | Motivo | Tipo | Referencia (mm) | Dispositivo (mm) | Erro (mm) | Fracao pura (mm) | 200 UH fixos (mm) | Maximo (UH) | p95 (UH) | T (UH) | Comp. >= 200 UH | Comp. >= T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 23 | - | brushite | 11,52 | 11,34 | −0,19 | 11,13 | 11,98 | 2146 | 2005 | 451 | 1 | 1 |
| 56 | - | uric acid | 12,56 | 12,46 | −0,10 | 12,78 | 12,13 | 642 | 581 | 131 | 1 | 1 |

## Calculo 23

- Tipo: brushite. Recorte publico de 83 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 11,52 mm; dispositivo 11,34 mm (erro −0,19); reimplementacao a 0,225 x p95 11,13 mm (−0,39); reimplementacao a 200 UH fixos 11,98 mm (+0,46).
- Atenuacao: maximo 2146 UH; p95 2004,8 UH; T = 451,1 UH (T >= 200 UH); piso da mascara 102 UH.
- Componentes >= 200 UH: 1. 825 voxels (313,1 mm3; 8,4 x 10,3 x 8,8 mm em z, y, x; fatias 36 a 47). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 677 voxels (256,9 mm3; 8,4 x 8,8 x 8,8 mm em z, y, x; fatias 36 a 47).
- Diametro maximo do dispositivo (11,34 mm): de (z 37,0; y 50,9; x 37,0) a (z 45,0; y 40,9; x 46,0), em voxels do recorte; fatias 37 e 45; componentes do vetor: +5,60 mm em z, −7,30 mm em y, +6,63 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_desenv_calc_023.png`.

## Calculo 56

- Tipo: uric acid. Recorte publico de 51 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 12,56 mm; dispositivo 12,46 mm (erro −0,10); reimplementacao a 0,225 x p95 12,78 mm (+0,22); reimplementacao a 200 UH fixos 12,13 mm (−0,43).
- Atenuacao: maximo 642 UH; p95 581,1 UH; T = 130,7 UH (T < 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 670 voxels (254,3 mm3; 9,1 x 6,6 x 11,8 mm em z, y, x; fatias 25 a 37). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 816 voxels (309,7 mm3; 10,5 x 7,4 x 12,5 mm em z, y, x; fatias 25 a 39).
- Diametro maximo do dispositivo (12,46 mm): de (z 27,0; y 41,0; x 55,4) a (z 35,0; y 43,0; x 40,4), em voxels do recorte; fatias 27 e 35; componentes do vetor: +5,60 mm em z, +1,47 mm em y, −11,03 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_desenv_calc_056.png`.

