# Data provenance and attribution
Normalized folds derive from UCI datasets under CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/ . Code remains under LICENSE (MIT).
- Wireless Indoor Localization, Bhatt (2017), DOI10.24432/C51880,
  https://archive.ics.uci.edu/dataset/422/wireless+indoor+localization
- Turkish Music Emotion, Er (2019), DOI10.24432/C5JG93,
  https://archive.ics.uci.edu/dataset/862/turkish+music+emotion
- Rice (Cammeo and Osmancik), UCI (2019), DOI10.24432/C5MW4Z,
  https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik
  Associated paper: Ilkay Cinar and M. Koklu, "Classification of Rice
  Varieties Using Artificial Intelligence Methods" (2019),
  https://doi.org/10.18201/ijisae.2019355381 . UCI metadata lists no dataset
  creators; this paper attribution does not invent a dataset author.
Changes: numeric feature names f0..., float64 conversion, target separation,
frozen grouped folds and safe NPZ serialization. No class filtering or extra
restrictions are added. No author endorsement is implied. Artist, recording
session, building and physical grain-lot independence are not established.
