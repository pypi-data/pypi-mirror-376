# -*- coding: utf-8 -*-

"""
Poetry-based Lambda layer builder implementation.

This module provides Lambda layer creation using Poetry's dependency management,
supporting both local and containerized builds. Poetry offers reproducible builds
through lock files and sophisticated dependency resolution.

**Command Pattern Classes:**

- :class:`PoetryBasedLambdaLayerLocalBuilder`: Local poetry-based builds
- :class:`PoetryBasedLambdaLayerContainerBuilder`: Containerized poetry-based builds
"""

import subprocess
import dataclasses
from pathlib import Path

from func_args.api import REQ
from ..vendor.better_pathlib import temp_cwd

from ..constants import LayerBuildToolEnum
from ..paths import path_build_lambda_layer_using_poetry_in_container_script

from .builder import (
    BasedLambdaLayerLocalBuilder,
    BasedLambdaLayerContainerBuilder,
)


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerLocalBuilder(
    BasedLambdaLayerLocalBuilder,
):
    """
    This class implements Poetry-specific build workflow using virtual environments
    and lock file-based dependency resolution.

    **Key Features:**

    - Lock file-based reproducible builds
    - Environment variable authentication (POETRY_HTTP_BASIC_*)
    - In-project virtual environment setup
    - No root package installation (--no-root)

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerLocalBuilder`
    """

    path_bin_poetry: Path = dataclasses.field(default=REQ)
    _build_tool: str = dataclasses.field(default=LayerBuildToolEnum.poetry)

    def step_1_1_print_info(self):
        """
        Display Poetry-specific build information.
        """
        super().step_1_1_print_info()
        self.log(f"path_bin_poetry = {self.path_bin_poetry}")

    def step_2_prepare_environment(self):
        super().step_2_prepare_environment()
        self.step_2_2_prepare_poetry_stuff()

    def step_2_2_prepare_poetry_stuff(self):
        """
        Copy Poetry project files to build directory.

        Copies pyproject.toml and poetry.lock to ensure reproducible builds
        with exact dependency versions as resolved in development.
        """
        self.log("--- Step 2.2 - Prepare Poetry stuff")
        self.path_layout.copy_pyproject_toml(printer=self.log)
        self.path_layout.copy_poetry_lock(printer=self.log)

    def step_3_execute_build(self):
        """
        Perform Poetry-based Lambda layer build step.
        """
        self.step_3_1_poetry_login()
        self.step_3_2_run_poetry_install()

    def step_3_1_poetry_login(self):
        """
        Configure Poetry authentication via environment variables.
        """
        self.log("--- Step 3.1 - Setting up Poetry credentials")
        if self.credentials is not None:
            key_user, key_pass = self.credentials.poetry_login()
            self.log(f"Set environment variable {key_user}")
            self.log(f"Set environment variable {key_pass}")
        else:
            self.log("No Poetry credentials provided, skipping Poetry login step")

    def step_3_2_run_poetry_install(self):
        """
        Execute Poetry installation with lock file constraints.

        Runs Poetry install with --no-root to exclude the project package itself,
        installing only dependencies into an in-project virtual environment.
        """
        self.log("--- Step 3.2 - Run 'poetry install'")
        path_bin_poetry = self.path_bin_poetry
        dir_repo = self.path_layout.dir_repo
        with temp_cwd(dir_repo):
            self.log("--- Run 'poetry config virtualenvs.in-project true'")
            args = [
                f"{path_bin_poetry}",
                "config",
                "virtualenvs.in-project",
                "true",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)

            self.log("--- Run 'poetry install --no-root'")
            args = [
                f"{path_bin_poetry}",
                "install",
                "--no-root",
            ]
            subprocess.run(args, cwd=dir_repo, check=True)


@dataclasses.dataclass(frozen=True)
class PoetryBasedLambdaLayerContainerBuilder(
    BasedLambdaLayerContainerBuilder,
):
    """
    Command class for containerized Poetry-based Lambda layer builds.

    .. seealso::

        :class:`~aws_lambda_artifact_builder.layer.builder.BasedLambdaLayerContainerBuilder`
    """

    path_script: Path = dataclasses.field(
        default=path_build_lambda_layer_using_poetry_in_container_script
    )

    def step_1_preflight_check(self):
        super().step_1_preflight_check()
        if self.path_layout.path_poetry_lock.exists() is False:
            raise FileNotFoundError(
                f"Poetry lock file not found: {self.path_layout.path_poetry_lock},"
                f"cannot proceed with poetry-based build."
                f"Please run 'poetry lock' to generate the lock file."
            )
