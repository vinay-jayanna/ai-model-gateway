# Copyright (c) 2024 Vipas.AI
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of a proprietary license which prohibits
# redistribution and use in any form, without the express prior written consent
# of Vipas.AI.
#
# This code is proprietary to Vipas.AI and is protected by copyright and
# other intellectual property laws. You may not modify, reproduce, perform,
# display, create derivative works from, repurpose, or distribute this code or any portion of it
# without the express prior written permission of Vipas.AI.
#
# For more information, contact Vipas.AI at legal@vipas.ai

import pytest
import httpx
from fastapi import HTTPException
from httpx import Response, Request, AsyncClient
from src.utils.retrieve_deployment_info_util import retrieve_deployment_info_for_model_and_related_transformer
from unittest.mock import AsyncMock

# Mock fixture for httpx client
@pytest.fixture(name="httpx_client_mock", scope="function")
def fixture_httpx_client(mocker):
    httpx_client_mock = mocker.Mock(spec=AsyncClient)
    return httpx_client_mock

# Test for successful retrieval of deployment info
@pytest.mark.asyncio
async def test_retrieve_deployment_info_for_model_and_related_transformer_success(httpx_client_mock):
    request = Request("GET", "http://testserver/deploy/model/transformer/info?model_id=model1")
    response = Response(200, json={"deployment_info": "info"}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    result = await retrieve_deployment_info_for_model_and_related_transformer(
        httpx_client_mock, "model1", "test_transaction_id"
    )
    assert result == {"deployment_info": "info"}

# Test for HTTP status error in retrieve function
@pytest.mark.asyncio
async def test_retrieve_deployment_info_for_model_and_related_transformer_http_error(httpx_client_mock):
    request = Request("GET", "http://testserver/deploy/model/transformer/info?model_id=model1")
    response = Response(500, request=request, text="An error occurred while getting the deployment details for the model")
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as excinfo:
        await retrieve_deployment_info_for_model_and_related_transformer(
            httpx_client_mock, "model1", "test_transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An error occurred while getting the deployment details for the model" in excinfo.value.detail

# Test for request error in retrieve function
@pytest.mark.asyncio
async def test_retrieve_deployment_info_for_model_and_related_transformer_request_error(httpx_client_mock, mocker):
    httpx_client_mock.get = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("GET", "http://testserver/deploy/model/transformer/info?model_id=model1")))

    with pytest.raises(HTTPException) as excinfo:
        await retrieve_deployment_info_for_model_and_related_transformer(
            httpx_client_mock, "model1", "test_transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An request error occurred while getting the deployment details for the model" in excinfo.value.detail

# Test for unexpected error in retrieve function
@pytest.mark.asyncio
async def test_retrieve_deployment_info_for_model_and_related_transformer_unexpected_error(httpx_client_mock, mocker):
    httpx_client_mock.get = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as excinfo:
        await retrieve_deployment_info_for_model_and_related_transformer(
            httpx_client_mock, "model1", "test_transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An unexpected error occurred while getting the deployment details for the model" in excinfo.value.detail
