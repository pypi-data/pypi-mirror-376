# -*- coding: utf-8 -*-

"""
Common infrastructure for Lambda layer builders using the Command Pattern.

This module provides the foundational classes and utilities that support multiple
build strategies (pip, poetry, uv) through a consistent command pattern architecture.
The design separates public API functions from internal command classes to balance
ease of use with code maintainability.

Architecture Overview:

- **Public Functions**: Simple API for end users
    (e.g., build_layer_artifacts_using_pip_in_local, build_layer_artifacts_using_pip_in_container)
- **Command Classes**: Internal implementation for better code organization and testability
- **Local Builders**: Direct dependency installation on the host machine
- **Container Builders**: Dockerized builds for AWS Lambda runtime compatibility
"""

import typing as T
import os
import json
import shutil
import hashlib
import subprocess
import dataclasses
from pathlib import Path
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..typehint import T_PRINTER
from ..constants import ZFILL, LayerBuildToolEnum
from ..imports import S3Path
from ..utils import write_bytes, clean_build_directory

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3 import S3Client


@dataclasses.dataclass(frozen=True)
class Credentials:
    """
    Private repository credentials for accessing authenticated package indexes.

    Used to configure pip, poetry, and uv to authenticate with private PyPI servers
    or corporate package repositories during layer builds.
    """

    index_name: str = dataclasses.field()
    index_url: str = dataclasses.field()
    username: str = dataclasses.field()
    password: str = dataclasses.field()

    @property
    def normalized_index_url(self) -> str:
        """
        Normalize index URL by stripping scheme and trailing slashes.
        """
        index_url = self.index_url
        if index_url.startswith("https://"):
            index_url = index_url[len("https://") :]
        if index_url.endswith("/"):
            index_url = index_url[:-1]
        if index_url.endswith("/simple"):
            index_url = index_url[: -len("/simple")]
        return index_url

    @property
    def uppercase_index_name(self) -> str:
        """
        This is used for environment variable keys for poetry / uv authentication.
        """
        return self.index_name.replace("-", "_").upper()

    @property
    def pip_extra_index_url(self) -> str:
        """
        Generate pip-compatible URL with embedded authentication.

        :return: URL in format https://username:password@hostname/simple/
        """
        return f"https://{self.username}:{self.password}@{self.normalized_index_url}/simple/"

    def dump(self, path: Path):
        """
        Save credentials to a JSON file.

        :param path: Path to the output JSON file
        """
        data = dataclasses.asdict(self)
        b = json.dumps(data, indent=4).encode("utf-8")
        write_bytes(path=path, content=b)

    @classmethod
    def load(cls, path: Path):
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    @property
    def additional_pip_install_args_index_url(self):
        """
        Override default PyPI with authenticated URL with embedded credentials.

        .. seealso::

            https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-i
        """
        return [
            "--index-url",  # Override default PyPI with authenticated URL
            self.pip_extra_index_url,  # Includes embedded credentials
        ]

    @property
    def additional_pip_install_args_extra_index_url(self):
        """
        Override default PyPI with authenticated URL with embedded credentials.

        .. seealso::

            https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-extra-index-url
        """
        return [
            "--extra-index-url",
            self.pip_extra_index_url,
        ]

    def poetry_login(self) -> tuple[str, str]:
        """
        Configure Poetry authentication via environment variables.

        Poetry uses POETRY_HTTP_BASIC_{SOURCE}_USERNAME/PASSWORD environment
        variables for private repository authentication, following Poetry's
        documented credential configuration pattern.

        .. seealso::

            https://python-poetry.org/docs/repositories/#configuring-credentials
        """
        key_user = f"POETRY_HTTP_BASIC_{self.uppercase_index_name}_USERNAME"
        os.environ[key_user] = "aws"
        key_pass = f"POETRY_HTTP_BASIC_{self.uppercase_index_name}_PASSWORD"
        os.environ[key_pass] = self.password
        return key_user, key_pass

    def uv_login(self) -> tuple[str, str]:
        """
        Configure UV authentication via environment variables.

        .. seealso::

            https://docs.astral.sh/uv/reference/environment/#uv_index_url
        """
        key_user = f"UV_INDEX_{self.uppercase_index_name}_USERNAME"
        os.environ[key_user] = "aws"
        key_pass = f"UV_INDEX_{self.uppercase_index_name}_PASSWORD"
        os.environ[key_pass] = self.password
        return key_user, key_pass


