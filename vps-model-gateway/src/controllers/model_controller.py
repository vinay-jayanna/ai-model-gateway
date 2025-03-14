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


from fastapi import APIRouter, Request, Query, Body
from src.utils.logger_util import setup_logger
from src.models.env.env_config_DTO import EnvConfigDTO
from src.services.model_service import model_prediction_service
from typing import Any

router = APIRouter()
config = EnvConfigDTO()
logger = setup_logger(__name__)

@router.post("/predict")
async def model_prediction(request: Request, model_id: str = Query(..., description="Unique identifier of the model")):
    logger.info(f"Received prediction request for model_id: {model_id}")
    
    # Await the request body to get its content
    input_data_bytes = await request.body()
    input_data = input_data_bytes.decode('utf-8')

    return await model_prediction_service(request, model_id, input_data)
