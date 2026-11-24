# Benchmark results by dataset

All values are transcribed at the displayed precision of the supplied development benchmark report (pages 26–53). These are **CodAdapt 2.1.0** competitive observations, not fresh 2.2.0 comparisons. Bold identifies the best displayed number in each column within a dataset; it is not a significance claim. Units and distinct memory measures are retained. A dash denotes missing or inapplicable data. See [methodology](METHODOLOGY.md) and [paired comparisons](COMPARISONS.md).

## Breast Cancer Wisconsin

**Binary** · CORE 274 / VALID 171 · 9 features (0 categorical) · 117 observed VALID groups. Source pages 26-27.

Best displayed primary metric: **CodAdapt 2.1.0 (0.989778)**. CodAdapt: 0.989778. Pairwise numerical directions: 6 favorable, 0 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | ROC-AUC ↑ | Log loss ↓ | FPR ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.929825 | 0.915669 | 0.923547 | **0.989778** | 0.156891 | **0.028037** |
| Logistic / Ridge | 0.941520 | 0.931294 | 0.936742 | 0.989194 | 0.143281 | **0.028037** |
| Random Forest | 0.929825 | 0.915669 | 0.923547 | 0.989048 | 0.132113 | **0.028037** |
| HistGradientBoosting | 0.935673 | 0.923481 | 0.930170 | 0.988464 | 0.139656 | **0.028037** |
| XGBoost | 0.941520 | 0.931294 | 0.936742 | 0.986273 | 0.187864 | **0.028037** |
| LightGBM | 0.929825 | 0.915669 | 0.923547 | 0.986565 | 0.165322 | **0.028037** |
| CatBoost | **0.959064** | **0.954731** | **0.956162** | 0.988610 | **0.123151** | **0.028037** |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0626** | 0.3287 | 1.0258 | 2924547 | 0.4591 |
| Logistic / Ridge | 0.0891 | 1.1989 | 1.4440 | 2077562 | **0.3811** |
| Random Forest | 0.1553 | 4.2038 | 6.6304 | 452461 | 1.6234 |
| HistGradientBoosting | 0.1103 | 1.3695 | 4.5686 | 656656 | 0.8625 |
| XGBoost | 0.2090 | 1.4358 | 2.5425 | 1179941 | 1.5949 |
| LightGBM | 0.0727 | **0.1506** | 1.9562 | 1533586 | 0.6745 |
| CatBoost | 0.2716 | 0.2820 | **0.6751** | **4443786** | 0.8143 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 40869 | **142.10** | 142.66 | **306.70** | 142.68 |
| Logistic / Ridge | **3298** | 143.16 | **142.56** | 308.62 | **142.58** |
| Random Forest | 277629 | 145.94 | 147.42 | 311.68 | 147.43 |
| HistGradientBoosting | 58972 | 145.53 | 145.40 | 310.56 | 145.42 |
| XGBoost | 56970 | 147.16 | 146.08 | 312.29 | 146.10 |
| LightGBM | 55759 | 155.47 | 153.71 | 319.18 | 154.11 |
| CatBoost | 174386 | 157.70 | 152.75 | 322.77 | 152.77 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 7.6710 | **2.1837** | 162.51 | 178.79 |
| Logistic / Ridge | **7.4840** | 2.2948 | 17.64 | **30.12** |
| Random Forest | 8.2030 | 2.4274 | 201.29 | 715.69 |
| HistGradientBoosting | 8.0940 | 2.4230 | 196.36 | 224.46 |
| XGBoost | 7.9370 | 2.4825 | **15.76** | 75.01 |
| LightGBM | 8.2340 | 2.5202 | 16.48 | 112.49 |
| CatBoost | 8.2960 | 2.6423 | 182.51 | 220.45 |

### Recall by class

| Estimator | Class 0 | Class 1 |
| --- | --- | --- |
| CodAdapt 2.1.0 | 0.97196 | 0.85938 |
| Logistic / Ridge | 0.97196 | 0.89062 |
| Random Forest | 0.97196 | 0.85938 |
| HistGradientBoosting | 0.97196 | 0.87500 |
| XGBoost | 0.97196 | 0.89062 |
| LightGBM | 0.97196 | 0.85938 |
| CatBoost | 0.97196 | 0.93750 |

## Danish occupancy

**Binary** · CORE 3264 / VALID 1280 · 6 features (1 categorical) · 20 observed VALID groups. Source pages 28-29.

Best displayed primary metric: **CatBoost (0.951437)**. CodAdapt: 0.939468. Pairwise numerical directions: 5 favorable, 1 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | ROC-AUC ↑ | Log loss ↓ | FPR ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.883594** | 0.832817 | 0.842639 | 0.939468 | 0.272298 | **0.063025** |
| Logistic / Ridge | 0.796875 | 0.691586 | 0.707335 | 0.839356 | 0.429341 | 0.092437 |
| Random Forest | 0.864844 | 0.817214 | 0.820722 | 0.901309 | 0.453711 | 0.085084 |
| HistGradientBoosting | 0.869531 | 0.818367 | 0.825127 | 0.922186 | 0.307165 | 0.076681 |
| XGBoost | 0.867969 | 0.810322 | 0.820742 | 0.919683 | 0.302156 | 0.071429 |
| LightGBM | 0.872656 | 0.816471 | 0.827106 | 0.919913 | 0.304851 | 0.068277 |
| CatBoost | **0.883594** | **0.835814** | **0.843645** | **0.951437** | **0.247998** | 0.066176 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0790** | 0.6948 | **1.5768** | **1902588** | 0.5311 |
| Logistic / Ridge | 0.1293 | 2.8249 | 4.1582 | 721466 | **0.4395** |
| Random Forest | 0.4744 | 5.8606 | 20.4014 | 147049 | 6.4628 |
| HistGradientBoosting | 0.1592 | 2.7352 | 8.0325 | 373483 | 1.0151 |
| XGBoost | 0.2655 | 2.8953 | 4.1183 | 728456 | 2.3429 |
| LightGBM | 0.0885 | 0.8925 | 3.2037 | 936417 | 0.9575 |
| CatBoost | 0.5687 | **0.4514** | 1.6057 | 1868344 | 0.6181 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 36577 | **143.22** | **143.44** | **307.74** | **143.46** |
| Logistic / Ridge | **3348** | 144.38 | 143.57 | 308.39 | 143.59 |
| Random Forest | 3749438 | 159.39 | 164.83 | 320.38 | 164.96 |
| HistGradientBoosting | 141224 | 148.20 | 147.05 | 312.20 | 147.13 |
| XGBoost | 96784 | 149.04 | 146.91 | 312.77 | 146.94 |
| LightGBM | 103848 | 157.43 | 154.84 | 320.59 | 154.86 |
| CatBoost | 88395 | 163.24 | 154.17 | 323.57 | 154.23 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **8.0460** | **2.3704** | 138.19 | 154.36 |
| Logistic / Ridge | 8.4060 | 2.6146 | 19.40 | **32.60** |
| Random Forest | 10.2030 | 2.9463 | 202.91 | 4117.19 |
| HistGradientBoosting | 9.5310 | 2.7227 | 260.66 | 289.45 |
| XGBoost | 9.3750 | 2.9905 | **15.59** | 113.69 |
| LightGBM | 8.6720 | 2.4304 | 16.74 | 207.17 |
| CatBoost | 8.5160 | 2.8410 | 91.99 | 160.92 |

