"""Private structurally validated framing; pickle still requires authorized input.

No safe-unpickling, authenticity or estimator-API claim. Predictor unchanged.
"""

import hashlib
import io
import json
import math
import os
import pickle
import struct
import tempfile
from enum import Enum
from numbers import Integral, Real
from pathlib import Path

import numpy as np
import pandas as pd

from . import _contract
from . import portable_native_runtime as native

MAGIC = b"CDNIMG4\x00"
SCHEMA = 4
HEADER = struct.Struct("<8sHHIQQ32s")
VERSION = _contract.CONTRACT["native_version"]
MAX_JSON = 16 * 1024 * 1024


class NativeImageFormatError(ValueError):
    def __init__(self, section, expected, observed, failure_class="STRUCTURE"):
        self.section, self.expected = (section, str(expected))
        self.observed, self.failure_class = (str(observed)[:300], failure_class)
        super().__init__(
            f"Native image [{failure_class}] section={section}; expected={self.expected}; observed={self.observed}"
        )

    def as_dict(self):
        return dict(
            section=self.section,
            expected=self.expected,
            observed=self.observed,
            failure_class=self.failure_class,
        )


def require(condition, section, expected, observed, kind="STRUCTURE"):
    if not condition:
        raise NativeImageFormatError(section, expected, observed, kind)


def integer(value, section, low=0, high=(1 << 63) - 1):
    if not (isinstance(value, Integral) and (not isinstance(value, (bool, np.bool_)))):
        raise NativeImageFormatError(section, "integer", type(value).__name__, "TYPE")
    if not low <= int(value) <= high:
        raise NativeImageFormatError(section, f"{low} <= integer <= {high}", value, "BOUNDS")
    return int(value)


def keys(value, expected, section):
    if not isinstance(value, dict):
        raise NativeImageFormatError(section, "dictionary", type(value).__name__, "TYPE")
    if not set(value) == set(expected):
        raise NativeImageFormatError(
            section, f"exact keys {sorted(expected)}", sorted(map(str, value)), "SECTIONS"
        )


def digest_text(value, section):
    if not (
        isinstance(value, str)
        and len(value) == 64
        and all((c in "0123456789abcdef" for c in value))
    ):
        raise NativeImageFormatError(
            section, "64 lowercase hexadecimal SHA256 characters", repr(value), "CHECKSUM_METADATA"
        )


def json_read(blob, section):

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if not key not in result:
                raise NativeImageFormatError(
                    section, "unique JSON keys", f"duplicate key {key}", "DUPLICATE"
                )
            result[key] = value
        return result

    try:
        return json.loads(
            blob,
            object_pairs_hook=unique,
            parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)),
        )
    except NativeImageFormatError:
        raise
    except (ValueError, UnicodeError, TypeError) as exc:
        raise NativeImageFormatError(
            section, "complete finite UTF-8 JSON", type(exc).__name__, "JSON"
        ) from None


def array(value, section, kind=None, length=None, dtype=None):
    if not (isinstance(value, np.ndarray) and value.ndim == 1):
        raise NativeImageFormatError(
            section, "one-dimensional ndarray", type(value).__name__, "SHAPE"
        )
    if dtype is not None:
        if not value.dtype == np.dtype(dtype):
            raise NativeImageFormatError(
                section, f"dtype {np.dtype(dtype).str}", value.dtype.str, "DTYPE"
            )
    if kind is not None:
        if value.dtype.kind not in kind:
            raise NativeImageFormatError(section, f"dtype kind in {kind}", value.dtype.str, "DTYPE")
    if length is not None:
        if not len(value) == length:
            raise NativeImageFormatError(section, f"length {length}", len(value), "SHAPE")
    return value


def finite(value, section):
    if not (isinstance(value, Real) and math.isfinite(value)):
        raise NativeImageFormatError(section, "finite real scalar", type(value).__name__, "VALUE")


def scalar(value, section):
    if value is None or isinstance(value, (str, bool, np.bool_, Integral, native._BooleanKey)):
        return
    finite(value, section)


