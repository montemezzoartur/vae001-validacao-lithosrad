# VAE-001 - Fase 1: análise exploratória dos 25 de DESENVOLVIMENTO

Medição dos 25 cálculos do conjunto de **DESENVOLVIMENTO** do Freiburg com o
`detectar_calculos()` **real** do LithosRad (commit congelado
`37076ba25b00aa9a6290c35192e2211a9dd98d4c`), no ponto de operação de fábrica
(`hu_min = 200`, sem override). Máscara de rim cobrindo todo o volume — cada VOI
é um cálculo isolado em água (fundo ~0 UH), então o limiar já isola o cálculo.

Nenhum cálculo **LACRADO** foi tocado: `carregar_freiburg` é chamado apenas com
`grupo='DESENV'`. Isto é **exploratório**; a prova independente de H1/H2/H3 é
sobre o conjunto lacrado, após o congelamento — **não é critério de aceitação**
(ver `results/fase1_predicao.md`, Seção "Uso").

Script: `fase1_desenvolvimento.py`. Saídas: `results/fase1_desenv.csv` e as três
figuras citadas abaixo.

## 1. Método

- Volume por cálculo: `V_lithos = n_voxels × prod(spacing)` (o motor real).
- Erro de volume: `erro% = 100·(V_lithos / (gt_vol·1000) − 1)`. Atenção às
  unidades: `gt_vol` está em **mL**, `V_lithos` em **mm³**; `1 mL = 1000 mm³`.
- Erro de diâmetro: `D_lithos − gt_diam` (mm).
- `prev%`: viés que a esfera do **mesmo diâmetro** teria, interpolado da tabela
  pré-registrada (`fase1_predicao.md`). Serve de linha de base por cálculo.
- Estrato por `gt_diam`: `5-10`, `10-20`, `>20` mm.

## 2. Resultado por cálculo

Segmentação: **25/25 com exatamente 1 componente** (`status = ok`); nenhuma
falha, nenhum fracionamento.

```
 id  estr    gt_mm3   lit_mm3  erroV%  prev%    gtD   litD    eD  huMax
  1  5-10      10.0      32.3  +222.6  +33.4   5.26   5.59 +0.32    759
  2  5-10      13.3      88.4  +563.2  +24.2   6.53   7.55 +1.02    871
 12  5-10      53.3      83.5   +56.6  +23.4   6.92   7.81 +0.89    780
 13  5-10      60.0      92.6   +54.3  +22.1   7.58   7.91 +0.33    796
 15  5-10      60.0     107.0   +78.4  +23.9   6.66   8.03 +1.37   2005
 16  5-10      60.0     102.9   +71.4  +24.6   6.33   7.95 +1.62   1882
 18  5-10      60.0      80.1   +33.5  +22.1   7.60   8.50 +0.90    833
 21  5-10      80.0      80.1    +0.1  +23.7   6.78   7.72 +0.94    856
 23 10-20      93.3     313.1  +235.5  +13.1  11.52  12.79 +1.27   2146
 26  5-10      93.3      78.2   -16.2  +22.6   7.35   7.55 +0.20    771
 40  5-10     113.3     102.9    -9.2  +18.8   9.19   8.87 -0.32    688
 44 10-20     133.3     544.7  +308.5  +11.4  13.57  14.24 +0.68   1689
 49  5-10     160.0     102.1   -36.2  +20.6   8.32   9.16 +0.85    788
 53 10-20     196.7     365.9   +86.0  +11.5  13.31  14.22 +0.91   1948
 55 10-20     196.7     520.3  +164.6  +11.6  12.58  13.58 +1.00   1756
 54 10-20     200.0     229.2   +14.6  +14.9  10.84  11.24 +0.40    852
 56 10-20     200.0     254.3   +27.1  +11.7  12.56  12.91 +0.35    642
 67 10-20     400.0     468.7   +17.2  +11.7  12.31  13.44 +1.13    907
 80 10-20    1000.0     901.4    -9.9  +10.6  15.67  16.68 +1.01    868
 81 10-20    1000.0    1035.2    +3.5  +10.9  15.17  16.43 +1.26   1797
 87   >20    2066.7    2112.8    +2.2   +8.3  22.73  23.28 +0.55    668
 90 10-20    2766.7    3392.8   +22.6   +8.4  19.87  21.36 +1.49   2121
 92   >20    2866.7    2733.7    -4.6   +8.3  20.66  21.56 +0.90    689
 95   >20    6333.3    5854.2    -7.6   +8.3  27.94  28.99 +1.05    903
 96   >20    6600.0    7472.1   +13.2   +8.3  32.08  32.81 +0.73    867
```

