"""Classificazione binaria: DataFrame misto e split train/validation/test espliciti."""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from codadapt import CodAdapt


def make_data(n_samples=900, random_state=42):
    rng = np.random.default_rng(random_state)
    amount = rng.normal(size=n_samples)
    region = rng.choice(["nord", "centro", "sud"], size=n_samples)
    active = rng.choice([True, False], size=n_samples)
    logits = 2.0 * amount + 1.4 * (region == "nord") + 0.8 * active
    target = np.where(rng.random(n_samples) < 1 / (1 + np.exp(-logits)), "sì", "no")
    frame = pd.DataFrame(
        {"importo": amount, "regione": region, "attivo": pd.array(active, dtype="boolean")}
    )
    frame.loc[rng.choice(n_samples, 60, replace=False), "importo"] = np.nan
    frame.loc[rng.choice(n_samples, 40, replace=False), "regione"] = None
    frame.loc[rng.choice(n_samples, 30, replace=False), "attivo"] = pd.NA
    return frame, target


def main():
    X, y = make_data()
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_valid, y_train, y_valid = train_test_split(
        X_dev, y_dev, test_size=0.25, random_state=43, stratify=y_dev
    )
    model = CodAdapt(random_state=42, verbosity=0)
    model.fit(X_train, y_train, eval_set=(X_valid, y_valid))
    probabilities = model.predict_proba(X_test)
    positive = (y_test == model.classes_[1]).astype(int)
    print(f"ROC-AUC: {roc_auc_score(positive, probabilities[:, 1]):.4f}")
    print(f"Log-loss: {log_loss(y_test, probabilities, labels=model.classes_):.4f}")
    print(f"Accuracy: {accuracy_score(y_test, model.predict(X_test)):.4f}")
    print(f"Iterazioni eseguite: {model.n_iter_}; stato scelto: {model.best_iteration_}")

    new_rows = X_test.iloc[:3].copy()
    new_rows.loc[:, "regione"] = "categoria_mai_vista"
    new_rows.loc[:, "importo"] = np.nan
    print("Previsioni con nuove categorie e mancanti:", model.predict(new_rows))


if __name__ == "__main__":
    main()
