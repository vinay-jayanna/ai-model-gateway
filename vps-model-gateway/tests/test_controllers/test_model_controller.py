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

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import pytest
from src.main import app  # Ensure this is the correct path to your FastAPI app

client = TestClient(app)

@pytest.mark.asyncio
async def test_model_prediction():
    mock_response = 'fake_response'
    with patch('src.controllers.model_controller.model_prediction_service', return_value=mock_response):
        model_id = "mdl-test"
        response = client.post(f"/predict?model_id={model_id}", json="fake_input_data")
        assert response.status_code == 200
        assert response.json() == "fake_response"
