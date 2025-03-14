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

from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from src.utils.retrieve_model_details_info_util import retrieve_model_details_info
from httpx import Response, AsyncClient, Request
import pytest
import httpx
import json
from src.models.env.env_config_DTO import EnvConfigDTO

@pytest.fixture(name="httpx_client_mock", scope="function")
def fixture_httpx_client(mocker):
    httpx_client_mock = mocker.Mock(spec=AsyncClient)
    return httpx_client_mock

@pytest.mark.asyncio
async def test_retrieve_model_details_info_success(httpx_client_mock):
    model_id = "valid_model_id"
    request = Request("GET", f"http://testserver/model/exists?model_id={model_id}")
    response = Response(200, json={"result": True, "data": {"model_details": '{"key": "value"}'}}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    result = await retrieve_model_details_info(httpx_client_mock, model_id, "test_transaction_id")
    assert result == {"model_details": '{"key": "value"}'}

@pytest.mark.asyncio
async def test_retrieve_model_details_info_not_found(httpx_client_mock):
    model_id = "invalid_model_id"
    request = Request("GET", f"http://testserver/model/exists?model_id={model_id}")
    response = Response(200, json={"result": False}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_model_details_info(httpx_client_mock, model_id, "test_transaction_id")
    assert exc_info.value.status_code == 404
    assert "Model not found in the project admin service" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_model_details_info_http_error(httpx_client_mock):
    model_id = "http_error_model_id"
    request = Request("GET", f"http://testserver/model/exists?model_id={model_id}")
    response = Response(500, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_model_details_info(httpx_client_mock, model_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An error occurred while getting the model details" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_model_details_info_request_error(httpx_client_mock, mocker):
    model_id = "request_error_model_id"
    httpx_client_mock.get = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("GET", f"http://testserver/model/exists?model_id={model_id}")))

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_model_details_info(httpx_client_mock, model_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An request error occurred while getting the model details" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_model_details_info_unexpected_error(httpx_client_mock, mocker):
    model_id = "unexpected_error_model_id"
    httpx_client_mock.get = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_model_details_info(httpx_client_mock, model_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An unexpected error occurred while getting the model details" in str(exc_info.value.detail)
