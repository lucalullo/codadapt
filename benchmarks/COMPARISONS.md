# Paired comparisons

Recorded outcome labels and original effect intervals are preserved, rather than reclassified from rounded values. Positive original-effect intervals favor CodAdapt under the source protocol. The interval scale is not interchangeable across tasks or with the displayed primary metric delta. No global Holm-confirmed wins or formal equivalence tests were established. `M01` is the missing Glass/XGBoost pair; the source assigns no P identifier to it.

## Binary

| ID | Dataset | Comparator | Primary metric | CodAdapt | Comparator | Numerical direction | Recorded outcome | Original effect CI95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | Danish occupancy | Logistic / Ridge | roc_auc | 0.939468 | 0.839356 | favorable | exploratory favorable | [0.07278, 0.12047] |
| P02 | Danish occupancy | Random Forest | roc_auc | 0.939468 | 0.901309 | favorable | exploratory favorable | [0.02218, 0.05466] |
| P03 | Danish occupancy | HistGradientBoosting | roc_auc | 0.939468 | 0.922186 | favorable | exploratory favorable | [0.00593, 0.02952] |
| P04 | Danish occupancy | XGBoost | roc_auc | 0.939468 | 0.919683 | favorable | exploratory favorable | [0.00621, 0.03316] |
| P05 | Danish occupancy | LightGBM | roc_auc | 0.939468 | 0.919913 | favorable | exploratory favorable | [0.00702, 0.03265] |
| P06 | Danish occupancy | CatBoost | roc_auc | 0.939468 | 0.951437 | unfavorable | inconclusive | [-0.02343, 0.00029] |
| P07 | Denver trees | Logistic / Ridge | roc_auc | 0.500000 | 0.645060 | unfavorable | inconclusive | — |
| P08 | Denver trees | Random Forest | roc_auc | 0.500000 | 0.648162 | unfavorable | inconclusive | — |
| P09 | Denver trees | HistGradientBoosting | roc_auc | 0.500000 | 0.500000 | identical | inconclusive | — |
| P10 | Denver trees | XGBoost | roc_auc | 0.500000 | 0.392611 | favorable | inconclusive | — |
| P11 | Denver trees | LightGBM | roc_auc | 0.500000 | 0.500000 | identical | inconclusive | — |
| P12 | Denver trees | CatBoost | roc_auc | 0.500000 | 0.655039 | unfavorable | inconclusive | — |
| P25 | SECOM | Logistic / Ridge | roc_auc | 0.500000 | 0.505762 | unfavorable | inconclusive | [-0.19665, 0.23013] |
| P26 | SECOM | Random Forest | roc_auc | 0.500000 | 0.643309 | unfavorable | exploratory unfavorable | [-0.30374, -0.00972] |
| P27 | SECOM | HistGradientBoosting | roc_auc | 0.500000 | 0.691078 | unfavorable | inconclusive | [-0.35971, 0.0289] |
| P28 | SECOM | XGBoost | roc_auc | 0.500000 | 0.444052 | favorable | inconclusive | [-0.12207, 0.21261] |
| P29 | SECOM | LightGBM | roc_auc | 0.500000 | 0.653717 | unfavorable | inconclusive | [-0.38059, 0.07239] |
| P30 | SECOM | CatBoost | roc_auc | 0.500000 | 0.666543 | unfavorable | inconclusive | [-0.35718, -0.00163] |
| P61 | Statlog German Credit | Logistic / Ridge | roc_auc | 0.770989 | 0.784626 | unfavorable | inconclusive | [-0.05494, 0.0296] |
| P62 | Statlog German Credit | Random Forest | roc_auc | 0.770989 | 0.778142 | unfavorable | inconclusive | [-0.04804, 0.03346] |
| P63 | Statlog German Credit | HistGradientBoosting | roc_auc | 0.770989 | 0.741243 | favorable | inconclusive | [-0.01443, 0.07383] |
| P64 | Statlog German Credit | XGBoost | roc_auc | 0.770989 | 0.700067 | favorable | exploratory favorable | [0.01385, 0.12488] |
| P65 | Statlog German Credit | LightGBM | roc_auc | 0.770989 | 0.725434 | favorable | inconclusive | [-0.00304, 0.09176] |
| P66 | Statlog German Credit | CatBoost | roc_auc | 0.770989 | 0.783222 | unfavorable | inconclusive | [-0.05811, 0.02938] |
| P67 | Breast Cancer Wisconsin | Logistic / Ridge | roc_auc | 0.989778 | 0.989194 | favorable | inconclusive | [-0.00787, 0.0108] |
| P68 | Breast Cancer Wisconsin | Random Forest | roc_auc | 0.989778 | 0.989048 | favorable | inconclusive | [-0.00778, 0.01139] |
| P69 | Breast Cancer Wisconsin | HistGradientBoosting | roc_auc | 0.989778 | 0.988464 | favorable | inconclusive | [-0.0103, 0.01668] |
| P70 | Breast Cancer Wisconsin | XGBoost | roc_auc | 0.989778 | 0.986273 | favorable | inconclusive | [-0.00362, 0.01725] |
| P71 | Breast Cancer Wisconsin | LightGBM | roc_auc | 0.989778 | 0.986565 | favorable | inconclusive | [-0.00676, 0.01998] |
| P72 | Breast Cancer Wisconsin | CatBoost | roc_auc | 0.989778 | 0.988610 | favorable | inconclusive | [-0.00836, 0.01544] |