@dataclasses.dataclass(frozen=True)
class LayerPathLayout(BaseFrozenModel):
    """
    Local directory layout manager for Lambda layer build artifacts.

    Assuming your Git repository is located at ``${dir_project_root}/``,
    we use ``${dir_project_root}`` to represent this path. The Lambda layer-related paths are as follows:

    - ``${dir_project_root}``
        :meth:`dir_project_root`, Git repository root directory.
    - ``${dir_project_root}/pyproject.toml``
        :attr:`path_pyproject_toml`, pyproject.toml file path.
    - ``${dir_project_root}/build/lambda/layer``
        :meth:`dir_build_lambda_layer`, temporary directory for building Lambda layer,
        cleared before each build.
    - ``${dir_project_root}/build/lambda/layer/layer.zip``
        :meth:`path_build_lambda_layer_zip`, final Lambda layer zip file path for deployment.
    - ``${dir_project_root}/build/lambda/layer/repo``
        :meth:`dir_repo`, to avoid affecting original files in the repository, we create a temporary
        directory here with a structure similar to dir_project_root, copying important files like pyproject.toml.
        If temporary virtual environments need to be built, they will also be created here.
    - ``${dir_project_root}/build/lambda/layer/artifacts``
        :meth:`dir_artifacts`, directory for storing all files to be packaged into layer.zip
    - ``${dir_project_root}/build/lambda/layer/artifacts/python``
        :meth:`dir_python`, AWS Lambda required ``python`` subdirectory.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)

    @property
    def dir_project_root(self) -> Path:
        """
        Project root directory, usually the Git repository root.
        """
        return self.path_pyproject_toml.parent

    @cached_property
    def dir_venv(self) -> Path:
        return self.dir_project_root / ".venv"

    @cached_property
    def path_venv_bin_python(self) -> Path:
        return self.dir_venv / "bin" / "python"

    @cached_property
    def venv_python_version(self) -> tuple[int, int, int]:
        args = [f"{self.path_venv_bin_python}", "--version"]
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        s = result.stdout
        major, minor, micro = s.split()[1].split(".")
        major = int(major)
        minor = int(minor)
        micro = int(micro)
        return major, minor, micro

    @cached_property
    def dir_build_lambda_layer_repo_venv_site_packages(self) -> Path:
        """
        The site-packages directory of the virtual environment that stores
        all Lambda layer dependencies. Created by poetry or uv.
        """
        # TODO: support Windows
        major, minor, micro = self.venv_python_version
        return self.dir_repo / ".venv" / "lib" / f"python{major}.{minor}" / "site-packages"

    def get_path_in_container(self, path_in_local: Path) -> str:
        """
        Convert local filesystem path to corresponding Docker container path.

        Docker containers mount the project root to /var/task, so this method
        translates local paths to their container equivalents for script execution.

        :param path_in_local: Local filesystem path relative to project root
        :return: Corresponding path inside Docker container
        """
        relpath = path_in_local.relative_to(self.dir_project_root)
        parts = ["var", "task"]
        parts.extend(relpath.parts)
        path = "/" + "/".join(parts)
        return path

    @property
    def dir_build_lambda(self) -> Path:
        """
        The build directory for Lambda-related artifacts.
        """
        return self.dir_project_root / "build" / "lambda"

    @property
    def dir_build_lambda_layer(self) -> Path:
        """
        The build directory for Lambda layer build.

        .. important::

            This directory is cleared before each build to ensure a clean environment.
        """
        return self.dir_build_lambda / "layer"

    @property
    def path_build_lambda_layer_zip(self) -> Path:
        """
        The output zip file path for the built Lambda layer.
        """
        return self.dir_build_lambda_layer / "layer.zip"

    @property
    def dir_repo(self) -> Path:
        """
        A temporary copy of the project repository for building the layer.
        """
        return self.dir_build_lambda_layer / "repo"

    @property
    def path_tmp_pyproject_toml(self) -> Path:
        """
        A temporary copy of pyproject.toml for building the layer.
        """
        return self.dir_repo / self.path_pyproject_toml.name

    @property
    def path_build_lambda_layer_in_container_script_in_local(self) -> Path:
        """
        Local path where the containerized build script is copied.

        This script contains the build logic that will be executed inside
        the Docker container to install dependencies.

        .. important::

            This path has to be outside the :meth:`dir_build_lambda_layer` folder,
            because the :meth:`dir_build_lambda_layer` folder is cleared before each
            ``build_lambda_layer_***_in_local(...)`` function call, but this script
            must persist before that.
        """
        return self.dir_project_root / "build_lambda_layer_in_container.py"

    @property
    def path_build_lambda_layer_in_container_script_in_container(self) -> str:
        """
        Container path where the build script can be executed.

        :return: Path string for use in Docker run commands
        """
        p = self.path_build_lambda_layer_in_container_script_in_local
        return self.get_path_in_container(p)

    @property
    def path_requirements_txt(self) -> Path:
        """
        The generated requirements.txt file path.
        """
        return self.dir_project_root / "requirements.txt"

    @property
    def path_poetry_lock(self) -> Path:
        """
        The original poetry.lock file path.
        """
        return self.dir_project_root / "poetry.lock"

    @property
    def path_tmp_poetry_lock(self) -> Path:
        """
        A temporary copy of poetry.lock for building the layer.
        """
        return self.dir_repo / "poetry.lock"

    @property
    def path_uv_lock(self) -> Path:
        """
        The original uv.lock file path.
        """
        return self.dir_project_root / "uv.lock"

    @property
    def path_tmp_uv_lock(self) -> Path:
        """
        A temporary copy of uv.lock for building the layer.
        """
        return self.dir_repo / "uv.lock"

    @property
    def path_private_repository_credentials_in_local(self) -> Path:
        """
        The private repository credentials file path.

        .. important::

            This path has to be outside the :meth:`dir_build_lambda_layer` folder,
            because the :meth:`dir_build_lambda_layer` folder is cleared before each
            ``build_lambda_layer_***_in_local(...)`` function call, but this script
            must persist before that.
        """
        return self.dir_build_lambda / "private-repository-credentials.json"

    @property
    def path_private_repository_credentials_in_container(self) -> str:
        """
        The private repository credentials file path inside the container.
        """
        p = self.path_private_repository_credentials_in_local
        return self.get_path_in_container(p)

    @property
    def dir_artifacts(self) -> Path:
        """
        The directory to store all files to be included in the layer.zip.
        """
        return self.dir_build_lambda_layer / "artifacts"

    @property
    def dir_python(self) -> Path:
        """
        The AWS Lambda required ``python`` subdirectory.

        Ref:

        - https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html
        """
        return self.dir_artifacts / "python"

    def clean(self, skip_prompt: bool = False):
        """
        Clean existing build directory to ensure fresh installation.

        Removes all artifacts from previous builds to prevent conflicts
        and ensure reproducible layer creation.

        :param skip_prompt: If True, skip user confirmation for directory removal
        """
        clean_build_directory(
            dir_build=self.dir_build_lambda_layer,
            folder_alias="lambda layer build folder",
            skip_prompt=skip_prompt,
        )

    def mkdirs(self):
        """
        Create all necessary directories for the build process.

        Ensures the directory structure is ready for dependency installation
        and layer artifact creation.
        """
        self.dir_repo.mkdir(parents=True, exist_ok=True)
        self.dir_python.mkdir(parents=True, exist_ok=True)

    def copy_file(
        self,
        p_src: Path,
        p_dst: Path,
        printer: T_PRINTER = print,
    ):
        """
        Copy a file with logging support.

        :param p_src: Source file path
        :param p_dst: Destination file path
        :param printer: Function to handle log messages
        """
        printer(f"Copy {p_src} to {p_dst}")
        shutil.copy(p_src, p_dst)

    def copy_build_script(
        self,
        p_src: Path,
        printer: T_PRINTER = print,
    ):
        """
        Copy containerized build script to the project directory.

        The build script contains tool-specific logic (pip/poetry/uv) that will
        be executed inside the Docker container.

        :param p_src: Path to the tool-specific build script
        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=p_src,
            p_dst=self.path_build_lambda_layer_in_container_script_in_local,
            printer=printer,
        )

    def copy_pyproject_toml(self, printer: T_PRINTER = print):
        """
        Copy pyproject.toml to the isolated build directory.

        Creates a clean copy for dependency resolution without affecting
        the original project configuration.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_pyproject_toml,
            p_dst=self.path_tmp_pyproject_toml,
            printer=printer,
        )

    def copy_poetry_lock(self, printer: T_PRINTER = print):
        """
        Copy poetry.lock to the isolated build directory.

        Ensures dependency versions remain consistent by using the locked
        dependency resolution from the original project.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_poetry_lock,
            p_dst=self.path_tmp_poetry_lock,
            printer=printer,
        )

    def copy_uv_lock(self, printer: T_PRINTER = print):
        """
        Copy uv.lock to the isolated build directory.

        Maintains reproducible builds by preserving the exact dependency
        versions resolved by uv.

        :param printer: Function to handle log messages
        """
        self.copy_file(
            p_src=self.path_uv_lock,
            p_dst=self.path_tmp_uv_lock,
            printer=printer,
        )

    def get_path_manifest(
        self,
        tool: LayerBuildToolEnum,
    ) -> Path:
        """
        Get the dependency manifest file path for the specified build tool.

        A dependency manifest is the "source of truth" file that contains the exact
        specification of all dependencies and their versions. With this manifest file,
        the Python layer can be rebuilt identically, ensuring reproducible builds
        across different environments.

        **Manifest Types by Tool:**

        - **pip**: ``requirements.txt`` - Lists exact package versions and hashes
        - **poetry**: ``poetry.lock`` - Lock file with resolved dependency tree
        - **uv**: ``uv.lock`` - Lock file with ultra-fast resolved dependencies

        :param tool: The build tool enum specifying which manifest to return
        :return: Path to the appropriate dependency manifest file
        :raises ValueError: If an unsupported build tool is specified
        """

        if tool == LayerBuildToolEnum.pip:
            return self.path_requirements_txt
        elif tool == LayerBuildToolEnum.poetry:
            return self.path_poetry_lock
        elif tool == LayerBuildToolEnum.uv:
            return self.path_uv_lock
        else:
            raise ValueError(f"Unsupported tool: {tool}")


