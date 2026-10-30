"""Environment-flow controls only; they do not qualify Windows or macOS."""
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('build_environment_test',ROOT/'tools/build_environment.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

def test_msvc_sdk_environment_survives_the_native_build_boundary():
    source={key:'present' for key in ('PATH','INCLUDE','LIB','LIBPATH','DISTUTILS_USE_SDK','MSSdk',
        'WindowsSdkDir','WindowsSDKVersion','UCRTVersion','UniversalCRTSdkDir','VCToolsInstallDir','VSCMD_ARG_TGT_ARCH')}
    assert tool.forward_environment(source)==source

def test_macos_libomp_runtime_paths_survive_the_child_boundary():
    source=dict(DYLD_LIBRARY_PATH='/opt/homebrew/opt/libomp/lib',
        DYLD_FALLBACK_LIBRARY_PATH='/opt/homebrew/opt/libomp/lib:/usr/local/lib:/usr/lib',
        LIBOMP_PREFIX='/opt/homebrew/opt/libomp',SDKROOT='/SDK',MACOSX_DEPLOYMENT_TARGET='15.0')
    assert tool.forward_environment(source)==source

def test_credentials_and_unrelated_python_paths_are_not_forwarded():
    source=dict(PATH='tools',PYTHONPATH='untrusted',GITHUB_TOKEN='not-a-real-token',
        AWS_SECRET_ACCESS_KEY='not-a-real-secret',PIP_INDEX_URL='not-an-authorized-index',HOME='private')
    assert tool.forward_environment(source)==dict(PATH='tools')
