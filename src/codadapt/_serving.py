"""One evaluation of the native coded memories for a combined response."""
import numpy as np

def predict_all(model, X):
    """Return (scores, probabilities, labels), or (predictions,) for regression."""
    if getattr(model, "_task", None) == "regression":
        return (model.predict(X),)
    from ._core import sigmoid
    from ._multiclass_artifact import probabilities
    z = model.decision_function(X)
    if len(model.classes_) == 2:
        p1 = sigmoid(z)
        p = np.column_stack((1 - p1, p1))
        y = model.classes_[(z > 0).astype(np.intp)]
    else:
        p = probabilities(z)
        y = model.classes_[p.argmax(1)]
    return z, p, y

