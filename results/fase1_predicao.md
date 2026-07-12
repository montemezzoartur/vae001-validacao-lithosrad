\# VAE-001 — Predição pré-registrada



\*\*Data:\*\* 12/07/2026

\*\*Base:\*\* verificação em esferas sintéticas (`fase1\_esferas\_v2.py`), geometria

do Freiburg (0,7 × 0,7363 × 0,7363 mm; PSF 0,7 mm), esfera de 900 UH em fundo 0,

limiar de 200 UH (ponto de operação do LithosRad).



\*\*Registrada ANTES de qualquer execução sobre dado real do Freiburg\*\* —

inclusive antes dos 25 cálculos de desenvolvimento.



\## Predição



Sobre esferas ideais, o LithosRad superestima o volume físico em:



| D (mm) | Erro previsto |

|---|---|

| 3  | +53,0% |

| 4  | +34,8% |

| 5  | +36,3% |

| 6  | +25,2% |

| 8  | +21,3% |

| 10 | +17,1% |

| 12 | +11,8% |

| 15 | +11,0% |

| 20 |  +8,3% |



\*\*No estrato primário (≥ 10 mm): viés previsto entre +8% e +17%.\*\*



O diâmetro superestima em \~+1,6 mm, de forma aproximadamente constante e

independente do tamanho.



\## Hipóteses derivadas, a serem testadas



\*\*H1.\*\* Em cálculos reais, o viés de volume no estrato ≥10 mm será \*\*maior\*\*

que o previsto pelas esferas. Motivo: cálculos reais são irregulares e

espiculados, com razão superfície/volume superior à da esfera; como o erro é

um efeito de casca, ele escala com a superfície.



\*\*H2.\*\* O viés dependerá da \*\*densidade\*\* do cálculo. Com limiar fixo de 200 UH,

o corte relativo varia de 49% do pico (cálculo de 408 UH) a 8,6% do pico

(cálculo de 2312 UH). Cálculos mais densos serão mais superestimados.



\*\*H3.\*\* A taxa de falha de segmentação será nula ou próxima de zero, dado que

os VOIs contêm um único cálculo isolado, e o menor pico do dataset (408 UH)

está bem acima do limiar de 200 UH.



\## Uso



Estas predições NÃO são critérios de aceitação. São hipóteses pré-registradas.

Sua confirmação ou refutação, sobre o conjunto lacrado, constitui evidência

independente de que o comportamento do motor é compreendido e modelado — ou

de que há um fenômeno não modelado a investigar.

