# -*- coding: utf-8 -*-

"""
Lambda layer publication implementation - Step 4 of the layer creation workflow.

This module handles the publication phase of AWS Lambda layer deployment, taking
the uploaded layer zip file from S3 and creating versioned Lambda layer resources.
It represents the fourth and final step in the complete layer workflow:

1. **Build**: Install dependencies using pip/Poetry/UV builders
2. **Package**: Structure and compress dependencies into zip file  
3. **Upload**: Deploy zip file to S3 storage
4. **Publish**: Create versioned Lambda layer from S3 artifact (this module)

**Public API Functions:**
    - :func:`publish_layer_version`: Intelligent layer publishing with change detection

**Key Features:**
    - **Change Detection**: Compares dependency manifests to avoid unnecessary publications
    - **Version Management**: Automatically increments layer versions
    - **Manifest Backup**: Stores dependency manifests for reproducibility
    - **S3 Integration**: Uses existing S3 artifacts for layer creation

**Publication Process:**
    The module implements smart publishing that only creates new layer versions when
    dependencies have actually changed, determined by comparing local dependency
    manifests against stored versions from previous publications.
"""

import typing as T
import dataclasses
from functools import cached_property

from func_args.api import BaseFrozenModel, REQ

from ..constants import S3MetadataKeyEnum
from ..imports import S3Path, simple_aws_lambda

from .foundation import LayerManifestManager


if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_lambda import LambdaClient