### Recall by class

| Estimator | Class 0 | Class 1 |
| --- | --- | --- |
| CodAdapt 2.1.0 | 0.93697 | 0.72866 |
| Logistic / Ridge | 0.90756 | 0.47561 |
| Random Forest | 0.91492 | 0.71951 |
| HistGradientBoosting | 0.92332 | 0.71341 |
| XGBoost | 0.92857 | 0.69207 |
| LightGBM | 0.93172 | 0.70122 |
| CatBoost | 0.93382 | 0.73780 |

## Denver trees

**Binary** · CORE 52 / VALID 3372 · 4 features (3 categorical) · 1 observed VALID groups. Source pages 30-31.

Best displayed primary metric: **CatBoost (0.655039)**. CodAdapt: 0.500000. Pairwise numerical directions: 1 favorable, 3 unfavorable, 2 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | ROC-AUC ↑ | Log loss ↓ | FPR ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.700771** | 0.500000 | 0.412031 | 0.500000 | 0.677164 | **0.000000** |
| Logistic / Ridge | 0.664591 | **0.511382** | **0.488360** | 0.645060 | 0.781352 | 0.107067 |
| Random Forest | 0.700178 | 0.503268 | 0.423961 | 0.648162 | 1.398444 | 0.006348 |
| HistGradientBoosting | **0.700771** | 0.500000 | 0.412031 | 0.500000 | 0.677164 | **0.000000** |
| XGBoost | **0.700771** | 0.500000 | 0.412031 | 0.392611 | 0.707282 | **0.000000** |
| LightGBM | **0.700771** | 0.500000 | 0.412031 | 0.500000 | 0.677164 | **0.000000** |
| CatBoost | 0.700178 | 0.500713 | 0.415628 | **0.655039** | **0.580610** | 0.002539 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0611** | 0.8234 | **1.9113** | **1569612** | 0.3873 |
| Logistic / Ridge | 0.0832 | 2.6342 | 5.9053 | 508018 | **0.2914** |
| Random Forest | 0.1466 | 5.2674 | 17.1647 | 174777 | 1.7034 |
| HistGradientBoosting | 0.1131 | 3.1602 | 6.9082 | 434267 | 0.5669 |
| XGBoost | 0.1349 | 3.5849 | 5.2699 | 569271 | 1.5284 |
| LightGBM | 0.0720 | 1.7958 | 3.6632 | 818956 | 0.4913 |
| CatBoost | 0.3562 | **0.7212** | 4.1571 | 721657 | 0.5759 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 7101 | **144.46** | **144.90** | **308.10** | **144.92** |
| Logistic / Ridge | **4629** | 144.70 | 145.91 | 309.59 | 145.93 |
| Random Forest | 169265 | 147.96 | 149.18 | 313.39 | 149.22 |
| HistGradientBoosting | 10144 | 147.87 | 147.52 | 312.78 | 148.86 |
| XGBoost | 31917 | 149.30 | 148.49 | 313.94 | 148.51 |
| LightGBM | 9115 | 158.12 | 156.00 | 322.20 | 156.02 |
| CatBoost | 55625 | 159.13 | 156.05 | 326.05 | 156.14 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **7.2040** | **2.1500** | 54.92 | 69.59 |
| Logistic / Ridge | 7.2970 | 2.1748 | 23.54 | 37.35 |
| Random Forest | 8.1090 | 2.1616 | 206.71 | 615.39 |
| HistGradientBoosting | 8.4690 | 2.4704 | 95.52 | 116.89 |
| XGBoost | 7.8130 | 2.3958 | **18.56** | 53.38 |
| LightGBM | 8.3280 | 2.5758 | 20.83 | **34.36** |
| CatBoost | 8.2970 | 2.6220 | 67.72 | 100.93 |

### Recall by class

| Estimator | Class 0 | Class 1 |
| --- | --- | --- |
| CodAdapt 2.1.0 | 1.00000 | 0.00000 |
| Logistic / Ridge | 0.89293 | 0.12983 |
| Random Forest | 0.99365 | 0.01288 |
| HistGradientBoosting | 1.00000 | 0.00000 |
| XGBoost | 1.00000 | 0.00000 |
| LightGBM | 1.00000 | 0.00000 |
| CatBoost | 0.99746 | 0.00396 |

## SECOM

**Binary** · CORE 201 / VALID 279 · 590 features (0 categorical) · 10 observed VALID groups. Source pages 32-33.