def node(value, buffers, section, memo):
    if not (isinstance(value, tuple) and len(value) > 0):
        raise NativeImageFormatError(section, "tagged tuple", type(value).__name__, "WIRE")
    tag = value[0]
    if tag == "a":
        if not len(value) == 4:
            raise NativeImageFormatError(
                section, "array tag,dtype,offset,shape", len(value), "WIRE"
            )
        _, dtype, offset, shape = value
        if not (isinstance(dtype, str) and dtype in buffers):
            raise NativeImageFormatError(section, "known buffer dtype code", dtype, "DTYPE")
        offset = integer(offset, section + ".offset")
        if not isinstance(shape, tuple):
            raise NativeImageFormatError(section, "shape tuple", type(shape).__name__, "SHAPE")
        length = math.prod((integer(v, section + ".shape") for v in shape))
        if not (offset <= len(buffers[dtype]) and length <= len(buffers[dtype]) - offset):
            raise NativeImageFormatError(
                section,
                "array span within buffer, no overflowing product",
                f"offset={offset},elements={length},buffer={len(buffers[dtype])}",
                "BOUNDS",
            )
        key = (dtype, offset, shape)
        if key not in memo:
            result = buffers[dtype][offset : offset + length].reshape(shape)
            result.flags.writeable = False
            memo[key] = result
        return memo[key]
    elif tag == "p":
        if not len(value) == 2:
            raise NativeImageFormatError(section, "primitive tag and value", len(value), "WIRE")
        v = value[1]
        if isinstance(v, (np.ndarray, pd.Index)):
            if not v.ndim == 1:
                raise NativeImageFormatError(
                    section, "one-dimensional primitive array/index", v.ndim, "SHAPE"
                )
        else:
            scalar(v, section)
        return v
    elif tag == "d":
        if not (len(value) == 2 and isinstance(value[1], tuple)):
            raise NativeImageFormatError(section, "dictionary pairs tuple", len(value), "WIRE")
        seen = set()
        decoded = {}
        for pair in value[1]:
            if not (isinstance(pair, tuple) and len(pair) == 2):
                raise NativeImageFormatError(section, "key/value pair", type(pair).__name__, "WIRE")
            key, val = pair
            scalar(key, section + ".key")
            if not key not in seen:
                raise NativeImageFormatError(
                    section, "unique dictionary keys", str(key), "DUPLICATE"
                )
            seen.add(key)
            decoded[key] = node(val, buffers, section + "." + str(key), memo)
        return decoded
    elif tag in {"l", "t"}:
        if not (len(value) == 2 and isinstance(value[1], tuple)):
            raise NativeImageFormatError(section, "tagged sequence", len(value), "WIRE")
        decoded = [node(val, buffers, f"{section}[{i}]", memo) for i, val in enumerate(value[1])]
        return decoded if tag == "l" else tuple(decoded)
    elif tag == "v":
        if not len(value) == 2:
            raise NativeImageFormatError(section, "resolution-view record", len(value), "WIRE")
        decoded = node(value[1], buffers, section + ".view", memo)
        result = object.__new__(native._ResolutionView)
        result.__dict__.update(decoded)
        return result
    else:
        raise NativeImageFormatError(section, "known packed state tag", str(tag), "WIRE")


