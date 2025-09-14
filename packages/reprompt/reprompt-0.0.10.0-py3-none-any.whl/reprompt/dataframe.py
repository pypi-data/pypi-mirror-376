"""DataFrame helpers and CSV upload utilities for Reprompt."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import List, TYPE_CHECKING, Any

from .exceptions import RepromptAPIError
from .generated.models import PlaceJobResult, BatchJob

if TYPE_CHECKING:
    import pandas as pd

    PANDAS_AVAILABLE = True
else:
    try:
        import pandas as pd

        PANDAS_AVAILABLE = True
    except ImportError:
        pd = None
        PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


# DataFrame serialization helpers
def batches_to_dataframe(batches: List[BatchJob]) -> Any:
    """
    Convert a list of BatchJob objects to a pandas DataFrame.

    Args:
        batches: List of BatchJob objects from the API

    Returns:
        pd.DataFrame with flattened batch data

    Raises:
        ImportError: If pandas is not installed
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame conversion. Install with: pip install pandas")

    if not batches:
        return pd.DataFrame()

    # Convert BatchJob objects to flattened dictionaries
    data = []
    for batch in batches:
        # Work directly with the BatchJob model
        flattened = _flatten_batch_job(batch)
        data.append(flattened)

    return pd.DataFrame(data)


