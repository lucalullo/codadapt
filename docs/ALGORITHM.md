# Learning algorithm

CodAdapt encodes numerical and categorical tabular features using train-only quantile/vocabulary information. It learns residual contributions through compact coded lookup memories, with adaptive levels and a bounded lookup budget. Unseen and missing values are handled under the encoder's supported input contract. Classification uses one binary head or shared encoding with independent one-vs-rest heads and normalized sigmoid outputs; this is not a softmax learner. Regression predicts a single target. Sample and class weights follow the estimator contract.

The 2.2.0 additions concern combined requests, authenticated reuse and snapshot persistence. They do not establish an improved predictive learner. Read the [API](API.md), [resource admission limits](LARGE_DATASETS.md), and [benchmarks](../BENCHMARKS.md). The unchanged implementation is the authoritative specification.
