"""Source and producer identity checked before trusted predictive unpickling."""

import hashlib
import json
import platform
import struct
import sys
import sysconfig
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = (HERE / "source_contract.json").read_bytes()
CONTRACT = json.loads(RAW)
CONTRACT_SHA256 = hashlib.sha256(RAW).hexdigest()
for name, expected in CONTRACT["serving_sources"].items():
    if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
        raise ImportError("Private serving source integrity mismatch: " + name)


def producer():
    return dict(
        contract_sha256=CONTRACT_SHA256,
        native_source_sha256=CONTRACT["native_source_sha256"],
        python=list(sys.version_info[:3]),
        implementation=platform.python_implementation(),
        numpy=np.__version__,
        pandas=pd.__version__,
        byteorder=sys.byteorder,
        pointer_bits=struct.calcsize("P") * 8,
        GIL_disabled=bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        platform=sys.platform,
        machine=platform.machine(),
    )


def validate_producer(value):
    current = producer()
    if not isinstance(value, dict) or set(value) != set(current):
        raise ValueError("Unsupported producer metadata fields")
    if not (
        isinstance(value["python"], list)
        and len(value["python"]) == 3
        and all(type(v) is int and v >= 0 for v in value["python"])
    ):
        raise ValueError("Invalid producer Python version")
    if value["python"][:2] != current["python"][:2]:
        raise ValueError("Cross-Python-minor images require separate qualification")
    readable_contracts = {current["contract_sha256"]}
    if (
        type(value["contract_sha256"]) is not str
        or value["contract_sha256"] not in readable_contracts
    ):
        raise ValueError("Unsupported producer compatibility: contract_sha256")
    for name in (
        "native_source_sha256",
        "implementation",
        "numpy",
        "pandas",
        "byteorder",
        "pointer_bits",
        "GIL_disabled",
    ):
        if type(value[name]) is not type(current[name]) or value[name] != current[name]:
            raise ValueError("Unsupported producer compatibility: " + name)
    if current["implementation"] != "CPython" or current["GIL_disabled"]:
        raise ValueError("Only standard-GIL CPython is admitted")
    if (current["numpy"], current["pandas"]) not in {("2.5.4", "3.1.0"), ("1.26.4", "2.2.3")}:
        raise ValueError(
            "This serving contract requires a qualified NumPy/pandas dependency profile"
        )
    for name in ("platform", "machine"):
        if not isinstance(value[name], str) or not value[name]:
            raise ValueError("Invalid producer platform identity")
