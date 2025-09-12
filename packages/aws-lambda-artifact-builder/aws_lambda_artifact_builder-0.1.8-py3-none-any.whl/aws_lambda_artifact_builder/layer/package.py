# -*- coding: utf-8 -*-

"""
Lambda layer packaging implementation - Step 2 of the layer creation workflow.

This module handles the packaging phase of AWS Lambda layer creation, transforming
the built dependencies into a properly structured zip file ready for deployment.
"""

from pathlib import Path
import glob
import shutil
import subprocess
import dataclasses
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..constants import LayerBuildToolEnum

from .foundation import LayerPathLayout
from ..vendor.better_pathlib import temp_cwd


def move_to_dir_python(
    dir_site_packages: Path,
    dir_python: Path,
):
    """
    Restructure installed packages into AWS Lambda layer format.

    This function moves packages from a standard Python site-packages directory
    into the AWS Lambda layer's required ``python/`` directory structure. This
    transformation is necessary because different build tools (pip, Poetry, UV)
    install packages to different locations, but Lambda layers must follow a
    standardized directory layout.

    **Directory Transformation:**

    - **Source**: ``build/lambda/layer/repo/.venv/lib/python3.x/site-packages/``
    - **Target**: ``build/lambda/layer/artifacts/python/``

    The function handles the move operation safely by removing any existing
    target directory before moving to prevent conflicts and ensure clean packaging.

    :param dir_site_packages: Path to the source site-packages directory from build process
    :param path_pyproject_toml: Path to pyproject.toml file (determines project root and layout)
        to identify the correct layer artifacts directory

    :raises FileNotFoundError: If the source site-packages directory doesn't exist
    """
    if dir_site_packages.exists():
        # Move the content of dir_site_packages to dir_python
        if dir_site_packages != dir_python:
            if dir_python.exists():
                shutil.rmtree(dir_python)
            shutil.move(dir_site_packages, dir_python)
        # otherwise, dir_site_packages is the same as dir_python, do nothing
    else:
        raise FileNotFoundError(f"dir_site_packages {dir_site_packages} not found")


default_ignore_package_list = [
    "boto3",
    "botocore",
    "s3transfer",
    "urllib3",
    "setuptools",
    "pip",
    "wheel",
    "twine",
    "_pytest",
    "pytest",
]
"""
Default packages to exclude from Lambda layer zip files.
These packages are commonly excluded because they are either:

- **AWS Runtime Provided**: boto3, botocore, s3transfer, urllib3 are pre-installed in Lambda
- **Build Tools**: setuptools, pip, wheel, twine are not needed at runtime
- **Development Tools**: pytest, _pytest are testing frameworks not needed in production

Excluding these packages reduces layer size and avoids version conflicts with
the Lambda runtime environment. Custom ignore lists can override this default.
"""