def wire_validate(wire):
    if not (isinstance(wire, tuple) and len(wire) == 8):
        raise NativeImageFormatError("wire", "8-field packed tuple", type(wire).__name__, "WIRE")
    version, enc, classes, buffers, values, records, table_size, params = wire
    if not (type(version) is int and version == 1):
        raise NativeImageFormatError(
            "wire.version", "integer1 (not Boolean)", str(version), "SCHEMA"
        )
    if not isinstance(buffers, dict):
        raise NativeImageFormatError(
            "wire.buffers", "dtype-buffer dictionary", type(buffers).__name__
        )
    for code, buffer in buffers.items():
        if not isinstance(code, str):
            raise NativeImageFormatError(
                "wire.dtype", "string dtype code", type(code).__name__, "DTYPE"
            )
        try:
            dtype = np.dtype(code)
        except (TypeError, ValueError):
            raise NativeImageFormatError(
                "wire.dtype", "valid numeric/bool dtype code", repr(code), "DTYPE"
            ) from None
        if not (dtype.kind in "buif" and dtype.str == code):
            raise NativeImageFormatError(
                "wire.dtype", "canonical numeric/bool dtype", code, "DTYPE"
            )
        array(buffer, "wire.buffer." + code, dtype=dtype)
    array(values, "wire.coefficients", dtype=np.float64)
    if not np.isfinite(values).all():
        raise NativeImageFormatError(
            "wire.coefficients", "finite coefficients", "nonfinite", "VALUE"
        )
    for buffer in [values, *buffers.values()]:
        buffer.flags.writeable = False
    memo = {}
    decoded_encoder = node(enc, buffers, "wire.encoder", memo)
    decoded_heads = []
    if not isinstance(records, tuple):
        raise NativeImageFormatError("wire.records", "head tuple", type(records).__name__)
    for hi, record in enumerate(records):
        if not (isinstance(record, tuple) and len(record) == 2):
            raise NativeImageFormatError("wire.head", "intercept/levels", hi)
        intercept, levels = record
        finite(intercept, "wire.intercept")
        if not isinstance(levels, tuple):
            raise NativeImageFormatError("wire.levels", "level tuple", type(levels).__name__)
        decoded_levels = []
        for li, level in enumerate(levels):
            section = f"wire.head[{hi}].level[{li}]"
            if not (isinstance(level, tuple) and len(level) == 6):
                raise NativeImageFormatError(section, "6-field level", type(level).__name__)
            n, main, refs, groups, codes, tables = level
            integer(n, section + ".bins", 1, 65535)
            decoded_main = node(main, buffers, section + ".main", memo)
            if not all((isinstance(v, tuple) for v in [refs, groups, codes, tables])):
                raise NativeImageFormatError(section, "tuple collections", "wrong collection type")
            if not len(groups) == len(codes) == len(tables):
                raise NativeImageFormatError(
                    section,
                    "equal interaction section lengths",
                    f"{len(groups)}/{len(codes)}/{len(tables)}",
                    "SHAPE",
                )
            decoded_groups = [node(group, buffers, section + ".groups", memo) for group in groups]
            decoded_codes = []
            for group in codes:
                if not isinstance(group, tuple):
                    raise NativeImageFormatError(section, "codes tuple", type(group).__name__)
                decoded_codes.append(
                    [node(code, buffers, section + ".codes", memo) for code in group]
                )
            for ref in [*refs, *tables]:
                if not (isinstance(ref, tuple) and len(ref) == 2):
                    raise NativeImageFormatError(
                        section, "coefficient offset/length", type(ref).__name__
                    )
                offset, length = [integer(v, section + ".coefficient_ref") for v in ref]
                if not (offset <= len(values) and length <= len(values) - offset):
                    raise NativeImageFormatError(
                        section, "coefficient span within buffer", ref, "BOUNDS"
                    )

            def coefficients(ref):
                offset, length = ref
                result = values[offset : offset + length]
                result.flags.writeable = False
                return result

            decoded_levels.append(
                dict(
                    n_bins=n,
                    main_features=decoded_main,
                    main_tables=[coefficients(ref) for ref in refs],
                    groups=decoded_groups,
                    codes=decoded_codes,
                    tables=[coefficients(ref) for ref in tables],
                )
            )
        decoded_heads.append((intercept, decoded_levels))
    integer(table_size, "wire.table_size", 1, 65536)
    if not isinstance(params, dict):
        raise NativeImageFormatError("wire.params", "parameter dictionary", type(params).__name__)
    encoder = object.__new__(native.BucketEncoder)
    encoder.__dict__.update(decoded_encoder)
    return (encoder, classes, decoded_heads, table_size, params)


