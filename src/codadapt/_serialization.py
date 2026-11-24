"""Trusted native snapshot persistence with optional compression."""
from hashlib import sha256
import io
import pickle
import struct
import zlib
import numpy as np

MAGIC=b"CDA74TEC"
HEADER="<BQ32s"
# Restrict reconstruction to the supported native snapshot schema.
KNOWN={("codadapt.classifier","CodAdaptClassifier"),("codadapt.regressor","CodAdaptRegressor"),
("codadapt._multiclass_artifact","Artifact"),("codadapt.preprocessing","BucketEncoder"),
("codadapt.preprocessing","_ResolutionView"),("numpy","dtype"),("numpy","ndarray"),
("pandas.core.indexes.base","_new_Index"),("pandas.core.indexes.base","Index"),
("pandas.core.indexes.range","RangeIndex"),("pandas.core.arrays.string_","StringArray"),
("pandas.core.arrays.string_","StringDtype"),("pandas._libs.missing","NA"),("pandas","Index"),
("pandas","StringDtype"),("pandas.arrays","StringArray"),("pandas._libs.arrays","__pyx_unpickle_NDArrayBacked"),
("builtins","slice")}
KNOWN.update((m,n) for m in ("numpy._core.multiarray","numpy.core.multiarray") for n in ("_reconstruct","scalar"))
KNOWN.update((m,"_frombuffer") for m in ("numpy._core.numeric","numpy.core.numeric"))

# Native key, index and RNG state constructors demonstrated by codec witnesses.
KNOWN.update([('codadapt.preprocessing', '_BooleanKey'), ('numpy', 'dtype'), ('numpy', 'ndarray'), ('numpy._core.multiarray', '_reconstruct'), ('numpy._core.numeric', '_frombuffer'), ('numpy.random._mt19937', 'MT19937'), ('numpy.random._pickle', '__bit_generator_ctor'), ('numpy.random._pickle', '__randomstate_ctor'), ('pandas', 'Categorical'), ('pandas', 'CategoricalDtype'), ('pandas', 'CategoricalIndex'), ('pandas', 'DatetimeIndex'), ('pandas', 'Index'), ('pandas', 'MultiIndex'), ('pandas', 'PeriodDtype'), ('pandas', 'PeriodIndex'), ('pandas', 'RangeIndex'), ('pandas', 'StringDtype'), ('pandas', 'TimedeltaIndex'), ('pandas._libs.arrays', '__pyx_unpickle_NDArrayBacked'), ('pandas._libs.tslibs.offsets', 'Day'), ('pandas.arrays', 'DatetimeArray'), ('pandas.arrays', 'PeriodArray'), ('pandas.arrays', 'StringArray'), ('pandas.arrays', 'TimedeltaArray'), ('pandas.core.indexes.base', '_new_Index'), ('pandas.core.indexes.datetimes', '_new_DatetimeIndex'), ('pandas.core.indexes.timedeltas', '_new_TimedeltaIndex')])

# pandas 2.x uses fully qualified index and extension-array constructors.
# Admit only these specific aliases, not arbitrary pandas globals.
KNOWN.update({
    ("pandas.core.indexes.datetimes", "DatetimeIndex"),
    ("pandas.core.indexes.multi", "MultiIndex"),
    ("pandas.core.indexes.category", "CategoricalIndex"),
    ("pandas.core.indexes.timedeltas", "TimedeltaIndex"),
    ("pandas.core.indexes.period", "PeriodIndex"),
    ("pandas.core.arrays.datetimes", "DatetimeArray"),
    ("pandas.core.arrays.categorical", "Categorical"),
    ("pandas.core.arrays.timedeltas", "TimedeltaArray"),
    ("pandas.core.arrays.period", "PeriodArray"),
    ("pandas.core.dtypes.dtypes", "CategoricalDtype"),
    ("pandas.core.dtypes.dtypes", "PeriodDtype"),
})


class _ArchivedStringDtype:
    """Marker for the pandas 3 string dtype not representable in pandas 2."""
    def __init__(self, storage, na_value):
        self.storage = storage
        self.na_value = na_value


class _ArchivedStringArray:
    """Only materialized as a checked index; never returned as model state."""
    def __setstate__(self, state):
        self.state = state

    def index_values(self):
        import pandas as pd
        state = getattr(self, "state", None)
        if not isinstance(state, tuple) or len(state) not in (2, 3):
            raise ValueError("Unsupported archived StringArray state")
        dtype, values = state[:2]
        if len(state) == 3 and state[2] != {}:
            raise ValueError("Unsupported archived StringArray attributes")
        if type(values) is not np.ndarray or values.ndim != 1 or values.dtype != object:
            raise ValueError("Unsupported archived string index storage")
        if isinstance(dtype, _ArchivedStringDtype):
            # A nonmissing string index has the same labels and order when
            # represented by an object index. Never convert missing-value
            # semantics (NaN versus pd.NA) on an older pandas version.
            if dtype.storage != "python" or not all(type(v) is str for v in values):
                raise ValueError("Cross-version string index requires nonmissing Python strings")
            if dtype.na_value is not pd.NA and not (
                isinstance(dtype.na_value, (float, np.floating)) and np.isnan(dtype.na_value)
            ):
                raise ValueError("Unsupported archived string missing-value convention")
            return values.copy()
        if not isinstance(dtype, pd.StringDtype):
            raise ValueError("Unexpected string array dtype")
        return pd.array(values, dtype=dtype)


