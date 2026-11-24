"""Explicit immutable, source-bound input reuse. Never cache arbitrary raw requests."""
from hashlib import sha256
from io import BytesIO
import numpy as np

class InferenceSession:
    __slots__=("_native","_task","_codes","_raw","binding")
    def __init__(self,native,task,codes,raw,binding):
        self._native=native;self._task=task;self._codes=codes;self._raw=raw;self.binding=tuple(sorted(binding.items()))
    @classmethod
    def open_bound(cls,model_wire,task,raw,meta,expected_binding,restore):
        if type(model_wire) is not bytes or type(raw) is not bytes:raise ValueError("Immutable snapshot and compiled-input bytes required")
        if sha256(model_wire).hexdigest()!=expected_binding["model"]:raise ValueError("Wrong model binding")
        if any(meta.get(k)!=v for k,v in expected_binding.items()):raise ValueError("Wrong input provenance")
        if len(raw)!=meta["bytes"] or sha256(raw).hexdigest()!=meta["sha256"]:raise ValueError("Corrupt compiled input")
        with BytesIO(raw[:4096]) as h:
            version=np.lib.format.read_magic(h)
            if version==(1,0):shape,order,dtype=np.lib.format.read_array_header_1_0(h,max_header_size=4096)
            elif version==(2,0):shape,order,dtype=np.lib.format.read_array_header_2_0(h,max_header_size=4096)
            else:raise ValueError("Unsupported compiled-input version")
            offset=h.tell()
        if len(shape)!=2 or list(shape)!=meta["shape"] or dtype.str!=meta["dtype"] or order or dtype.kind not in "iu":
            raise ValueError("Invalid compiled-input schema")
        count=int(np.prod(shape,dtype=np.int64))
        if count<0 or offset+count*dtype.itemsize!=len(raw):raise ValueError("Invalid compiled-input extent")
        model=restore(model_wire)
        if shape[1]!=model.shared_encoder_.n_features_in_:raise ValueError("Feature count mismatch")
        codes=np.frombuffer(raw,dtype,count=count,offset=offset).reshape(shape)
        if codes.flags.writeable:raise ValueError("Compiled input must be immutable")
        return cls(model,task,codes,raw,expected_binding)
    @property
    def resident_input_bytes(self):return len(self._raw)
    @property
    def rows(self):return len(self._codes)
    def predict_rows(self,rows):
        # Row identity is explicit. There is no raw-input cache lookup.
        rows=np.asarray(rows)
        if rows.ndim!=1 or rows.dtype.kind not in "iu":raise ValueError("Integer row ids required")
        if len(rows) and (rows.min()<0 or rows.max()>=len(self._codes)):raise ValueError("Row outside bound input")
        fine=self._codes[rows]
        enc=self._native.shared_encoder_
        levels=[]
        for mappings in enc.level_mappings_:
            block=np.empty_like(fine)
            for j,mapping in enumerate(mappings):block[:,j]=mapping[fine[:,j]]
            levels.append(block)
        from codadapt._inference import predict_coded_memory_buckets as predict
        from codadapt._core import sigmoid
        from codadapt._multiclass_artifact import probabilities
        if self._task=="multiclass":
            z=np.column_stack([h.scores(levels) for h in self._native._heads_])
        else:
            z=predict(self._native.levels_,self._native.encoders_,levels,self._native.intercept_,self._native.table_size)
        if self._task=="regression":return (z,)
        p=(lambda s:np.column_stack((1-s,s)))(sigmoid(z)) if self._task=="binary" else probabilities(z)
        y=self._native.classes_[(z>0).astype(np.intp)] if self._task=="binary" else self._native.classes_[p.argmax(1)]
        return z,p,y


def prepare_inference(native, X):
    """Snapshot the native model and one validated input for indexed reuse."""
    import pickle
    from sklearn.utils.validation import check_is_fitted
    from ._serialization import restore
    check_is_fitted(native, "_is_fitted_")
    fine = native.shared_encoder_.transform(X)
    model_wire = pickle.dumps(native, protocol=5)
    buffer = BytesIO()
    np.save(buffer, fine, allow_pickle=False)
    raw = buffer.getvalue()
    task = "regression" if getattr(native, "_task", None) == "regression" else (
        "multiclass" if len(native.classes_) > 2 else "binary")
    meta = {"model": sha256(model_wire).hexdigest(),
            "sha256": sha256(raw).hexdigest(), "bytes": len(raw),
            "shape": list(fine.shape), "dtype": fine.dtype.str}
    expected = {"model": meta["model"], "sha256": meta["sha256"]}
    return InferenceSession.open_bound(model_wire, task, raw, meta, expected, restore)
