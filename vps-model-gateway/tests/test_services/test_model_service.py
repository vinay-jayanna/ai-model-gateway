# 
#  Copyright (c) 2024 Vipas.AI
# 
#  All rights reserved. This program and the accompanying materials
#  are made available under the terms of a proprietary license which prohibits
#  redistribution and use in any form, without the express prior written consent
#  of Vipas.AI.
#  
#  This code is proprietary to Vipas.AI and is protected by copyright and
#  other intellectual property laws. You may not modify, reproduce, perform,
#  display, create derivative works from, repurpose, or distribute this code or any portion of it
#  without the express prior written permission of Vipas.AI.
#  
#  For more information, contact Vipas.AI at legal@vipas.ai
#  

from unittest.mock import patch, MagicMock, AsyncMock
from src.services.model_service import model_prediction_service
from fastapi import FastAPI,Request
from fastapi.exceptions import HTTPException
from botocore.exceptions import ClientError
from uuid import uuid4
import pytest
import json

@pytest.fixture(name="request_mock", scope="function")
def fixture_es_client(mocker):

    redis_client_return_mock = AsyncMock()
    s3_client_return_mock = MagicMock()

    app = FastAPI()
    app.state.redis_client = redis_client_return_mock
    app.state.s3_client = s3_client_return_mock

    # Create a mock Request object with the mock app
    request_mock = mocker.Mock(spec=Request)
    request_mock.app = app

    return request_mock

@pytest.mark.asyncio
async def test_model_prediction_service_success_transformer_present_payload_type_content(request_mock):
    transaction_id = str(uuid4())
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": transaction_id, "vps-app-id": "fake-vps-app-id", "vps-env-type": "vipas-streamlit"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_list_of_authorized_model_for_app', new_callable=AsyncMock) as mock_retrieve_list_of_authorized_model_for_app, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer, \
        patch('src.services.model_service.retrieve_info_for_model_and_transformer_if_exists') as mock_retrieve_info_for_model_and_transformer_if_exists, \
        patch('src.services.model_service.check_pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_check_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.get_model_prediction_for_input_data', new_callable=AsyncMock) as mock_get_model_prediction_for_input_data:

        deployment_id = "dep-test"
        model_id = "mdl-test"
        project_id = "prj-test"
        transformer_id = "trf-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_list_of_authorized_model_for_app.return_value = [model_id]

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"

        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None

        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {
            "model": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id},
            "transformer": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id, "transformer_id": transformer_id}
        }

        mock_retrieve_info_for_model_and_transformer_if_exists.return_value = (
            "fake-model-kourier-url", 
            "fake-transformer-kourier-url", 
            {}, 
            {},
            project_id, 
            "fake-deployment-system"
        )

        mock_check_pre_or_post_transform_input_data_for_model.side_effect = [True, True]

        mock_pre_or_post_transform_input_data_for_model.side_effect = [{"data":"fake-transformed-output-data", "payload_type":"content"}, {"data":"fake-transformed-output-data", "payload_type":"content"}]

        mock_get_model_prediction_for_input_data.return_value = ("fake-prediction-result", "content")

        response = await model_prediction_service(request_mock, model_id, json.dumps("fake-input-data"))

        assert response["output_data"] == "fake-transformed-output-data"
        assert response["payload_type"] == "content"

        assert mock_check_pre_or_post_transform_input_data_for_model.call_count == 2
        assert mock_pre_or_post_transform_input_data_for_model.call_count == 2

        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.assert_called_once_with(
            request_mock.app.state.redis_client, "fake-username", transaction_id 
        )

@pytest.mark.asyncio
async def test_model_prediction_service_success_transformer_present_payload_type_url(request_mock):
    transaction_id = str(uuid4())
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": transaction_id, "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_download_url') as mock_generate_presigned_download_url, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_upload_url') as mock_generate_presigned_upload_url, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer, \
        patch('src.services.model_service.retrieve_info_for_model_and_transformer_if_exists') as mock_retrieve_info_for_model_and_transformer_if_exists, \
        patch('src.services.model_service.check_pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_check_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.get_model_prediction_for_input_data', new_callable=AsyncMock) as mock_get_model_prediction_for_input_data, \
        patch('src.services.model_service.BucketStructure', new_callable=MagicMock) as mock_bucket_structure:

        deployment_id = "dep-test"
        model_id = "mdl-test"
        project_id = "prj-test"
        transformer_id = "trf-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None

        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {
            "model": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id},
            "transformer": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id, "transformer_id": transformer_id}
        }

        mock_retrieve_info_for_model_and_transformer_if_exists.return_value = (
            "fake-model-kourier-url", 
            "fake-transformer-kourier-url", 
            {}, 
            {},
            project_id, 
            "fake-deployment-system"
        )

        mock_check_pre_or_post_transform_input_data_for_model.side_effect = [True, True]

        mock_pre_or_post_transform_input_data_for_model.side_effect = [{"data":"fake-transformed-output-data", "payload_type":"url"}, {"data":None, "payload_type":"url"}]

        mock_get_model_prediction_for_input_data.return_value = (None, "url")

        mock_bucket_structure.return_value.get_bucket_structure.return_value = {"runtime_folder": "fake-runtime-folder"}

        mock_generate_presigned_download_url.side_effect = ["fake-model-prediction-output-url", "fake-post-transformer-output-url"]
        mock_generate_presigned_upload_url.return_value = "fake-upload-url"

        response = await model_prediction_service(request_mock, model_id, json.dumps("fake-input-data"))

        assert response["output_data"] == None
        assert response["payload_type"] == "url"

        assert mock_check_pre_or_post_transform_input_data_for_model.call_count == 2
        assert mock_pre_or_post_transform_input_data_for_model.call_count == 2

        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.assert_called_once_with(
            request_mock.app.state.redis_client, "fake-username", transaction_id 
        )

