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
from fastapi import HTTPException, Request, FastAPI
from httpx import Response, AsyncClient
from src.utils.model_prediction_util import get_model_prediction_for_input_data
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError

# Mock fixture for request and httpx client
@pytest.fixture(name="request_mock", scope="function")
def fixture_request_mock(mocker):

    redis_client_return_mock = AsyncMock()
    s3_client_return_mock = MagicMock()

    app = FastAPI()
    app.state.redis_client = redis_client_return_mock
    app.state.s3_client = s3_client_return_mock

    # Create a mock Request object with the mock app
    request_mock = mocker.Mock(spec=Request)
    request_mock.app = app

    return request_mock

@pytest.fixture(name="httpx_client_mock", scope="function")
def fixture_httpx_client(mocker):
    httpx_client_mock = mocker.Mock(spec=AsyncClient)
    return httpx_client_mock

# Test for successful prediction with KserveV1 deployment system
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_KserveV1_success(request_mock, httpx_client_mock):
    response = AsyncMock()
    response.aread = AsyncMock(return_value=b'{"predictions": ["prediction_result"]}')
    response.headers = {"Content-Length": "1000"}
    
    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response
    stream_context_manager.__aexit__.return_value = AsyncMock()

    httpx_client_mock.stream.return_value = stream_context_manager

    result, payload_type = await get_model_prediction_for_input_data(
        request_mock, httpx_client_mock, "model1", "transaction1", "KserveV1", "http://testserver/predict", {}, {}, {"input": "data"}
    )
    assert result == "prediction_result"
    assert payload_type == "content"

# Test for successful prediction with KserveV2 deployment system
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_KserveV2_success(request_mock, httpx_client_mock):
    response = AsyncMock()
    response.aread = AsyncMock(return_value=b'{"outputs": [{"data":"output_result"}]}')
    response.headers = {"Content-Length": "1000"}

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response
    stream_context_manager.__aexit__.return_value = AsyncMock()

    httpx_client_mock.stream.return_value = stream_context_manager

    result, payload_type = await get_model_prediction_for_input_data(
        request_mock, httpx_client_mock, "model1", "transaction1", "KserveV2", "http://testserver/predict", {}, {"input":{"dims": [1, 1], "data_type": "FP32"}}, {"input": "data"}
    )
    assert result == "output_result"
    assert payload_type == "content"

@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_large_payload(request_mock, httpx_client_mock):
    async def mock_aiter_bytes(*args, **kwargs):
        yield b'a' * 5 * 1024 * 1024  # First chunk of 5 MB
        yield b'a' * 1024 * 1024  # Second chunk of 1 MB

    response = AsyncMock()
    response.headers = {"Content-Length": "6000000"}  # 6MB to simulate large payload
    response.aiter_bytes = mock_aiter_bytes

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response
    stream_context_manager.__aexit__.return_value = AsyncMock()

    httpx_client_mock.stream.return_value = stream_context_manager

    with patch("src.utils.model_prediction_util.AWSFeaturePlugin.create_mutlipart_upload_and_retrieve_upload_id", return_value="upload_id") as mock_create_upload_id, \
         patch("src.utils.model_prediction_util.AWSFeaturePlugin.upload_chunk_part_for_the_multipart_upload", return_value={"ETag": "etag"}) as mock_upload_chunk, \
         patch("src.utils.model_prediction_util.AWSFeaturePlugin.complete_multipart_upload_for_the_multipart_upload") as mock_complete_upload, \
         patch('src.utils.model_prediction_util.BucketStructure', new_callable=MagicMock) as mock_bucket_structure:

        mock_bucket_structure.return_value.get_bucket_structure.return_value = {"runtime_folder": "fake-runtime-folder"}

        result, payload_type = await get_model_prediction_for_input_data(
            request_mock, httpx_client_mock, "model1", "transaction1", "KserveV1", "http://testserver/predict", {}, {}, {"input": "data"}
        )

        assert result is None
        assert payload_type == "url"
        mock_create_upload_id.assert_called_once()
        assert mock_upload_chunk.call_count == 2
        mock_complete_upload.assert_called_once()

