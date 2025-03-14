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
from src.utils.aws_feature_plugin import AWSFeaturePlugin
from src.models.env.env_config_DTO  import EnvConfigDTO
from src.config.bucket_structure import BucketStructure
from boto3 import client
from botocore.exceptions import ClientError
from httpx import AsyncClient
from typing import Any
import httpx
import json

logger = setup_logger(__name__)

async def get_model_prediction_for_input_data(request: Request, client: AsyncClient, model_id: str, model_service_name: str, transaction_id: str, deployment_system: str, kourier_model_url: str, model_headers: dict, model_details: dict, model: dict, input_data: Any):

    config = EnvConfigDTO()

    notes = json.loads(model.get("notes")) if model.get("notes") else {}

    hf_max_token = notes.get("hf_max_token")

    logger.info(f"hugging_face_config: {hf_max_token}")
     
    max_tokens = 100
    if hf_max_token:
        max_tokens = hf_max_token

    if deployment_system == "KserveV1":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is kserve with protocol version v1, transforming the input data with instances.")
        input_data = {"instances": [input_data]}

    elif deployment_system == "KserveV2":
        
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is kserve with protocol version v2, transforming the input data with inputs.")
        model_input = model_details.get("input")
        kserve_data = {"inputs": []}
        input_instance = {}
        input_instance["data"] = input_data
        input_instance["shape"] = model_input.get("dims")
        input_instance["datatype"] = model_input.get("data_type")
        input_instance["name"] = model_input.get("name")
        kserve_data["inputs"].append(input_instance)
        input_data = kserve_data
        
    elif deployment_system == "TextGeneration":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is TextGeneration, transforming the input data with inputs.")
        input_instance = {}
        input_instance["model"] = model_service_name
        input_instance["prompt"] = input_data
        input_instance["stream"] = False
        input_instance["max_tokens"] = max_tokens
        input_data = input_instance

    elif deployment_system == "Text2TextGeneration":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is Text2TextGeneration, transforming the input data with inputs.")
        input_instance = {}
        input_instance["model"] = model_service_name
        input_instance["prompt"] = input_data
        input_instance["stream"] = False
        input_instance["max_tokens"] = max_tokens
        input_data = input_instance
    
    elif deployment_system == "TokenClassification":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is TokenClassification, transforming the input data with inputs.")
        input_data = {"instances": [input_data]}

    elif deployment_system == "TextClassification":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is TextClassification, transforming the input data with inputs.")
        input_data = {"instances": [input_data]}

    elif deployment_system == "MLFlow":
        logger.info(f"Transaction-id: {transaction_id}, Deployment system is MLFlow with protocol version v2, transforming the input data with inputs.")
        if isinstance(input_data, list):
            model_input = input_data[0] 
            mlflow_data = {"inputs": []}
            input_instance = {}
            input_instance["data"] = input_data  
            input_instance["shape"] = input_data["shape"]
            input_instance["datatype"] = input_data["datatype"]
            input_instance["name"] = input_data["name"] 

            mlflow_data["inputs"].append(input_instance)
            input_data = mlflow_data

    logger.info(f"Transaction-id: {transaction_id}, Making prediction request to the deployed model {model_id}.")

    async with client.stream("POST", kourier_model_url, headers=model_headers, json=input_data) as response:
        try:
            response.raise_for_status()
            # Check if content length is less than 5MB
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) <= config.MAX_PAYLOAD_SIZE * 1024 * 1024:
                logger.info(f"Content length is less than and equal to 5MB, returning response directly.")
                data = await response.aread()
                data = json.loads(data)

                if deployment_system == "KserveV1":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is kserve with protocol version v1, returning response directly.")
                    data = data["predictions"][0]

                elif deployment_system == "KserveV2":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is kserve with protocol version v2, returning response directly.")
                    data = data["outputs"][0]["data"]

                elif deployment_system == "TextGeneration":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is TextGeneration, returning response directly.")
                    logger.info(f"prediction data: {data}")
                    data = data

                elif deployment_system == "Text2TextGeneration":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is Text2TextGeneration, returning response directly.")
                    logger.info(f"prediction data: {data}")
                    data = data

                elif deployment_system == "TokenClassification":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is TokenClassification, returning response directly.")
                    logger.info(f"prediction data: {data}")
                    data = data

                elif deployment_system == "TextClassification":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is TextClassification, returning response directly.")
                    logger.info(f"prediction data: {data}")
                    data = data
                
                elif deployment_system == "MLFlow":
                    logger.info(f"Transaction-id: {transaction_id}, Deployment system is MLFlow, returning response directly.")
                    logger.info(f"prediction data: {data}")
                    data = data
                        
                return data, "content"
                
            logger.info(f"Transaction-id: {transaction_id}, Content length is more than 5MB, uploading the predicted data to S3 for the deployed model {model_id}.")
            aws_plugin = AWSFeaturePlugin()

            #Extracting the s3 client from the request state
            s3_client = request.app.state.s3_client

            bucket_structure = BucketStructure({"transaction_id": transaction_id}).get_bucket_structure()
            preffix = f"{bucket_structure['runtime_folder']}/model_prediction_response.txt"

            upload_id = aws_plugin.create_mutlipart_upload_and_retrieve_upload_id(s3_client, config.RUNTIME_BUCKET_NAME, preffix, transaction_id)

            parts = [] # List of parts to be uploaded
            part_number = 1

            async for chunk in response.aiter_bytes(chunk_size=5 * 1024 * 1024): # 5 MB chunk size
                part = aws_plugin.upload_chunk_part_for_the_multipart_upload(s3_client, upload_id, part_number, chunk, preffix, config.RUNTIME_BUCKET_NAME, transaction_id)
                parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                part_number += 1

            aws_plugin.complete_multipart_upload_for_the_multipart_upload(s3_client, upload_id, preffix, config.RUNTIME_BUCKET_NAME, parts, transaction_id)

            logger.info(f"Transaction-id: {transaction_id},Successfully uploaded the predicted data to S3 for the deployed model {model_id} on preffix {preffix}.")
            return  None, "url"

    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.info(f"Transaction-id: {transaction_id}, An HTTP status error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
            else:
                logger.error(f"Transaction-id: {transaction_id}, An HTTP status error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
            # Read the error detail from the response, if available
            error_detail = await e.response.aread()
            error_detail = get_error_detail(error_detail.decode())

            raise HTTPException(status_code=e.response.status_code, detail=f"An error occurred while making prediction request to the deployed model {model_id}: {error_detail}")
            
        except httpx.RequestError as e:
            logger.error(f"Transaction-id: {transaction_id}, An request error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An request error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
    
        except ClientError as e:
            logger.error(f"Transaction-id: {transaction_id}, An Client error occurred while uploading the predicted data to S3 for the deployed model {model_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred while uploading the predicted data to S3 for the deployed model {model_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Transaction-id: {transaction_id}, An unexpected error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while making prediction request to the deployed model {model_id}: {str(e)}")
        
            
