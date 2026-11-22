# VAE-001, Adendo P: analises pos-hoc -- LACRADO (n = 76)

Entrada: `results/poshoc_lacrado.csv` (SHA-256 `b38fa2053a25f19bb22b5cbbd18d87a7bf5e5b652ac5c524ea7967e716f52faf`). Semente 20260712; 10000 reamostras.

## Item 1. Emulacao do dispositivo contra as saidas da execucao unica

- Diametro identico (|dif| < 1e-6 mm): **76 de 76**; maior diferenca 6.24e-07 mm.
- Maximo identico: 76 de 76. Numero de voxels identico: 76 de 76.
- Calculos com mais de uma componente >= 200 UH: [83, 100].

## Item 2. Erro do dispositivo e atenuacao

- rho(p95, erro) = **−0,15** (IC95 −0,36 a +0,08; p = 0,194; n = 76). Estimador pre-especificado.
- rho(maximo, erro) = −0,12 (IC95 −0,34 a +0,11).
- rho(p95, |erro|) = −0,22 (IC95 −0,42 a +0,01; p = 0,060).
- T = 0,225 x p95 abaixo de 200 UH: **39 de 76**. Razao media p95/maximo: 0,9092.

| Regime | n | Vies (mm) | DP (mm) | Minimo | Maximo |
|---|---|---|---|---|---|
| T < 200 UH | 39 | +0,07 | 0,53 | −0,99 | +1,46 |
| T >= 200 UH | 37 | −0,07 | 0,41 | −1,01 | +0,94 |

Levene (mediana) entre regimes: p = 0,208.

| Tercil de p95 | p95 (UH) | n | Vies (mm) | DP (mm) |
|---|---|---|---|---|
| inferior | 379 a 750 | 26 | +0,10 | 0,62 |
| medio | 765 a 1600 | 25 | +0,01 | 0,45 |
| superior | 1601 a 2234 | 25 | −0,11 | 0,32 |

Levene (mediana) entre tercis: p = 0,022.

## Item 3. Limiar fixo contra fracao, na reimplementacao de referencia

| Regra | n | Vies (mm) | DP (mm) | Semi-LoA (mm) | Pior (mm) | rho(p95) | IC95 do rho | p |
|---|---|---|---|---|---|---|---|---|
| Reimplementacao, 200 UH fixos | 76 | +0,11 | 0,55 | 1,08 | 1,49 | +0,54 | +0,36 a +0,68 | < 0,0001 |
| Reimplementacao, 0,225 x p95 | 76 | +0,03 | 0,50 | 0,99 | 1,46 | −0,34 | −0,52 a −0,12 | 0,0031 |
| Dispositivo congelado | 76 | 0,00 | 0,48 | 0,94 | 1,46 | −0,15 | −0,36 a +0,08 | 0,1941 |

- Diferenca dos rho (fixo menos fracao): **+0,88** (IC95 BCa +0,70 a +1,08; percentil +0,68 a +1,06).
- Pitman-Morgan (DP fixo 0,549 x DP fracao 0,504): r = +0,103, t = +0,89, **p = 0,3770**.
- Razao DP(fracao)/DP(fixo): 0,917 (IC95 BCa 0,734 a 1,112).
- Dispositivo e reimplementacao (mesma regra) identicos em 37 de 76. Com T < 200 UH (n = 39): 18 menores no dispositivo (−0,61 a 0,00 mm). Com T >= 200 UH (n = 37): 21 maiores no dispositivo (0,00 a +0,25 mm).

## Item 5. Sensibilidade sem os calculos com T abaixo do piso da mascara

Excluidos: [3, 74] (n = 74).

- rho(p95, erro do dispositivo) = −0,17 (IC95 −0,38 a +0,06).

Limiar fixo contra fracao, sem os excluidos:

| Regra | n | Vies (mm) | DP (mm) | Semi-LoA (mm) | Pior (mm) | rho(p95) | IC95 do rho | p |
|---|---|---|---|---|---|---|---|---|
| Reimplementacao, 200 UH fixos | 74 | +0,13 | 0,52 | 1,03 | 1,25 | +0,53 | +0,35 a +0,68 | < 0,0001 |
| Reimplementacao, 0,225 x p95 | 74 | +0,02 | 0,50 | 0,97 | 1,46 | −0,35 | −0,53 a −0,13 | 0,0025 |
| Dispositivo congelado | 74 | 0,00 | 0,47 | 0,92 | 1,46 | −0,17 | −0,38 a +0,06 | 0,1552 |

- Diferenca dos rho (fixo menos fracao): **+0,88** (IC95 BCa +0,69 a +1,09; percentil +0,67 a +1,07).
- Pitman-Morgan (DP fixo 0,524 x DP fracao 0,496): r = +0,066, t = +0,56, **p = 0,5762**.
- Razao DP(fracao)/DP(fixo): 0,947 (IC95 BCa 0,776 a 1,129).

Regra de leitura na sensibilidade:

- Ordenacao pela atenuacao: SUSTENTADA: o IC da diferenca dos rho exclui zero, com rho(fixo) > rho(fracao).
- Associacao na fracao: DEPENDENCIA RESIDUAL (negativa): o IC do rho da fracao exclui zero.
- Dispersao menor na fracao: NAO SUSTENTADA: Pitman-Morgan p >= 0,05.

## Regra de leitura (fixada antes da execucao)

- Ordenacao pela atenuacao: **SUSTENTADA: o IC da diferenca dos rho exclui zero, com rho(fixo) > rho(fracao)**.
- Associacao na fracao: **DEPENDENCIA RESIDUAL (negativa): o IC do rho da fracao exclui zero**.
- Dispersao menor na fracao: **NAO SUSTENTADA: Pitman-Morgan p >= 0,05**.

