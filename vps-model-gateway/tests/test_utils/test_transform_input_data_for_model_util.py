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
from fastapi import HTTPException
from httpx import Response, Request, AsyncClient
from src.utils.transform_input_data_for_model_util import check_pre_or_post_transform_input_data_for_model, pre_or_post_transform_input_data_for_model
from unittest.mock import AsyncMock, call
import httpx

# Mock fixture for httpx client
@pytest.fixture(name="httpx_client_mock", scope="function")
def fixture_httpx_client(mocker):
    httpx_client_mock = mocker.Mock(spec=AsyncClient)
    return httpx_client_mock

# Test for successful check if transform is required
@pytest.mark.asyncio
async def test_check_pre_or_post_transform_input_data_for_model_success(httpx_client_mock):
    request = Request("GET", "http://testserver/check_transform")
    response = Response(200, json={"result": True}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    result = await check_pre_or_post_transform_input_data_for_model(
        httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, "transaction_id"
    )
    assert result == {"result": True}

# Test for HTTP status error in check function
@pytest.mark.asyncio
async def test_check_pre_or_post_transform_input_data_for_model_http_error(httpx_client_mock, mocker):
    request = Request("GET", "http://testserver/check_transform")
    response = Response(500, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as excinfo:
        await check_pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An error occurred while checking if a pre transform is required for the model" in excinfo.value.detail

# Test for request error in check function
@pytest.mark.asyncio
async def test_check_pre_or_post_transform_input_data_for_model_request_error(httpx_client_mock, mocker):
    httpx_client_mock.get = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("GET", "http://testserver/check_transform")))

    with pytest.raises(HTTPException) as excinfo:
        await check_pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An request error occurred while checking if a pre transform is required for the model" in excinfo.value.detail

# Test for unexpected error in check function
@pytest.mark.asyncio
async def test_check_pre_or_post_transform_input_data_for_model_unexpected_error(httpx_client_mock, mocker):
    httpx_client_mock.get = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as excinfo:
        await check_pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An unexpected error occurred while checking if a pre transform is required for the model" in excinfo.value.detail

# Test for successful input data transformation
@pytest.mark.asyncio
async def test_pre_or_post_transform_input_data_for_model_success(httpx_client_mock):
    request = Request("POST", "http://testserver/transform")
    response = Response(200, json={"transformed_data": "data"}, request=request)
    httpx_client_mock.post = AsyncMock(return_value=response)

    result = await pre_or_post_transform_input_data_for_model(
        httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, {"input": "data"}, "transaction_id"
    )
    assert result == {"transformed_data": "data"}

# Test for HTTP status error in transform function
@pytest.mark.asyncio
async def test_pre_or_post_transform_input_data_for_model_http_error(httpx_client_mock, mocker):
    request = Request("POST", "http://testserver/transform")
    response = Response(500, request=request)
    httpx_client_mock.post = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as excinfo:
        await pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, {"input": "data"}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An error occurred while transforming the input data" in excinfo.value.detail

# Test for request error in transform function
@pytest.mark.asyncio
async def test_pre_or_post_transform_input_data_for_model_request_error(httpx_client_mock, mocker):
    httpx_client_mock.post = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("POST", "http://testserver/transform")))

    with pytest.raises(HTTPException) as excinfo:
        await pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, {"input": "data"}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An request error occurred while transforming the input data" in excinfo.value.detail

# Test for unexpected error in transform function
@pytest.mark.asyncio
async def test_pre_or_post_transform_input_data_for_model_unexpected_error(httpx_client_mock, mocker):
    httpx_client_mock.post = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as excinfo:
        await pre_or_post_transform_input_data_for_model(
            httpx_client_mock, "project1", "model1", "transformer1", "pre", "http://testserver", {}, {"input": "data"}, "transaction_id"
        )
    assert excinfo.value.status_code == 500
    assert "An unexpected error occurred while transforming the input data" in excinfo.value.detail