@pytest.mark.asyncio
async def test_model_prediction_service_success_transformer_not_present_payload_type_content(request_mock):
    transaction_id = str(uuid4())
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": transaction_id, "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer, \
        patch('src.services.model_service.retrieve_info_for_model_and_transformer_if_exists') as mock_retrieve_info_for_model_and_transformer_if_exists,  \
        patch('src.services.model_service.get_model_prediction_for_input_data', new_callable=AsyncMock) as mock_get_model_prediction_for_input_data:

        deployment_id = "dep-test"
        model_id = "mdl-test"
        project_id = "prj-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None

        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {
            "model": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id}
        }

        mock_retrieve_info_for_model_and_transformer_if_exists.return_value = (
            "fake-model-kourier-url", 
            None, 
            "fake-model-headers", 
            None, 
            project_id, 
            "fake-deployment-system"
        )

        mock_get_model_prediction_for_input_data.return_value = ("fake-prediction-result", "content")

        response = await model_prediction_service(request_mock, model_id, json.dumps("fake-input-data"))

        assert response["output_data"] == "fake-prediction-result"
        assert response["payload_type"] == "content"

        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.assert_called_once_with(
            request_mock.app.state.redis_client, "fake-username", transaction_id 
        )

@pytest.mark.asyncio
async def test_model_prediction_service_failure_vps_auth_token_missing(request_mock):
    request_mock.headers = {"vps-env-type": "vipas-external", "vps-auth-token": None}
    with pytest.raises(HTTPException) as exc_info:
        await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
    assert exc_info.value.status_code == 400
    assert "Vps-auth-token is missing or empty in the request header" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_transaction_id_missing(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "vps-env-type": "vipas-external"}
    with pytest.raises(HTTPException) as exc_info:
        await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
    assert exc_info.value.status_code == 400
    assert "Transaction-id is missing or empty in the request header" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_username_not_present(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()),"vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token :

        mock_validate_auth_token.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 404
        assert "Username not found for vps-auth-token: fake-vps-auth-token" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_app_not_authorized(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()),"vps-app-id": "fake-vps-app-id", "vps-env-type": "vipas-streamlit"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token,\
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_list_of_authorized_model_for_app', new_callable=AsyncMock) as mock_retrieve_list_of_authorized_model_for_app:

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_retrieve_list_of_authorized_model_for_app.return_value = []

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 403
        assert "App: fake-vps-app-id is not authorized" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_rate_limit_exceeded(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()), "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user :

        model_id = "mdl-test"
        project_id = "prj-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value =  True

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded for user: fake-username" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_model_prediction_service_failure_authorization_failure_for_caller_user(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()), "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model:
        
        model_id = "mdl-test"
        project_id = "prj-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id, "api_access": "private"}
        mock_retrieve_entity_id_for_model.return_value = "other-entity-id"

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 403
        assert "User: fake-username does not have access to call the model" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_model_not_found(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()), "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer:

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_model_details_info.return_value = {"model_id":"mdl-test","project_id":"prj-test"}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None

        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 404
        assert "Model deployment information not found for the model_id: fake-model-id" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_model_prediction_service_failure_presigned_upload_url(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()), "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_download_url') as mock_generate_presigned_download_url, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_upload_url') as mock_generate_presigned_upload_url, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer, \
        patch('src.services.model_service.retrieve_info_for_model_and_transformer_if_exists') as mock_retrieve_info_for_model_and_transformer_if_exists, \
        patch('src.services.model_service.check_pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_check_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.get_model_prediction_for_input_data', new_callable=AsyncMock) as mock_get_model_prediction_for_input_data, \
        patch('src.services.model_service.BucketStructure', new_callable=MagicMock) as mock_bucket_structure:

        deployment_id = "dep-test"
        model_id = "mdl-test"
        project_id = "prj-test"
        transformer_id = "trf-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None


        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {
            "model": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id},
            "transformer": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id, "transformer_id": transformer_id}
        }

        mock_retrieve_info_for_model_and_transformer_if_exists.return_value = (
            "fake-model-kourier-url", 
            "fake-transformer-kourier-url", 
            {}, 
            {},
            project_id, 
            "fake-deployment-system"
        )

        mock_check_pre_or_post_transform_input_data_for_model.side_effect = [True, True]

        mock_pre_or_post_transform_input_data_for_model.side_effect = [{"data":"fake-transformed-output-data", "payload_type":"url"}, {"data":None, "payload_type":"url"}]

        mock_get_model_prediction_for_input_data.return_value = (None, "url")

        mock_bucket_structure.return_value.get_bucket_structure.return_value = {"runtime_folder": "fake-runtime-folder"}

        mock_generate_presigned_download_url.side_effect = ["fake-model-prediction-output-url", "fake-transformed-output-url"]
        mock_generate_presigned_upload_url.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 500
        assert "Failed to generate the presigned upload URL for the post processor response for the model" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_model_prediction_service_failure_presigned_upload_url_client_error(request_mock):
    request_mock.headers = {"vps-auth-token": "fake-vps-auth-token", "transaction-id": str(uuid4()), "vps-env-type": "vipas-external"}
    with patch('src.services.model_service.httpx.AsyncClient', return_value=AsyncMock()) as mock_client, \
        patch('src.services.model_service.validate_auth_token', new_callable=AsyncMock) as mock_validate_auth_token, \
        patch('src.services.model_service.validate_entity_balance', new_callable=AsyncMock) as mock_validate_entity_balance, \
        patch('src.services.model_service.retrieve_model_details_info', new_callable=AsyncMock) as mock_retrieve_model_details_info, \
        patch('src.services.model_service.retrieve_entity_id_for_model', new_callable=AsyncMock) as mock_retrieve_entity_id_for_model, \
        patch('src.utils.redis_feature_plugin.RedisFeaturePlugin.check_rate_limit_exceeded_or_not_for_a_particular_user', new_callable=MagicMock) as mock_check_rate_limit_exceeded_or_not_for_a_particular_user, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_download_url') as mock_generate_presigned_download_url, \
        patch('src.utils.aws_feature_plugin.AWSFeaturePlugin.generate_presigned_upload_url') as mock_generate_presigned_upload_url, \
        patch('src.services.model_service.retrieve_deployment_info_for_model_and_related_transformer', new_callable=AsyncMock) as mock_retrieve_deployment_info_for_model_and_related_transformer, \
        patch('src.services.model_service.retrieve_info_for_model_and_transformer_if_exists') as mock_retrieve_info_for_model_and_transformer_if_exists, \
        patch('src.services.model_service.check_pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_check_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.pre_or_post_transform_input_data_for_model', new_callable=AsyncMock) as mock_pre_or_post_transform_input_data_for_model, \
        patch('src.services.model_service.get_model_prediction_for_input_data', new_callable=AsyncMock) as mock_get_model_prediction_for_input_data, \
        patch('src.services.model_service.BucketStructure', new_callable=MagicMock) as mock_bucket_structure:

        deployment_id = "dep-test"
        model_id = "mdl-test"
        project_id = "prj-test"
        transformer_id = "trf-test"

        mock_validate_auth_token.return_value = {"entity_id": "fake-entity-id", "username": "fake-username"}

        mock_validate_entity_balance.return_value = None

        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        mock_retrieve_model_details_info.return_value = {"model_id": model_id, "project_id": project_id}
        mock_retrieve_entity_id_for_model.return_value = "fake-entity-id"
        mock_check_rate_limit_exceeded_or_not_for_a_particular_user.return_value = None

        mock_retrieve_deployment_info_for_model_and_related_transformer.return_value = {
            "model": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id},
            "transformer": {"deployment_id": deployment_id, "model_id": model_id, "project_id": project_id, "transformer_id": transformer_id}
        }

        mock_retrieve_info_for_model_and_transformer_if_exists.return_value = (
            "fake-model-kourier-url", 
            "fake-transformer-kourier-url", 
            {}, 
            {},
            project_id, 
            "fake-deployment-system"
        )

        mock_check_pre_or_post_transform_input_data_for_model.side_effect = [True, True]

        mock_pre_or_post_transform_input_data_for_model.side_effect = [{"data":"fake-transformed-output-data", "payload_type":"url"}, {"data":None, "payload_type":"url"}]

        mock_get_model_prediction_for_input_data.return_value = (None, "url")

        mock_bucket_structure.return_value.get_bucket_structure.return_value = {"runtime_folder": "fake-runtime-folder"}

        mock_generate_presigned_download_url.side_effect = ["fake-model-prediction-output-url", "fake-transformed-output-url"]
        mock_generate_presigned_upload_url.side_effect = ClientError({"Error": {"Code": "NoSuchUpload"}}, "GeneratePresignedUrl")

        with pytest.raises(HTTPException) as exc_info:
            await model_prediction_service(request_mock, "fake-model-id", json.dumps("fake-input-data"))
        assert exc_info.value.status_code == 500
        assert "An client error occurred while making prediction request to the deployed model" in str(exc_info.value.detail)