Best displayed primary metric: **HistGradientBoosting (0.691078)**. CodAdapt: 0.500000. Pairwise numerical directions: 1 favorable, 5 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | ROC-AUC ↑ | Log loss ↓ | FPR ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.964158** | 0.500000 | **0.490876** | 0.500000 | 0.219617 | **0.000000** |
| Logistic / Ridge | 0.784946 | **0.551487** | 0.484479 | 0.505762 | 1.342562 | 0.197026 |
| Random Forest | 0.960573 | 0.498141 | 0.489945 | 0.643309 | 0.297692 | 0.003717 |
| HistGradientBoosting | 0.960573 | 0.498141 | 0.489945 | **0.691078** | **0.207708** | 0.003717 |
| XGBoost | 0.942652 | 0.488848 | 0.485240 | 0.444052 | 0.257377 | 0.022305 |
| LightGBM | **0.964158** | 0.500000 | **0.490876** | 0.653717 | 0.223966 | **0.000000** |
| CatBoost | **0.964158** | 0.500000 | **0.490876** | 0.666543 | 0.215173 | **0.000000** |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.1337 | 4.4147 | 89.2765 | 33603 | 4.3669 |
| Logistic / Ridge | 0.1371 | 3.4050 | 31.0535 | 96607 | **0.4460** |
| Random Forest | 0.2645 | 7.3287 | 65.4892 | 45809 | 1.9367 |
| HistGradientBoosting | 0.3262 | 3.0673 | 25.2542 | 118792 | 1.4769 |
| XGBoost | 0.3877 | 9.7205 | 44.0977 | 68031 | 1.7275 |
| LightGBM | **0.1312** | **1.3099** | **8.7900** | **341297** | 0.5217 |
| CatBoost | 11.3590 | 6.2041 | 22.0675 | 135947 | 0.8959 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 292406 | **150.08** | 157.56 | **338.75** | 158.57 |
| Logistic / Ridge | 50082 | 152.43 | **147.43** | 385.04 | **151.97** |
| Random Forest | 312808 | 154.61 | 151.82 | 375.95 | 156.36 |
| HistGradientBoosting | 567273 | 163.96 | 153.17 | 361.95 | 157.76 |
| XGBoost | 63634 | 184.43 | 151.11 | 357.26 | 152.54 |
| LightGBM | **35780** | 176.52 | 157.46 | 351.57 | 158.71 |
| CatBoost | 186871 | 238.07 | 158.26 | 399.59 | 159.52 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 10.3590 | 2.6183 | 3315.16 | 3918.37 |
| Logistic / Ridge | 9.1400 | 2.6821 | 109.52 | 140.16 |
| Random Forest | 10.2180 | 2.8251 | 272.42 | 813.76 |
| HistGradientBoosting | **8.7810** | 2.7708 | 1194.88 | 1286.45 |
| XGBoost | 9.6400 | **2.6090** | 48.40 | 120.73 |
| LightGBM | 8.9220 | 2.7309 | **46.90** | **93.22** |
| CatBoost | 20.2960 | 13.8032 | 259.31 | 329.93 |

### Recall by class

| Estimator | Class 0 | Class 1 |
| --- | --- | --- |
| CodAdapt 2.1.0 | 1.00000 | 0.00000 |
| Logistic / Ridge | 0.80297 | 0.30000 |
| Random Forest | 0.99628 | 0.00000 |
| HistGradientBoosting | 0.99628 | 0.00000 |
| XGBoost | 0.97770 | 0.00000 |
| LightGBM | 1.00000 | 0.00000 |
| CatBoost | 1.00000 | 0.00000 |

## Statlog German Credit

**Binary** · CORE 426 / VALID 267 · 20 features (13 categorical) · 267 observed VALID groups. Source pages 34-35.

Best displayed primary metric: **Logistic / Ridge (0.784626)**. CodAdapt: 0.770989. Pairwise numerical directions: 3 favorable, 3 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | ROC-AUC ↑ | Log loss ↓ | FPR ↓ |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.775281** | 0.696524 | 0.709572 | 0.770989 | 0.514904 | **0.106952** |
| Logistic / Ridge | 0.764045 | **0.724265** | **0.721843** | **0.784626** | **0.507609** | 0.176471 |
| Random Forest | 0.741573 | 0.640274 | 0.651033 | 0.778142 | 0.521003 | **0.106952** |
| HistGradientBoosting | 0.730337 | 0.685896 | 0.683191 | 0.741243 | 0.578956 | 0.203209 |
| XGBoost | 0.734082 | 0.649231 | 0.657896 | 0.700067 | 0.565989 | 0.139037 |
| LightGBM | 0.730337 | 0.650134 | 0.657692 | 0.725434 | 0.547459 | 0.149733 |
| CatBoost | 0.745318 | 0.650100 | 0.661269 | 0.783222 | 0.527053 | 0.112299 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0776** | **3.4848** | **7.6156** | **393928** | 0.8978 |
| Logistic / Ridge | 0.1266 | 6.2549 | 16.5163 | 181639 | **0.4811** |
| Random Forest | 0.2180 | 9.7220 | 78.6739 | 38132 | 4.1040 |
| HistGradientBoosting | 0.1686 | 6.0113 | 24.9837 | 120078 | 0.6879 |
| XGBoost | 0.1849 | 10.7051 | 27.6726 | 108410 | 1.9448 |
| LightGBM | 0.0988 | 5.3048 | 13.2173 | 226975 | 0.6214 |
| CatBoost | 2.0267 | 6.2127 | 46.6791 | 64269 | 1.0305 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 20465 | **142.82** | 143.70 | **308.57** | 143.73 |
| Logistic / Ridge | **5067** | 144.06 | **143.39** | 310.14 | **143.43** |
| Random Forest | 1623992 | 152.91 | 155.29 | 320.13 | 156.74 |
| HistGradientBoosting | 104686 | 148.89 | 147.18 | 319.19 | 147.47 |
| XGBoost | 72907 | 148.31 | 147.31 | 315.25 | 147.34 |
| LightGBM | 44933 | 156.91 | 154.74 | 323.74 | 154.80 |
| CatBoost | 138252 | 169.88 | 154.70 | 331.36 | 154.73 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **8.5000** | **2.4468** | 180.20 | 206.98 |
| Logistic / Ridge | 8.5310 | 2.4672 | 29.32 | **43.56** |
| Random Forest | 10.3590 | 2.5920 | 212.34 | 2041.61 |
| HistGradientBoosting | 8.9370 | 2.6316 | 297.58 | 327.49 |
| XGBoost | 9.7340 | 2.6266 | **20.31** | 95.33 |
| LightGBM | 8.9690 | 2.5834 | 25.26 | 95.41 |
| CatBoost | 11.1090 | 4.4676 | 152.61 | 187.48 |

