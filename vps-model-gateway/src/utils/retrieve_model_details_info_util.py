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
from httpx import AsyncClient
import httpx
import json

logger = setup_logger(__name__)


async def retrieve_model_details_info(client: AsyncClient, model_id: str, transaction_id: str):
    try:
        # Making a instance of env config DTO, changing it from global to local, for testing purpose as global instance cant be mocked
        config = EnvConfigDTO()

        logger.info(f"Transaction-id: {transaction_id}, Trying to get the model details for model {model_id}, from project admin service.")
        response = await client.get(f"{config.PROJECT_ADMIN_SERVICE_URL}/model/exists?model_id={model_id}")
        response.raise_for_status()

        response_data = response.json()
        if response_data.get("result") == False:
            logger.error(f"Transaction-id: {transaction_id},Model with id {model_id} not found in the project admin service")
            raise HTTPException(status_code=404, detail="Model not found in the project admin service")
        
        model = response_data.get("data")
        logger.info(f"Transaction-id: {transaction_id},Got the model details for model {model_id} from project admin service.")

        return model
    
    except httpx.HTTPStatusError as e:
        logger.error(f"Transaction-id: {transaction_id}, An error occurred while getting the model details: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while getting the model details: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Transaction-id: {transaction_id}, An request error occurred while getting the model details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while getting the model details: {str(e)}")
    except HTTPException as e:
        logger.error(f"Transaction-id: {transaction_id}, An HTTP error occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while getting the model details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while getting the model details: {str(e)}")