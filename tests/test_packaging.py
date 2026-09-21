"""Install the built wheel outside the source tree, never through PYTHONPATH.

For offline unit tests the new venv reuses the host's installed dependencies;
the codadapt wheel itself must resolve strictly from the fresh venv. A fully
fresh dependency installation is additionally checked during release validation.
"""

import os
import pickle
import subprocess
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

from codadapt import __version__

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def wheel():
    wheels = sorted((ROOT / "dist").glob(f"codadapt-{__version__}-*.whl"))
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
        assert "codadapt/experimental/_compiler.py" in names
        assert "codadapt/experimental/_model.py" in names
        assert not any("research" in name for name in names)


def test_installed_wheel_fit_predict_and_persistence_in_external_environment(
    wheel, tmp_path, dependency_paths
):
    environment = tmp_path / "wheel-environment"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site_packages = next(environment.glob("Lib/site-packages"), None)
    if site_packages is None:
        site_packages = next(environment.glob("lib/python*/site-packages"))
    (site_packages / "offline_dependencies.pth").write_text(
        f"import sys; sys.path.extend({dependency_paths!r})\n", encoding="utf8"
    )
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
    try:
        from interpret.glassbox import ExplainableBoostingClassifier, ExplainableBoostingRegressor
    except ImportError:
        pass  # Base-only CI still checks that importing the compiler needs no teacher.
    else:
        import numpy as np
        import pandas as pd

        from codadapt.experimental import compile_ebm

        x = pd.DataFrame({"value": np.linspace(-2, 2, 100)})
        artifacts = []
        for cls, y in (
            (ExplainableBoostingClassifier, (x.value > 0).astype(int)),
            (ExplainableBoostingRegressor, x.value**2),
        ):
            teacher = cls(interactions=0, outer_bags=1, max_rounds=8, n_jobs=1).fit(x, y)
            model = compile_ebm(teacher, X_verify=x)
            artifacts.append((model, x, model.predict(x)))
        (tmp_path / "compiled.pkl").write_bytes(pickle.dumps(artifacts))
    script = tmp_path / "wheel_smoke.py"
    script.write_text(
        "from pathlib import Path\nimport sys, importlib.abc, pickle, joblib, numpy as np, pandas as pd\n"
        "class BlockTeacher(importlib.abc.MetaPathFinder):\n"
        "    def find_spec(self, fullname, path=None, target=None):\n"
        "        if fullname.split('.')[0] == 'interpret': raise ImportError('teacher unavailable')\n"
        "sys.meta_path.insert(0, BlockTeacher())\n"
        "import codadapt\nfrom codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor\n"
        "from codadapt.experimental import compile_ebm\n"
        "try: compile_ebm(object(), X_verify=None)\n"
        "except ImportError as e: assert 'codadapt[ebm]' in str(e)\n"
        "else: raise AssertionError('compile must require optional dependency')\n"
        f"assert CodAdapt is CodAdaptClassifier\nassert codadapt.__version__ == {__version__!r}\n"
        "assert Path(codadapt.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())\n"
        "if Path('compiled.pkl').exists():\n"
        "    for m, x, expected in pickle.loads(Path('compiled.pkl').read_bytes()):\n"
        "        np.testing.assert_array_equal(m.predict(x), expected)\n"
        "assert not any(k.startswith('interpret') for k in sys.modules)\n"
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


def test_source_distribution_excludes_research_memory_and_private_artifacts():
    archive = ROOT / "dist" / f"codadapt-{__version__}.tar.gz"
    if not archive.exists():
        pytest.skip("Build the source distribution before distribution checks")
    with tarfile.open(archive) as contents:
        names = contents.getnames()
    assert not any("research_private" in n or "/docs/research" in n for n in names)
    assert any(n.endswith("docs/EBM_COMPILER.md") for n in names)


def test_optional_dependency_metadata(wheel):
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = archive.read(name).decode()
    requirements = [r for r in metadata.splitlines() if r.startswith("Requires-Dist: interpret")]
    assert len(requirements) == 1
    assert 'extra == "ebm"' in requirements[0]