### Recall by class

| Estimator | Class 0 | Class 1 |
| --- | --- | --- |
| CodAdapt 2.1.0 | 0.89305 | 0.50000 |
| Logistic / Ridge | 0.82353 | 0.62500 |
| Random Forest | 0.89305 | 0.38750 |
| HistGradientBoosting | 0.79679 | 0.57500 |
| XGBoost | 0.86096 | 0.43750 |
| LightGBM | 0.85027 | 0.45000 |
| CatBoost | 0.88770 | 0.41250 |

## Annealing

**Multiclass** · CORE 340 / VALID 213 · 38 features (32 categorical) · 211 observed VALID groups. Source pages 36-37.

Best displayed primary metric: **Random Forest (0.861111)**. CodAdapt: 0.610802. Pairwise numerical directions: 0 favorable, 6 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | Log loss ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.910798 | 0.610802 | 0.617230 | 0.235004 |
| Logistic / Ridge | 0.967136 | 0.822531 | 0.876807 | 0.138350 |
| Random Forest | **0.981221** | **0.861111** | **0.910434** | **0.082378** |
| HistGradientBoosting | 0.948357 | 0.796296 | 0.850559 | 0.149441 |
| XGBoost | 0.971831 | 0.837654 | 0.891909 | 0.093657 |
| LightGBM | 0.953052 | 0.818210 | 0.815907 | 0.126538 |
| CatBoost | 0.976526 | 0.754321 | 0.767860 | 0.083795 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.1042** | **7.9912** | **20.0424** | **149683** | 1.7044 |
| Logistic / Ridge | 0.1326 | 9.3209 | 32.8540 | 91313 | **0.4212** |
| Random Forest | 0.1901 | 12.2834 | 131.2122 | 22864 | 1.9195 |
| HistGradientBoosting | 0.3052 | 10.5513 | 147.4144 | 20351 | 2.1922 |
| XGBoost | 0.2786 | 20.5929 | 64.1589 | 46759 | 2.8486 |
| LightGBM | 0.1167 | 10.9603 | 75.4028 | 39786 | 2.4343 |
| CatBoost | 48.9695 | 9.2741 | 108.8287 | 27566 | 1.6458 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 145132 | **144.66** | 145.14 | **311.40** | 145.18 |
| Logistic / Ridge | **9248** | 145.18 | **145.01** | 320.90 | **145.06** |
| Random Forest | 664002 | 149.93 | 151.48 | 323.15 | 151.49 |
| HistGradientBoosting | 426646 | 151.28 | 151.23 | 325.08 | 151.27 |
| XGBoost | 236218 | 150.90 | 150.57 | 322.37 | 150.59 |
| LightGBM | 328494 | 160.85 | 157.86 | 331.95 | 157.88 |
| CatBoost | 1067665 | 254.85 | 160.06 | 410.25 | 160.07 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 8.7820 | 2.2135 | 370.93 | 430.05 |
| Logistic / Ridge | **7.8750** | **2.1987** | 43.67 | **63.29** |
| Random Forest | 9.4690 | 2.2895 | 226.34 | 1115.41 |
| HistGradientBoosting | 10.2190 | 2.3991 | 1184.32 | 1304.08 |
| XGBoost | 10.1250 | 2.3684 | **27.19** | 262.87 |
| LightGBM | 9.3130 | 2.2828 | 35.94 | 650.47 |
| CatBoost | 58.4530 | 51.0022 | 1062.86 | 1105.59 |

### Recall by class

| Estimator | Class 0 | Class 1 | Class 2 | Class 3 | Class 4 |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.00000 | 0.87500 | 0.95679 | 1.00000 | 0.22222 |
| Logistic / Ridge | 0.50000 | 0.95833 | 0.98765 | 1.00000 | 0.66667 |
| Random Forest | 0.50000 | 0.91667 | 1.00000 | 1.00000 | 0.88889 |
| HistGradientBoosting | 0.50000 | 0.83333 | 0.98148 | 1.00000 | 0.66667 |
| XGBoost | 0.50000 | 0.91667 | 0.99383 | 1.00000 | 0.77778 |
| LightGBM | 0.50000 | 0.70833 | 0.99383 | 1.00000 | 0.88889 |
| CatBoost | 0.00000 | 1.00000 | 0.99383 | 1.00000 | 0.77778 |

## Forest Types

**Multiclass** · CORE 83 / VALID 53 · 9 features (0 categorical) · 53 observed VALID groups. Source pages 38-39.

Best displayed primary metric: **Random Forest (0.881250)**. CodAdapt: 0.850000. Pairwise numerical directions: 1 favorable, 5 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | Log loss ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.849057 | 0.850000 | 0.848472 | 0.445004 |
| Logistic / Ridge | 0.849057 | 0.835417 | 0.843953 | 0.380228 |
| Random Forest | **0.886792** | **0.881250** | **0.886551** | 0.966581 |
| HistGradientBoosting | 0.849057 | 0.854167 | 0.852151 | 0.731412 |
| XGBoost | **0.886792** | **0.881250** | **0.886551** | 0.438379 |
| LightGBM | **0.886792** | **0.881250** | **0.886551** | **0.364041** |
| CatBoost | **0.886792** | **0.881250** | **0.886551** | 0.479530 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.0816 | 0.9864 | 3.1650 | 947867 | 0.9167 |
| Logistic / Ridge | 0.1025 | 1.1301 | **1.6394** | **1829938** | **0.2920** |
| Random Forest | 0.1535 | 3.9171 | 6.3909 | 469417 | 1.5574 |
| HistGradientBoosting | 0.1121 | 1.7791 | 7.3940 | 405734 | 1.1420 |
| XGBoost | 0.1937 | 1.4722 | 2.7357 | 1096611 | 2.2565 |
| LightGBM | **0.0806** | **0.1430** | 2.6236 | 1143467 | 0.8693 |
| CatBoost | 0.5497 | 0.2905 | 1.7240 | 1740139 | 1.1326 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 124858 | **142.28** | **142.77** | 307.18 | **142.79** |
| Logistic / Ridge | **3384** | 142.65 | 142.78 | **306.75** | 142.80 |
| Random Forest | 152269 | 146.09 | 146.71 | 311.75 | 146.73 |
| HistGradientBoosting | 77729 | 146.03 | 147.05 | 311.49 | 147.08 |
| XGBoost | 133939 | 147.48 | 146.86 | 312.06 | 146.88 |
| LightGBM | 60994 | 155.98 | 153.55 | 319.35 | 153.97 |
| CatBoost | 547647 | 159.66 | 155.09 | 323.28 | 155.12 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 7.9840 | 2.5139 | 225.85 | 249.54 |
| Logistic / Ridge | **7.8910** | 2.5152 | 17.78 | **30.20** |
| Random Forest | 8.3130 | 2.5199 | 202.67 | 593.22 |
| HistGradientBoosting | 8.1880 | **2.5134** | 509.16 | 572.43 |
| XGBoost | 8.1870 | 2.6440 | 16.06 | 150.46 |
| LightGBM | 8.3430 | 2.6140 | **15.98** | 123.13 |
| CatBoost | 8.4060 | 2.9304 | 547.45 | 585.37 |

