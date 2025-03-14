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

from fastapi import HTTPException
from src.utils.logger_util import setup_logger
from src.models.env.env_config_DTO import EnvConfigDTO
from httpx import AsyncClient
from typing import Any
import httpx
import json

logger = setup_logger(__name__)

def retrieve_info_for_model_and_transformer_if_exists(model: dict, model_deployment: any, transformer_deployment: any, transaction_id: str):
    # Making a instance of env config DTO, changing it from global to local, for testing purpose as global instance cant be mocked
    config = EnvConfigDTO()

    # Initialize headers and extract additional headers if available
    model_headers = transformer_headers = {}
    kourier_model_url = kourier_transformer_url = None

    model_id = model.get("model_id")

    logger.info(f"Transaction-id: {transaction_id},Extracting the model deployment headers")
    model_headers = model_deployment.get("url_additions",{}).get("Headers", {})

    # Construct service name based on model data
    logger.info(f"Transaction-id: {transaction_id}, Extracting the service name for the deployed model {model_id}")
    project_id = model_deployment.get("project_id")
    if not project_id:
        logger.error(f"Transaction-id: {transaction_id}, Project id not found in the model deployment information for the model_id: {model_id}")
        raise HTTPException(status_code=404, detail=f"Project id not found in the model deployment information for the model_id: {model_id}")

    mdl_service_name = f"mdl-{model_deployment.get('project_id')[4:]}-{model_id[4:]}"

    # Construct URL for model deployment based on the deployment system 
    deployment_system = model_deployment.get("deployment_system")
    if deployment_system is None:
        logger.error(f"Transaction-id: {transaction_id}, No deployment system specified for model_id: {model_id}")
        raise HTTPException(status_code=400, detail=f"No deployment system specified for model_id: {model_id}")

    if deployment_system  == "KserveV1":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed kserveV1 model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/v1/models/{mdl_service_name}:predict"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier kserve model url for the deployed model: {kourier_model_url}")

    elif deployment_system == "KserveV2":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed kserveV2 model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/v2/models/{mdl_service_name}/infer"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier kserve model url for the deployed model: {kourier_model_url}")

    elif deployment_system == "TextGeneration":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed TextGeneration model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/openai/v1/completions"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier TextGeneration model url for the deployed model: {kourier_model_url}")

    elif deployment_system == "Text2TextGeneration":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed Text2TextGeneration model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/openai/v1/completions"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier Text2TextGeneration model url for the deployed model: {kourier_model_url}")

    elif deployment_system == "TokenClassification":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed TokenClassification model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/v1/models/{mdl_service_name}:predict"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier TokenClassification model url for the deployed model: {kourier_model_url}")
    
    elif deployment_system == "TextClassification":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed TextClassification model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/v1/models/{mdl_service_name}:predict"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier TextClassification model url for the deployed model: {kourier_model_url}")
    
    elif deployment_system == "MLFlow":
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed mlflow model {model_id}")
        kourier_model_url = f"{config.MODEL_KOURIER_SERVICE_URL}/v2/models/{mdl_service_name}/infer"
        model_headers["Content-Type"] = "application/json"
        logger.debug(f"Transaction-id: {transaction_id}, Kourier mlflow model url for the deployed model: {kourier_model_url}")

    else:
        logger.error(f"Transaction-id: {transaction_id}, Deployment system not supported for the model_id: {model_id}")
        raise HTTPException(status_code=400, detail=f"Deployment system not supported for the model_id: {model_id}")

    if transformer_deployment:
        logger.info(f"Transaction-id: {transaction_id}, Extracting the transformer deployment headers, as the model has a transformer")
        transformer_headers = transformer_deployment.get("url_additions",{}).get("Headers",{})
            
        logger.info(f"Transaction-id: {transaction_id}, Constructing the kourier url for the deployed transformer {transformer_deployment.get('transformer_id')}")
        kourier_transformer_url = f"{config.TRANSFORMER_KOURIER_SERVICE_URL}"
        transformer_headers["Content-Type"] = "application/json"

        logger.debug(f"Transaction-id: {transaction_id}, Kourier transformer url for the deployed transformer: {kourier_transformer_url}")

    return kourier_model_url, kourier_transformer_url, model_headers, transformer_headers, project_id, deployment_system, mdl_service_name
