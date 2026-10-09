"""Native multiclass classification with a common train-only validation split."""

import numpy as np
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

from codadapt import CodAdapt, CodAdaptClassifier


def main():
    # Small self-contained API fixture, with no dataset download or I/O dependency.
    rng = np.random.default_rng(42)
    y = np.tile(np.arange(3), 100)
    X = rng.normal(size=(len(y), 4)) + y[:, None] * 2.0
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    model = CodAdaptClassifier(random_state=42, verbosity=0).fit(X_train, y_train)
    pred, proba = model.predict(X_test), model.predict_proba(X_test)
    assert CodAdapt is CodAdaptClassifier
    assert proba.shape == (len(X_test), 3)
    print(f"Accuracy: {accuracy_score(y_test, pred):.4f}")
    print(f"Log-loss: {log_loss(y_test, proba, labels=model.classes_):.4f}")


if __name__ == "__main__":
    main()