### Recall by class

| Estimator | Class 0 | Class 1 | Class 2 | Class 3 |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.93333 | 0.91667 | 0.80000 | 0.75000 |
| Logistic / Ridge | 1.00000 | 0.66667 | 0.80000 | 0.87500 |
| Random Forest | 1.00000 | 0.75000 | 0.90000 | 0.87500 |
| HistGradientBoosting | 1.00000 | 0.66667 | 1.00000 | 0.75000 |
| XGBoost | 1.00000 | 0.75000 | 0.90000 | 0.87500 |
| LightGBM | 1.00000 | 0.75000 | 0.90000 | 0.87500 |
| CatBoost | 1.00000 | 0.75000 | 0.90000 | 0.87500 |

## Glass

**Multiclass** · CORE 91 / VALID 57 · 9 features (0 categorical) · 57 observed VALID groups. Source pages 40-41.

Best displayed primary metric: **CatBoost (0.794956)**. CodAdapt: 0.432456. Pairwise numerical directions: 1 favorable, 4 unfavorable, 0 equal, 1 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | Log loss ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.631579 | 0.432456 | 0.450990 | 1.067650 |
| Logistic / Ridge | 0.578947 | 0.418202 | 0.442230 | 1.131484 |
| Random Forest | 0.754386 | 0.697295 | 0.731993 | 0.756781 |
| HistGradientBoosting | 0.649123 | 0.474635 | 0.483425 | 0.957407 |
| LightGBM | 0.649123 | 0.524196 | 0.571681 | 0.944583 |
| CatBoost | **0.807018** | **0.794956** | **0.812035** | **0.717343** |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0739** | 0.8788 | 2.8111 | 1067198 | 0.8280 |
| Logistic / Ridge | 0.0889 | 1.0740 | **1.4731** | **2036522** | **0.2516** |
| Random Forest | 0.1407 | 3.6859 | 7.5564 | 397014 | 1.5300 |
| HistGradientBoosting | 0.1128 | 2.2870 | 9.4179 | 318542 | 1.2271 |
| LightGBM | 0.0743 | **0.1407** | 5.3282 | 563042 | 1.3997 |
| CatBoost | 1.4199 | 0.2845 | 3.0652 | 978729 | 1.7568 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 108580 | **142.57** | **142.34** | **307.98** | **142.36** |
| Logistic / Ridge | **3559** | 142.76 | 142.60 | 308.48 | 142.62 |
| Random Forest | 519689 | 147.41 | 148.64 | 311.60 | 148.66 |
| HistGradientBoosting | 108858 | 146.28 | 146.98 | 309.38 | 147.00 |
| LightGBM | 126845 | 156.68 | 154.19 | 319.46 | 154.39 |
| CatBoost | 1204008 | 163.81 | 157.18 | 327.60 | 157.18 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **6.8590** | **2.0659** | 216.20 | 248.20 |
| Logistic / Ridge | 7.1250 | 2.1508 | 17.91 | **30.33** |
| Random Forest | 7.4530 | 2.1975 | 204.21 | 951.94 |
| HistGradientBoosting | 7.4380 | 2.1617 | 653.12 | 725.12 |
| LightGBM | 8.1400 | 2.5468 | **17.00** | 251.27 |
| CatBoost | 9.0160 | 3.7678 | 1188.31 | 1227.62 |

### Recall by class

| Estimator | Class 1 | Class 2 | Class 3 | Class 5 | Class 6 | Class 7 |
| --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.89474 | 0.70000 | 0.00000 | 0.00000 | 0.50000 | 0.50000 |
| Logistic / Ridge | 0.68421 | 0.70000 | 0.00000 | 0.00000 | 0.50000 | 0.62500 |
| Random Forest | 0.84211 | 0.85000 | 0.20000 | 0.66667 | 1.00000 | 0.62500 |
| HistGradientBoosting | 0.78947 | 0.70000 | 0.40000 | 0.33333 | 0.00000 | 0.62500 |
| LightGBM | 0.73684 | 0.75000 | 0.20000 | 0.33333 | 0.50000 | 0.62500 |
| CatBoost | 0.89474 | 0.85000 | 0.40000 | 1.00000 | 1.00000 | 0.62500 |

XGBoost: missing (frozen job failed); no replacement or imputation.

## Pen Digits

**Multiclass** · CORE 3199 / VALID 1998 · 16 features (0 categorical) · 1998 observed VALID groups. Source pages 42-43.