def create_layer_zip_file(
    dir_python: Path,
    path_layer_zip: Path,
    ignore_package_list: list[str] | None = None,
    verbose: bool = True,
):
    """
    Create optimized zip file for AWS Lambda layer deployment (Public API).

    This function creates the final deployable artifact by compressing the layer's
    ``python/`` directory into a zip file with selective package exclusions. The
    resulting zip file is ready for upload to S3 and Lambda layer publication.

    **Compression and Optimization**

    - **Compression Level**: Uses maximum compression (-9) to minimize layer size
    - **Package Exclusions**: Removes AWS runtime-provided and development packages
    - **Directory Structure**: Preserves Lambda-required ``python/`` directory layout
    - **Recursive Packaging**: Includes all subdirectories and maintains file permissions

    **Default Exclusions:**

    The function automatically excludes common packages that are either provided
    by the AWS Lambda runtime (boto3, botocore) or not needed at runtime (pytest,
    setuptools). This reduces layer size and prevents version conflicts.

    **Output Location:**

    Creates ``build/lambda/layer/layer.zip`` in the project root, following the
    standard layer artifact naming convention established by the LayerPathLayout.

    :param path_pyproject_toml: Path to pyproject.toml file (determines project root and output location)
    :param ignore_package_list: Optional list of additional packages to exclude from zip.
        If None, uses :data:`default_ignore_package_list`. Package names support glob patterns.
    :param verbose: If True, shows detailed zip creation progress; if False, runs silently
    """
    if ignore_package_list is None:
        ignore_package_list = list(default_ignore_package_list)

    args = [
        "zip",
        f"{path_layer_zip}",
        "-r",
        "-9",
    ]
    if verbose is False:
        args.append("-q")

    # Change to artifacts directory to ensure proper relative path structure in zip
    # The zip file must contain 'python/' as the root directory, not the full path
    # from the host system, so we execute zip from within the artifacts directory
    with temp_cwd(dir_python.parent):
        # Add all files and directories from the artifacts directory
        # This typically includes the 'python/' directory containing all packages
        args.extend(glob.glob("*"))

        # Apply package exclusions using zip's -x flag for selective filtering
        # Each exclusion pattern targets packages within the python/ directory
        if ignore_package_list:
            args.append("-x")  # Enable exclusion mode
            for package in ignore_package_list:
                # Exclude package directories and all their contents using glob patterns
                args.append(f"python/{package}*")
        # Execute zip command with all configured arguments
        # The resulting layer.zip will be created in the project's build directory
        subprocess.run(args, check=True)


@dataclasses.dataclass(frozen=True)
class LambdaLayerZipper(BaseFrozenModel):
    """
    Command class for Lambda layer packaging and zip file creation.

    This class handles the second phase of Lambda layer creation: transforming build artifacts
    into a properly structured, compressed zip file ready for AWS deployment. It bridges the
    gap between different build tools by standardizing the packaging process regardless of
    whether dependencies were installed via pip, Poetry, or UV.

    **Packaging Workflow:**

    1. **Directory Standardization**: Moves packages from tool-specific locations into Lambda's required ``python/`` structure
    2. **Selective Compression**: Creates optimized zip files with package exclusions for size optimization
    3. **Deployment Preparation**: Produces artifacts ready for S3 upload and Lambda layer publication

    **Multi-Tool Support:**

    - **pip**: Uses packages already in correct ``python/`` location (no movement needed)
    - **Poetry**: Moves from ``.venv/lib/python3.x/site-packages/`` to ``python/``
    - **UV**: Moves from ``.venv/lib/python3.x/site-packages/`` to ``python/``

    **Optimization Features:**

    - **Package Exclusions**: Removes AWS runtime-provided packages (boto3, botocore) and development tools
    - **Maximum Compression**: Uses zip level -9 for smallest possible layer size
    - **Custom Filtering**: Supports additional package exclusions through ignore lists

    **Output Location:**

    Creates ``build/lambda/layer/layer.zip`` ready for deployment.
    """
    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    layer_build_tool: LayerBuildToolEnum = dataclasses.field(default=REQ)
    ignore_package_list: list[str] | None = dataclasses.field(default=None)
    verbose: bool = dataclasses.field(default=True)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`~aws_lambda_artifact_builder.layer.foundation.LayerPathLayout`
        object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def move_to_dir_python(self):
        move_to_dir_python(
            dir_site_packages=self.path_layout.dir_build_lambda_layer_repo_venv_site_packages,
            dir_python=self.path_layout.dir_python,
        )

    def run(self):
        if self.layer_build_tool == LayerBuildToolEnum.pip:
            pass
        elif self.layer_build_tool == LayerBuildToolEnum.poetry:
            self.move_to_dir_python()
        elif self.layer_build_tool == LayerBuildToolEnum.uv:
            self.move_to_dir_python()
        else:
            raise ValueError(f"Unsupported build tool: {self.layer_build_tool}")

        create_layer_zip_file(
            dir_python=self.path_layout.dir_python,
            path_layer_zip=self.path_layout.path_build_lambda_layer_zip,
            ignore_package_list=self.ignore_package_list,
            verbose=self.verbose,
        )
