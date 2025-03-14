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
from src.utils.validate_auth_token_util import validate_auth_token
from httpx import Response, AsyncClient, Request
import pytest
import httpx

@pytest.fixture(name="httpx_client_mock", scope="function")
def fixture_httpx_client(mocker):
    httpx_client_mock = mocker.Mock(spec=AsyncClient)
    return httpx_client_mock

@pytest.mark.asyncio
async def test_validate_auth_token_success(httpx_client_mock):
    request = Request("POST", "http://testserver/validate-user")
    response = Response(200, json={"result": True, "username": "test_user"}, request=request)
    httpx_client_mock.post = AsyncMock(return_value=response)

    result = await validate_auth_token(httpx_client_mock, "valid_token", "test_transaction_id")
    assert result == {"result": True, "username": "test_user"}

@pytest.mark.asyncio
async def test_validate_auth_token_invalid(httpx_client_mock):
    request = Request("POST", "http://testserver/validate-user")
    response = Response(200, json={"result": False}, request=request)
    httpx_client_mock.post = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await validate_auth_token(httpx_client_mock, "invalid_token", "test_transaction_id")
    assert exc_info.value.status_code == 401
    assert "The vps-auth-token is invalid, stopping the prediction process." in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_validate_auth_token_http_error(httpx_client_mock):
    request = Request("POST", "http://testserver/validate-user")
    response = Response(500, request=request)
    httpx_client_mock.post = AsyncMock(return_value=response)

    with pytest.raises(HTTPException) as exc_info:
        await validate_auth_token(httpx_client_mock, "error_token","test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An error occurred while authenticating the vps-auth-token" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_validate_auth_token_request_error(httpx_client_mock, mocker):
    httpx_client_mock.post = AsyncMock(side_effect=httpx.RequestError("Network error", request=Request("POST", "http://testserver/validate-user")))

    with pytest.raises(HTTPException) as exc_info:
        await validate_auth_token(httpx_client_mock, "request_error_token", "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An request error occurred while authenticating the vps-auth-token" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_validate_auth_token_unexpected_error(httpx_client_mock, mocker):
    httpx_client_mock.post = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as exc_info:
        await validate_auth_token(httpx_client_mock, "unexpected_error_token", "test_transaction_id")
    assert exc_info.value.status_code == 500
    assert "An unexpected error occurred while authenticating the vps-auth-token" in str(exc_info.value.detail)