Best displayed primary metric: **CatBoost (0.994546)**. CodAdapt: 0.927756. Pairwise numerical directions: 0 favorable, 6 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | Accuracy ↑ | Balanced accuracy ↑ | Macro F1 ↑ | Log loss ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.927928 | 0.927756 | 0.927469 | 0.428367 |
| Logistic / Ridge | 0.952452 | 0.952617 | 0.952268 | 0.168635 |
| Random Forest | 0.987988 | 0.988053 | 0.988099 | 0.106451 |
| HistGradientBoosting | 0.991992 | 0.992057 | 0.992100 | 0.039144 |
| XGBoost | 0.986486 | 0.986437 | 0.986521 | 0.049849 |
| LightGBM | 0.990490 | 0.990532 | 0.990595 | 0.040632 |
| CatBoost | **0.994494** | **0.994546** | **0.994583** | **0.022516** |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.1483** | 2.2184 | 7.7389 | 387652 | 2.1598 |
| Logistic / Ridge | **0.1483** | 1.2499 | **1.9397** | **1546631** | **0.2934** |
| Random Forest | 0.4252 | 4.3306 | 18.3728 | 163285 | 8.6379 |
| HistGradientBoosting | 0.7929 | 3.5865 | 64.3338 | 46632 | 5.3973 |
| XGBoost | 0.6405 | 1.7385 | 19.0021 | 157877 | 9.9958 |
| LightGBM | 0.4441 | **0.2156** | 63.6561 | 47128 | 11.1335 |
| CatBoost | 23.6405 | 0.3897 | 10.0087 | 299739 | 7.9202 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 268543 | 145.82 | 145.85 | 309.79 | 146.08 |
| Logistic / Ridge | **4954** | **145.68** | **145.17** | **309.48** | **145.19** |
| Random Forest | 5409572 | 164.30 | 169.89 | 328.86 | 173.70 |
| HistGradientBoosting | 2119690 | 155.60 | 159.92 | 321.26 | 160.49 |
| XGBoost | 1032861 | 156.88 | 152.56 | 320.10 | 157.18 |
| LightGBM | 1837820 | 168.50 | 162.12 | 326.91 | 165.62 |
| CatBoost | 5821349 | 185.18 | 180.62 | 351.21 | 181.31 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 8.3280 | 2.5360 | 464.83 | 515.23 |
| Logistic / Ridge | **7.9690** | **2.4947** | 19.68 | **32.20** |
| Random Forest | 9.5930 | 2.9791 | 208.18 | 5736.29 |
| HistGradientBoosting | 11.6410 | 3.1858 | 3474.80 | 3710.99 |
| XGBoost | 9.5310 | 3.0755 | **18.52** | 1031.59 |
| LightGBM | 11.2340 | 3.0377 | 19.75 | 3591.54 |
| CatBoost | 31.8750 | 26.0762 | 5629.39 | 5920.84 |

### Recall by class

| Estimator | Class 0 | Class 1 | Class 2 | Class 3 | Class 4 | Class 5 | Class 6 | Class 7 | Class 8 | Class 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 0.92788 | 0.83173 | 0.93750 | 0.96354 | 0.97596 | 0.84896 | 1.00000 | 0.98551 | 0.84293 | 0.96354 |
| Logistic / Ridge | 0.90865 | 0.91346 | 0.96635 | 0.99479 | 0.99519 | 0.92708 | 0.98958 | 0.95652 | 0.91099 | 0.96354 |
| Random Forest | 0.99038 | 0.96635 | 0.97596 | 0.98958 | 1.00000 | 0.97396 | 1.00000 | 1.00000 | 0.98429 | 1.00000 |
| HistGradientBoosting | 0.99519 | 0.97596 | 0.98558 | 0.98958 | 1.00000 | 0.99479 | 1.00000 | 0.99517 | 0.98429 | 1.00000 |
| XGBoost | 0.99519 | 0.96154 | 0.98558 | 0.98958 | 1.00000 | 0.97917 | 1.00000 | 0.99517 | 0.96335 | 0.99479 |
| LightGBM | 0.99519 | 0.97115 | 0.98558 | 0.98958 | 1.00000 | 0.99479 | 1.00000 | 0.99517 | 0.97906 | 0.99479 |
| CatBoost | 0.99038 | 0.98558 | 0.99038 | 0.99479 | 1.00000 | 0.99479 | 1.00000 | 1.00000 | 0.98953 | 1.00000 |

## Abalone

**Regression** · CORE 1781 / VALID 1114 · 8 features (1 categorical) · 1114 observed VALID groups. Source pages 44-45.

Best displayed primary metric: **CatBoost (2.237011)**. CodAdapt: 2.481442. Pairwise numerical directions: 0 favorable, 6 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | RMSE ↓ | MAE ↓ |
| --- | --- | --- |
| CodAdapt 2.1.0 | 2.481442 | 1.785859 |
| Logistic / Ridge | 2.359945 | 1.670982 |
| Random Forest | 2.267673 | 1.638411 |
| HistGradientBoosting | 2.241184 | 1.606522 |
| XGBoost | 2.322259 | 1.648707 |
| LightGBM | 2.240455 | **1.593757** |
| CatBoost | **2.237011** | 1.595750 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0679** | **0.6382** | **1.5015** | **1998002** | 0.4053 |
| Logistic / Ridge | 0.1040 | 2.7409 | 3.8518 | 778857 | **0.3446** |
| Random Forest | 1.1581 | 5.3416 | 33.2237 | 90297 | 14.5961 |
| HistGradientBoosting | 0.1589 | 2.8052 | 8.8442 | 339205 | 0.6425 |
| XGBoost | 0.1809 | 2.4670 | 3.8656 | 776076 | 1.6013 |
| LightGBM | 0.0924 | 0.9286 | 3.8301 | 783269 | 0.8020 |
| CatBoost | 0.9913 | 0.6743 | 2.0559 | 1459215 | 0.9102 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 23383 | **142.25** | **143.16** | **306.29** | **143.18** |
| Logistic / Ridge | **3172** | 143.71 | 143.57 | 309.33 | 143.59 |
| Random Forest | 9748015 | 175.27 | 188.43 | 343.04 | 193.20 |
| HistGradientBoosting | 149809 | 147.10 | 146.87 | 312.27 | 146.99 |
| XGBoost | 108117 | 150.31 | 147.53 | 312.93 | 147.55 |
| LightGBM | 80137 | 156.91 | 154.32 | 320.36 | 154.50 |
| CatBoost | 213828 | 161.72 | 154.70 | 323.96 | 154.71 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **7.9840** | **2.5193** | 115.03 | 129.49 |
| Logistic / Ridge | 8.2500 | 2.5985 | 17.06 | **30.16** |
| Random Forest | 10.5470 | 3.6130 | 122.65 | 9879.68 |
| HistGradientBoosting | 8.6250 | 2.6493 | 270.38 | 299.07 |
| XGBoost | 8.3280 | 2.5551 | **13.73** | 122.21 |
| LightGBM | 9.1250 | 3.2148 | 14.33 | 161.64 |
| CatBoost | 9.0000 | 3.4227 | 217.57 | 269.71 |

