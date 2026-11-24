# Limitations

CodAdapt 2.2.0 improves technical interfaces and storage. It does not introduce a
new qualified predictive learner. The learning algorithm remains that of 2.1.0.

| Requirement | Status |
|---|---|
| Resource-bound qualification (C60) | **Not qualified**. Observed 837 and 787 accesses exceed the original limit of 512. A small compressed file alone does not satisfy the joint byte, access, latency and memory contract. |
| Independent Pareto confirmation | **Not certified**. No panel of at least 20 independently certified origins has completed confirmation. The original loss ratio limit of 1.05 and byte ratio limit of 0.50 are unchanged. |
| Predictive superiority | No general superiority or new predictive improvement is established. |
| Cross-platform support | Limited to the tests and dependency profiles in the compatibility record. Hosted runner results remain separate from local evidence. |

The development panel contains 14 exploratory favorable, 40 inconclusive and 29
unfavorable comparisons, plus one missing comparison. Inconclusive does not mean
equivalent. Fifteen favorable quality-resource points on six origins are
pointwise observations, not independent Pareto certificates. No globally
Holm-confirmed primary superiority is established.

Accuracy and AUC can conceal inadequate operating recall. Danish occupancy has
native-threshold FPR about 6.30%, exceeding the 0.5% limit in protocols that
require it. SECOM shows weak ranking and zero operational recall in the recorded
case. Multiclass and regression results also include substantial losses against
established competitors. Evaluate all protected metrics for the intended use.

Compression may add loading overhead and does not imply lower resident RAM.
Prepared inputs retain encoded rows and a model copy and only help workloads that
can amortize preparation. The regression combined-output interface can add
overhead. Training speed improvements are not claimed.

The wheel is pure Python. Historical C++ binaries and their qualification are
not inherited. Experimental modules remain experimental; their presence does
not qualify their predictive behavior. The separate lightweight serving/trace
companion is not included in the distributions. Its historical measurements do
not establish a bundled feature or superiority to another serving system.

See [compatibility](COMPATIBILITY.md), [persistence](PERSISTENCE.md),
[performance](PERFORMANCE.md) and the [complete benchmarks](../benchmarks/README.md).