def encoder_validate(encoder):
    e = vars(encoder)
    base = {
        "n_bins",
        "max_categories",
        "quantile_sample_size",
        "categorical_features",
        "random_state",
        "n_features_in_",
        "_fit_dataframe_",
        "schemas_",
        "support_",
        "n_buckets_",
        "categorical_features_",
        "_is_fitted_",
        "resolution_bins_",
        "level_mappings_",
        "level_views_",
    }
    if not base <= set(e) <= base | {"_columns_", "feature_names_in_"}:
        raise NativeImageFormatError(
            "encoder", "mandatory known encoder fields, no extras", sorted(e), "SECTIONS"
        )
    p = integer(e["n_features_in_"], "encoder.n_features", 1, 10**7)
    if not (e["_is_fitted_"] is True and isinstance(e["_fit_dataframe_"], (bool, np.bool_))):
        raise NativeImageFormatError("encoder.flags", "fitted Boolean flags", "invalid flags")
    if e["_fit_dataframe_"]:
        columns = e.get("_columns_")
        if not (
            isinstance(columns, pd.Index) and len(columns) == p and (not columns.has_duplicates)
        ):
            raise NativeImageFormatError(
                "encoder.columns", f"{p} unique column labels", type(columns).__name__, "SHAPE"
            )
    if "feature_names_in_" in e:
        array(e["feature_names_in_"], "encoder.feature_names", length=p)
    for key in ["schemas_", "support_", "n_buckets_"]:
        if not (isinstance(e[key], list) and len(e[key]) == p):
            raise NativeImageFormatError(
                "encoder." + key, f"list of length {p}", type(e[key]).__name__, "SHAPE"
            )
    for j, (schema, support, count) in enumerate(
        zip(e["schemas_"], e["support_"], e["n_buckets_"])
    ):
        section = f"encoder.feature[{j}]"
        count = integer(count, section + ".bucket_count", 1, 65536)
        array(support, section + ".support", length=count, dtype=np.bool_)
        if not (isinstance(schema, dict) and schema.get("kind") in {"numeric", "categorical"}):
            raise NativeImageFormatError(section, "numeric/categorical schema", "unknown kind")
        if schema["kind"] == "numeric":
            keys(schema, {"kind", "thresholds", "missing_bucket"}, section)
            edges = array(schema["thresholds"], section + ".thresholds", dtype=np.float64)
            if not (np.isfinite(edges).all() and np.all(edges[1:] > edges[:-1])):
                raise NativeImageFormatError(
                    section, "finite strictly ordered cuts", "nonfinite/unordered cuts", "VALUE"
                )
            if not (len(edges) + 2 == count and schema["missing_bucket"] == count - 1):
                raise NativeImageFormatError(
                    section, "cuts+2 buckets, missing last", count, "SHAPE"
                )
        else:
            keys(
                schema,
                {
                    "kind",
                    "vocabulary",
                    "observed_categories",
                    "missing_bucket",
                    "rare_bucket",
                    "unknown_bucket",
                    "n_rare_categories",
                },
                section,
            )
            vocab, observed = (schema["vocabulary"], schema["observed_categories"])
            if not (isinstance(vocab, dict) and isinstance(observed, pd.Index)):
                raise NativeImageFormatError(
                    section, "vocabulary dict and observed Index", "wrong categorical state"
                )
            if not (schema["missing_bucket"], schema["rare_bucket"], schema["unknown_bucket"]) == (
                0,
                1,
                2,
            ):
                raise NativeImageFormatError(
                    section, "distinct reserved0/1/2", "invalid reserved states", "VALUE"
                )
            if not (
                count == len(vocab) + 3
                and len(observed) - len(vocab) == schema["n_rare_categories"]
            ):
                raise NativeImageFormatError(
                    section, "consistent category and rare counts", count, "SHAPE"
                )
            targets = set()
            for value, code in vocab.items():
                scalar(value, section + ".category")
                targets.add(integer(code, section + ".category_code", 3, count - 1))
            if not len(targets) == len(vocab):
                raise NativeImageFormatError(
                    section, "unique vocabulary codes", "duplicate codes", "DUPLICATE"
                )
    resolutions, mappings, views = (e["resolution_bins_"], e["level_mappings_"], e["level_views_"])
    if not (
        isinstance(resolutions, list)
        and len(resolutions) > 0
        and (len(resolutions) == len(mappings) == len(views))
    ):
        raise NativeImageFormatError(
            "encoder.levels",
            "matching nonempty resolutions/maps/views",
            "inconsistent level dimensions",
            "SHAPE",
        )
    for li, (bins, maps, view) in enumerate(zip(resolutions, mappings, views)):
        integer(bins, "encoder.level_bins", 1, 65535)
        if not isinstance(view, native._ResolutionView):
            raise NativeImageFormatError(
                "encoder.level_view", "ResolutionView", type(view).__name__
            )
        keys(vars(view), {"n_buckets_", "support_"}, "encoder.level_view")
        if not len(maps) == len(view.n_buckets_) == len(view.support_) == p:
            raise NativeImageFormatError(
                "encoder.level_view", f"{p} feature maps", "inconsistent dimensions", "SHAPE"
            )
        for j, (mapping, count, support) in enumerate(zip(maps, view.n_buckets_, view.support_)):
            count = integer(count, "encoder.level_buckets", 1, 65536)
            a = array(mapping, f"encoder.map[{li},{j}]", kind="ui", length=e["n_buckets_"][j])
            if not (a.size > 0 and int(a.max()) < count):
                raise NativeImageFormatError(
                    "encoder.map", "bucket codes within target view", "out of range", "BOUNDS"
                )
            array(support, "encoder.level_support", dtype=np.bool_, length=count)
    cats = array(e["categorical_features_"], "encoder.categorical_features", kind="ui")
    if not np.all(cats < p):
        raise NativeImageFormatError(
            "encoder.categorical_features", "indices within feature count", "out of range", "BOUNDS"
        )
    return p


