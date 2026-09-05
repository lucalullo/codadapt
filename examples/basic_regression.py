"""Regressione: DataFrame con mancanti, categoriche e validation separata."""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from codadapt import CodAdaptRegressor


def make_data(n_samples=900, random_state=42):
    rng = np.random.default_rng(random_state)
    age = rng.uniform(18, 80, size=n_samples)
    segment = rng.choice(["base", "plus", "premium"], size=n_samples)
    count = rng.integers(0, 10, size=n_samples)
    target = 0.8 * age + 12 * (segment == "premium") + 2 * count + rng.normal(0, 3, n_samples)
    frame = pd.DataFrame(
        {"età": age, "segmento": segment, "conteggio": pd.array(count, dtype="Int64")}
    )
    frame.loc[rng.choice(n_samples, 50, replace=False), "età"] = np.nan
    frame.loc[rng.choice(n_samples, 30, replace=False), "segmento"] = None
    frame.loc[rng.choice(n_samples, 30, replace=False), "conteggio"] = pd.NA
    return frame, target


def main():
    X, y = make_data()
    X_dev, X_test, y_dev, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_train, X_valid, y_train, y_valid = train_test_split(
        X_dev, y_dev, test_size=0.25, random_state=43
    )
    model = CodAdaptRegressor(random_state=42, verbosity=0)
    model.fit(X_train, y_train, eval_set=(X_valid, y_valid))
    predictions = model.predict(X_test)
    print(f"RMSE: {np.sqrt(mean_squared_error(y_test, predictions)):.4f}")
    print(f"MAE: {mean_absolute_error(y_test, predictions):.4f}")
    print(f"Iterazioni eseguite: {model.n_iter_}; stato scelto: {model.best_iteration_}")

    new_rows = X_test.iloc[:3].copy()
    new_rows.loc[:, "segmento"] = "categoria_mai_vista"
    new_rows.loc[:, "età"] = np.nan
    print("Previsioni con nuove categorie e mancanti:", model.predict(new_rows))


if __name__ == "__main__":
    main()
