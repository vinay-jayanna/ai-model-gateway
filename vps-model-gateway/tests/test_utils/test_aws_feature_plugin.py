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
from unittest.mock import patch, MagicMock
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from src.utils.aws_feature_plugin import AWSFeaturePlugin

@pytest.fixture
def aws_feature_plugin():
    return AWSFeaturePlugin()

@pytest.fixture(autouse=True)
def mock_env_config(mocker):
    mock_config = mocker.patch("src.utils.aws_feature_plugin.EnvConfigDTO", autospec=True)
    mock_config_instance = mock_config.return_value
    mock_config_instance.AWS_REGION = "us-east-1"
    mock_config_instance.MAX_POST_FILE_SIZE = 500  # In MB
    return mock_config

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch("src.utils.aws_feature_plugin.setup_logger", autospec=True)

def test_create_s3_client_success(aws_feature_plugin):
    with patch('src.utils.aws_feature_plugin.boto3.client', new_callable=MagicMock) as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        
        client = aws_feature_plugin.create_s3_client()
        assert client == mock_client
        mock_boto_client.assert_called_once_with("s3", region_name="us-east-1")

def test_create_s3_client_boto_core_error(aws_feature_plugin):
    with patch('src.utils.aws_feature_plugin.boto3.client', new_callable=MagicMock) as mock_boto_client:
        mock_boto_client.side_effect = BotoCoreError()
        
        with pytest.raises(BotoCoreError):
            aws_feature_plugin.create_s3_client()

def test_create_s3_client_client_error(aws_feature_plugin):
    with patch('src.utils.aws_feature_plugin.boto3.client', new_callable=MagicMock) as mock_boto_client:
        mock_boto_client.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "CreateClient")
        
        with pytest.raises(ClientError):
            aws_feature_plugin.create_s3_client()

def test_create_s3_client_unexpected_error(aws_feature_plugin):
    with patch('src.utils.aws_feature_plugin.boto3.client', new_callable=MagicMock) as mock_boto_client:
        mock_boto_client.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException):
            aws_feature_plugin.create_s3_client()

def test_close_s3_client(aws_feature_plugin):
    mock_client = MagicMock()
    aws_feature_plugin.close_s3_client(mock_client)
    mock_client.close.assert_called_once()

def test_generate_presigned_download_url_success(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://fake-presigned-url"
    
    url = aws_feature_plugin.generate_presigned_download_url(mock_client, "test-bucket", "test-key", "test-transaction-id")
    assert url == "https://fake-presigned-url"
    mock_client.generate_presigned_url.assert_called_once_with('get_object', Params={'Bucket': 'test-bucket', 'Key': 'test-key'}, ExpiresIn=300)

def test_generate_presigned_download_url_client_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "GeneratePresignedUrl")
    
    with pytest.raises(ClientError):
        aws_feature_plugin.generate_presigned_download_url(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_generate_presigned_download_url_unexpected_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException):
        aws_feature_plugin.generate_presigned_download_url(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_generate_presigned_upload_url_success(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_post.return_value = {"url": "https://fake-presigned-upload-url"}
    
    url = aws_feature_plugin.generate_presigned_upload_url(mock_client, "test-bucket", "test-key", "test-transaction-id")
    assert url == {"url": "https://fake-presigned-upload-url"}
    mock_client.generate_presigned_post.assert_called_once()

def test_generate_presigned_upload_url_client_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_post.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "GeneratePresignedPost")
    
    with pytest.raises(ClientError):
        aws_feature_plugin.generate_presigned_upload_url(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_generate_presigned_upload_url_unexpected_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.generate_presigned_post.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException):
        aws_feature_plugin.generate_presigned_upload_url(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_create_multipart_upload_success(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.create_multipart_upload.return_value = {"UploadId": "upload-id"}
    
    upload_id = aws_feature_plugin.create_mutlipart_upload_and_retrieve_upload_id(mock_client, "test-bucket", "test-key", "test-transaction-id")
    assert upload_id == "upload-id"
    mock_client.create_multipart_upload.assert_called_once_with(Bucket="test-bucket", Key="test-key")

def test_create_multipart_upload_client_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.create_multipart_upload.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "CreateMultipartUpload")
    
    with pytest.raises(ClientError):
        aws_feature_plugin.create_mutlipart_upload_and_retrieve_upload_id(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_create_multipart_upload_unexpected_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.create_multipart_upload.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException):
        aws_feature_plugin.create_mutlipart_upload_and_retrieve_upload_id(mock_client, "test-bucket", "test-key", "test-transaction-id")

def test_upload_chunk_part_success(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.upload_part.return_value = {"ETag": "etag"}
    
    response = aws_feature_plugin.upload_chunk_part_for_the_multipart_upload(mock_client, "upload-id", 1, b"chunk", "test-key", "test-bucket", "test-transaction-id")
    assert response == {"ETag": "etag"}
    mock_client.upload_part.assert_called_once_with(Bucket="test-bucket", Key="test-key", PartNumber=1, UploadId="upload-id", Body=b"chunk")

def test_upload_chunk_part_client_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.upload_part.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "UploadPart")
    
    with pytest.raises(ClientError):
        aws_feature_plugin.upload_chunk_part_for_the_multipart_upload(mock_client, "upload-id", 1, b"chunk", "test-key", "test-bucket", "test-transaction-id")

def test_upload_chunk_part_unexpected_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.upload_part.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException):
        aws_feature_plugin.upload_chunk_part_for_the_multipart_upload(mock_client, "upload-id", 1, b"chunk", "test-key", "test-bucket", "test-transaction-id")

def test_complete_multipart_upload_success(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.complete_multipart_upload.return_value = {"Response": "Complete"}
    
    response = aws_feature_plugin.complete_multipart_upload_for_the_multipart_upload(mock_client, "upload-id", "test-key", "test-bucket", [{"PartNumber": 1, "ETag": "etag"}], "test-transaction-id")
    assert response == {"Response": "Complete"}
    mock_client.complete_multipart_upload.assert_called_once_with(Bucket="test-bucket", Key="test-key", UploadId="upload-id", MultipartUpload={'Parts': [{"PartNumber": 1, "ETag": "etag"}]})

def test_complete_multipart_upload_client_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.complete_multipart_upload.side_effect = ClientError({"Error": {"Code": "ClientError"}}, "CompleteMultipartUpload")
    
    with pytest.raises(ClientError):
        aws_feature_plugin.complete_multipart_upload_for_the_multipart_upload(mock_client, "upload-id", "test-key", "test-bucket", [{"PartNumber": 1, "ETag": "etag"}], "test-transaction-id")

def test_complete_multipart_upload_unexpected_error(aws_feature_plugin):
    mock_client = MagicMock()
    mock_client.complete_multipart_upload.side_effect = Exception("Unexpected error")
    
    with pytest.raises(HTTPException):
        aws_feature_plugin.complete_multipart_upload_for_the_multipart_upload(mock_client, "upload-id", "test-key", "test-bucket", [{"PartNumber": 1, "ETag": "etag"}], "test-transaction-id")
