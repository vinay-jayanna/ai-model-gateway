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

async def validate_auth_token(client: AsyncClient, vps_auth_token: str, transaction_id: str):
    try:
        # Making a instance of env config DTO, changing it from global to local, for testing purpose as global instance cant be mocked
        config = EnvConfigDTO()

        logger.info(f"Transaction-id: {transaction_id}, Trying to authenticate the vps-auth-token, sending async request to the user admin.")
        response = await client.post(f"{config.USER_ADMIN_SERVICE_URL}/validate_user", data=json.dumps({"vps-auth-token": vps_auth_token}))
        response.raise_for_status()

        data = response.json()
        logger.info(f"Response for the user admin service: {data}")

        if data.get("result", False) == False:
            logger.error(f"Transaction-id: {transaction_id}, the vps-auth-token is invalid, stopping the prediction process.")
            raise HTTPException(status_code=401, detail="The vps-auth-token is invalid, stopping the prediction process.")
        
        logger.debug(f"Transaction-id: {transaction_id}, the vps-auth-token is valid, continuing with the prediction process.")
        return data

    except httpx.HTTPStatusError as e:
        logger.error(f"Transaction-id: {transaction_id}, An error occurred while authenticating the vps-auth-token: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while authenticating the vps-auth-token: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Transaction-id: {transaction_id}, An request error occurred while authenticating the vps-auth-token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while authenticating the vps-auth-token: {str(e)}")
    except HTTPException as e:
        logger.error(f"An HTTP error occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while authenticating the vps-auth-token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while authenticating the vps-auth-token: {str(e)}")