def levels_validate(heads, encoder, table_size):
    for hi, (intercept, levels) in enumerate(heads):
        finite(intercept, f"head[{hi}].intercept")
        if not (isinstance(levels, list) and len(levels) <= len(encoder.level_views_)):
            raise NativeImageFormatError(
                "heads.levels", "level list within shared encoder", type(levels).__name__, "SHAPE"
            )
        for li, level in enumerate(levels):
            section = f"head[{hi}].level[{li}]"
            keys(
                level,
                {"n_bins", "main_features", "main_tables", "groups", "codes", "tables"},
                section,
            )
            if not level["n_bins"] == encoder.resolution_bins_[li]:
                raise NativeImageFormatError(
                    section, "bins match shared encoder", level["n_bins"], "SHAPE"
                )
            main = array(level["main_features"], section + ".main_features", kind="ui")
            counts = encoder.level_views_[li].n_buckets_
            if not (np.all(main < encoder.n_features_in_) and len(np.unique(main)) == len(main)):
                raise NativeImageFormatError(
                    section,
                    "unique feature indices within encoder",
                    "invalid main features",
                    "BOUNDS",
                )
            if not len(main) == len(level["main_tables"]):
                raise NativeImageFormatError(
                    section, "one table per selected main", "mismatched lengths", "SHAPE"
                )
            for feature, values in zip(main, level["main_tables"]):
                a = array(
                    values, section + ".main_table", dtype=np.float64, length=counts[int(feature)]
                )
                if not np.isfinite(a).all():
                    raise NativeImageFormatError(
                        section, "finite main coefficients", "nonfinite", "VALUE"
                    )
            if not len(level["groups"]) == len(level["codes"]) == len(level["tables"]):
                raise NativeImageFormatError(
                    section, "equal interaction collections", "inconsistent dimensions", "SHAPE"
                )
            for group, codes, values in zip(level["groups"], level["codes"], level["tables"]):
                group = array(group, section + ".group", kind="ui")
                if not (
                    len(group) >= 2
                    and np.all(group < encoder.n_features_in_)
                    and (len(np.unique(group)) == len(group))
                ):
                    raise NativeImageFormatError(
                        section, "unique interaction feature indices", "invalid group", "BOUNDS"
                    )
                if not len(group) == len(codes):
                    raise NativeImageFormatError(
                        section, "one codebook per group feature", "inconsistent codes", "SHAPE"
                    )
                for feature, code in zip(group, codes):
                    a = array(code, section + ".codes", kind="ui", length=counts[int(feature)])
                    if not np.all(a < table_size):
                        raise NativeImageFormatError(
                            section, "codes within memory address domain", "out of range", "BOUNDS"
                        )
                a = array(
                    values, section + ".interaction_table", dtype=np.float64, length=table_size
                )
                if not np.isfinite(a).all():
                    raise NativeImageFormatError(
                        section, "finite interaction coefficients", "nonfinite", "VALUE"
                    )


def state_digest(view):
    digest = hashlib.sha256()

    def update(tag, value):
        digest.update(pickle.dumps((tag, value), protocol=4))

    def walk(value):
        if isinstance(value, Enum) and type(value).__name__ == "_BooleanKey":
            update("BooleanKey", value.name)
        elif type(value).__name__ == "_ResolutionView":
            update("ResolutionView", None)
            walk(vars(value))
        elif isinstance(value, np.ndarray):
            update("ndarray", (value.dtype.str, value.shape))
            if value.dtype.hasobject:
                for item in value.flat:
                    walk(item)
            else:
                digest.update(value.tobytes(order="C"))
        elif isinstance(value, pd.Index):
            update("Index", (str(value.dtype), value.name, len(value)))
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            update("dict", len(value))
            for key, item in value.items():
                walk(key)
                walk(item)
        elif isinstance(value, (list, tuple)):
            update(type(value).__name__, len(value))
            for item in value:
                walk(item)
        else:
            update(type(value).__name__, value)

    walk(view)
    return digest.hexdigest()


