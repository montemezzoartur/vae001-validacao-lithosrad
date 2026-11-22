# VAE-001, Adendo P, item 4: inspecao descritiva -- LACRADO (8 calculos)

Entradas: `results/poshoc_casos.npz` (SHA-256 `109d5d0107f8301727f997ab56e8aef0cfb1df068adedc8298ad956813acfe65`) e `results/poshoc_lacrado.csv` (SHA-256 `b38fa2053a25f19bb22b5cbbd18d87a7bf5e5b652ac5c524ea7967e716f52faf`), as da execucao registrada em 2026-11-22T17:50:18.952974+00:00. O .mat nao e lido.
Script: `poshoc_item4.py` (SHA-256, fins de linha normalizados, `574f40fdc6295d09d105bb49a428802eb86f04b40d6e34ccb9b40ff7f31f10ff`).

Descricao apenas: numero e tamanho das componentes, posicao do diametro maximo e figura. Nenhuma estatistica e derivada destes calculos (Adendo P, item 4).

| Calculo | Motivo | Tipo | Referencia (mm) | Dispositivo (mm) | Erro (mm) | Fracao pura (mm) | 200 UH fixos (mm) | Maximo (UH) | p95 (UH) | T (UH) | Comp. >= 200 UH | Comp. >= T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 29 | erro acima de 1 mm | nan | 11,89 | 10,88 | −1,01 | 10,65 | 11,10 | 1231 | 1091 | 245 | 1 | 1 |
| 83 | erro acima de 1 mm; componentes multiplas | nan | 18,17 | 19,39 | +1,22 | 19,39 | 19,26 | 1217 | 747 | 168 | 2 | 2 |
| 91 | erro acima de 1 mm | nan | 22,58 | 24,04 | +1,46 | 24,04 | 23,73 | 756 | 615 | 138 | 1 | 1 |
| 41 | estruvita | struvite | 13,85 | 12,87 | −0,99 | 12,87 | 12,60 | 671 | 620 | 140 | 1 | 1 |
| 88 | estruvita | struvite | 25,36 | 24,38 | −0,98 | 24,79 | 24,18 | 766 | 668 | 150 | 1 | 1 |
| 100 | componentes multiplas | nan | 46,03 | 45,29 | −0,75 | 45,18 | 45,75 | 1903 | 1698 | 382 | 2 | 3 |
| 28 | troca de categoria a 10 mm | nan | 10,48 | 9,79 | −0,69 | 9,61 | 10,49 | 2023 | 1854 | 417 | 1 | 1 |
| 3 | troca de categoria a 5 mm; menor atenuacao | nan | 5,71 | 4,88 | −0,83 | 5,33 | 4,22 | 408 | 379 | 85 | 1 | 1 |

## Calculo 29 -- erro acima de 1 mm

