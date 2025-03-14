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
from src.utils.validate_auth_token_util import validate_auth_token
from src.utils.retrieve_deployment_info_util import retrieve_deployment_info_for_model_and_related_transformer
from src.utils.transform_input_data_for_model_util import check_pre_or_post_transform_input_data_for_model, pre_or_post_transform_input_data_for_model
from src.utils.model_prediction_util import get_model_prediction_for_input_data
from src.utils.retrieve_info_for_model_util import retrieve_info_for_model_and_transformer_if_exists
from src.utils.retrieve_model_details_info_util import retrieve_model_details_info
from src.utils.retrieve_entity_id_for_model_util import retrieve_entity_id_for_model
from src.utils.retrieve_list_of_authorized_model_for_app_util import retrieve_list_of_authorized_model_for_app
from src.utils.validate_entity_balance_util import validate_entity_balance
from src.config.bucket_structure import BucketStructure
from src.utils.redis_feature_plugin import RedisFeaturePlugin
from src.utils.aws_feature_plugin import AWSFeaturePlugin
from src.models.env.env_config_DTO  import EnvConfigDTO
from src.mappings.output_data_extraction_mapping import DEPLOYMENT_SYSTEM_TO_EXTRACTOR_MAPPING
from botocore.exceptions import ClientError
from typing import Any
import json
import httpx

logger = setup_logger(__name__)