@dataclasses.dataclass
class LayerS3Layout:
    """
    S3 directory layout manager for Lambda layer artifacts and versioning.

    This class provides a structured approach to organizing Lambda layer artifacts
    in S3 with proper versioning support. It manages both temporary upload locations
    and permanent versioned storage for requirements tracking and layer management.

    Assuming ``s3dir_lambda`` is ``s3://bucket/path/lambda``, the relevant paths are:

    - ``${s3dir_lambda}/layer/layer.zip``
        :meth:`s3path_temp_layer_zip`, Temporary upload location for layer zip file.
    - ``${s3dir_lambda}/layer/000001/requirements.txt``
        :meth:`get_s3path_layer_requirements_txt`, Versioned requirements file for layer version 1.
    - ``${s3dir_lambda}/layer/000002/requirements.txt``
        :meth:`get_s3path_layer_requirements_txt`, Versioned requirements file for layer version 2.
    - ``${s3dir_lambda}/layer/last-requirements.txt``
        :meth:`s3path_last_requirements_txt`, Requirements file from the most recently published layer version.
    """

    s3dir_lambda: "S3Path" = dataclasses.field()

    @property
    def s3path_temp_layer_zip(self) -> "S3Path":
        """
        Temporary S3 location for layer zip uploads before AWS Lambda layer publishing.

        This is a staging location used during the layer publishing process. AWS Lambda
        reads the zip from this location and stores it internally, so we don't need to
        maintain historical versions in S3.

        .. note::

            Since AWS manages layer storage internally, there's no need to maintain
            historical versions of the layer zip in S3.

        :return: S3Path to the temporary layer.zip file
        """
        return self.s3dir_lambda.joinpath("layer", "layer.zip")

    def get_s3dir_layer_version(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 dir for a specific layer version' artifacts.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned requirements.txt file
                 (e.g., s3://bucket/path/lambda/layer/000001/)
        """
        return self.s3dir_lambda.joinpath(
            "layer",
            str(layer_version).zfill(ZFILL),
        ).to_dir()

    def get_s3path_layer_requirements_txt(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's requirements.txt file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned requirements.txt file
                 (e.g., s3://bucket/path/lambda/layer/000001/requirements.txt)
        """
        return self.get_s3dir_layer_version(layer_version) / "requirements.txt"

    def get_s3path_layer_poetry_lock(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's poetry.lock file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned poetry.lock file
                 (e.g., s3://bucket/path/lambda/layer/000001/poetry.lock)
        """
        return self.get_s3dir_layer_version(layer_version) / "poetry.lock"

    def get_s3path_layer_uv_lock(
        self,
        layer_version: int,
    ) -> "S3Path":
        """
        Generate S3 path for a specific layer version's uv.lock file.

        Each layer version gets its own directory with zero-padded numbering
        to maintain proper lexicographic ordering in S3.

        :param layer_version: Layer version number (e.g., 1, 2, 3...)
        :return: S3Path object pointing to the versioned uv.lock file
                 (e.g., s3://bucket/path/lambda/layer/000001/uv.lock)
        """
        return self.get_s3dir_layer_version(layer_version) / "uv.lock"

    @property
    def s3path_last_requirements_txt(self) -> "S3Path":
        """
        S3 path to the most recently published layer's requirements.txt file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local requirements.txt with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local requirements differ from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-requirements.txt")

    @property
    def s3path_last_poetry_lock(self) -> "S3Path":
        """
        S3 path to the most recently published layer's poetry.lock file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local poetry.lock with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local poetry.lock differs from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-poetry.lock")

    @property
    def s3path_last_uv_lock(self) -> "S3Path":
        """
        S3 path to the most recently published layer's uv.lock file.

        This file serves as a reference point for dependency change detection.
        The build system compares the local uv.lock with this file to
        determine whether a new layer version needs to be published.

        **Change Detection Logic**: If local uv.lock differs from this file,
        a new layer version is automatically created and published.

        :return: S3Path to the last-requirements.txt file
        """
        return self.s3dir_lambda.joinpath("layer", "last-uv.lock")


@dataclasses.dataclass(frozen=True)
class BaseLogger(BaseFrozenModel):
    verbose: bool = dataclasses.field(default=True)
    printer: T_PRINTER = dataclasses.field(default=print)

    def log(self, msg: str):
        """
        Log a message if verbosity is enabled.
        """
        if self.verbose:
            self.printer(msg)


@dataclasses.dataclass(frozen=True)
class LayerManifestManager(BaseLogger):
    """
    Manages dependency manifest files for Lambda layers.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    s3dir_lambda: "S3Path" = dataclasses.field(default=REQ)
    layer_build_tool: LayerBuildToolEnum = dataclasses.field(default=REQ)
    s3_client: "S3Client" = dataclasses.field(default=REQ)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`LayerPathLayout` object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    @cached_property
    def s3_layout(self) -> LayerS3Layout:
        """
        :class:`LayerS3Layout` object for managing build paths.
        """
        return LayerS3Layout(
            s3dir_lambda=self.s3dir_lambda,
        )

    @cached_property
    def path_manifest(self) -> Path:
        """
        Get the dependency manifest file path.
        """
        return self.path_layout.get_path_manifest(tool=self.layer_build_tool)

    @cached_property
    def manifest_md5(self) -> str:
        """
        Calculate the MD5 hash of the dependency manifest file.
        """
        return hashlib.md5(self.path_manifest.read_bytes()).hexdigest()

    def get_versioned_manifest(self, version: int) -> "S3Path":
        """
        Get the S3 path of the dependency manifest file for a specific layer version.

        This method constructs the S3 path where the dependency manifest (source of truth)
        is stored for a given layer version. The manifest serves as a backup that enables
        future change detection and layer reproducibility.

        :param version: The layer version number to get the manifest path for
        :return: S3Path pointing to the stored manifest file for the specified version
        """
        s3dir = self.s3_layout.get_s3dir_layer_version(layer_version=version)
        s3path = s3dir.joinpath(self.path_manifest.name)
        return s3path
