import glob
import shutil
import tempfile
from pathlib import Path

import pytest


import functools
import os
import subprocess
from pathlib import Path

root_repo_dir = Path(__file__).resolve().parent.parent.parent
scripts_dir = root_repo_dir / "scripts"

_TEST_PREFIX = "trestlebot_tests"

def is_complytime_installed(install_dir: Path) -> bool:
    install_dir / ".config/complytime"
    openscap_plugin_bin = (install_dir / '.config/complytime/plugins/openscap-plugin').resolve()
    openscap_plugin_conf = (install_dir / '.config/complytime/plugins/openscap-plugin.yml').resolve()
    if not openscap_plugin_bin.exists():
        return False
    if not openscap_plugin_conf.exists():
        return False
    return True

def is_complytime_cached(download_dir: Path) -> bool:
    return bool(glob.glob(str((download_dir / 'releases/*/complytime_linux_x86_64.tar.gz').resolve())))


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    # Setup
    complytime_home = Path(tempfile.mkdtemp(prefix=_TEST_PREFIX))
    orig_home = os.getenv('HOME')
    orig_xdg_config_home = os.getenv('XDG_CONFIG_HOME')

    complytime_home.mkdir(parents=True, exist_ok=True)
    complytime_release_dir = complytime_home
    if not is_complytime_installed(complytime_home):
        if not is_complytime_cached(complytime_home):
            result = subprocess.run(
                [scripts_dir / "get-github-release.sh", "--prerelease"],
                cwd=complytime_release_dir,
                capture_output=True,
                text=True)
            if result.returncode != 0:
                raise ValueError(f"Unable to install ComplyTime for int test!\n{result.stdout}\n{result.stderr}")
        result = subprocess.run(
            'find releases -name complytime_linux_x86_64.tar.gz -exec tar -xvf {} ";" -exit',
            cwd=complytime_release_dir,
            shell=True,
        )
        if result.returncode != 0:
            raise ValueError(f"Unable to extract ComplyTime for int test!\n{result.stdout}\n{result.stderr}")

        Path(complytime_home / '.config/complytime/plugins/').mkdir(parents=True, exist_ok=True)
        Path(complytime_home / '.config/complytime/bundles/').mkdir(parents=True, exist_ok=True)
        Path(complytime_home / '.config/complytime/controls/').mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            f'for file in releases/*/*_linux_x86_64.tar.gz; do tar -xf "$file"; done',
            cwd=complytime_release_dir,
            shell=True,
        )
        if result.returncode != 0:
            raise ValueError(f"Unable to install ComplyTime for int test!\n{result.stdout}\n{result.stderr}")

    yield # run the test

    # Teardown
    os.environ['HOME'] = orig_home
    os.environ['XDG_CONFIG_HOME'] = orig_xdg_config_home
    shutil.rmtree(complytime_home)

