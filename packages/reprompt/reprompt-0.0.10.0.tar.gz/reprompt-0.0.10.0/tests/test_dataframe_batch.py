"""Tests for DataFrame batch creation functionality."""

from __future__ import annotations

import unittest.mock

import pytest

from reprompt import RepromptClient
from reprompt.exceptions import RepromptAPIError
from reprompt.generated.models import AttributeSet


def test_client_gating_read_only():
    """Test that read-only client prevents batch creation."""
    # Client with allow_writes=False (default)
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=False)

    # Mock DataFrame
    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        df = pd.DataFrame([{"name": "Test Place", "full_address": "123 Main St"}])

        with pytest.raises(ValueError, match="Client is read-only; set allow_writes=True to create batches"):
            client.batches.create_from_dataframe(df, batch_name="Test Batch")

    client.close()


def test_validation_required_name():
    """Test that missing name raises RepromptAPIError with correct status code."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # DataFrame with row missing name
        df = pd.DataFrame(
            [
                {"name": "Valid Place", "full_address": "123 Main St"},
                {"full_address": "456 Oak Ave"},  # Missing name
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "Row 1" in str(exc_info.value)
        assert "missing or empty 'name'" in str(exc_info.value)

    client.close()


def test_validation_location_variants():
    """Test valid location specifications and one failing row."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # Mock successful transport.post
        with unittest.mock.patch.object(client.batches._transport, "post") as mock_post:
            mock_post.return_value = {
                "id": "batch_123",
                "batch_name": "Test Batch",
                "status": "pending",
                "jobs": {},
                "metadata": None,
            }

            # Three valid rows with different location types
            df = pd.DataFrame(
                [
                    {"name": "Place 1", "full_address": "123 Main St"},
                    {"name": "Place 2", "latitude": 40.7128, "longitude": -74.0060},
                    {
                        "name": "Place 3",
                        "street": "789 Pine St",
                        "city": "Boston",
                        "state": "MA",
                        "postal_code": "02101",
                        "country": "USA",
                    },
                ]
            )

            # Should succeed
            response = client.batches.create_from_dataframe(df, batch_name="Test Batch")
            assert response.id == "batch_123"
            assert mock_post.called

        # Test failing row with partial components
        df_invalid = pd.DataFrame(
            [
                {"name": "Valid Place", "full_address": "123 Main St"},
                {"name": "Invalid Place", "street": "456 Oak Ave"},  # Missing city, state, postal_code, country
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df_invalid, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "Row 1" in str(exc_info.value)
        assert "missing valid location" in str(exc_info.value)

    client.close()


def test_duplicate_detection_with_place_id():
    """Test duplicate place_id detection when place_id is provided."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # DataFrame with duplicate place_id
        df = pd.DataFrame(
            [
                {"place_id": "place_1", "name": "Place 1", "full_address": "123 Main St"},
                {"place_id": "place_1", "name": "Place 2", "full_address": "456 Oak Ave"},  # Duplicate
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "Duplicate place_id detected" in str(exc_info.value)
        assert "place_1" in str(exc_info.value)

    client.close()


def test_duplicate_detection_without_place_id():
    """Test duplicate detection when place_id is derived from data."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # DataFrame with rows that would generate the same derived place_id
        df = pd.DataFrame(
            [
                {"name": "Test Place", "full_address": "123 Main St"},
                {"name": "Test Place", "full_address": "123 Main St"},  # Same normalized key
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "Duplicate place_id detected" in str(exc_info.value)
        assert "appears in rows [0, 1]" in str(exc_info.value)

    client.close()


def test_attribute_selection_exclusivity():
    """Test that providing both attribute_set and attributes raises ValueError."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        df = pd.DataFrame([{"name": "Test Place", "full_address": "123 Main St"}])

        with pytest.raises(ValueError, match="Cannot specify both attribute_set and attributes"):
            client.batches.create_from_dataframe(
                df, batch_name="Test Batch", attribute_set=AttributeSet.core, attributes=["name", "address"]
            )

    client.close()


def test_post_behavior_and_mapping():
    """Test POST payload structure and response parsing."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # Mock transport.post to capture payload
        with unittest.mock.patch.object(client.batches._transport, "post") as mock_post:
            mock_post.return_value = {
                "id": "batch_456",
                "batch_name": "API Test Batch",
                "status": "pending",
                "jobs": {},
                "metadata": None,
            }

            df = pd.DataFrame(
                [
                    {"name": "Place 1", "full_address": "123 Main St"},
                    {"name": "Place 2", "latitude": 40.7128, "longitude": -74.0060},
                ]
            )

            # Call with specific parameters
            response = client.batches.create_from_dataframe(
                df, batch_name="API Test Batch", batch_id=None, enrich_now=False, attribute_set=AttributeSet.core
            )

            # Verify POST was called with correct payload
            assert mock_post.called
            call_args = mock_post.call_args
            assert call_args[0][0] == "/place_enrichment/batches"  # path

            payload = call_args[1]["json"]
            assert payload["batch_name"] == "API Test Batch"
            assert payload["kick_off_jobs_now"] is False  # enrich_now=False
            assert payload["attribute_set"] == "core"
            assert "batch_id" not in payload  # batch_id=None
            assert len(payload["jobs"]) == 2

            # Check job structure (jobs should NOT have attribute_set - it's at batch level)
            job1 = payload["jobs"][0]
            assert "place_id" in job1
            assert job1["place_id"].startswith("tmp_")  # Derived place_id
            assert job1["inputs"]["name"] == "Place 1"
            assert job1["inputs"]["full_address"] == "123 Main St"
            assert "attribute_set" not in job1  # Should be at batch level only
            assert list(job1["inputs"].keys()) == ["name", "full_address"]  # Only present fields

            job2 = payload["jobs"][1]
            assert job2["inputs"]["name"] == "Place 2"
            assert job2["inputs"]["latitude"] == 40.7128
            assert job2["inputs"]["longitude"] == -74.0060
            assert "attribute_set" not in job2  # Should be at batch level only
            assert list(job2["inputs"].keys()) == ["name", "latitude", "longitude"]  # Only present fields

            # Verify response parsing
            assert response.id == "batch_456"
            assert response.batch_name == "API Test Batch"
            assert response.status.value == "pending"

    client.close()


def test_pandas_not_available():
    """Test graceful handling when pandas is not available."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    # Mock pandas as not available
    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", False):
        with pytest.raises(ImportError, match="pandas is required"):
            client.batches.create_from_dataframe([], batch_name="Test")

    client.close()


def test_coordinate_range_validation():
    """Test that invalid coordinate ranges are caught."""
    client = RepromptClient(api_key="test-key", org_slug="test-org", allow_writes=True)

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        # DataFrame with invalid coordinates
        df = pd.DataFrame(
            [
                {"name": "Invalid Place", "latitude": 91.0, "longitude": -74.0060},  # lat > 90
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "latitude 91.0 out of range" in str(exc_info.value)

        # Test invalid longitude
        df2 = pd.DataFrame(
            [
                {"name": "Invalid Place", "latitude": 40.0, "longitude": 181.0},  # lng > 180
            ]
        )

        with pytest.raises(RepromptAPIError) as exc_info:
            client.batches.create_from_dataframe(df2, batch_name="Test Batch")

        assert exc_info.value.status_code == 400
        assert "longitude 181.0 out of range" in str(exc_info.value)

    client.close()


def test_get_statistics_empty_batch_ids():
    """Test that empty batch_ids raises ValueError."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    with pytest.raises(ValueError, match="batch_ids must be a non-empty list"):
        client.get_statistics([])

    client.close()


def test_get_statistics_pandas_not_available():
    """Test graceful handling when pandas is not available for DataFrame return."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    # Mock pandas as not available
    with unittest.mock.patch("reprompt.client.pd", None):
        with pytest.raises(ImportError, match="pandas is required to return a DataFrame"):
            client.get_statistics(["batch-123"], return_dataframe=True)

    client.close()


def test_get_statistics_missing_batches():
    """Test handling of missing batch IDs."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    # Mock the jobs API to raise 404 errors
    def mock_get_jobs_by_batch_id(batch_id, page_size=1000):
        import httpx

        response = unittest.mock.Mock()
        response.status_code = 404
        raise httpx.HTTPStatusError("Not Found", request=None, response=response)

    with unittest.mock.patch.object(client.jobs, "get_jobs_by_batch_id", side_effect=mock_get_jobs_by_batch_id):
        # Test with raise_on_missing=True (default)
        with pytest.raises(ValueError, match="None of the provided batch IDs were found"):
            client.get_statistics(["missing-batch-1", "missing-batch-2"])

        # Test with raise_on_missing=False
        result = client.get_statistics(["missing-batch-1", "missing-batch-2"], raise_on_missing=False)
        assert "error" in result
        assert "None of the provided batch IDs were found" in result["error"]

    client.close()


def test_get_statistics_attribute_shape_mismatch():
    """Test detection of attribute set mismatches between batches."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    from reprompt.generated.models import PlaceJobResult, JobMetadata, UniversalPlace, AttributeStatusEnum

    # Create mock jobs with different attribute sets
    def create_mock_job(place_id, attribute_status_map):
        return PlaceJobResult(
            place_id=place_id,
            status="completed",
            job_metadata=JobMetadata(
                attribute_status=attribute_status_map, last_enriched=None, enrichment_metadata=None, country_code="US"
            ),
            inputs=UniversalPlace(input_type="place"),
            outputs={},
            reasoning={},
            confidence_scores=None,
        )

    # Batch 1 has websites, phoneNumbers
    batch1_jobs = [
        create_mock_job("place1", {"websites": AttributeStatusEnum.RUN, "phoneNumbers": AttributeStatusEnum.RUN})
    ]

    # Batch 2 has only websites (missing phoneNumbers)
    batch2_jobs = [
        create_mock_job(
            "place2", {"websites": AttributeStatusEnum.RUN, "address": AttributeStatusEnum.RUN}  # Different attribute
        )
    ]

    def mock_get_jobs_by_batch_id(batch_id, page_size=1000):
        if batch_id == "batch1":
            return iter(batch1_jobs)
        elif batch_id == "batch2":
            return iter(batch2_jobs)
        return iter([])

    with unittest.mock.patch.object(client.jobs, "get_jobs_by_batch_id", side_effect=mock_get_jobs_by_batch_id):
        with pytest.raises(ValueError, match="Attribute set mismatch across batches"):
            client.get_statistics(["batch1", "batch2"])

    client.close()


def test_get_statistics_successful_aggregation():
    """Test successful statistics aggregation across multiple batches."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        from reprompt.generated.models import PlaceJobResult, JobMetadata, UniversalPlace, AttributeStatusEnum

        def create_mock_job(place_id, attribute_status_map, outputs_map=None):
            return PlaceJobResult(
                place_id=place_id,
                status="completed",
                job_metadata=JobMetadata(
                    attribute_status=attribute_status_map,
                    last_enriched=None,
                    enrichment_metadata=None,
                    country_code="US",
                ),
                inputs=UniversalPlace(input_type="place"),
                outputs=outputs_map or {},
                reasoning={},
                confidence_scores=None,
            )

        # Create consistent jobs across both batches
        # Note: Use correct output field names (website, phone) not attribute names (websites, phoneNumbers)
        batch1_jobs = [
            create_mock_job(
                "place1",
                {"websites": AttributeStatusEnum.RUN, "phoneNumbers": AttributeStatusEnum.RUN},
                {"website": "https://example.com", "phone": None},
            ),
            create_mock_job(
                "place2",
                {"websites": AttributeStatusEnum.NOT_RUN, "phoneNumbers": AttributeStatusEnum.RUN},
                {"website": None, "phone": "+1234567890"},
            ),
        ]

        batch2_jobs = [
            create_mock_job(
                "place3",
                {"websites": AttributeStatusEnum.RUN, "phoneNumbers": AttributeStatusEnum.ERROR},
                {"website": "", "phone": None},
            ),  # Empty string should not count as filled
            create_mock_job(
                "place4",
                {"websites": AttributeStatusEnum.RUN, "phoneNumbers": AttributeStatusEnum.RUN},
                {"website": "https://test.com", "phone": "+9876543210"},
            ),
        ]

        def mock_get_jobs_by_batch_id(batch_id, page_size=1000):
            if batch_id == "batch1":
                return iter(batch1_jobs)
            elif batch_id == "batch2":
                return iter(batch2_jobs)
            return iter([])

        with unittest.mock.patch.object(client.jobs, "get_jobs_by_batch_id", side_effect=mock_get_jobs_by_batch_id):
            # Test DataFrame return
            df = client.get_statistics(["batch1", "batch2"], return_dataframe=True)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2  # Two attributes: websites, phoneNumbers
            assert set(df["attribute"]) == {"websites", "phoneNumbers"}

            # Check websites stats: 3 RUN out of 4 total, 2 value filled out of 4 total
            websites_row = df[df["attribute"] == "websites"].iloc[0]
            assert websites_row["total_jobs"] == 4
            assert websites_row["run_count"] == 3  # 3 RUN status
            assert websites_row["run_rate"] == 0.75
            assert websites_row["value_filled"] == 2  # 2 non-empty values
            assert websites_row["value_fill_rate"] == 0.5

            # Check phoneNumbers stats: 3 RUN out of 4 total, 2 value filled out of 4 total
            phone_row = df[df["attribute"] == "phoneNumbers"].iloc[0]
            assert phone_row["total_jobs"] == 4
            assert phone_row["run_count"] == 3  # 3 RUN status
            assert phone_row["run_rate"] == 0.75
            assert phone_row["value_filled"] == 2  # 2 non-empty values
            assert phone_row["value_fill_rate"] == 0.5

            # Test dict return
            result_dict = client.get_statistics(["batch1", "batch2"], return_dataframe=False)
            assert isinstance(result_dict, dict)
            assert "websites" in result_dict
            assert "phoneNumbers" in result_dict
            assert result_dict["websites"]["total_jobs"] == 4
            assert result_dict["websites"]["run_count"] == 3

    client.close()


def test_get_statistics_exclude_not_run():
    """Test exclude_not_run parameter functionality."""
    client = RepromptClient(api_key="test-key", org_slug="test-org")

    with unittest.mock.patch("reprompt.dataframe.PANDAS_AVAILABLE", True):
        import pandas as pd

        from reprompt.generated.models import PlaceJobResult, JobMetadata, UniversalPlace, AttributeStatusEnum

        def create_mock_job(place_id, attribute_status_map):
            return PlaceJobResult(
                place_id=place_id,
                status="completed",
                job_metadata=JobMetadata(
                    attribute_status=attribute_status_map,
                    last_enriched=None,
                    enrichment_metadata=None,
                    country_code="US",
                ),
                inputs=UniversalPlace(input_type="place"),
                outputs={},
                reasoning={},
                confidence_scores=None,
            )

        # Create jobs where one attribute is always NOT_RUN
        jobs = [
            create_mock_job(
                "place1", {"websites": AttributeStatusEnum.RUN, "always_not_run": AttributeStatusEnum.NOT_RUN}
            ),
            create_mock_job(
                "place2", {"websites": AttributeStatusEnum.RUN, "always_not_run": AttributeStatusEnum.NOT_RUN}
            ),
        ]

        def mock_get_jobs_by_batch_id(batch_id, page_size=1000):
            return iter(jobs)

        with unittest.mock.patch.object(client.jobs, "get_jobs_by_batch_id", side_effect=mock_get_jobs_by_batch_id):
            # Without exclude_not_run
            df_with_not_run = client.get_statistics(["batch1"], exclude_not_run=False)
            assert len(df_with_not_run) == 2  # Both attributes included
            assert set(df_with_not_run["attribute"]) == {"websites", "always_not_run"}

            # With exclude_not_run
            df_without_not_run = client.get_statistics(["batch1"], exclude_not_run=True)
            assert len(df_without_not_run) == 1  # Only websites included
            assert df_without_not_run["attribute"].iloc[0] == "websites"

    client.close()
