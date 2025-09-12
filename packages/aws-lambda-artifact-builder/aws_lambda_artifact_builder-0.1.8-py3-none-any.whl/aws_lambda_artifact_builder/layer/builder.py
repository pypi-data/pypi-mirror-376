# -*- coding: utf-8 -*-

"""
Lambda layer building implementation - Step 1 of the layer creation workflow.
"""

import dataclasses
import subprocess
from pathlib import Path
from functools import cached_property

from func_args.api import REQ

from ..constants import LayerBuildToolEnum

from .foundation import Credentials, LayerPathLayout, BaseLogger


@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerLocalBuilder(BaseLogger):
    """
    Base command class for local Lambda layer builds.

    This abstract base implements a standardized 4-step workflow for building Lambda layers
    directly on the host machine using local dependency management tools (pip, Poetry, UV).
    The command pattern design allows fine-grained control and customization of each build phase.

    **4-Step Build Workflow:**

    1. **Preflight Check** (:meth:`step_1_preflight_check`): Validate environment, tools, and project structure
    2. **Prepare Environment** (:meth:`step_2_prepare_environment`): Clean build directories and set up workspace
    3. **Execute Build** (:meth:`step_3_execute_build`): Run tool-specific dependency installation (abstract)
    4. **Finalize Artifacts** (:meth:`step_4_finalize_artifacts`): Transform output into Lambda-compatible structure

    **Command Pattern Benefits:**

    - Each step can be overridden independently for customization
    - Sub-steps within each phase provide granular control points
    - Workflow can be extended with pre/post hooks or additional steps
    - Easy to test individual phases in isolation

    **Local Build Advantages:**

    - Fast execution without Docker overhead
    - Direct access to host environment and tools
    - Ideal for development iteration and Linux environments
    - Simple dependency resolution using host-installed package managers

    **Usage**: Subclass and implement :meth:`step_3_execute_build` with tool-specific logic.
    Call :meth:`run` to execute the complete workflow, or invoke individual steps for custom workflows.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    credentials: Credentials | None = dataclasses.field(default=None)
    skip_prompt: bool = dataclasses.field(default=False)

    _build_tool: LayerBuildToolEnum = dataclasses.field(default=REQ)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`~aws_lambda_artifact_builder.layer.foundation.LayerPathLayout`
        object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    def run(self):
        """
        Execute the complete local build workflow in sequence.

        Runs all four build phases in order. Override individual steps
        or call steps directly for custom workflows.
        """
        self.log("--- Start local Lambda layer build workflow")
        self.step_1_preflight_check()
        self.step_2_prepare_environment()
        self.step_3_execute_build()
        self.step_4_finalize_artifacts()

    def step_1_preflight_check(self):
        """
        Perform read-only validation of build environment and project configuration.
        """
        self.log("--- Step 1 - Flight Check")
        self.step_1_1_print_info()

    def step_2_prepare_environment(self):
        """
        Set up necessary prerequisites for the build process.
        """
        self.log("--- Step 2 - Prepare Environment")
        self.step_2_1_setup_build_dir()

    def step_3_execute_build(self):
        """
        Execute dependency manager-specific installation commands (pip/poetry/uv).
        """
        self.log("--- Step 3 - Execute Build")

    def step_4_finalize_artifacts(self):
        """
        Transform build output into Lambda layer's required python/ directory structure.
        """
        self.log("--- Step 4 - Finalize Artifacts")

    # --- step_1_preflight_check sub-steps
    def step_1_1_print_info(self):
        """
        Display build configuration and paths.

        Provides visibility into the build process by showing which tool
        is being used and where artifacts will be created.
        """
        self.log(f"--- Step 1.1 - Print Build Info")
        self.log(f"build tool = {self._build_tool.value}")
        p = self.path_pyproject_toml
        self.log(f"path_pyproject_toml = {p}")
        p = self.path_layout.dir_build_lambda_layer
        self.log(f"dir_build_lambda_layer = {p}")

    # --- step_2_prepare_environment sub-steps
    def step_2_1_setup_build_dir(self):
        """
        Prepare the build environment by cleaning and creating directories.

        Ensures a clean slate for layer creation by removing previous artifacts
        and establishing the required directory structure.

        :param skip_prompt: If True, automatically remove existing build directory
        """
        self.log(f"--- Step 2.1 - Setup Build Directory")
        dir = self.path_layout.dir_build_lambda_layer
        self.log(f"--- Clean existing build directory: {dir}")
        self.path_layout.clean(skip_prompt=self.skip_prompt)
        self.path_layout.mkdirs()

    # --- step_3_execute_build sub-steps

    # --- step_4_finalize_artifacts sub-steps


@dataclasses.dataclass(frozen=True)
class BasedLambdaLayerContainerBuilder(BaseLogger):
    """
    Base command class for containerized Lambda layer builds.

    This abstract base implements a standardized 4-step workflow for building Lambda layers
    inside Docker containers using official AWS SAM build images. The containerized approach
    ensures perfect runtime compatibility while maintaining the same command pattern flexibility.

    **4-Step Containerized Workflow:**

    1. **Preflight Check** (:meth:`step_1_preflight_check`): Validate Docker environment and build prerequisites
    2. **Prepare Environment** (:meth:`step_2_prepare_environment`): Copy build scripts and set up credentials
    3. **Execute Build** (:meth:`step_3_execute_build`): Run Docker container with mounted volumes
    4. **Finalize Artifacts** (:meth:`step_4_finalize_artifacts`): Clean up temporary files and validate results

    **Container Build Process:**

    - Mounts project root to ``/var/task`` inside container
    - Executes tool-specific build script within Lambda runtime environment
    - Uses local builder classes inside container for consistency
    - Transfers credentials securely via JSON files

    **Architecture Benefits:**

    - **Runtime Compatibility**: Uses official AWS Lambda container images
    - **Cross-Platform**: Builds Linux-compatible layers on any host OS
    - **Isolation**: No interference with host Python environment
    - **Reproducibility**: Identical results across different development machines
    - **Architecture Support**: Handles both x86_64 and ARM64 Lambda runtimes

    **Command Pattern Benefits:**

    - Individual container setup steps can be customized
    - Easy to extend with additional pre/post processing
    - Docker configuration can be modified through property overrides
    - Build script deployment can be customized per tool

    **Usage**: Subclass and provide tool-specific build script via :attr:`path_script`.
    Call :meth:`run` to execute containerized build, or customize individual steps as needed.
    """

    path_pyproject_toml: Path = dataclasses.field(default=REQ)
    py_ver_major: int = dataclasses.field(default=REQ)
    py_ver_minor: int = dataclasses.field(default=REQ)
    is_arm: bool = dataclasses.field(default=REQ)
    path_script: Path = dataclasses.field(default=REQ)
    credentials: Credentials | None = dataclasses.field(default=None)

    @cached_property
    def path_layout(self) -> LayerPathLayout:
        """
        :class:`~aws_lambda_artifact_builder.layer.foundation.LayerPathLayout`
        object for managing build paths.
        """
        return LayerPathLayout(
            path_pyproject_toml=self.path_pyproject_toml,
        )

    @property
    def image_tag(self) -> str:
        """
        Docker image tag based on target architecture.

        :return: Architecture-specific tag for AWS SAM build images
        """
        if self.is_arm:
            return "latest-arm64"
        else:
            return "latest-x86_64"

    @property
    def image_uri(self) -> str:
        """
        Full Docker image URI for AWS SAM build container.

        Uses official AWS SAM images that match the Lambda runtime environment
        to ensure compatibility between local builds and deployed functions.

        :return: Complete Docker image URI from AWS public ECR
        """
        return (
            f"public.ecr.aws/sam"
            f"/build-python{self.py_ver_major}.{self.py_ver_minor}"
            f":{self.image_tag}"
        )

    @property
    def platform(self) -> str:
        """
        Docker platform specification for target architecture.

        :return: Platform string for docker run --platform argument
        """
        if self.is_arm:
            return "linux/arm64"
        else:
            return "linux/amd64"

    @property
    def container_name(self) -> str:
        """
        Unique container name for the build process.

        Includes Python version and architecture to avoid conflicts when
        running multiple builds concurrently.

        :return: Descriptive container name for docker run --name argument
        """
        suffix = "arm64" if self.is_arm else "amd64"
        return (
            f"lambda_layer_builder"
            f"-python{self.py_ver_major}{self.py_ver_minor}"
            f"-{suffix}"
        )

    @property
    def docker_run_args(self) -> list[str]:
        """
        Complete Docker run command arguments.

        Constructs the full command for executing the build script inside
        a Docker container with proper volume mounting and platform specification.

        :return: List of command arguments for subprocess execution
        """
        return [
            "docker",
            "run",
            "--rm",  # Auto-remove container when done
            "--name",
            self.container_name,
            "--platform",
            self.platform,
            "--mount",
            f"type=bind,source={self.path_layout.dir_project_root},target=/var/task",
            self.image_uri,
            "python",
            "-u",  # Unbuffered output for real-time logging
            self.path_layout.path_build_lambda_layer_in_container_script_in_container,
        ]

    def run(self):
        """
        Execute the complete containerized build workflow in sequence.

        Runs all four container build phases in order. Override individual
        steps or call steps directly for custom workflows.
        """
        self.log("--- Start containerized Lambda layer build workflow")
        self.step_1_preflight_check()
        self.step_2_prepare_environment()
        self.step_3_execute_build()
        self.step_4_finalize_artifacts()

    def step_1_preflight_check(self):
        """
        Validate Docker environment and container build prerequisites.
        """
        self.log("--- Step 1 - Preflight Check")

    def step_2_prepare_environment(self):
        """
        Set up container build prerequisites including scripts and credentials.
        """
        self.log("--- Step 2 - Prepare Environment")
        self.step_2_1_copy_build_script()
        self.step_2_2_setup_private_repository_credential()

    def step_3_execute_build(self):
        """
        Run Docker container with AWS SAM build image for dependency installation.
        """
        self.log("--- Step 3 - Execute Build")
        self.step_3_1_docker_run()

    def step_4_finalize_artifacts(self):
        """
        Clean up temporary files and validate container build results.
        """
        self.log("--- Step 4 - Finalize Artifacts")

    # --- step_1_preflight_check sub-steps
    # --- step_2_prepare_environment sub-steps
    def step_2_1_copy_build_script(self):
        """
        Copy the tool-specific container build script to the project directory.

        Subclasses must implement this method to provide the appropriate
        build script that will be executed inside the Docker container.
        """
        self.log("--- Step 2.1 - Copy Build Script")
        self.path_layout.copy_build_script(
            p_src=self.path_script,
            printer=self.log,
        )

    def step_2_2_setup_private_repository_credential(self):
        """
        Configure private repository authentication (optional).

        Subclasses can override this method to set up credentials for
        accessing private PyPI servers or corporate package repositories.
        """
        self.log(f"--- Step 2.2 - Setup Private Repository Credential")
        if isinstance(self.credentials, Credentials) is False:
            self.log("No private repository credentials provided, skip.")
            return
        p = self.path_layout.path_private_repository_credentials_in_local
        self.log(f"Dump private repository credentials to {p}")
        self.credentials.dump(path=p)

    # --- step_3_execute_build sub-steps
    def step_3_1_docker_run(self):
        """
        Execute the Docker container build process.

        Runs the configured Docker command to build the Lambda layer
        inside the container environment.
        """
        self.log(f"--- Step 3.1 - Docker Run")
        # If the python script (``_build_lambda_layer_using_*.py``) raises an exception,
        # docker run command will also fail with a non-zero exit code
        subprocess.run(self.docker_run_args, check=True)

    # --- step_4_finalize_artifacts sub-steps
