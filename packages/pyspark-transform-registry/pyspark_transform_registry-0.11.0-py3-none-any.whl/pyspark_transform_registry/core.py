"""
Simplified PySpark Transform Registry Core Module

This module provides a clean, simple interface for registering and loading
PySpark transform functions using MLflow's model registry.
"""

import importlib.util
import logging
import tempfile
import subprocess
import sys
from pathlib import Path
import os
from collections.abc import Callable
from typing import Any, Optional, Union

import mlflow
import mlflow.pyfunc
from mlflow.models import ModelSignature
from mlflow.models.model import ModelInfo
from mlflow.types.schema import ColSpec, Schema

from .model_wrapper import PySparkTransformModel
from .helpers import _filter_requirements

# Configure logger for this module
logger = logging.getLogger(__name__)


def register_transform(
    func: Optional[Callable] = None,
    *,
    name: str,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[dict[str, Any]] = None,
    infer_schema: bool = False,
    infer_requirements: bool = False,
    extra_pip_requirements: Optional[list[str]] = None,
) -> ModelInfo:
    """
    Register a PySpark transform function in MLflow's model registry.

    Supports two modes:
    1. Direct function registration: pass the function directly
    2. File-based registration: load function from Python file

    Args:
        func: The function to register (for direct registration)
        name: Model name for registry (supports 3-part naming: catalog.schema.table)
        file_path: Path to Python file containing the function (for file-based registration)
        function_name: Name of function to extract from file (required for file-based)
        description: Model description
        tags: Tags to attach to the registered model
        infer_schema: Whether to automatically infer schema constraints using static analysis
        infer_requirements: Whether to automatically infer pip requirements using static analysis
        extra_pip_requirements: Additional pip requirements beyond auto-detected ones

    Returns:
        ModelInfo: The logged model with a transform_uri attribute

    Note: The logged model has a transform_uri attribute that can be used to load the function. This exchanges the models:/ prefix for transforms:/ prefix,
          however both prefixes are supported. The transforms:/ prefix is only used for clarity.

    Examples:
        # Direct function registration
        >>> def my_transform(df: DataFrame) -> DataFrame:
        ...     return df.select("*")
        >>> register_transform(my_transform, name="my_catalog.my_schema.my_transform")

        # Multi-parameter function registration
        >>> def filter_transform(df: DataFrame, min_value: int = 0) -> DataFrame:
        ...     return df.filter(df.value >= min_value)
        >>> register_transform(
        ...     filter_transform,
        ...     name="my_catalog.my_schema.filter_transform",
        ... )

        # File-based registration
        >>> register_transform(
        ...     file_path="transforms/my_transform.py",
        ...     function_name="my_transform",
        ...     name="my_catalog.my_schema.my_transform"
        ... )

    """
    # Validate input arguments
    if func is None and file_path is None:
        raise ValueError("Either 'func' or 'file_path' must be provided")

    if func is not None and file_path is not None:
        raise ValueError("Cannot specify both 'func' and 'file_path'")

    if file_path is not None and function_name is None:
        raise ValueError("'function_name' is required when using 'file_path'")

    # Load function from file if needed
    if file_path is not None:
        func = _load_transform_from_file(file_path, function_name)

    # Create model wrapper
    model = PySparkTransformModel(func)

    # Prepare MLflow logging parameters
    log_params = {
        "python_model": model,
        "registered_model_name": name,
        "infer_code_paths": True,  # Auto-detect Python modules
        "extra_pip_requirements": extra_pip_requirements,
        "tags": tags or {},
    }

    # Add description as metadata
    if description:
        log_params["tags"]["description"] = description

    log_params["tags"]["model_type"] = "transform"

    # Add function metadata
    _func_name = function_name if function_name else func.__name__
    log_params["tags"]["function_name"] = _func_name
    if func.__doc__:
        log_params["tags"]["docstring"] = func.__doc__

    # Generate a dummy signature for MLFlow as our actual signature is not supported by MLFlow
    dummy_signature = generate_dummy_signature()
    log_params["signature"] = dummy_signature

    logged_model = _log_model(name=_func_name, **log_params)
    version = logged_model.registered_model_version
    transform_uri = f"transforms:/{name}/{version}"
    logged_model.transform_uri = transform_uri
    print(f"Model {_func_name} registered with URI {transform_uri}")
    return logged_model


