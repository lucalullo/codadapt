# Security
Use trusted models and verified artifacts. Do not load untrusted pickle/joblib
or bypass Windows application control. Source checksums are integrity checks,
not signatures. Report issues to the maintainer through an appropriate private
channel; this repository contains no credentials or automated publishing code.
Do not include datasets, logs or model data containing sensitive information.

## Native ownership and review scope

The kernel holds the GIL and strong array owners through each call. It validates
dtype,shape,stride,index/support bounds and finite numerical values before use.
It does not serialize pointers or grant safe concurrent mutation of caller arrays.
Finite invalid-input and lifetime tests accompany static review; no absolute
security claim follows from a scanner or passing suite. Qualification receipts
check consistency against a trusted reference, not sender authenticity.