# Test for HTTP status error in prediction request
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_http_error(request_mock, httpx_client_mock):
    request = MagicMock()
    response = MagicMock()
    response.status_code = 500  # Explicitly set the status code
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Error", request=request, response=response
    )
    response.aread = AsyncMock(return_value=b'{"detail": "Internal Server Error"}')

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response

    httpx_client_mock.stream.return_value = stream_context_manager

    with patch('src.utils.get_error_detail_util.get_error_detail', return_value="Internal Server Error Detail"):
        with pytest.raises(HTTPException) as exc_info:
            await get_model_prediction_for_input_data(
                request_mock, httpx_client_mock, "model1", "transaction1", "non-Kserve", "http://testserver/predict", {}, {}, {"input": "data"}
            )

    assert exc_info.value.status_code == 500
    assert "An error occurred while making prediction request to the deployed model model1" in exc_info.value.detail

# # Test for client error during upload
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_client_error(request_mock, httpx_client_mock):
    async def mock_aiter_bytes(*args, **kwargs):
        yield b'a' * 5 * 1024 * 1024  # First chunk of 5 MB
        yield b'a' * 1024 * 1024  # Second chunk of 1 MB

    response = AsyncMock()
    response.headers = {"Content-Length": "6000000"}  # 6MB to simulate large payload
    response.aiter_bytes = mock_aiter_bytes

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response

    httpx_client_mock.stream.return_value = stream_context_manager

    with patch("src.utils.model_prediction_util.AWSFeaturePlugin.create_mutlipart_upload_and_retrieve_upload_id") as mock_create_upload_id, \
        patch('src.utils.model_prediction_util.BucketStructure', new_callable=MagicMock) as mock_bucket_structure:

        mock_create_upload_id.side_effect = ClientError({"Error": {"Code": "NoSuchUpload"}}, "GeneratePresignedUrl")
        mock_bucket_structure.return_value.get_bucket_structure.return_value = {"runtime_folder": "fake-runtime-folder"}

        with pytest.raises(HTTPException) as excinfo:
            await get_model_prediction_for_input_data(
                request_mock, httpx_client_mock, "model1", "transaction1", "KserveV1", "http://testserver/predict", {}, {}, {"input": "data"}
            )

        assert excinfo.value.status_code == 500
        assert "An error occurred while uploading the predicted data to S3 for the deployed model model1" in excinfo.value.detail

# Test for request error in prediction request
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_request_error(request_mock, httpx_client_mock):
    request = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.RequestError("Network error", request=request)
    response.aread = AsyncMock(return_value=b'{"detail": "Network error"}')

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response

    httpx_client_mock.stream.return_value = stream_context_manager

    with pytest.raises(HTTPException) as excinfo:
        await get_model_prediction_for_input_data(
            request_mock, httpx_client_mock, "model1", "transaction1", "non-Kserve", "http://testserver/predict", {}, {}, {"input": "data"}
        )

    assert excinfo.value.status_code == 500
    assert "An request error occurred while making prediction request to the deployed model model1" in excinfo.value.detail

# Test for unexpected error in prediction request
@pytest.mark.asyncio
async def test_get_model_prediction_for_input_data_unexpected_error(request_mock, httpx_client_mock):
    request = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = Exception("Unexpected error")
    response.aread = AsyncMock(return_value=b'{"detail": "Unexpected error"}')

    stream_context_manager = AsyncMock()
    stream_context_manager.__aenter__.return_value = response

    httpx_client_mock.stream.return_value = stream_context_manager

    with pytest.raises(HTTPException) as excinfo:
        await get_model_prediction_for_input_data(
            request_mock, httpx_client_mock, "model1", "transaction1", "non-Kserve", "http://testserver/predict", {}, {}, {"input": "data"}
        )

    assert excinfo.value.status_code == 500
    assert "An unexpected error occurred while making prediction request to the deployed model model1" in excinfo.value.detail