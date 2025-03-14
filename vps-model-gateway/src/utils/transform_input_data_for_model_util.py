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
from src.utils.get_error_detail_util import get_error_detail
from httpx import AsyncClient
from typing import Any
import httpx
import json

logger = setup_logger(__name__)

async def check_pre_or_post_transform_input_data_for_model(client: AsyncClient, project_id: str, model_id: str, transformer_id: str, call_type: str,  kourier_transformer_url: str, transformer_headers: dict, transaction_id: str):
    try:

        logger.info(f"Transaction-id: {transaction_id}, Checking if a {call_type} transform is required for the model: {model_id}.")
        response = await client.get(f"{kourier_transformer_url}/check_transform?project_id={project_id}&model_id={model_id}&transformer_id={transformer_id}&call_type={call_type}", headers=transformer_headers)
        response.raise_for_status()
        return response.json()
    
    except httpx.HTTPStatusError as e:
        error_detail = get_error_detail(e.response.text)
        logger.error(f"Transaction-id: {transaction_id}, An error occurred while checking if a {call_type} transform is required for the model: {model_id}: {error_detail}")
        raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while checking if a {call_type} transform is required for the model: {model_id}: {error_detail}")
        
    except httpx.RequestError as e:
        logger.error(f"Transaction-id: {transaction_id}, An request error occurred while checking if a {call_type} transform is required for the model: {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while checking if a {call_type} transform is required for the model: {model_id}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while checking if a {call_type} transform is required for the model: {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while checking if a {call_type} transform is required for the model: {model_id}: {str(e)}")
    
async def pre_or_post_transform_input_data_for_model(client: AsyncClient, project_id: str, model_id: str, transformer_id: str, call_type: str, kourier_transformer_url: str, transformer_headers: dict, input_data: Any, transaction_id: str):
    try:

        logger.info(f"Transaction-id: {transaction_id},{call_type} is present for the transformer {transformer_id}, transforming the input data.")
        request_body = {
            "project_id": project_id,
            "model_id": model_id,
            "transformer_id": transformer_id,
            "call_type": call_type,
            "input": input_data
        }
        
        response = await client.post(f"{kourier_transformer_url}/transform", headers=transformer_headers, data=json.dumps(request_body))
        response.raise_for_status()
        return response.json()
    
    except httpx.HTTPStatusError as e:
        error_detail = get_error_detail(e.response.text)
        if e.response.status_code == 400:
            logger.info(f"Transaction-id: {transaction_id}, An error occurred while transforming the input data: {error_detail}")
        else:
            logger.error(f"Transaction-id: {transaction_id}, An error occurred while transforming the input data: {error_detail}")
        raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while transforming the input data: {error_detail}")
            
    except httpx.RequestError as e:
        logger.error(f"Transaction-id: {transaction_id}, An request error occurred while transforming the input data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An request error occurred while transforming the input data: {str(e)}")
            
    except Exception as e:
        logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while transforming the input data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while transforming the input data: {str(e)}")
            