## Multiclass

| ID | Dataset | Comparator | Primary metric | CodAdapt | Comparator | Numerical direction | Recorded outcome | Original effect CI95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P31 | Annealing | Logistic / Ridge | balanced_accuracy | 0.610802 | 0.822531 | unfavorable | exploratory unfavorable | [-0.38751, -0.04456] |
| P32 | Annealing | Random Forest | balanced_accuracy | 0.610802 | 0.861111 | unfavorable | exploratory unfavorable | [-0.39954, -0.10591] |
| P33 | Annealing | HistGradientBoosting | balanced_accuracy | 0.610802 | 0.796296 | unfavorable | exploratory unfavorable | [-0.34107, -0.0308] |
| P34 | Annealing | XGBoost | balanced_accuracy | 0.610802 | 0.837654 | unfavorable | exploratory unfavorable | [-0.3786, -0.08317] |
| P35 | Annealing | LightGBM | balanced_accuracy | 0.610802 | 0.818210 | unfavorable | exploratory unfavorable | [-0.36107, -0.05556] |
| P36 | Annealing | CatBoost | balanced_accuracy | 0.610802 | 0.754321 | unfavorable | exploratory unfavorable | [-0.21709, -0.07124] |
| P37 | Pen Digits | Logistic / Ridge | balanced_accuracy | 0.927756 | 0.952617 | unfavorable | exploratory unfavorable | [-0.03759, -0.01234] |
| P38 | Pen Digits | Random Forest | balanced_accuracy | 0.927756 | 0.988053 | unfavorable | exploratory unfavorable | [-0.07212, -0.05034] |
| P39 | Pen Digits | HistGradientBoosting | balanced_accuracy | 0.927756 | 0.992057 | unfavorable | exploratory unfavorable | [-0.07601, -0.05395] |
| P40 | Pen Digits | XGBoost | balanced_accuracy | 0.927756 | 0.986437 | unfavorable | exploratory unfavorable | [-0.06989, -0.0486] |
| P41 | Pen Digits | LightGBM | balanced_accuracy | 0.927756 | 0.990532 | unfavorable | exploratory unfavorable | [-0.07491, -0.05255] |
| P42 | Pen Digits | CatBoost | balanced_accuracy | 0.927756 | 0.994546 | unfavorable | exploratory unfavorable | [-0.07825, -0.05641] |
| P73 | Forest Types | Logistic / Ridge | balanced_accuracy | 0.850000 | 0.835417 | favorable | inconclusive | [-0.09545, 0.11542] |
| P74 | Forest Types | Random Forest | balanced_accuracy | 0.850000 | 0.881250 | unfavorable | inconclusive | [-0.14173, 0.07025] |
| P75 | Forest Types | HistGradientBoosting | balanced_accuracy | 0.850000 | 0.854167 | unfavorable | inconclusive | [-0.12595, 0.09946] |
| P76 | Forest Types | XGBoost | balanced_accuracy | 0.850000 | 0.881250 | unfavorable | inconclusive | [-0.14173, 0.07025] |
| P77 | Forest Types | LightGBM | balanced_accuracy | 0.850000 | 0.881250 | unfavorable | inconclusive | [-0.14173, 0.07025] |
| P78 | Forest Types | CatBoost | balanced_accuracy | 0.850000 | 0.881250 | unfavorable | inconclusive | [-0.14173, 0.07025] |
| P79 | Glass | Logistic / Ridge | balanced_accuracy | 0.432456 | 0.418202 | favorable | inconclusive | [-0.19791, 0.22195] |
| P80 | Glass | Random Forest | balanced_accuracy | 0.432456 | 0.697295 | unfavorable | exploratory unfavorable | [-0.44405, -0.07086] |
| P81 | Glass | HistGradientBoosting | balanced_accuracy | 0.432456 | 0.474635 | unfavorable | inconclusive | [-0.24763, 0.14658] |
| M01 | Glass | XGBoost | balanced_accuracy | — | — | missing | missing | — |
| P82 | Glass | LightGBM | balanced_accuracy | 0.432456 | 0.524196 | unfavorable | inconclusive | [-0.35713, 0.16466] |
| P83 | Glass | CatBoost | balanced_accuracy | 0.432456 | 0.794956 | unfavorable | exploratory unfavorable | [-0.52184, -0.21115] |