- Tipo: nan. Recorte publico de 81 x 81 x 81 voxels (z, y, x); voxel de 0,700 x 0,760 x 0,760 mm.
- Diametro: referencia 11,89 mm; dispositivo 10,88 mm (erro −1,01); reimplementacao a 0,225 x p95 10,65 mm (−1,24); reimplementacao a 200 UH fixos 11,10 mm (−0,79).
- Atenuacao: maximo 1231 UH; p95 1091,0 UH; T = 245,5 UH (T >= 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 418 voxels (168,9 mm3; 7,0 x 5,3 x 11,4 mm em z, y, x; fatias 36 a 45). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 384 voxels (155,2 mm3; 7,0 x 4,6 x 10,6 mm em z, y, x; fatias 36 a 45).
- Diametro maximo do dispositivo (10,88 mm): de (z 40,0; y 39,0; x 51,4) a (z 40,0; y 40,0; x 37,2), em voxels do recorte; fatias 40 e 40; componentes do vetor: 0,00 mm em z, +0,76 mm em y, −10,85 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_029.png`.

## Calculo 83 -- erro acima de 1 mm; componentes multiplas

- Tipo: nan. Recorte publico de 65 x 65 x 65 voxels (z, y, x); voxel de 0,700 x 0,701 x 0,701 mm.
- Diametro: referencia 18,17 mm; dispositivo 19,39 mm (erro +1,22); reimplementacao a 0,225 x p95 19,39 mm (+1,22); reimplementacao a 200 UH fixos 19,26 mm (+1,10).
- Atenuacao: maximo 1217 UH; p95 747,0 UH; T = 168,1 UH (T < 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 2. 3028 voxels (1042,1 mm3; 18,9 x 16,8 x 18,9 mm em z, y, x; fatias 18 a 44); 1 voxels (0,3 mm3; 0,7 x 0,7 x 0,7 mm em z, y, x; fatias 26 a 26). Voxels >= 200 UH fora da maior: 1.
- Componentes >= T: 2. 3289 voxels (1131,9 mm3; 18,9 x 16,8 x 19,6 mm em z, y, x; fatias 18 a 44); 2 voxels (0,7 mm3; 1,4 x 1,4 x 1,4 mm em z, y, x; fatias 26 a 27).
- Diametro maximo do dispositivo (19,39 mm): de (z 17,5; y 28,0; x 31,0) a (z 44,6; y 34,0; x 31,0), em voxels do recorte; fatias 18 e 45; componentes do vetor: +18,93 mm em z, +4,21 mm em y, 0,00 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_083.png`.

## Calculo 91 -- erro acima de 1 mm

- Tipo: nan. Recorte publico de 83 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 22,58 mm; dispositivo 24,04 mm (erro +1,46); reimplementacao a 0,225 x p95 24,04 mm (+1,46); reimplementacao a 200 UH fixos 23,73 mm (+1,15).
- Atenuacao: maximo 756 UH; p95 615,0 UH; T = 138,4 UH (T < 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 7869 voxels (2986,5 mm3; 18,9 x 17,7 x 22,8 mm em z, y, x; fatias 30 a 56). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 8489 voxels (3221,8 mm3; 18,9 x 18,4 x 22,8 mm em z, y, x; fatias 30 a 56).
- Diametro maximo do dispositivo (24,04 mm): de (z 38,0; y 46,0; x 60,5) a (z 48,0; y 51,0; x 29,6), em voxels do recorte; fatias 38 e 48; componentes do vetor: +7,00 mm em z, +3,68 mm em y, −22,70 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_091.png`.

## Calculo 41 -- estruvita

- Tipo: struvite. Recorte publico de 83 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 13,85 mm; dispositivo 12,87 mm (erro −0,99); reimplementacao a 0,225 x p95 12,87 mm (−0,99); reimplementacao a 200 UH fixos 12,60 mm (−1,25).
- Atenuacao: maximo 671 UH; p95 620,5 UH; T = 139,6 UH (T < 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 432 voxels (164,0 mm3; 11,2 x 4,4 x 8,8 mm em z, y, x; fatias 33 a 48). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 517 voxels (196,2 mm3; 11,9 x 4,4 x 9,6 mm em z, y, x; fatias 33 a 49).
- Diametro maximo do dispositivo (12,87 mm): de (z 32,6; y 42,0; x 46,0) a (z 47,5; y 44,0; x 36,0), em voxels do recorte; fatias 33 e 48; componentes do vetor: +10,45 mm em z, +1,47 mm em y, −7,36 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_041.png`.

## Calculo 88 -- estruvita

- Tipo: struvite. Recorte publico de 83 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 25,36 mm; dispositivo 24,38 mm (erro −0,98); reimplementacao a 0,225 x p95 24,79 mm (−0,57); reimplementacao a 200 UH fixos 24,18 mm (−1,18).
- Atenuacao: maximo 766 UH; p95 668,0 UH; T = 150,3 UH (T < 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 6686 voxels (2537,5 mm3; 23,8 x 10,3 x 20,6 mm em z, y, x; fatias 25 a 58). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 7192 voxels (2729,5 mm3; 24,5 x 10,3 x 21,4 mm em z, y, x; fatias 24 a 58).
- Diametro maximo do dispositivo (24,38 mm): de (z 25,5; y 47,0; x 34,0) a (z 56,6; y 48,0; x 49,0), em voxels do recorte; fatias 26 e 57; componentes do vetor: +21,72 mm em z, +0,74 mm em y, +11,04 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_088.png`.

## Calculo 100 -- componentes multiplas

- Tipo: nan. Recorte publico de 85 x 85 x 85 voxels (z, y, x); voxel de 0,700 x 0,701 x 0,701 mm.
- Diametro: referencia 46,03 mm; dispositivo 45,29 mm (erro −0,75); reimplementacao a 0,225 x p95 45,18 mm (−0,86); reimplementacao a 200 UH fixos 45,75 mm (−0,29).
- Atenuacao: maximo 1903 UH; p95 1698,0 UH; T = 382,1 UH (T >= 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 2. 38650 voxels (13301,4 mm3; 37,8 x 36,5 x 35,1 mm em z, y, x; fatias 16 a 69); 17 voxels (5,9 mm3; 2,8 x 2,1 x 2,1 mm em z, y, x; fatias 45 a 48). Voxels >= 200 UH fora da maior: 17.
- Componentes >= T: 3. 35973 voxels (12380,1 mm3; 37,1 x 36,5 x 35,1 mm em z, y, x; fatias 16 a 68); 3 voxels (1,0 mm3; 1,4 x 1,4 x 0,7 mm em z, y, x; fatias 35 a 36); 2 voxels (0,7 mm3; 1,4 x 0,7 x 0,7 mm em z, y, x; fatias 46 a 47).
- Diametro maximo do dispositivo (45,29 mm): de (z 24,0; y 82,6; x 56,0) a (z 60,0; y 38,1; x 26,0), em voxels do recorte; fatias 24 e 60; componentes do vetor: +25,20 mm em z, −31,20 mm em y, −21,04 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_100.png`.

## Calculo 28 -- troca de categoria a 10 mm

- Tipo: nan. Recorte publico de 81 x 81 x 81 voxels (z, y, x); voxel de 0,700 x 0,752 x 0,752 mm.
- Diametro: referencia 10,48 mm; dispositivo 9,79 mm (erro −0,69); reimplementacao a 0,225 x p95 9,61 mm (−0,87); reimplementacao a 200 UH fixos 10,49 mm (+0,01).
- Atenuacao: maximo 2023 UH; p95 1854,0 UH; T = 417,2 UH (T >= 200 UH); piso da mascara 101 UH.
- Componentes >= 200 UH: 1. 610 voxels (241,4 mm3; 7,0 x 7,5 x 10,5 mm em z, y, x; fatias 37 a 46). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 485 voxels (192,0 mm3; 7,0 x 6,8 x 9,8 mm em z, y, x; fatias 37 a 46).
- Diametro maximo do dispositivo (9,79 mm): de (z 40,0; y 42,0; x 47,8) a (z 41,0; y 41,0; x 34,8), em voxels do recorte; fatias 40 e 41; componentes do vetor: +0,70 mm em z, −0,75 mm em y, −9,74 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_028.png`.

## Calculo 3 -- troca de categoria a 5 mm; menor atenuacao

- Tipo: nan. Recorte publico de 83 x 83 x 83 voxels (z, y, x); voxel de 0,700 x 0,736 x 0,736 mm.
- Diametro: referencia 5,71 mm; dispositivo 4,88 mm (erro −0,83); reimplementacao a 0,225 x p95 5,33 mm (−0,38); reimplementacao a 200 UH fixos 4,22 mm (−1,49).
- Atenuacao: maximo 408 UH; p95 378,9 UH; T = 85,3 UH (T < 200 UH); piso da mascara 104 UH; T ABAIXO DO PISO.
- Componentes >= 200 UH: 1. 35 voxels (13,3 mm3; 4,2 x 2,2 x 2,9 mm em z, y, x; fatias 41 a 46). Voxels >= 200 UH fora da maior: 0.
- Componentes >= T: 1. 75 voxels (28,5 mm3; 4,9 x 2,9 x 3,7 mm em z, y, x; fatias 41 a 47).
- Diametro maximo do dispositivo (4,88 mm): de (z 40,4; y 42,0; x 41,0) a (z 46,6; y 42,0; x 44,0), em voxels do recorte; fatias 40 e 47; componentes do vetor: +4,35 mm em z, 0,00 mm em y, +2,21 mm em x.
- Conferencia com o CSV da execucao: diametro, maximo, p95, T e componentes iguais.
- Figura: `poshoc_item4_calc_003.png`.