## 3. Bland-Altman percentual do volume, por estrato

Viés = média do `erro%`; LoA 95% = viés ± 1,96·sd. Figura:
`results/fase1_bland_altman.png` (viés global **+76%**, LoA 95% **[−187, +338]%**).

| Estrato | n | Viés | sd | LoA 95% |
|---|---|---|---|---|
| 5-10 mm | 11 | **+92,6%** | 171,1 | [−242,7; +427,9] |
| 10-20 mm | 10 | **+87,0%** | 111,2 | [−131,0; +305,0] |
| >20 mm | 4 | **+0,8%** | 9,2 | [−17,3; +18,9] |

A dispersão é enorme nos estratos menores e some no `>20 mm`. No `5-10 mm` os
volumes de referência são minúsculos (10–160 mm³) e grosseiramente quantizados
na fonte (0,06 mL repetido), então o `erro%` ali é volátil e pouco informativo —
o estrato primário pré-registrado (≥10 mm) é o que carrega significado.

## 4. Diâmetro

Erro de diâmetro: média **+0,83 mm**, sd 0,45 mm — positivo e aproximadamente
constante, como a esfera prevê, porém com cerca de **metade** do +1,6 mm previsto.

## 5. Hipóteses pré-registradas — H1, H2, H3

### H3 — falha de segmentação ~0: **CONFIRMADA**

**0/25** falhas. O menor pico do conjunto (642 UH) está muito acima do limiar de
200 UH, e cada VOI contém um único cálculo isolado.

### H2 — o viés cresce com a densidade (`hu_max`): **CONFIRMADA**

Spearman(`hu_max`, `erro%`) **rho = +0,44, p = 0,027** (n = 25). É o efeito
dominante: com limiar fixo de 200 UH, o corte relativo cai para ~10% do pico nos
cálculos densos, e o bloom de PSF infla o volume. Os maiores erros
(id 44 +308%, id 23 +236%, id 55 +165%) são todos de alto `hu_max` (1689–2146 UH);
os de ~650–900 UH ficam perto de 0 ou negativos. Figura:
`results/fase1_erro_vs_humax.png`.

### H1 — viés real (≥10 mm) maior que o das esferas (+8..+17%): **NÃO confirmada** como efeito próprio

| Métrica (estrato ≥10 mm, n=14) | Valor |
|---|---|
| Média do `erro%` observado | +62,4% |
| **Mediana** do `erro%` observado | **+15,9%** (dentro de +8..+17%) |
| Faixa | [−9,9%; +308,5%] |
| Média prevista pelas esferas (mesmos D) | +10,6% |
| Cálculos acima do previsto | 8/14 |
| Wilcoxon pareado (obs vs previsto) | p = 0,30 (n.s.) |
| Spearman(`V_gt`, `erro%`) | rho = −0,52, p = 0,008 |

A **média** ≥10 mm (+62%) fica muito acima da banda, mas engana: a **mediana**
(+15,9%) cai **dentro** da banda das esferas, o teste pareado é não-significativo,
e o erro **decresce** com o tamanho (rho = −0,52) — exatamente a direção que a
esfera prevê. A média sobe por poucos *outliers*, e esses *outliers* são os
**densos** (H2), não os irregulares/espiculados que H1 postulava. O excesso é de
**densidade (H2), não de forma/superfície**. Figura:
`results/fase1_erro_vs_gtvol.png`.

## 6. Leitura

- O motor se comporta como a física do limiar manda: superestimação positiva que
  **decresce com o tamanho** e **cresce com a densidade**. No `>20 mm` o viés
  praticamente desaparece (+0,8%).
- O fenômeno de primeira ordem a testar sobre o **LACRADO** é **H2** (dependência
  de densidade sob limiar fixo de 200 UH), o sinal forte e pré-registrado. H1,
  como efeito de forma independente da densidade, **não** aparece aqui.
- Tudo acima é exploratório no desenvolvimento. Confirmação/refutação definitiva:
  conjunto lacrado, após o congelamento do LithosRad.

## 7. Registro

- `results/fase1_desenv.csv` — 25 linhas, uma por cálculo (todas `status=ok`).
- `results/fase1_bland_altman.png` — Bland-Altman percentual por estrato.
- `results/fase1_erro_vs_humax.png` — teste de H2 (erro vs `hu_max`).
- `results/fase1_erro_vs_gtvol.png` — teste de H1 (erro vs `V_gt`, real vs esferas).
- Gerador: `fase1_desenvolvimento.py`.
