# SPDX-License-Identifier: Apache-2.0
# Copyright Red Hat, Inc.

import glob
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, TypeVar

import pytest


root_repo_dir = Path(__file__).resolve().parent.parent.parent
scripts_dir = root_repo_dir / "scripts"
complytime_cache_dir = Path("/tmp/trestle-bot-complytime-cache")
complytime_cache_dir.mkdir(parents=True, exist_ok=True)
int_test_data_dir = Path(__file__).parent.parent / "integration_data/"
_TEST_PREFIX = "trestlebot_tests"

T = TypeVar("T")
YieldFixture = Generator[T, None, None]


def is_complytime_installed(install_dir: Path) -> bool:
    install_dir / ".config/complytime"
    openscap_plugin_bin = (
        install_dir / ".config/complytime/plugins/openscap-plugin"
    ).resolve()
    openscap_plugin_conf = (
        install_dir / ".config/complytime/plugins/c2p-openscap-manifest.json"
    ).resolve()
    return openscap_plugin_bin.exists() and openscap_plugin_conf.exists()


def is_complytime_cached(download_dir: Path) -> bool:
    return bool(
        glob.glob(
            str((download_dir / "releases/*/complytime_linux_x86_64.tar.gz").resolve())
        )
    )


def sha256sum(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    chunk_size = 65536
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
        return sha256.hexdigest()


@pytest.fixture(autouse=True)
def complytime_home() -> YieldFixture[Path]:
    # Setup
    complytime_cache_dir.mkdir(parents=True, exist_ok=True)
    complytime_home = Path(tempfile.mkdtemp(prefix=_TEST_PREFIX))
    orig_home = os.getenv("HOME")
    orig_path = os.getenv("PATH")
    orig_xdg_config_home = os.getenv("XDG_CONFIG_HOME")

    complytime_home.mkdir(parents=True, exist_ok=True)
    if not is_complytime_installed(complytime_home):
        if not is_complytime_cached(complytime_cache_dir):
            result = subprocess.run(
                [
                    scripts_dir / "get-github-release.py",
                    "--prerelease",
                    "https://github.com/complytime/complytime",
                ],
                cwd=complytime_cache_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise ValueError(
                    "Unable to install ComplyTime for integration test!"
                    f"\n{result.stdout}"
                    f"\n{result.stderr}"
                )
        result = subprocess.run(
            [
                "find",
                f"{complytime_cache_dir}/releases",
                "-name",
                "complytime_linux_x86_64.tar.gz",
                "-exec",
                "tar",
                "-xvf",
                "{}",
                ";",
                "-quit",
            ],
            cwd=complytime_home,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError(
                f"Unable to extract ComplyTime for integration test!\n{result.stdout}\n{result.stderr}"
            )

        # Install complytime
        install_complytime(complytime_home)

        # Create dummy base files
        shutil.copy(
            int_test_data_dir / "sample-catalog.json",
            complytime_home / ".config/complytime/controls/sample-catalog.json",
        )
        shutil.copy(
            int_test_data_dir / "sample-profile.json",
            complytime_home / ".config/complytime/controls/sample-profile.json",
        )
        shutil.copy(
            int_test_data_dir / "sample-component-definition.json",
            complytime_home
            / ".config/complytime/bundles/sample-component-definition.json",
        )

    os.environ["HOME"] = str(complytime_home)
    os.environ["XDG_CONFIG_HOME"] = str(complytime_home / ".config")
    os.environ["PATH"] = str(complytime_home / "bin") + ":" + os.environ["PATH"]

    yield complytime_home  # run the test

    # Teardown
    if orig_home is None:
        os.unsetenv("HOME")
    else:
        os.environ["HOME"] = orig_home
    if orig_path is None:
        os.unsetenv("PATH")
    else:
        os.environ["PATH"] = orig_path
    if orig_xdg_config_home is None:
        os.unsetenv("XDG_CONFIG_HOME")
    else:
        os.environ["XDG_CONFIG_HOME"] = orig_xdg_config_home
    shutil.rmtree(complytime_home)


def install_complytime(complytime_home: Path) -> None:
    Path(complytime_home / "bin/").mkdir(parents=True, exist_ok=True)
    Path(complytime_home / ".config/complytime/plugins/").mkdir(
        parents=True, exist_ok=True
    )
    Path(complytime_home / ".config/complytime/bundles/").mkdir(
        parents=True, exist_ok=True
    )
    Path(complytime_home / ".config/complytime/controls/").mkdir(
        parents=True, exist_ok=True
    )
    shutil.move(complytime_home / "complytime", complytime_home / "bin/complytime")
    shutil.move(
        complytime_home / "openscap-plugin",
        complytime_home / ".config/complytime/plugins/openscap-plugin",
    )
    openscap_plugin_sha256 = sha256sum(
        complytime_home / ".config/complytime/plugins/openscap-plugin"
    )
    with open(
        int_test_data_dir / "c2p-openscap-manifest.json"
    ) as c2p_openscap_manifest_file:
        c2p_openscap_manifest = json.load(c2p_openscap_manifest_file)
        c2p_openscap_manifest["sha256"] = openscap_plugin_sha256
        with open(
            complytime_home / ".config/complytime/plugins/c2p-openscap-manifest.json",
            "w",
        ) as templated_file:
            json.dump(c2p_openscap_manifest, templated_file)
