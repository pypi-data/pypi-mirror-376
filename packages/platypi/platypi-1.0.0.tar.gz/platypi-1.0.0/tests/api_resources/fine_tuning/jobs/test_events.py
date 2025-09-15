# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from platypi import Platypi, AsyncPlatypi
from tests.utils import assert_matches_type
from platypi.types.fine_tuning.jobs import EventListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvents:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Platypi) -> None:
        event = client.fine_tuning.jobs.events.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Platypi) -> None:
        event = client.fine_tuning.jobs.events.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
            after="after",
            limit=0,
        )
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Platypi) -> None:
        response = client.fine_tuning.jobs.events.with_raw_response.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Platypi) -> None:
        with client.fine_tuning.jobs.events.with_streaming_response.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(EventListResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Platypi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `fine_tuning_job_id` but received ''"):
            client.fine_tuning.jobs.events.with_raw_response.list(
                fine_tuning_job_id="",
            )


class TestAsyncEvents:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncPlatypi) -> None:
        event = await async_client.fine_tuning.jobs.events.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPlatypi) -> None:
        event = await async_client.fine_tuning.jobs.events.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
            after="after",
            limit=0,
        )
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPlatypi) -> None:
        response = await async_client.fine_tuning.jobs.events.with_raw_response.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(EventListResponse, event, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPlatypi) -> None:
        async with async_client.fine_tuning.jobs.events.with_streaming_response.list(
            fine_tuning_job_id="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(EventListResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncPlatypi) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `fine_tuning_job_id` but received ''"):
            await async_client.fine_tuning.jobs.events.with_raw_response.list(
                fine_tuning_job_id="",
            )
