# Historical 2.1.0 classification panel

Separate previously published 90-fit panel (three sources, five grouped folds, six fixed presets, zero tuning budget). Windows 11 x64, AMD Ryzen 7 255, about 32 GB RAM, CPython 3.12.10, one numerical thread; CPU affinity and frequency were not pinned. This panel must not be pooled with the later 14-origin development benchmark or described as 2.2.0 timing.

| Dataset | CodAdapt BA / log loss | Random Forest | HistGradientBoosting | LightGBM |
|---|---:|---:|---:|---:|
| Music | 0.7450 / 0.71474 | 0.7925 / 0.66724 | 0.8000 / 0.85197 | 0.7875 / 0.74840 |
| Wireless | 0.9720 / 0.13803 | 0.9850 / 0.05875 | 0.9810 / 0.08621 | 0.9825 / 0.07270 |
| Rice | 0.92462 / 0.19845 | 0.91843 / 0.34571 | 0.91943 / 0.22696 | 0.91544 / 0.23246 |

Music mean fit time / batch-2048 latency / pickle size: CodAdapt 48.26 ms / 3.672 ms / 87.86 KiB; Random Forest 222.08 ms / 10.00 ms / 972.14 KiB; HistGradientBoosting 531.96 ms / 32.65 ms / 634.25 KiB. No universal superiority is established.

The [original fold observations](historical/observed_classification.csv) and [data attribution](historical/DATA_LICENSE.md) are preserved. Original dataset archives and runner history remain in the original 2.1.0 repository, not in this source bundle. Earlier experimental and native reports retain their historical identities.