## Automobile

**Regression** · CORE 84 / VALID 54 · 24 features (8 categorical) · 52 observed VALID groups. Source pages 46-47.

Best displayed primary metric: **XGBoost (2682.098217)**. CodAdapt: 4668.945963. Pairwise numerical directions: 2 favorable, 4 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | RMSE ↓ | MAE ↓ |
| --- | --- | --- |
| CodAdapt 2.1.0 | 4668.945963 | 2643.351201 |
| Logistic / Ridge | 4092.151609 | 2448.968191 |
| Random Forest | 3458.724768 | 1994.298796 |
| HistGradientBoosting | 5959.620963 | 3569.355735 |
| XGBoost | **2682.098217** | **1675.099980** |
| LightGBM | 5981.165432 | 3550.001436 |
| CatBoost | 4609.294471 | 2435.801816 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0688** | 2.5327 | **5.7081** | **525569** | 0.6505 |
| Logistic / Ridge | 0.1125 | 4.5704 | 11.9414 | 251227 | **0.3468** |
| Random Forest | 0.1977 | 7.2805 | 32.1655 | 93268 | 1.9344 |
| HistGradientBoosting | 0.1240 | 4.5714 | 14.2973 | 209830 | 0.5461 |
| XGBoost | 0.2248 | 7.0427 | 13.5422 | 221530 | 1.8957 |
| LightGBM | 0.0796 | 3.6690 | 8.3332 | 360006 | 0.3942 |
| CatBoost | 0.8674 | **1.7659** | 10.2105 | 293815 | 0.7926 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 31171 | **142.46** | **142.73** | **308.02** | **142.76** |
| Logistic / Ridge | **5214** | 142.98 | 143.03 | 311.99 | 143.05 |
| Random Forest | 774865 | 147.85 | 150.84 | 317.27 | 150.94 |
| HistGradientBoosting | 24695 | 146.32 | 145.59 | 313.56 | 145.62 |
| XGBoost | 103146 | 148.08 | 146.77 | 314.71 | 146.80 |
| LightGBM | 16749 | 156.18 | 154.34 | 322.75 | 154.66 |
| CatBoost | 155557 | 160.20 | 153.51 | 326.86 | 153.55 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **8.2040** | **2.5214** | 222.95 | 248.51 |
| Logistic / Ridge | 8.2500 | 2.5389 | 24.88 | **38.78** |
| Random Forest | 9.2500 | 2.6832 | 129.68 | 1130.90 |
| HistGradientBoosting | 8.5000 | 2.5967 | 159.34 | 189.24 |
| XGBoost | 8.7810 | 2.6374 | **17.99** | 121.69 |
| LightGBM | 8.6410 | 2.7151 | 21.06 | 43.05 |
| CatBoost | 8.9850 | 3.3015 | 167.02 | 201.03 |

## Concrete

**Regression** · CORE 431 / VALID 271 · 8 features (0 categorical) · 113 observed VALID groups. Source pages 48-49.

Best displayed primary metric: **CatBoost (6.222557)**. CodAdapt: 7.670131. Pairwise numerical directions: 3 favorable, 3 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | RMSE ↓ | MAE ↓ |
| --- | --- | --- |
| CodAdapt 2.1.0 | 7.670131 | 6.114294 |
| Logistic / Ridge | 11.241282 | 8.996588 |
| Random Forest | 8.377899 | 5.972000 |
| HistGradientBoosting | 7.125968 | 5.064744 |
| XGBoost | 7.679753 | 5.355533 |
| LightGBM | 7.058914 | 5.077083 |
| CatBoost | **6.222557** | **4.455996** |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0633** | 0.3073 | **0.9506** | **3155902** | 0.4867 |
| Logistic / Ridge | 0.1003 | 1.1047 | 1.2609 | 2379253 | **0.3063** |
| Random Forest | 0.2111 | 4.2439 | 11.4445 | 262135 | 6.2726 |
| HistGradientBoosting | 0.1452 | 1.5088 | 10.7190 | 279877 | 1.2663 |
| XGBoost | 0.3900 | 1.5863 | 4.7653 | 629551 | 2.2790 |
| LightGBM | 0.0794 | **0.1411** | 10.1958 | 294239 | 1.5612 |
| CatBoost | 1.1074 | 0.4327 | 1.5108 | 1985703 | 1.6833 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 37081 | **141.84** | **142.96** | **305.92** | **142.98** |
| Logistic / Ridge | **2883** | 142.80 | 143.05 | 308.16 | 143.07 |
| Random Forest | 3888995 | 157.56 | 164.14 | 318.20 | 164.15 |
| HistGradientBoosting | 207668 | 145.98 | 147.38 | 310.60 | 147.41 |
| XGBoost | 313424 | 150.30 | 148.39 | 313.84 | 148.41 |
| LightGBM | 157931 | 155.64 | 153.80 | 319.11 | 154.02 |
| CatBoost | 821261 | 163.21 | 157.31 | 319.46 | 157.33 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **8.0620** | **2.4357** | 147.96 | 162.38 |
| Logistic / Ridge | 8.2190 | 2.4779 | 14.98 | **25.32** |
| Random Forest | 8.9680 | 2.7540 | 120.80 | 4155.93 |
| HistGradientBoosting | 8.6090 | 2.6456 | 475.17 | 509.07 |
| XGBoost | 8.7180 | 2.9186 | **14.92** | 323.96 |
| LightGBM | 9.1870 | 2.7502 | 17.96 | 311.33 |
| CatBoost | 9.3280 | 3.5867 | 813.49 | 852.52 |

## Edge task execution times

**Regression** · CORE 1236 / VALID 502 · 3 features (1 categorical) · 12 observed VALID groups. Source pages 50-51.