def validate_payload(blob, metadata):
    stream = io.BytesIO(blob)
    try:
        payload = pickle.Unpickler(stream).load()
    except Exception as exc:
        raise NativeImageFormatError(
            "payload.pickle", "complete authorized pickle payload", type(exc).__name__, "UNPICKLE"
        ) from None
    if not stream.tell() == len(blob):
        raise NativeImageFormatError(
            "payload.EOF", "no trailing payload data", len(blob) - stream.tell(), "EOF"
        )
    if not isinstance(payload, dict):
        raise NativeImageFormatError("payload", "state dictionary", type(payload).__name__)
    task = payload.get("task")
    if not (task in {"binary", "regression", "multiclass"} and task == metadata["task"]):
        raise NativeImageFormatError("payload.task", metadata["task"], str(task), "VALUE")
    if not (
        type(payload.get("schema")) is int
        and payload.get("schema") == 1
        and (payload.get("version") == VERSION)
    ):
        raise NativeImageFormatError(
            "payload.version",
            f"integer schema1/{VERSION}",
            str((payload.get("schema"), payload.get("version"))),
            "SCHEMA",
        )
    if task == "multiclass":
        keys(payload, {"schema", "version", "kind", "task", "wire"}, "payload.sections")
        if not payload["kind"] == "multiclass_wire":
            raise NativeImageFormatError("payload.kind", "multiclass_wire", payload["kind"])
        encoder, classes, heads, table_size, _ = wire_validate(payload["wire"])
    else:
        keys(
            payload,
            {
                "schema",
                "version",
                "kind",
                "task",
                "encoder",
                "levels",
                "intercept",
                "table_size",
                "classes",
            },
            "payload.sections",
        )
        if not payload["kind"] == "single":
            raise NativeImageFormatError("payload.kind", "single", payload["kind"])
        if not isinstance(payload["encoder"], dict):
            raise NativeImageFormatError(
                "payload.encoder", "state dictionary", type(payload["encoder"]).__name__
            )
        encoder = object.__new__(native.BucketEncoder)
        encoder.__dict__.update(payload["encoder"])
        classes, heads, table_size = (
            payload["classes"],
            [(payload["intercept"], payload["levels"])],
            payload["table_size"],
        )
    integer(table_size, "memory.table_size", 1, 65536)
    encoder_validate(encoder)
    if task != "regression":
        array(classes, "classes")
        if not (len(classes) == (2 if task == "binary" else len(heads)) and len(classes) >= 2):
            raise NativeImageFormatError(
                "classes", "one ordered label per head/task", len(classes), "SHAPE"
            )
        for value in classes:
            scalar(value, "classes.label")
        if not not pd.Index(classes).has_duplicates:
            raise NativeImageFormatError(
                "classes", "unique labels", "duplicate labels", "DUPLICATE"
            )
    elif classes is not None:
        raise NativeImageFormatError(
            "classes", "no classification state for regression", type(classes).__name__
        )
    levels_validate(heads, encoder, table_size)
    observed = state_digest(
        dict(encoder=vars(encoder), heads=heads, classes=classes, table_size=table_size)
    )
    if not observed == metadata["state_sha256"]:
        raise NativeImageFormatError(
            "predictive_state", metadata["state_sha256"], observed, "STATE_CHECKSUM"
        )
    return (task, encoder, classes, heads, table_size)


def construct(parts):
    task, encoder, classes, heads, table_size = parts
    result = object.__new__(native.NativeImage)
    result.task, result.encoder, result.heads, result.table_size = (
        task,
        encoder,
        heads,
        table_size,
    )
    if task != "regression":
        result.classes_ = classes
    result.n_features_in_ = encoder.n_features_in_
    return result


def metadata_validate(metadata, metadata_length, payload_length):
    keys(
        metadata,
        {
            "schema",
            "source_version",
            "task",
            "payload_sha256",
            "state_sha256",
            "original_model_sha256",
            "sections",
            "producer",
        },
        "metadata",
    )
    try:
        _contract.validate_producer(metadata["producer"])
    except ValueError as exc:
        raise NativeImageFormatError(
            "metadata.producer", "qualified matching producer profile", str(exc), "COMPATIBILITY"
        ) from None
    if not (
        type(metadata["schema"]) is int
        and metadata["schema"] == SCHEMA
        and (metadata["source_version"] == VERSION)
    ):
        raise NativeImageFormatError(
            "metadata.version",
            f"envelope{SCHEMA}/{VERSION}",
            str((metadata["schema"], metadata["source_version"])),
            "SCHEMA",
        )
    if metadata["task"] not in {"binary", "multiclass", "regression"}:
        raise NativeImageFormatError(
            "metadata.task", "supported native Base task", str(metadata["task"]), "VALUE"
        )
    for key in ["payload_sha256", "state_sha256", "original_model_sha256"]:
        digest_text(metadata[key], "metadata." + key)
    sections = metadata["sections"]
    if not (isinstance(sections, list) and len(sections) == 2):
        raise NativeImageFormatError(
            "metadata.sections", "exactly2 sections", type(sections).__name__, "SECTIONS"
        )
    expected = [
        ("metadata", HEADER.size, metadata_length),
        ("payload", HEADER.size + metadata_length, payload_length),
    ]
    for section, (name, offset, length) in zip(sections, expected):
        keys(section, {"name", "offset", "length"}, "metadata.section")
        if not section["name"] == name:
            raise NativeImageFormatError(
                "metadata.section.name", name, str(section["name"]), "SECTIONS"
            )
        integer(section["offset"], "metadata.section.offset")
        integer(section["length"], "metadata.section.length")
        if not (section["offset"] == offset and section["length"] == length):
            raise NativeImageFormatError(
                "metadata.section.span", f"offset{offset},length{length}", str(section), "BOUNDS"
            )


