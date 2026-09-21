"""Install the built wheel outside the source tree, never through PYTHONPATH.

For offline unit tests the new venv reuses the host's installed dependencies;
the codadapt wheel itself must resolve strictly from the fresh venv. A fully
fresh dependency installation is additionally checked during release validation.
"""

import os
import subprocess
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def wheel():
    wheels = sorted((ROOT / "dist").glob("codadapt-*.whl"))
    if not wheels:
        pytest.skip("Build the wheel with python -m build before distribution checks")
    return wheels[-1]


def test_wheel_contains_package_and_distribution_metadata(wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        for module in (
            "__init__",
            "_version",
            "preprocessing",
            "_core",
            "_training",
            "_base",
            "classifier",
            "regressor",
        ):
            assert f"codadapt/{module}.py" in names
        assert any(name.endswith(".dist-info/METADATA") for name in names)
        assert any(name.endswith("LICENSE") for name in names)
        assert not any("__pycache__" in name or name.startswith("tests/") for name in names)


def test_installed_wheel_fit_predict_and_persistence_in_external_environment(wheel, tmp_path):
    environment = tmp_path / "wheel-environment"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    install = subprocess.run(
        [str(python), "-I", "-m", "pip", "install", "--no-deps", "--force-reinstall", str(wheel)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    script = tmp_path / "wheel_smoke.py"
    script.write_text(
        "from pathlib import Path\nimport sys, pickle, joblib, numpy as np, pandas as pd\n"
        "import codadapt\nfrom codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor\n"
        "assert CodAdapt is CodAdaptClassifier\nassert codadapt.__version__ == '0.1.0'\n"
        "assert Path(codadapt.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())\n"
        "rng = np.random.default_rng(7)\nv = rng.normal(size=300)\n"
        "X = pd.DataFrame({'value': v, 'category': np.where(v > 0, 'a', 'b')})\n"
        "X.loc[::11, 'value'] = np.nan\nX.loc[::13, 'category'] = None\n"
        "def forbidden_fit(*args, **kwargs):\n    raise AssertionError('Loading must not fit')\n"
        "if sys.argv[1] == 'load':\n"
        "    CodAdaptClassifier.fit = forbidden_fit\n    CodAdaptRegressor.fit = forbidden_fit\n"
        "for cls, y in [(CodAdapt, (v > 0).astype(int)), (CodAdaptRegressor, v)]:\n"
        "    if sys.argv[1] == 'fit':\n"
        "        model = cls(random_state=42, verbosity=0).fit(X, y)\n"
        "        expected = model.predict(X.iloc[:5])\n"
        "        assert expected.shape == (5,) and np.isfinite(expected).all()\n"
        "        np.save(cls.__name__ + '.npy', expected)\n"
        "        Path(cls.__name__ + '.pickle').write_bytes(pickle.dumps(model))\n"
        "        joblib.dump(model, cls.__name__ + '.joblib')\n"
        "    else:\n"
        "        expected = np.load(cls.__name__ + '.npy')\n"
        "        for suffix in ['pickle', 'joblib']:\n"
        "            path = Path(cls.__name__ + '.' + suffix)\n"
        "            restored = pickle.loads(path.read_bytes()) if suffix == 'pickle' else joblib.load(path)\n"
        "            np.testing.assert_array_equal(restored.predict(X.iloc[:5]), expected)\n"
        "print('wheel import, mixed fit/predict and both persistence formats verified')\n",
        encoding="utf-8",
    )
    for phase in ("fit", "load"):
        completed = subprocess.run(
            [str(python), "-I", str(script), phase],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "verified" in completed.stdout