Best displayed primary metric: **HistGradientBoosting (0.062866)**. CodAdapt: 0.081945. Pairwise numerical directions: 2 favorable, 4 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | RMSE ↓ | MAE ↓ |
| --- | --- | --- |
| CodAdapt 2.1.0 | 0.081945 | 0.058522 |
| Logistic / Ridge | 0.077812 | 0.057217 |
| Random Forest | 0.180472 | 0.129588 |
| HistGradientBoosting | **0.062866** | **0.038904** |
| XGBoost | 0.063858 | 0.040219 |
| LightGBM | 0.223428 | 0.162700 |
| CatBoost | 0.072990 | 0.050373 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0643** | **0.4068** | **0.9086** | **3301783** | 0.3687 |
| Logistic / Ridge | 0.0914 | 2.1436 | 3.3405 | 898069 | **0.3234** |
| Random Forest | 0.5143 | 5.5254 | 16.7182 | 179445 | 15.0252 |
| HistGradientBoosting | 0.1378 | 2.3325 | 5.4924 | 546209 | 0.6660 |
| XGBoost | 0.1873 | 2.2523 | 4.0377 | 742997 | 1.5291 |
| LightGBM | 0.0892 | 0.9110 | 2.6780 | 1120239 | 1.0994 |
| CatBoost | 0.2648 | 0.5986 | 1.7264 | 1737720 | 0.6671 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 10605 | **142.66** | **143.24** | 306.45 | **143.26** |
| Logistic / Ridge | **2875** | 142.81 | 143.27 | **305.01** | 143.29 |
| Random Forest | 11262001 | 178.70 | 190.38 | 333.57 | 200.05 |
| HistGradientBoosting | 192757 | 146.34 | 146.56 | 310.22 | 146.58 |
| XGBoost | 84866 | 148.01 | 147.16 | 312.27 | 147.18 |
| LightGBM | 133195 | 156.79 | 154.96 | 319.86 | 155.20 |
| CatBoost | 76805 | 158.22 | 152.69 | 319.52 | 152.71 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **8.1250** | **2.5073** | 56.06 | 66.52 |
| Logistic / Ridge | 8.2030 | 2.5352 | 16.45 | **29.60** |
| Random Forest | 9.3440 | 3.0084 | 122.25 | 11357.96 |
| HistGradientBoosting | 8.4370 | 2.6014 | 343.77 | 372.65 |
| XGBoost | 8.3750 | 2.6712 | **13.07** | 98.86 |
| LightGBM | 8.8440 | 2.7029 | 15.41 | 264.72 |
| CatBoost | 8.3910 | 2.6911 | 83.37 | 134.61 |

## NYC Reservoir

**Regression** · CORE 588 / VALID 252 · 4 features (1 categorical) · 6 observed VALID groups. Source pages 52-53.

Best displayed primary metric: **Logistic / Ridge (0.941486)**. CodAdapt: 2.861377. Pairwise numerical directions: 3 favorable, 3 unfavorable, 0 equal, 0 missing.

### Predictive quality

| Estimator | RMSE ↓ | MAE ↓ |
| --- | --- | --- |
| CodAdapt 2.1.0 | 2.861377 | 2.093726 |
| Logistic / Ridge | **0.941486** | **0.811943** |
| Random Forest | 2.143513 | 1.677494 |
| HistGradientBoosting | 100.126852 | 37.815487 |
| XGBoost | 1.295929 | 0.941128 |
| LightGBM | 91.686656 | 61.191481 |
| CatBoost | 130.573622 | 116.085899 |

### Latency and throughput

| Estimator | Fit + prep (s) ↓ | Batch 1 (ms) ↓ | Batch 3000 (ms) ↓ | Rows/s ↑ | Load (ms) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | **0.0724** | 0.7921 | **1.5766** | **1902829** | 0.4758 |
| Logistic / Ridge | 0.1029 | 2.2280 | 3.1723 | 945686 | **0.4102** |
| Random Forest | 0.2770 | 5.4958 | 17.8853 | 167736 | 7.8965 |
| HistGradientBoosting | 0.1202 | 2.3601 | 6.7247 | 446117 | 0.6719 |
| XGBoost | 0.1953 | 2.4124 | 3.8452 | 780193 | 1.8976 |
| LightGBM | 0.0844 | 0.9286 | 6.9504 | 431630 | 1.6434 |
| CatBoost | 0.5699 | **0.6262** | 1.9310 | 1553599 | 0.8411 |

### Memory and model footprint

| Estimator | Model (bytes) ↓ | Train RSS (MiB) ↓ | Loaded RSS (MiB) ↓ | Tree peak (MiB) ↓ | OS peak (MiB) ↓ |
| --- | --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 45736 | **142.12** | **142.79** | 306.88 | **142.82** |
| Logistic / Ridge | **3054** | 142.52 | 143.42 | **306.59** | 143.44 |
| Random Forest | 5272995 | 162.63 | 167.80 | 322.88 | 171.62 |
| HistGradientBoosting | 125454 | 145.73 | 146.35 | 311.21 | 146.38 |
| XGBoost | 97063 | 148.13 | 146.68 | 312.05 | 146.70 |
| LightGBM | 211832 | 156.80 | 154.95 | 320.33 | 154.97 |
| CatBoost | 183944 | 159.36 | 152.86 | 324.27 | 152.88 |

### Additional recorded costs

| Estimator | Job wall (s) ↓ | Cold snapshot (s) ↓ | Load retained (KiB) ↓ | Load peak (KiB) ↓ |
| --- | --- | --- | --- | --- |
| CodAdapt 2.1.0 | 8.5320 | 2.5481 | 144.13 | 158.63 |
| Logistic / Ridge | **8.4220** | **2.5284** | 16.94 | **30.05** |
| Random Forest | 9.1090 | 2.7789 | 122.63 | 5510.02 |
| HistGradientBoosting | 8.7030 | 2.6393 | 259.29 | 287.98 |
| XGBoost | 8.5470 | 2.6367 | **13.53** | 111.10 |
| LightGBM | 9.0470 | 2.7151 | 19.15 | 416.88 |
| CatBoost | 8.7340 | 3.0561 | 190.59 | 231.16 |