class NativeReader(pickle.Unpickler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import pandas as pd
        # This compatibility path is restricted to the tested pandas 2.2.3
        # profile. Newer pandas keeps its original reconstruction semantics.
        self._legacy_strings = pd.__version__ == "2.2.3"
        self._pending_arrays = set()
        self._pending_dtypes = set()

    def _string_dtype(self, storage=None, *args):
        import pandas as pd
        if not args:
            return pd.StringDtype(storage=storage)
        if len(args) != 1:
            raise ValueError("Unsupported archived StringDtype constructor")
        marker = _ArchivedStringDtype(storage, args[0])
        self._pending_dtypes.add(marker)
        return marker

    def _string_array(self, cls, checksum, state):
        import pandas as pd
        if cls is not pd.arrays.StringArray:
            return super().find_class("pandas._libs.arrays", "__pyx_unpickle_NDArrayBacked")(cls, checksum, state)
        if checksum != 82904607 or state is not None:
            raise ValueError("Unsupported archived StringArray constructor")
        holder = _ArchivedStringArray()
        self._pending_arrays.add(holder)
        return holder

    def _index(self, cls, values):
        import pandas as pd
        if isinstance(values, dict) and isinstance(values.get("data"), _ArchivedStringArray):
            holder = values["data"]
            if cls is not pd.Index:
                raise ValueError("Only base string indexes may be migrated")
            data = holder.index_values()
            dtype = holder.state[0]
            self._pending_dtypes.discard(dtype)
            self._pending_arrays.discard(holder)
            values = dict(values, data=data)
        return super().find_class("pandas.core.indexes.base", "_new_Index")(cls, values)

    def find_class(self, module, name):
        if (module, name) not in KNOWN:
            raise ValueError("Unexpected archived model type")
        if self._legacy_strings:
            if (module, name) in {("pandas", "StringDtype"), ("pandas.core.arrays.string_", "StringDtype")}:
                return self._string_dtype
            if (module, name) == ("pandas._libs.arrays", "__pyx_unpickle_NDArrayBacked"):
                return self._string_array
            if (module, name) == ("pandas.core.indexes.base", "_new_Index"):
                return self._index
        return super().find_class(module, name)

    def load(self):
        result = super().load()
        if self._pending_arrays or self._pending_dtypes:
            raise ValueError("Unsupported archived string state outside a checked index")
        return result

    def persistent_load(self, pid):
        raise ValueError("External model references not supported")


def restore(raw):
    return NativeReader(io.BytesIO(raw)).load()


def encode_model(native,archive=False):
    raw=pickle.dumps(native,protocol=5)
    if len(raw)>32*1024**2:raise ValueError("Snapshot exceeds the 32 MiB envelope limit")
    body=zlib.compress(raw,6) if archive else raw
    return MAGIC+struct.pack(HEADER,int(archive),len(raw),sha256(raw).digest())+body


def decode_model(wire):
    n=8+struct.calcsize(HEADER)
    if len(wire)<n or wire[:8]!=MAGIC:raise ValueError("Invalid model snapshot header")
    compressed,size,digest=struct.unpack(HEADER,wire[8:n])
    if compressed not in (0,1) or size>32*1024**2:raise ValueError("Invalid artifact bounds")
    try:
        if compressed:
            decoder=zlib.decompressobj()
            raw=decoder.decompress(wire[n:],size+1)
            if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                raise ValueError("Incomplete or overlong compressed artifact")
        else:
            raw=wire[n:]
    except zlib.error as e:raise ValueError("Invalid compressed artifact") from e
    if len(raw)!=size or sha256(raw).digest()!=digest:raise ValueError("Artifact length or digest mismatch")
    return restore(raw)


def save_model(native, path, *, compress=False):
    from pathlib import Path
    import os
    if type(compress) is not bool:
        raise TypeError("compress must be bool")
    wire = encode_model(native, compress)
    with Path(path).open("xb") as handle:
        handle.write(wire)
        handle.flush()
        os.fsync(handle.fileno())
    return len(wire)

def load_model(path, *, expected_sha256=None):
    from pathlib import Path
    path = Path(path)
    if path.stat().st_size > 33 * 1024**2:
        raise ValueError("Snapshot file exceeds the envelope limit")
    wire = path.read_bytes()
    if expected_sha256 is not None and sha256(wire).hexdigest() != expected_sha256:
        raise ValueError("Snapshot file digest mismatch")
    return decode_model(wire) if wire.startswith(MAGIC) else restore(wire)