## Regression

| ID | Dataset | Comparator | Primary metric | CodAdapt | Comparator | Numerical direction | Recorded outcome | Original effect CI95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P13 | NYC Reservoir | Logistic / Ridge | rmse | 2.861377 | 0.941486 | unfavorable | exploratory unfavorable | [-0.71063, -0.65296] |
| P14 | NYC Reservoir | Random Forest | rmse | 2.861377 | 2.143513 | unfavorable | exploratory unfavorable | [-0.33258, -0.13748] |
| P15 | NYC Reservoir | HistGradientBoosting | rmse | 2.861377 | 100.126852 | favorable | exploratory favorable | [25.86153, 44.77315] |
| P16 | NYC Reservoir | XGBoost | rmse | 2.861377 | 1.295929 | unfavorable | exploratory unfavorable | [-0.70353, -0.3445] |
| P17 | NYC Reservoir | LightGBM | rmse | 2.861377 | 91.686656 | favorable | exploratory favorable | [24.98906, 39.8927] |
| P18 | NYC Reservoir | CatBoost | rmse | 2.861377 | 130.573622 | favorable | exploratory favorable | [42.94065, 46.43218] |
| P19 | Concrete | Logistic / Ridge | rmse | 7.670131 | 11.241282 | favorable | exploratory favorable | [0.30912, 0.61114] |
| P20 | Concrete | Random Forest | rmse | 7.670131 | 8.377899 | favorable | inconclusive | [-0.18674, 0.33213] |
| P21 | Concrete | HistGradientBoosting | rmse | 7.670131 | 7.125968 | unfavorable | inconclusive | [-0.22715, 0.0576] |
| P22 | Concrete | XGBoost | rmse | 7.670131 | 7.679753 | favorable | inconclusive | [-0.19896, 0.16506] |
| P23 | Concrete | LightGBM | rmse | 7.670131 | 7.058914 | unfavorable | inconclusive | [-0.20776, 0.03149] |
| P24 | Concrete | CatBoost | rmse | 7.670131 | 6.222557 | unfavorable | exploratory unfavorable | [-0.29648, -0.08683] |
| P43 | Edge task execution times | Logistic / Ridge | rmse | 0.081945 | 0.077812 | unfavorable | exploratory unfavorable | [-0.07376, -0.01576] |
| P44 | Edge task execution times | Random Forest | rmse | 0.081945 | 0.180472 | favorable | exploratory favorable | [0.81281, 1.45539] |
| P45 | Edge task execution times | HistGradientBoosting | rmse | 0.081945 | 0.062866 | unfavorable | exploratory unfavorable | [-0.39211, -0.02846] |
| P46 | Edge task execution times | XGBoost | rmse | 0.081945 | 0.063858 | unfavorable | exploratory unfavorable | [-0.36617, -0.03153] |
| P47 | Edge task execution times | LightGBM | rmse | 0.081945 | 0.223428 | favorable | exploratory favorable | [1.2489, 2.04515] |
| P48 | Edge task execution times | CatBoost | rmse | 0.081945 | 0.072990 | unfavorable | exploratory unfavorable | [-0.16469, -0.02894] |
| P49 | Abalone | Logistic / Ridge | rmse | 2.481442 | 2.359945 | unfavorable | inconclusive | [-0.10214, 0.03383] |
| P50 | Abalone | Random Forest | rmse | 2.481442 | 2.267673 | unfavorable | exploratory unfavorable | [-0.11783, -0.04909] |
| P51 | Abalone | HistGradientBoosting | rmse | 2.481442 | 2.241184 | unfavorable | exploratory unfavorable | [-0.12419, -0.06457] |
| P52 | Abalone | XGBoost | rmse | 2.481442 | 2.322259 | unfavorable | exploratory unfavorable | [-0.0957, -0.03216] |
| P53 | Abalone | LightGBM | rmse | 2.481442 | 2.240455 | unfavorable | exploratory unfavorable | [-0.12293, -0.06812] |
| P54 | Abalone | CatBoost | rmse | 2.481442 | 2.237011 | unfavorable | exploratory unfavorable | [-0.12122, -0.07347] |
| P55 | Automobile | Logistic / Ridge | rmse | 4668.945963 | 4092.151609 | unfavorable | inconclusive | [-0.51376, 1.02698] |
| P56 | Automobile | Random Forest | rmse | 4668.945963 | 3458.724768 | unfavorable | exploratory unfavorable | [-0.34042, -0.0456] |
| P57 | Automobile | HistGradientBoosting | rmse | 4668.945963 | 5959.620963 | favorable | exploratory favorable | [0.1105, 0.9402] |
| P58 | Automobile | XGBoost | rmse | 4668.945963 | 2682.098217 | unfavorable | inconclusive | [-0.66155, 0.22706] |
| P59 | Automobile | LightGBM | rmse | 4668.945963 | 5981.165432 | favorable | exploratory favorable | [0.07808, 1.03588] |
| P60 | Automobile | CatBoost | rmse | 4668.945963 | 4609.294471 | unfavorable | inconclusive | [-0.12534, 0.09693] |