def read_validated(path, *, expected_sha256=None, max_bytes=None):
    try:
        if expected_sha256 is not None:
            digest_text(expected_sha256, "expected_file_sha256")
        if max_bytes is not None:
            integer(max_bytes, "max_bytes", 1)
        with Path(path).open("rb") as stream:
            total = os.fstat(stream.fileno()).st_size
            if max_bytes is not None and total > max_bytes:
                raise NativeImageFormatError("file.size_limit", max_bytes, total, "RESOURCE")
            raw = stream.read(HEADER.size)
            if not len(raw) == HEADER.size:
                raise NativeImageFormatError("header", f"{HEADER.size} bytes", len(raw), "EOF")
            magic, version, header_size, count, mlen, plen, digest = HEADER.unpack(raw)
            if not magic == MAGIC:
                raise NativeImageFormatError("header.magic", MAGIC.hex(), magic.hex(), "MAGIC")
            if not (version == SCHEMA and header_size == HEADER.size):
                raise NativeImageFormatError(
                    "header.version",
                    f"schema{SCHEMA}/header{HEADER.size}",
                    f"{version}/{header_size}",
                    "SCHEMA",
                )
            if not count == 2:
                raise NativeImageFormatError("header.section_count", "2", count, "SECTIONS")
            if not (0 < mlen <= MAX_JSON and 0 < plen <= (1 << 63) - 1):
                raise NativeImageFormatError(
                    "header.lengths",
                    "bounded positive metadata/payload lengths",
                    f"{mlen}/{plen}",
                    "BOUNDS",
                )
            if not HEADER.size + mlen + plen == total:
                raise NativeImageFormatError(
                    "header.file_size", HEADER.size + mlen + plen, total, "EOF"
                )
            meta_raw, blob = (stream.read(mlen), stream.read(plen))
            if not (len(meta_raw) == mlen and len(blob) == plen and (stream.read(1) == b"")):
                raise NativeImageFormatError(
                    "sections.EOF",
                    "exact declared bytes/no trailing data",
                    f"{len(meta_raw)}/{len(blob)}",
                    "EOF",
                )
        whole = hashlib.sha256(raw)
        whole.update(meta_raw)
        whole.update(blob)
        if expected_sha256 is not None and whole.hexdigest() != expected_sha256:
            raise NativeImageFormatError(
                "file.expected_checksum", expected_sha256, whole.hexdigest(), "CHECKSUM"
            )
        checksum = hashlib.sha256(meta_raw)
        checksum.update(blob)
        observed = checksum.digest()
        if not observed == digest:
            raise NativeImageFormatError(
                "container.checksum", digest.hex(), observed.hex(), "CHECKSUM"
            )
        metadata = json_read(meta_raw, "metadata")
        metadata_validate(metadata, mlen, plen)
        observed = hashlib.sha256(blob).hexdigest()
        if not observed == metadata["payload_sha256"]:
            raise NativeImageFormatError(
                "payload.checksum", metadata["payload_sha256"], observed, "CHECKSUM"
            )
        return (validate_payload(blob, metadata), metadata)
    except NativeImageFormatError:
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
        RecursionError,
    ) as exc:
        raise NativeImageFormatError(
            "container.validation",
            "readable complete structurally consistent artifact",
            type(exc).__name__,
            "VALIDATION",
        ) from None


def load(path):
    parts, _ = read_validated(path)
    return construct(parts)