@dataclasses.dataclass(frozen=True)
class LambdaLayerVersionPublisher(LayerManifestManager):
    """
    Command class for intelligent Lambda layer version publishing (Internal API).

    This class implements the layer publication workflow with dependency change detection,
    ensuring new layer versions are only created when dependencies have actually changed.
    It follows the Command Pattern established by other builder classes.

    **Not for direct use**: This is an internal command class. Use the public function
    :func:`publish_layer_version` instead.

    **Key Responsibilities:**

    - **Change Detection**: Compare local manifests with previously published versions
    - **Layer Publication**: Create new Lambda layer versions from S3 artifacts
    - **Manifest Storage**: Backup dependency manifests for future comparisons
    - **Version Management**: Handle layer version incrementation automatically

    **Publication Logic:**

    The publisher only creates new layer versions when the dependency manifest has
    changed since the last publication. This prevents unnecessary version proliferation
    and ensures layer versions represent meaningful dependency updates.
    """

    layer_name: str = dataclasses.field(default=REQ)
    lambda_client: "LambdaClient" = dataclasses.field(default=REQ)
    publish_layer_version_kwargs: dict[str, T.Any] | None = dataclasses.field(
        default=None
    )

    def run(self) -> "LayerDeployment":
        """
        Execute the complete layer publication workflow.
        """
        self.log("--- Start publish Lambda layer workflow")
        self.step_1_preflight_check()
        layer_deployment = self.step_2_publish_layer_version()
        return layer_deployment

    def step_1_preflight_check(self):
        """
        Perform read-only validation of build environment and project configuration.
        """
        self.log("--- Step 1 - Flight Check")
        self.step_1_1_ensure_layer_zip_exists()
        self.step_1_2_ensure_layer_zip_is_consistent()
        self.step_1_3_ensure_dependencies_have_changed()

    def step_2_publish_layer_version(self) -> "LayerDeployment":
        """
        Execute the layer publication workflow, creating a new Lambda layer version
        """
        self.log("--- Step 2 - Publish Lambda Layer Version")
        layer_version, layer_version_arn = self.step_2_1_run_publish_layer_version_api()
        s3path_manifest = self.step_2_2_upload_dependency_manifest(
            version=layer_version
        )
        layer_deployment = LayerDeployment(
            layer_name=self.layer_name,
            layer_version=layer_version,
            layer_version_arn=layer_version_arn,
            s3path_manifest=s3path_manifest,
        )
        return layer_deployment

    # --- step_1_preflight_check sub-steps
    def step_1_1_ensure_layer_zip_exists(self):
        """
        Verifies that the layer.zip file was successfully uploaded to S3 during
        the :mod:`aws_lambda_artifact_builder.layer.upload` phase and is available
        for Lambda layer creation. This is a prerequisite validation before
        attempting to publish a new layer version.
        """
        s3path = self.s3_layout.s3path_temp_layer_zip
        self.log(f"--- Step 1.1 - Verify layer.zip exists in S3 at {s3path.uri}...")
        if self.is_layer_zip_exists() is False:
            s3path = self.s3_layout.s3path_temp_layer_zip
            raise FileNotFoundError(
                f"Layer zip file {s3path.uri} does not exist! "
                f"Please run the upload step first to create the layer.zip in S3."
            )
        else:
            self.log("✅ Layer zip file found in S3.")

    def is_layer_zip_exists(self) -> bool:
        """
        Check if the layer zip file exists in S3 temporary storage.

        :return: True if layer.zip exists in S3, False otherwise
        """
        s3path = self.s3_layout.s3path_temp_layer_zip
        return s3path.exists(bsm=self.s3_client)

    def step_1_2_ensure_layer_zip_is_consistent(self):
        """
        Validate that the uploaded layer.zip matches the current local manifest.
        """
        self.log("--- Step 1.2 - Validate layer.zip consistency with manifest")
        if self.is_layer_zip_consistent() is False:
            path = self.path_manifest
            s3path = self.s3_layout.s3path_temp_layer_zip
            raise ValueError(
                f"Layer zip file {s3path.uri} is inconsistent with current manifest {path}! "
                f"The uploaded layer.zip corresponds to a different dependency state. "
                f"Please re-run the upload step to sync the layer.zip with current dependencies."
            )
        else:
            self.log("✅ Layer zip file is consistent with current manifest.")

    def is_layer_zip_consistent(self) -> bool:
        """
        Compares the manifest MD5 hash stored in the S3 layer.zip metadata
        with the MD5 hash of the current local manifest file. This ensures that
        the uploaded layer artifact corresponds to the current dependency state
        before creating a new layer version.

        **Consistency Issues That Can Occur:**

        - **Manifest Modified**: Local manifest file was changed after upload
        - **Wrong Upload**: A different project's layer.zip was uploaded
        - **Missing Metadata**: Upload process failed to store manifest MD5
        - **Stale Upload**: Old layer.zip from previous dependency state

        **Why This Check Matters:**

        Without this validation, you might publish a layer version that doesn't
        match your current dependencies, leading to runtime errors or unexpected
        behavior in Lambda functions that use the layer.

        :return: True if uploaded layer.zip matches current manifest, False otherwise
        """
        s3path = self.s3_layout.s3path_temp_layer_zip
        s3path.head_object(bsm=self.s3_client)
        manifest_md5 = s3path.metadata.get(
            S3MetadataKeyEnum.manifest_md5.value, "__invalid__"
        )
        return manifest_md5 == self.manifest_md5

    def step_1_3_ensure_dependencies_have_changed(self):
        """
        Check if the local dependency manifest has changed since the last publication
        This is the core intelligence that prevents unnecessary layer version creation
        """
        self.log(
            "--- Step 1.3 - Check if dependencies have changed since last publication"
        )
        has_changed = self.has_dependency_manifest_changed()
        if not has_changed:
            # Dependencies are identical to the last published version
            # Skip publication to avoid creating redundant layer versions
            raise ValueError("Dependencies unchanged since last publication - skipping")
        else:
            self.log("✅ Dependencies have changed - proceeding with publishing.")

    def has_dependency_manifest_changed(self) -> bool:
        """
        Detect if the local dependency manifest has changed from the last published layer.
        
        This method compares the current local dependency manifest (source of truth)
        against the manifest stored with the latest published layer version. If they
        are different, it indicates that dependencies have been updated and a new
        layer version should be published.
        
        **Manifest Comparison Process:**
        
        1. **Retrieve Latest Version**: Get the most recent published layer version
        2. **Locate Stored Manifest**: Find the manifest file stored with that version
        3. **Content Comparison**: Compare local manifest content with stored version
        4. **Change Detection**: Return True if contents differ (change detected)
        
        **Deterministic Requirement:**
        
        The comparison assumes that dependency manifests are deterministic and
        reproducible. This means the manifest should contain exact versions and
        hashes, not loose version constraints.
        
        **Good (Deterministic):**
        
        .. code-block:: text
        
            atomicwrites==1.4.1 ; python_version >= "3.9.dev0" and python_version < "3.10.dev0" \
            --hash=sha256:81b2c9071a49367a7f770170e5eec8cb66567cfbbc8c73d20ce5ca4a8d71cf11
        
        **Bad (Non-deterministic):**
        
        .. code-block:: text
        
            atomicwrites  # Version not pinned
        
        **Return Logic:**
        
        - **True**: Dependencies have changed, new layer version needed
        - **False**: Dependencies unchanged, can skip layer publication
        - **True**: No previous layer exists (first publication)
        - **True**: Previous manifest file not found (missing backup)
        
        :return: True if local manifest differs from latest published version,
                False if they are identical (no changes detected)
        """
        # Check if any layer version has been published previously
        # If no layer exists, we need to publish (dependencies have "changed" from nothing)
        latest_layer_version = self.latest_layer_version
        if latest_layer_version is None:
            return True  # No previous version exists, treat as changed

        # Get local manifest file and construct S3 path for the stored version
        path_manifest = self.path_manifest
        s3path_manifest = self.get_versioned_manifest(
            version=latest_layer_version.version
        )
        # Never seen a manifest for this version, treat as changed
        if s3path_manifest.exists(bsm=self.s3_client) is False:
            return True

        # Compare local manifest content with stored version
        # Read both files as text and perform exact content comparison
        local_manifest_content = path_manifest.read_text()
        stored_manifest_content = s3path_manifest.read_text(bsm=self.s3_client)

        # Return True if contents differ (change detected), False if identical
        return local_manifest_content != stored_manifest_content

    @cached_property
    def latest_layer_version(self) -> T.Union["simple_aws_lambda.LayerVersion", None]:
        return simple_aws_lambda.get_latest_layer_version(
            lambda_client=self.lambda_client,
            layer_name=self.layer_name,
        )

    # --- step_2_publish_layer_version sub-steps
    def step_2_1_run_publish_layer_version_api(self) -> tuple[int, str]:
        """
        Publish a new Lambda layer version using the zip file stored in S3.

        This method creates a new versioned Lambda layer by referencing the layer zip
        file that was previously uploaded to S3 during the upload phase. AWS Lambda
        automatically assigns the next sequential version number.

        **Layer Creation Process:**

        1. **S3 Reference**: Points Lambda service to the uploaded zip file in S3
        2. **Version Creation**: Lambda automatically increments version number
        3. **ARN Generation**: Returns the full ARN of the newly created layer version

        :param publish_layer_version_kwargs: Optional additional arguments to pass to
            the Lambda publish_layer_version API call (e.g., Description, CompatibleRuntimes)
        :return: Tuple of (layer_version_number, layer_version_arn)
        """
        self.log("--- Step 2.1 - Publish new Lambda layer version via API")
        if self.publish_layer_version_kwargs is None:
            publish_layer_version_kwargs = {}
        else:
            publish_layer_version_kwargs = self.publish_layer_version_kwargs
        s3path = self.s3_layout.s3path_temp_layer_zip
        response = self.lambda_client.publish_layer_version(
            LayerName=self.layer_name,
            Content={
                "S3Bucket": s3path.bucket,
                "S3Key": s3path.key,
            },
            **publish_layer_version_kwargs,
        )
        layer_version_arn = response["LayerVersionArn"]
        layer_version = int(layer_version_arn.split(":")[-1])
        self.log(f"Successfully published layer version: {layer_version}")
        self.log(f"Layer version ARN: {layer_version_arn}")
        return layer_version, layer_version_arn

    def step_2_2_upload_dependency_manifest(
        self,
        version: int,
    ) -> "S3Path":
        """
        Upload the dependency manifest file to S3 for the specified layer version.

        This method stores the local dependency manifest (source of truth) alongside
        the published layer version for future change detection and reproducibility.
        The stored manifest enables the system to determine if dependencies have
        changed in subsequent publication attempts.

        **Storage Strategy:**

        - **Version-Specific**: Each layer version gets its own manifest backup
        - **Content Integrity**: Uses write_bytes() to ensure proper eTag generation
        - **Plain Text**: Stored as text/plain for easy inspection and comparison

        .. important::

            Uses write_bytes() instead of upload_file() to ensure that the eTag
            is the MD5 hash of the file content, which is important for content
            integrity verification.

        :param version: The layer version number to associate the manifest with
        :return: S3Path where the manifest was stored
        """
        self.log("--- Step 2.2 - Upload dependency manifest to S3")
        path = self.path_manifest
        s3path_manifest = self.get_versioned_manifest(version=version)
        s3path_manifest.write_bytes(
            path.read_bytes(),
            content_type="text/plain",
            bsm=self.s3_client,
        )
        if self.verbose:
            self.log(f"Manifest stored at: {s3path_manifest.uri}")
            self.log(f"Console URL: {s3path_manifest.console_url}")
        return s3path_manifest


@dataclasses.dataclass(frozen=True)
class LayerDeployment(BaseFrozenModel):
    """
    Data class representing a completed layer deployment (Public API).

    This immutable data class encapsulates all the key information about a
    successfully published Lambda layer version, providing a complete record
    of the deployment for downstream operations.

    **Usage:**

    The LayerDeployment is returned by :func:`publish_layer_version` when a new
    layer version is successfully created. It contains all the identifiers and
    references needed to work with the published layer.

    **Attributes:**

    - **layer_name**: The name of the Lambda layer
    - **layer_version**: The version number assigned by AWS Lambda
    - **layer_version_arn**: The full ARN of the published layer version
    - **s3path_manifest**: S3 location of the stored dependency manifest
    """

    layer_name: str = dataclasses.field(default=REQ)
    layer_version: int = dataclasses.field(default=REQ)
    layer_version_arn: str = dataclasses.field(default=REQ)
    s3path_manifest: "S3Path" = dataclasses.field(default=REQ)