def jobs_to_dataframe(
    jobs: List[PlaceJobResult],
    include_inputs: bool = True,
    include_reasoning: bool = True,
    include_confidence: bool = True,
    include_batch: bool = True,
    include_not_run: bool = False,
) -> Any:
    """
    Convert a list of PlaceJobResult objects to a pandas DataFrame with flattened structure.

    Args:
        jobs: List of PlaceJobResult objects from the API
        include_inputs: Include input fields (default: True)
        include_reasoning: Include reasoning fields (default: True)
        include_confidence: Include confidence score fields (default: True)
        include_batch: Include batch_id field (default: True)
        include_not_run: Include columns with all None/NaN values (default: False)

    Returns:
        pd.DataFrame with flattened job data

    Raises:
        ImportError: If pandas is not installed
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame conversion. Install with: pip install pandas")

    if not jobs:
        return pd.DataFrame()

    # Convert PlaceJobResult objects to flattened dictionaries
    data = []
    for job in jobs:
        # We know job is a PlaceJobResult, work with it directly
        flattened = _flatten_place_job_result(
            job,
            include_inputs=include_inputs,
            include_reasoning=include_reasoning,
            include_confidence=include_confidence,
            include_batch=include_batch,
        )
        data.append(flattened)

    df = pd.DataFrame(data)

    # Apply include_not_run filtering if requested
    if not include_not_run:
        df = _remove_null_columns(df)

    return df


def _remove_null_columns(df: Any) -> Any:
    """Remove columns that contain only None/NaN values."""
    if df.empty:
        return df

    # Find columns that are all null (None or NaN)
    null_columns = []
    for col in df.columns:
        if df[col].isnull().all():
            null_columns.append(col)

    # Drop null columns
    if null_columns:
        df = df.drop(columns=null_columns)

    return df


def _flatten_batch_job(batch: BatchJob) -> dict:
    """Flatten BatchJob model structure for DataFrame format."""
    flattened = {}

    # Only include batch_id and batch_name
    flattened["batch_id"] = batch.id
    flattened["batch_name"] = batch.batch_name

    return flattened


def _flatten_place_job_result(  # pylint: disable=too-many-locals,too-many-branches
    job: PlaceJobResult,
    include_inputs: bool = True,
    include_reasoning: bool = True,
    include_confidence: bool = True,
    include_batch: bool = True,  # pylint: disable=unused-argument
) -> dict:
    """Flatten PlaceJobResult structure for DataFrame format with selective field inclusion."""

    # Create a sentinel for unset values
    class UNSET:  # pylint: disable=too-few-public-methods
        pass

    flattened = {}

    # Basic job info - directly access typed attributes
    flattened["place_id"] = job.place_id
    flattened["status"] = job.status

    # Handle inputs with dot notation prefix
    if include_inputs and job.inputs:
        # Only include the core fields, ignore additional/extra fields
        if hasattr(job.inputs, "model_dump"):
            inputs_dict = job.inputs.model_dump(exclude_unset=True, mode="json")
            # Filter out standard UniversalPlace fields only
            core_fields = {"type", "input_type", "name", "full_address", "latitude", "longitude"}
            for key, value in inputs_dict.items():
                if key in core_fields:
                    flattened[f"inputs.{key}"] = value
        else:
            # Fallback for dict inputs
            inputs_dict = job.inputs if isinstance(job.inputs, dict) else {}
            for key, value in inputs_dict.items():
                flattened[f"inputs.{key}"] = value

    # Handle outputs with dot notation prefix
    # Handle outputs - it's a dict in the new models
    outputs = job.outputs if isinstance(job.outputs, dict) else {}
    if outputs:
        for key, value in outputs.items():
            # For nested dicts, keep the nested structure but with dot prefix
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flattened[f"outputs.{key}_{sub_key}"] = (
                        sub_value if not isinstance(sub_value, (dict, list)) else json.dumps(sub_value)
                    )
            elif isinstance(value, list):
                flattened[f"outputs.{key}"] = json.dumps(value)
            else:
                flattened[f"outputs.{key}"] = value

    # Handle reasoning with dot notation prefix
    if include_reasoning and job.reasoning:
        reasoning_dict = job.reasoning if isinstance(job.reasoning, dict) else {}
        if "additional_properties" in reasoning_dict:
            reasoning_dict = reasoning_dict["additional_properties"]
        # Add reasoning for each field with dot notation
        for key, value in reasoning_dict.items():
            flattened[f"reasoning.{key}"] = value if not isinstance(value, (dict, list)) else json.dumps(value)

    # Handle confidence_scores with dot notation prefix
    if include_confidence and job.confidence_scores is not None and not isinstance(job.confidence_scores, type(UNSET)):
        if hasattr(job.confidence_scores, "model_dump"):
            confidence_dict = job.confidence_scores.model_dump(mode="json")
        else:
            confidence_dict = {}
        if "additional_properties" in confidence_dict:
            confidence_dict = confidence_dict["additional_properties"]
        # Add confidence for each field with dot notation
        for key, value in confidence_dict.items():
            flattened[f"confidence.{key}"] = value if not isinstance(value, (dict, list)) else json.dumps(value)

    # Handle job_metadata
    if job.job_metadata:
        if hasattr(job.job_metadata, "model_dump"):
            # Use model_dump with mode='json' to handle datetime serialization
            metadata_dict = job.job_metadata.model_dump(mode="json")
        else:
            metadata_dict = {}
        flattened["job_metadata"] = json.dumps(metadata_dict)

    return flattened


def _validate_dataframe(df: Any) -> None:
    """Validate the pandas DataFrame."""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame validation. Install with: pip install pandas")

    if df.empty:
        raise ValueError("DataFrame is empty")

    if df.columns.empty:
        raise ValueError("DataFrame has no columns")

    REQUIRED_COLUMNS = {
        "place_id",
        "name",
        "full_address",
        "latitude",
        "longitude",
    }

    # Check for missing required columns
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"DataFrame is missing required columns: {', '.join(sorted(missing_columns))}")

    # Check for required columns that are all null
    null_columns = [col for col in REQUIRED_COLUMNS if df[col].isnull().all()]
    if null_columns:
        raise ValueError(f"DataFrame has all null values for required columns: {', '.join(sorted(null_columns))}")

    # Validate latitude and longitude columns
    for column, min_val, max_val in [("latitude", -90, 90), ("longitude", -180, 180)]:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"DataFrame has non-numeric values for required column: {column}")

        col_min, col_max = df[column].min(), df[column].max()
        if col_min < min_val or col_max > max_val:
            range_desc = "latitude" if column == "latitude" else "longitude"
            raise ValueError(
                f"DataFrame has values outside the valid {range_desc} range "
                f"({min_val} to {max_val}) for column: {column}"
            )


def _normalize_columns(df: Any) -> Any:
    """
    Normalize column names and map synonyms to standard names.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with normalized column names
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame normalization. Install with: pip install pandas")

    # Make a copy to avoid modifying the original
    df = df.copy()

    # Lowercase all column names
    df.columns = df.columns.str.lower()

    # Map synonyms to standard names
    column_mapping = {
        "lat": "latitude",
        "lon": "longitude",
        "lng": "longitude",
        "zip": "postal_code",
        "postalcode": "postal_code",
    }

    # Apply mapping
    df.columns = [column_mapping.get(col, col) for col in df.columns]

    return df