def from_legacy(folder):
    """Explicit migration only; never silently fall back to an old loader."""
    try:
        folder = Path(folder)
        metadata = json_read((folder / "manifest.json").read_bytes(), "legacy.manifest")
        keys(
            metadata,
            {
                "format",
                "source_version",
                "original_model_SHA256",
                "payload_SHA256",
                "predictive_state",
                "task",
                "trusted_pickle_only",
                "interface",
            },
            "legacy.manifest",
        )
        if not (
            metadata["format"] == "PRIVATE_NATIVE_IMAGE_V1"
            and metadata["source_version"] == VERSION
        ):
            raise NativeImageFormatError(
                "legacy.magic_version",
                f"PRIVATE_NATIVE_IMAGE_V1/{VERSION}",
                str((metadata["format"], metadata["source_version"])),
                "SCHEMA",
            )
        blob = (folder / "model.image.pkl").read_bytes()
        converted = dict(
            schema=SCHEMA,
            source_version=VERSION,
            task=metadata["task"],
            payload_sha256=metadata["payload_SHA256"],
            state_sha256=metadata["predictive_state"]["SHA256"],
            original_model_sha256=metadata["original_model_SHA256"],
            sections=[],
        )
        for key in ["payload_sha256", "state_sha256", "original_model_sha256"]:
            digest_text(converted[key], "legacy." + key)
        if not hashlib.sha256(blob).hexdigest() == converted["payload_sha256"]:
            raise NativeImageFormatError(
                "legacy.payload", "declared SHA256", "hash mismatch", "CHECKSUM"
            )
        validate_payload(blob, converted)
        return (blob, converted)
    except NativeImageFormatError:
        raise
    except Exception as exc:
        raise NativeImageFormatError(
            "legacy.input", "complete supported legacy image", type(exc).__name__, "VALIDATION"
        ) from None


def encode_metadata(metadata, payload_length):
    metadata = dict(metadata)
    length = 0
    for _ in range(16):
        metadata["sections"] = [
            dict(name="metadata", offset=HEADER.size, length=length),
            dict(name="payload", offset=HEADER.size + length, length=payload_length),
        ]
        raw = json.dumps(
            metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        if len(raw) == length:
            metadata_validate(metadata, length, payload_length)
            return raw
        length = len(raw)
    raise NativeImageFormatError(
        "metadata.sections", "convergent byte lengths", "not converged", "BOUNDS"
    )


def atomic_save(blob, metadata, destination, *, _fault=None):
    """One same-volume commit; no fallible finalization after successful replace."""
    temp_path = None

    def stage(name):
        if _fault is not None:
            _fault(name)

    try:
        require(
            hashlib.sha256(blob).hexdigest() == metadata["payload_sha256"],
            "save.payload",
            "declared SHA256",
            "hash mismatch",
            "CHECKSUM",
        )
        validate_payload(blob, metadata)
        meta_raw = encode_metadata(metadata, len(blob))
        destination = Path(destination)
        fd, name = tempfile.mkstemp(prefix=".native-image-", suffix=".tmp", dir=destination.parent)
        temp_path = Path(name)
        with os.fdopen(fd, "w+b") as stream:
            stream.write(
                HEADER.pack(MAGIC, SCHEMA, HEADER.size, 2, len(meta_raw), len(blob), b"\x00" * 32)
            )
            stream.write(meta_raw)
            stage("before_payload")
            split = max(1, len(blob) // 2)
            stream.write(blob[:split])
            stage("mid_payload")
            stream.write(blob[split:])
            stage("after_payload")
            stream.flush()
            stage("before_checksum")
            checksum = hashlib.sha256(meta_raw)
            checksum.update(blob)
            digest = checksum.digest()
            stream.seek(0)
            header = HEADER.pack(MAGIC, SCHEMA, HEADER.size, 2, len(meta_raw), len(blob), digest)
            whole = hashlib.sha256(header)
            whole.update(meta_raw)
            whole.update(blob)
            publication = dict(
                artifact_sha256=whole.hexdigest(),
                artifact_bytes=HEADER.size + len(meta_raw) + len(blob),
            )
            stream.write(header)
            stream.flush()
            os.fsync(stream.fileno())
            stage("after_checksum")
        read_validated(temp_path)
        stage("before_rename")
        stage("during_finalization")
        stage("replace_OS_error")
        os.replace(temp_path, destination)
        temp_path = None
        return publication
    except NativeImageFormatError:
        raise
    except Exception as exc:
        raise NativeImageFormatError(
            "atomic_save",
            "validated temporary and atomic replacement; old target unchanged on failure",
            type(exc).__name__ + ":" + str(exc),
            "IO",
        ) from None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError as exc:
                raise NativeImageFormatError(
                    "atomic_save.cleanup",
                    "remove temporary artifact",
                    f"OS refused {temp_path.name}:{type(exc).__name__}",
                    "OS_CLEANUP",
                ) from None


def save_from_legacy(folder, destination, *, _fault=None):
    blob, metadata = from_legacy(folder)
    atomic_save(blob, metadata, destination, _fault=_fault)