## Joint quality–resource observations

These 15 observations pass the recorded pointwise loss/bytes/five-cost screen, not an independent Pareto certification. Loss is log loss for classification and RMSE for regression. Ratios are CodAdapt / comparator (lower is better).

| ID | Dataset | Comparator | Loss ratio | Bytes ratio | Fit ratio | B1 ratio | B3000 ratio | Train RSS ratio | Load ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P02 | Danish occupancy | Random Forest | 0.6002 | 0.00976 | 0.1666 | 0.1186 | 0.0773 | 0.8985 | 0.0822 |
| P03 | Danish occupancy | HistGradientBoosting | 0.8865 | 0.25900 | 0.4964 | 0.2540 | 0.1963 | 0.9664 | 0.5232 |
| P04 | Danish occupancy | XGBoost | 0.9012 | 0.37792 | 0.2977 | 0.2400 | 0.3829 | 0.9610 | 0.2267 |
| P05 | Danish occupancy | LightGBM | 0.8932 | 0.35222 | 0.8933 | 0.7785 | 0.4922 | 0.9097 | 0.5547 |
| P08 | Denver trees | Random Forest | 0.4842 | 0.04195 | 0.4166 | 0.1563 | 0.1114 | 0.9764 | 0.2274 |
| P10 | Denver trees | XGBoost | 0.9574 | 0.22248 | 0.4528 | 0.2297 | 0.3627 | 0.9676 | 0.2534 |
| P15 | NYC Reservoir | HistGradientBoosting | 0.0286 | 0.36456 | 0.6025 | 0.3356 | 0.2344 | 0.9752 | 0.7081 |
| P17 | NYC Reservoir | LightGBM | 0.0312 | 0.21591 | 0.8582 | 0.8530 | 0.2268 | 0.9064 | 0.2895 |
| P20 | Concrete | Random Forest | 0.9155 | 0.00953 | 0.2999 | 0.0724 | 0.0831 | 0.9002 | 0.0776 |
| P22 | Concrete | XGBoost | 0.9987 | 0.11831 | 0.1624 | 0.1937 | 0.1995 | 0.9438 | 0.2136 |
| P44 | Edge task execution times | Random Forest | 0.4541 | 0.00094 | 0.1249 | 0.0736 | 0.0543 | 0.7983 | 0.0245 |
| P47 | Edge task execution times | LightGBM | 0.3668 | 0.07962 | 0.7203 | 0.4465 | 0.3393 | 0.9099 | 0.3354 |
| P62 | Statlog German Credit | Random Forest | 0.9883 | 0.01260 | 0.3560 | 0.3584 | 0.0968 | 0.9340 | 0.2188 |
| P64 | Statlog German Credit | XGBoost | 0.9097 | 0.28070 | 0.4198 | 0.3255 | 0.2752 | 0.9630 | 0.4616 |
| P66 | Statlog German Credit | CatBoost | 0.9769 | 0.14803 | 0.0383 | 0.5609 | 0.1631 | 0.8407 | 0.8712 |
