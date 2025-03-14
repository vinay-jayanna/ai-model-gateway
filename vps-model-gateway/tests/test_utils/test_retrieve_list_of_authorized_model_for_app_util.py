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
from src.utils.retrieve_list_of_authorized_model_for_app_util import retrieve_list_of_authorized_model_for_app
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
async def test_retrieve_list_of_authorized_model_for_app_success(httpx_client_mock):
    app_id = "valid_app_id"
    request = Request("GET", f"http://testserver/app/exists?app_id={app_id}")
    response = Response(200, json={"result": True, "data": {"auth_model_ids": ["model1", "model2"]}}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    result = await retrieve_list_of_authorized_model_for_app(httpx_client_mock, app_id, "test_transaction_id")
    assert result == ["model1", "model2"]

@pytest.mark.asyncio
async def test_retrieve_list_of_authorized_model_for_app_not_found(httpx_client_mock):
    app_id = "invalid_app_id"
    request = Request("GET", f"http://testserver/app/exists?app_id={app_id}")
    response = Response(200, json={"result": False}, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_list_of_authorized_model_for_app(httpx_client_mock, app_id, "test_transaction_id")
    assert exc_info.value.status_code == 404
    assert "App not found in the project admin service" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_list_of_authorized_model_for_app_http_error(httpx_client_mock):
    app_id = "http_error_app_id"
    request = Request("GET", f"http://testserver/app/exists?app_id={app_id}")
    response = Response(500, request=request)
    httpx_client_mock.get = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_list_of_authorized_model_for_app(httpx_client_mock, app_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An error occurred while getting the list of authorized models for app" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_list_of_authorized_model_for_app_request_error(httpx_client_mock, mocker):
    app_id = "request_error_app_id"
    httpx_client_mock.get = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("GET", f"http://testserver/app/exists?app_id={app_id}")))

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_list_of_authorized_model_for_app(httpx_client_mock, app_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An request error occurred while getting the list of authorized models for app" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_retrieve_list_of_authorized_model_for_app_unexpected_error(httpx_client_mock, mocker):
    app_id = "unexpected_error_app_id"
    httpx_client_mock.get = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_list_of_authorized_model_for_app(httpx_client_mock, app_id, "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An unexpected error occurred while getting the list of authorized models for app" in str(exc_info.value.detail)