register_function = register_transform


def _parse_transform_uri(uri: str) -> tuple[str, str]:
    """
    Parse a transform URI into a name and version.

    Expects the URI to be in the format of transforms:/name/version or models:/name/version.

    Args:
        uri: URI of the transform

    Returns:
        tuple[str, str]: Name and version of the transform
    """
    # Remove the transforms:/ or models:/ prefix
    parts = uri.split(":/")[-1]
    name, version = parts.split("/")
    return name, version


def load_transform_uri(
    uri: str,
    validate_input: bool = False,
    strict_validation: bool = False,
) -> Callable:
    """
    Load a function from a URI.

    Args:
        uri: URI of the model to load
        validate_input: Whether to validate input DataFrames against stored schema constraints
        strict_validation: Whether to use strict validation mode

    Returns:
        Callable: The loaded transform function expecting **kwargs

    Example:
        >>> transform =load_transform_uri("transforms:/my_catalog.my_schema.my_transform/1")
        >>> transform =load_transform_uri("models:/my_catalog.my_schema.my_transform/1")
    """
    name, version = _parse_transform_uri(uri)
    return load_transform(
        name,
        version,
        validate_input=validate_input,
        strict_validation=strict_validation,
    )


load_function_uri = load_transform_uri


def load_transform(
    name: str,
    version: Union[int, str],
    validate_input: bool = False,  # noqa - Keep this for backwards compatibility
    strict_validation: bool = False,  # noqa - Keep this for backwards compatibility
) -> Callable:
    """
    Load a previously registered PySpark transform function with optional validation.

    Args:
        name: Model name in registry (supports 3-part naming: catalog.schema.table)
        version: Model version to load (required)

    Returns:
        Callable: The loaded transform function expecting **kwargs

        The returned function also has additional methods:
        - transform.get_source(): Returns the source code of the original function
        - transform.get_original_function(): Returns the unwrapped original function

    Examples:
        # Load specific version with validation
        >>> transform = load_transform("my_catalog.my_schema.my_transform", version=1)

        # Use with single parameter
        >>> result = transform(df=df)

        # Use with multiple parameters
        >>> result = transform(df=df, min_value=10, threshold=0.5)

        # Inspect the original source code
        >>> print(transform.get_source())

        # Get the original function for advanced inspection
        >>> original_func = transform.get_original_function()
        >>> import inspect
        >>> print(inspect.signature(original_func))
    """
    # Build model URI with explicit version
    model_uri = f"models:/{name}/{version}"

    # Load the model
    loaded_model = mlflow.pyfunc.load_model(model_uri)

    # Get the original transform function directly from the model wrapper
    # We are bypassing MLflow's predict() method which won't handle **kwargs properly
    original_func = loaded_model._model_impl.python_model.get_transform_function()

    # Create a wrapper function that handles both single and multi-parameter calls
    def transform_wrapper(*args, **kwargs):
        """
        Wrapper function that supports keyword arguments.

        Args:
            **kwargs: Parameters for the original function

        Returns:
            Transformed DataFrame
        """
        return original_func(*args, **kwargs)

    # Add methods to access the original function and its source
    def get_source():
        """
        Get the source code of the original transform function.

        Returns:
            str: Source code of the original function
        """

        return loaded_model._model_impl.python_model.get_function_source()

    def get_original_function():
        """
        Get the original transform function (unwrapped).

        Returns:
            Callable: The original transform function
        """
        return original_func

    # Attach methods to the wrapper function
    transform_wrapper.get_source = get_source
    transform_wrapper.get_original_function = get_original_function

    return transform_wrapper


load_function = load_transform