def _trim_and_clean(df: Any) -> Any:
    """
    Clean and trim string values in the DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with cleaned string values
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame cleaning. Install with: pip install pandas")

    # Make a copy to avoid modifying the original
    df = df.copy()

    # Strip whitespace from string columns and convert empty strings to None
    for col in df.columns:
        if df[col].dtype == "object":  # String columns
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("", None)
            df[col] = df[col].replace("nan", None)

    return df


def _derive_place_id(row: Any) -> str:
    """
    Derive a deterministic place_id for a row if not already present.

    Args:
        row: DataFrame row

    Returns:
        place_id string
    """
    # If place_id already exists, return it
    if "place_id" in row.index and pd.notna(row["place_id"]) and str(row["place_id"]).strip():
        return str(row["place_id"]).strip()

    # Build normalized key for hashing
    name = str(row.get("name", "")).lower().strip()

    # Prefer full_address
    if "full_address" in row.index and pd.notna(row["full_address"]) and str(row["full_address"]).strip():
        full_address = str(row["full_address"]).lower().strip()
        key = f"{name}|{full_address}"
    # Then lat/lng
    elif (
        "latitude" in row.index
        and "longitude" in row.index
        and pd.notna(row["latitude"])
        and pd.notna(row["longitude"])
    ):
        lat = str(row["latitude"]).strip()
        lng = str(row["longitude"]).strip()
        key = f"{name}|{lat}|{lng}"
    # Finally address components
    else:
        components = []
        for field in ["street", "city", "state", "postal_code", "country"]:
            if field in row.index and pd.notna(row[field]) and str(row[field]).strip():
                components.append(str(row[field]).lower().strip())

        if components:
            address_part = "|".join(components)
            key = f"{name}|{address_part}"
        else:
            # Fallback to just name
            key = name

    # Generate deterministic hash
    hash_obj = hashlib.sha1(key.encode("utf-8"))
    return f"tmp_{hash_obj.hexdigest()[:12]}"


def _validate_dataframe_rules(df: Any) -> None:
    """
    Validate DataFrame against business rules.

    Args:
        df: Input DataFrame

    Raises:
        RepromptAPIError: If validation fails
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame validation. Install with: pip install pandas")

    if df.empty:
        raise RepromptAPIError("DataFrame is empty", status_code=400)

    errors = []

    # Check each row for required fields and location specification
    for idx, row in df.iterrows():
        row_errors = []

        # Check for required name
        if "name" not in row.index or pd.isna(row["name"]) or not str(row["name"]).strip():
            row_errors.append("missing or empty 'name'")

        # Check for valid location specification
        has_full_address = (
            "full_address" in row.index and pd.notna(row["full_address"]) and str(row["full_address"]).strip()
        )

        has_coordinates = (
            "latitude" in row.index
            and "longitude" in row.index
            and pd.notna(row["latitude"])
            and pd.notna(row["longitude"])
        )

        # Check for valid coordinate ranges if coordinates are present
        if has_coordinates:
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])
                if not (-90 <= lat <= 90):
                    row_errors.append(f"latitude {lat} out of range (-90 to 90)")
                if not (-180 <= lng <= 180):
                    row_errors.append(f"longitude {lng} out of range (-180 to 180)")
            except (ValueError, TypeError):
                has_coordinates = False
                row_errors.append("invalid latitude/longitude values")

        # Check for address components
        address_components = ["street", "city", "state", "postal_code", "country"]
        has_address_components = all(
            col in row.index and pd.notna(row[col]) and str(row[col]).strip() for col in address_components
        )

        # Must have at least one valid location specification
        if not (has_full_address or has_coordinates or has_address_components):
            location_msg = (
                "missing valid location: need either 'full_address', "
                "both 'latitude' and 'longitude', or all address components "
                "('street', 'city', 'state', 'postal_code', 'country')"
            )
            row_errors.append(location_msg)

        if row_errors:
            errors.append(f"Row {idx}: {'; '.join(row_errors)}")

    # Check for duplicate place_ids
    df_with_ids = df.copy()
    df_with_ids["_derived_place_id"] = df_with_ids.apply(_derive_place_id, axis=1)

    duplicates = df_with_ids["_derived_place_id"].duplicated()
    if duplicates.any():
        duplicate_ids = df_with_ids[duplicates]["_derived_place_id"].unique()
        duplicate_rows = []
        for dup_id in duplicate_ids[:5]:  # Limit to first 5 duplicates
            rows = df_with_ids[df_with_ids["_derived_place_id"] == dup_id].index.tolist()
            duplicate_rows.append(f"place_id '{dup_id}' appears in rows {rows}")

        errors.append(f"Duplicate place_id detected: {'; '.join(duplicate_rows)}")

    # If we have errors, raise them (limit to first 10 for readability)
    if errors:
        error_summary = "; ".join(errors[:10])
        if len(errors) > 10:
            error_summary += f" (and {len(errors) - 10} more errors)"
        raise RepromptAPIError(f"DataFrame validation failed: {error_summary}", status_code=400)


def prepare_places_dataframe(df: Any) -> Any:
    """
    Prepare and validate a DataFrame for place batch creation.

    This function normalizes column names, cleans data, validates business rules,
    and ensures each row has a place_id.

    Args:
        df: Input pandas DataFrame

    Returns:
        Normalized and validated DataFrame with guaranteed place_id column

    Raises:
        ImportError: If pandas is not installed
        RepromptAPIError: If validation fails
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DataFrame preparation. Install with: pip install pandas")

    # Apply transformations in sequence
    df = _normalize_columns(df)
    df = _trim_and_clean(df)

    # Validate business rules
    _validate_dataframe_rules(df)

    # Ensure place_id is present for all rows
    df["place_id"] = df.apply(_derive_place_id, axis=1)

    return df
