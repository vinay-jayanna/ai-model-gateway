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

from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from src.utils.retrieve_info_for_model_util import retrieve_info_for_model_and_transformer_if_exists
import pytest

def test_retrieve_info_success_with_transformer_and_KserveV1():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "project_id": "prj-1234",
            "deployment_system": "KserveV1",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = {
            "transformer_id": "trf-5678",
            "url_additions": {"Headers": {"Authorization": "Bearer transformer_token"}}
        }
        result = retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        expected_model_url = "http://testserver/kourier/v1/models/mdl-1234-1234:predict"
        expected_transformer_url = "http://testserver/kourier"
        expected_model_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        expected_transformer_headers = {"Authorization": "Bearer transformer_token", "Content-Type": "application/json"}

        assert result == (expected_model_url, expected_transformer_url, expected_model_headers, expected_transformer_headers, "prj-1234", "KserveV1")

def test_retrieve_info_success_with_transformer_and_KserveV2():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "project_id": "prj-1234",
            "deployment_system": "KserveV2",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = {
            "transformer_id": "trf-5678",
            "url_additions": {"Headers": {"Authorization": "Bearer transformer_token"}}
        }
        result = retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        expected_model_url = "http://testserver/kourier/v2/models/mdl-1234-1234/infer"
        expected_transformer_url = "http://testserver/kourier"
        expected_model_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        expected_transformer_headers = {"Authorization": "Bearer transformer_token", "Content-Type": "application/json"}

        assert result == (expected_model_url, expected_transformer_url, expected_model_headers, expected_transformer_headers, "prj-1234", "KserveV2")


def test_retrieve_info_success_without_transformer():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "project_id": "prj-1234",
            "deployment_system": "KserveV1",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = None
        result = retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        expected_model_url = "http://testserver/kourier/v1/models/mdl-1234-1234:predict"
        expected_model_headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}

        assert result == (expected_model_url, None, expected_model_headers, {}, "prj-1234", "KserveV1")

def test_retrieve_info_missing_project_id():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "deployment_system": "Kserve",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = None
        with pytest.raises(HTTPException) as excinfo:
            retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        assert excinfo.value.status_code == 404
        assert "Project id not found in the model deployment information for the model_id" in excinfo.value.detail

def test_retrieve_info_unsupported_deployment_system():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "project_id": "prj-1234",
            "deployment_system": "UnsupportedSystem",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = None
        with pytest.raises(HTTPException) as excinfo:
            retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        assert excinfo.value.status_code == 400
        assert "Deployment system not supported for the model_id" in excinfo.value.detail

def test_retrieve_info_no_deployment_system():
    with patch('src.utils.retrieve_info_for_model_util.EnvConfigDTO') as mock_config_class:
        mock_config_class_instance = MagicMock()
        mock_config_class.return_value = mock_config_class_instance
        mock_config_class_instance.MODEL_KOURIER_SERVICE_URL = "http://testserver/kourier"
        mock_config_class_instance.TRANSFORMER_KOURIER_SERVICE_URL = "http://testserver/kourier"

        model = {
            "project_id": "prj-1234",
            "url_additions": {"Headers": {"Authorization": "Bearer token"}}
        }
        transformer = None
        with pytest.raises(HTTPException) as excinfo:
            retrieve_info_for_model_and_transformer_if_exists("mdl-1234", model, transformer, "test-transaction-id")
        assert excinfo.value.status_code == 400
        assert "No deployment system specified for model_id" in excinfo.value.detail