def _load_transform_from_file(file_path: str, function_name: str) -> Callable:
    """
    Load a function from a Python file.

    Args:
        file_path: Path to the Python file
        function_name: Name of the function to extract

    Returns:
        The loaded function
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load the module
    spec = importlib.util.spec_from_file_location("transform_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the function
    if not hasattr(module, function_name):
        raise AttributeError(f"Function '{function_name}' not found in {file_path}")

    func = getattr(module, function_name)

    if not callable(func):
        raise TypeError(f"'{function_name}' is not a function")

    return func


def get_latest_transform_version(name: str) -> str:
    """
    Get the latest version of a transform in the registry.

    Args:
        name: Model name (registered_model_name) in registry

    Returns:
        Latest version of the transform
    """
    filter_string = f"name = '{name}'"
    model_versions = mlflow.search_model_versions(
        filter_string=filter_string,
    )
    if not model_versions:
        raise ValueError(f"No versions found for model {name}")
    latest_version = max(model_versions, key=lambda x: int(x.version))
    return str(latest_version.version)


get_latest_function_version = get_latest_transform_version


def get_transforms(
    search_string: Optional[str] = None,
    tags: str = "tags.model_type = 'transform'",
) -> list[ModelInfo]:
    """
    Get all transforms from the registry.

    Args:
        search_string: Filter string to search for models
        tags: Tags to search for models

    Returns:
        list[ModelInfo]: List of models
    """
    if search_string:
        filter_string = search_string + " and " + tags
    else:
        filter_string = tags
    return mlflow.search_model_versions(filter_string=filter_string)


def generate_dummy_signature() -> ModelSignature:
    """
    Generate a dummy signature for a transform.

    Returns:
        ModelSignature: A dummy signature
    """
    input_schema = Schema([ColSpec("string", "any", required=False)])
    output_schema = Schema([ColSpec("string", "any")])
    return ModelSignature(inputs=input_schema, outputs=output_schema)


def _log_model(name: str, **log_params):
    """
    Log a model to MLflow.

    Args:
        name: Model name
        **log_params: Additional parameters to pass to mlflow.pyfunc.log_model

    Returns:
        ModelInfo: The logged model
    """
    try:
        active_run = mlflow.active_run()
        if active_run is not None:
            with mlflow.start_run(nested=True):
                logged_model = _log_model_mlflow(name=name, **log_params)
        else:
            with mlflow.start_run():
                logged_model = _log_model_mlflow(name=name, **log_params)
    except Exception:
        with mlflow.start_run(nested=True):
            logged_model = _log_model_mlflow(name=name, **log_params)

    return logged_model


def _log_model_mlflow(name: str, **log_params):
    """
    Log a model to MLflow.

    Args:
        name: Model name
        **log_params: Additional parameters to pass to mlflow.pyfunc.log_model

    Returns:
        ModelInfo: The logged model
    """
    for tag_key, tag_value in log_params["tags"].items():
        mlflow.set_tag(tag_key, tag_value)

    return mlflow.pyfunc.log_model(name=name, **log_params)


def install_transform_requirements(
    model_uri: str,
    exclude_packages: list[str] = [
        "mlflow",
        "pyspark",
        "pyspark-transform-registry",
    ],
    index_url: Optional[str] = None,
) -> None:
    """
    Installs the requirements for a transform by transform_uri/model_uri, excluding any 'mlflow', 'pyspark', or 'pyspark-transform-registry' dependency.

    If you want to exclude specific packages, you can pass them in the exclude_packages list.
    Default packages to exclude are mlflow, pyspark, and pyspark-transform-registry.

    Args:
        transform_uri: The Pyspark Tranform Registry / MLflow model URI containing the model.
    """
    name, version = _parse_transform_uri(model_uri)
    print(f"Installing model requirements for {model_uri}")
    requirements_path = mlflow.pyfunc.get_model_dependencies(
        f"models:/{name}/{version}"
    )
    filtered = _filter_requirements(requirements_path, exclude_packages)

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_req:
        temp_req.writelines(filtered)
        temp_req_path = temp_req.name
    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        temp_req_path,
        "--progress-bar",
        "off",
    ]
    if index_url:
        args.append("--index-url")
        args.append(index_url)
    try:
        subprocess.run(
            args,
            check=True,
        )
    finally:
        # We can't use the context manager because we need to delete the file after the
        # subprocess has finished but need to make sure it is accessible to other processes.
        Path(temp_req_path).unlink(missing_ok=True)
