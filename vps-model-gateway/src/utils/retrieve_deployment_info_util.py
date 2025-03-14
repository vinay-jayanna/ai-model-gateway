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

from fastapi import HTTPException, Request
from src.utils.logger_util import setup_logger
from src.models.env.env_config_DTO import EnvConfigDTO
from src.utils.get_error_detail_util import get_error_detail
from httpx import AsyncClient
import httpx
import json

logger = setup_logger(__name__)

async def retrieve_deployment_info_for_model_and_related_transformer(client: AsyncClient, model_id: str, transaction_id: str):
    try:
        # Making a instance of env config DTO, changing it from global to local, for testing purpose as global instance cant be mocked
        config = EnvConfigDTO()

        logger.info(f"Transaction-id: {transaction_id}, Trying to get the deployment details for the model, sending async request to the deploy admin.")
        
        response = await client.get(f"{config.DEPLOY_ADMIN_SERVICE_URL}/deploy/model/transformer/info?model_id={model_id}")
        response.raise_for_status()

        data = response.json()
        logger.info(f"Transaction-id: {transaction_id}, Response for the deploy admin service: {data}")

        return data
    except httpx.HTTPStatusError as e:
        error_detail = get_error_detail(e.response.text)
        logger.error(f"Transaction-id: {transaction_id}, An error occurred while getting the deployment details for the model: {error_detail}")
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    
    except httpx.RequestError as e:
        logger.error(f"Transaction-id: {transaction_id}, An request error occurred while getting the deployment details for the model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while getting the deployment details for the model: {str(e)}")
    
    except Exception as e:
        logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while getting the deployment details for the model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while getting the deployment details for the model: {str(e)}")