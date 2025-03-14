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
#  # Copyright (c) 2024 Vipas.AI
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

async def validate_entity_balance(client: AsyncClient, entity_id: str, model_id: str, vps_app_id: str, vps_env_type: str, transaction_id: str):
    try:
        # Making a instance of env config DTO, changing it from global to local, for testing purpose as global instance cant be mocked
        config = EnvConfigDTO()
        logger.info(f"Transaction id: {transaction_id}, Trying to validate the entity {entity_id} balance, sending async request to the payment service.")

        headers = {
                "Content-Type": "application/json",
                "vps-env-type": vps_env_type,
                "transaction-id": transaction_id
            }
        if vps_app_id:
            #Set the vps-app-id in the header if it is present
            headers["vps-app-id"] = vps_app_id
        
        response = await client.get(f"{config.PAYMENT_SERVICE_URL}/balance/validate/prediction?entity_id={entity_id}&model_id={model_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Response from the payment service for the entity {entity_id} balance: {data}")

        if data.get("result", False) == False:
            logger.warning(f"Transaction id: {transaction_id}, User {entity_id} has insufficient balance to run the model {model_id}, stopping the prediction process.")
            raise HTTPException(status_code=402, detail="User has insufficient balance to run the model.")
        
        logger.info(f"Transaction id: {transaction_id}, Entity {entity_id} has sufficient balance to run the model {model_id}, continuing with the prediction process.")

    except httpx.HTTPStatusError as e:
        logger.error(f"An error occurred while validating the entity {entity_id} balance: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while validating the entity {entity_id} balance: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"An request error occurred while validating the entity {entity_id} balance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while validating the entity {entity_id} balance: {str(e)}")
    except HTTPException as e:
        logger.error(f"An HTTP error occurred while validating the entity {entity_id} balance: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred while validating the entity {entity_id} balance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while validating the entity {entity_id} balance: {str(e)}")