async def model_prediction_service(request: Request, model_id: str, input_data: Any):
    redis_client = None
    try:
        config = EnvConfigDTO()
        logger.info(f"Received prediction request for model_id: {model_id}")

        #Deserializing the input data
        input_data = json.loads(input_data)

        #Extracting the vps-app-id from the request headers
        vps_app_id = request.headers.get("vps-app-id", None)

        #Extracting the vps-environment from the request headers
        vps_env_type = request.headers.get('vps-env-type', None)
        if vps_env_type is None or len(vps_env_type) == 0:
            logger.info("vps-env-type is missing or empty in the request header, continuing the prediction process.")
            #As discussed, this is not a security issue, will allow the prediction process to continue.

        #Extracting the vps-auth-token from the request headers
        vps_auth_token = request.headers.get("vps-auth-token", None)
        if vps_auth_token is None or len(vps_auth_token) == 0:
            logger.error("vps-auth-token is missing or empty in the request header, stopping the prediction process.")
            raise HTTPException(status_code=400, detail="Vps-auth-token is missing or empty in the request header, stopping the prediction process.")
        
        transaction_id = request.headers.get("transaction-id", None)
        if transaction_id is None or len(transaction_id) == 0:
            logger.error("Transaction-id is missing or empty in the request header, stopping the prediction process.")
            raise HTTPException(status_code=400, detail="Transaction-id is missing or empty in the request header, stopping the prediction process.")
        
        if ((vps_env_type == "vipas-streamlit") ^ (vps_auth_token.startswith("sat-"))):
            logger.error(f"Transaction-id: {transaction_id}, session token is not allowed for vps-env-type: {vps_env_type}, stopping the prediction process.")
            raise HTTPException(status_code=400, detail=f"Session token is not allowed for vps-env-type: {vps_env_type}, stopping the prediction process.")
        
        timeout = httpx.Timeout(300.0) # Timout settings for the async process.

        # Use httpx.AsyncClient for asynchronous request handling
        async with httpx.AsyncClient(timeout=timeout) as client:

            #Calling the user admin service to validate the vps-auth-token(User Authentication)
            user_data = await validate_auth_token(client, vps_auth_token, transaction_id)
               
            username = user_data.get("username")
            caller_entity_id = user_data.get("entity_id")
            retrieved_app_id = user_data.get("vps_app_id")

            if not username:
                logger.error(f"Transaction-id: {transaction_id}, Username not found for vps-auth-token: {vps_auth_token}, stopping the prediction process.")
                raise HTTPException(status_code=404, detail=f"Username not found for vps-auth-token: {vps_auth_token}, stopping the prediction process.")
            
            logger.info(f"Transaction-id: {transaction_id}, Checking if the caller {caller_entity_id} has sufficient balance to run the model {model_id} prediction") 
            await validate_entity_balance(client, caller_entity_id, model_id, vps_app_id, vps_env_type, transaction_id)
            
            #Calling the project admin service to get the list of authorized models(App Authorization)
            if vps_env_type == "vipas-streamlit":
                logger.info(f"Transaction-id: {transaction_id}, vps_env_type is vipas-streamlit, checking if the app is authorized to call the model: {model_id}")
                
                if vps_app_id is None or len(vps_app_id) == 0:
                    logger.error("Vps-app-id is missing or empty in the request header, stopping the prediction process.")
                    raise HTTPException(status_code=400, detail="Vps-app-id is missing or empty in the request header, stopping the prediction process.")
                
                if retrieved_app_id is None or len(retrieved_app_id) == 0:
                    logger.error(f"Transaction-id: {transaction_id}, Access token is not assigned to any app, stopping the prediction process.")
                    raise HTTPException(status_code=404, detail=f"Access token is not assigned to any app, stopping the prediction process.")
                
                if retrieved_app_id != "app-*" and retrieved_app_id != vps_app_id:
                    logger.error(f"Transaction-id: {transaction_id}, Access token is assigned to the app: {retrieved_app_id}, not the app: {vps_app_id}, stopping the prediction process.")
                    raise HTTPException(status_code=409, detail=f"Access token is assigned to the app: {retrieved_app_id}, not the app: {vps_app_id}, stopping the prediction process.")

                logger.info(f"Transaction-id: {transaction_id}, App header is set, checking if the app {vps_app_id} is authorized to call the model: {model_id}")
                auth_model_ids = await retrieve_list_of_authorized_model_for_app(client, vps_app_id, transaction_id)
                logger.info(f"Transaction-id: {transaction_id}, List of authorized models for app {vps_app_id}: {auth_model_ids}")

                if model_id not in auth_model_ids:
                    logger.error(f"Transaction-id: {transaction_id}, App: {vps_app_id} is not authorized to call the model: {model_id}")
                    raise HTTPException(status_code=403, detail=f"App: {vps_app_id} is not authorized to call the model: {model_id}")
            
            #Calling the project admin service to get the model details(User Authorization)
            model = await retrieve_model_details_info(client, model_id, transaction_id)

            logger.info(f"Transaction-id: {transaction_id}, Retrieving the entity id for the model: {model_id}")
            entity_id = await retrieve_entity_id_for_model(client, model.get("project_id"), transaction_id)

            logger.info(f"Transaction-id: {transaction_id}, Fetching the api access permission for the model: {model_id} for user: {username}")
            api_access = model.get("api_access")
            if api_access == "private" and caller_entity_id != entity_id:
                logger.error(f"Transaction-id: {transaction_id}, User: {username} does not have access to call the model: {model_id}")
                raise HTTPException(status_code=403, detail=f"User: {username} does not have access to call the model: {model_id}")

            logger.info(f"Transaction-id: {transaction_id}, Fetching the model details for the model: {model_id}")
            model_details = model.get("model_details", None)
            if model_details:
                model_details = json.loads(model_details)

            logger.info(f"Transaction-id: {transaction_id}, Checking if the rate limit is exceeded or not for user: {username}, creating the redis client")
            
            #Checking if the rate limit is exceeded or not
            redis_plugin = RedisFeaturePlugin()
            redis_client = redis_plugin.create_redis_client()

            if redis_client:
                result = redis_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(redis_client, username, transaction_id)
                if result:
                    logger.error(f"Transaction-id: {transaction_id}, Rate limit exceeded for user: {username}, stopping the prediction process.")
                    raise HTTPException(status_code=429, detail=f"Rate limit exceeded for user: {username}, stopping the prediction process, please wait for 60 seconds.")

            #Calling the deploy admin service to get the deployment details for that paritcular model
            deployment_data = await retrieve_deployment_info_for_model_and_related_transformer(client, model_id, transaction_id)

            model_deployment = deployment_data.get("model")
            transformer_deployment = deployment_data.get("transformer")

            if not model_deployment:
                logger.error(f"Transaction-id: {transaction_id}, Model deployment information not found in the database for the model_id: {model_id}")
                raise HTTPException(status_code=404, detail=f"Model deployment information not found for the model_id: {model_id}")
            
            kourier_model_url, kourier_transformer_url, model_headers, transformer_headers, project_id, deployment_system, mdl_service_name = retrieve_info_for_model_and_transformer_if_exists(model, model_deployment, transformer_deployment, transaction_id)

            logger.info(f"Transaction-id: {transaction_id}, Started the prediction process for the model {model_id}")
            if transformer_deployment:
                logger.info(f"Transaction-id: {transaction_id}, Transformer is present for the model {model_id}, checking if the pre transformer is present.")
                transformer_headers["transaction-id"] = transaction_id

                data = await check_pre_or_post_transform_input_data_for_model(client, project_id, model_id, transformer_deployment.get("transformer_id"), "pre_transform", kourier_transformer_url, transformer_headers, transaction_id)

                if data == True:
                    input_data = await pre_or_post_transform_input_data_for_model(client, project_id, model_id, transformer_deployment.get("transformer_id"), "pre_transform", kourier_transformer_url, transformer_headers, input_data, transaction_id)
                    input_data = input_data.get("data")

            output_data, payload_type = await get_model_prediction_for_input_data(request, client, model_id, mdl_service_name, transaction_id, deployment_system, kourier_model_url, model_headers, model_details, model, input_data)

            if payload_type == "url":
                logger.info(f"Transaction-id: {transaction_id}, Generating the presigned download URL for the prediction response for the model {model_id}")
                aws_plugin = AWSFeaturePlugin()

                #Extracting the s3 client from the request state
                s3_client = request.app.state.s3_client

                bucket_structure = BucketStructure({"transaction_id": transaction_id}).get_bucket_structure()
                model_prediction_response_preffix = f"{bucket_structure['runtime_folder']}/model_prediction_response.txt"

                presigned_download_url = aws_plugin.generate_presigned_download_url(s3_client, config.RUNTIME_BUCKET_NAME, model_prediction_response_preffix, transaction_id)

            if transformer_deployment:
                logger.info(f"Transaction-id: {transaction_id}, Transformer is present for the model {model_id}, checking if the post transformer is present.")
                data = await check_pre_or_post_transform_input_data_for_model(client, project_id, model_id, transformer_deployment.get("transformer_id"), "post_transform", kourier_transformer_url, transformer_headers, transaction_id)

                if data == True:
                    if payload_type == "url":
                        logger.info(f"Transaction-id: {transaction_id}, Generating the presigned upload URL for the post processor response for the model {model_id}")

                        post_processor_response_preffix = f"{bucket_structure['runtime_folder']}/post_processor_response.txt"

                        presigned_upload_url = aws_plugin.generate_presigned_upload_url(s3_client, config.RUNTIME_BUCKET_NAME, post_processor_response_preffix, transaction_id)

                        if not presigned_upload_url:
                            logger.error(f"Transaction-id: {transaction_id}, Failed to generate the presigned upload URL for the post processor response for the model {model_id}")
                            raise HTTPException(status_code=500, detail=f"Failed to generate the presigned upload URL for the post processor response for the model {model_id}")

                        output_data = {"presigned_download_url": presigned_download_url, "presigned_upload_url": presigned_upload_url, "extractor": DEPLOYMENT_SYSTEM_TO_EXTRACTOR_MAPPING.get(deployment_system)}

                    transformer_headers["payload_type"] = payload_type 

                    output_data = await pre_or_post_transform_input_data_for_model(client, project_id, model_id, transformer_deployment.get("transformer_id"), "post_transform", kourier_transformer_url, transformer_headers, output_data, transaction_id)

                    if output_data.get("payload_type") == "url":

                        logger.info(f"Transaction-id: {transaction_id}, Content type is {output_data.get('payload_type')}, generating the presigned download URL for the post processor response for the model {model_id}")
                        presigned_download_url = aws_plugin.generate_presigned_download_url(s3_client, config.RUNTIME_BUCKET_NAME, post_processor_response_preffix, transaction_id)
                        return {"output_data": None, "payload_type": output_data.get("payload_type"), "payload_url": presigned_download_url, "extractor" : None}
                    
                    elif output_data.get("payload_type") == "content":

                        logger.info(f"Transaction-id: {transaction_id}, Content type is {output_data.get('payload_type')}, returning the output data for the model {model_id}")
                        return {"output_data": output_data.get("data"), "payload_type": output_data.get("payload_type"), "payload_url": None, "extractor" : None}
                    
                    else:
                        logger.error(f"Transaction-id: {transaction_id}, Payload type {output_data.get('payload_type')} is not supported")
                        raise HTTPException(status_code=500, detail=f"Payload type {output_data.get('payload_type')} is not supported")

            if payload_type == "url":
                logger.info(f"Transaction-id: {transaction_id}, Output data is None, returning the presigned download URL for the prediction response for the model {model_id}")
                return {"output_data": None, "payload_type": payload_type, "payload_url": presigned_download_url, "extractor": DEPLOYMENT_SYSTEM_TO_EXTRACTOR_MAPPING.get(deployment_system)}
            

            logger.info(f"Transaction-id: {transaction_id}, Output data is present, returning the output data for the model {model_id}")
            return {"output_data": output_data, "payload_type": payload_type, "payload_url": None, "extractor": None}
    
    except json.JSONDecodeError as e:
        logger.error(f"Transaction-id: {transaction_id}, The model details for model {model_id} is not a valid JSON: {str(e)}")
        HTTPException(status_code=500, detail=f"The model details for model {model_id} is not a valid JSON: {str(e)}")
            
    except HTTPException as e:
        if e.status_code == 400:
            logger.info(f"Transaction-id: {transaction_id}, The model details for model {model_id} is not a valid JSON: {str(e)}")
        else:
            logger.error(f"An error occurred while making prediction request to the deployed model {model_id}: {e.detail}")
        raise e

    except ClientError as e:
        logger.error(f"An client error occurred while making prediction request to the deployed model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An client error occurred while making prediction request to the deployed model {model_id}: {e}")
    
    except Exception as e:
        logger.error(f"An unexpected error occurred while making prediction request to the deployed model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while making prediction request to the deployed model {model_id}: {e}")
    
    finally:
        logger.info(f"Closing the redis client for model {model_id}. if it was initialized")
        if redis_client:
            redis_plugin.close_redis_client(redis_client)
        
                