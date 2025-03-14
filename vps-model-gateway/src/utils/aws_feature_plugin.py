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
#  

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from src.utils.logger_util import setup_logger  
from src.models.env.env_config_DTO import EnvConfigDTO
from fastapi.exceptions import HTTPException
from boto3 import client

class AWSFeaturePlugin:
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)  # Setup logger for the class
        self.config = EnvConfigDTO()

    def create_s3_client(self):
        try:
            self.logger.info("Creating S3 client")
            return boto3.client(
                "s3",
                region_name=self.config.AWS_REGION
            )
        except BotoCoreError as e:
            self.logger.error(f"Failed to create S3 client due to BotoCoreError: {e}")
            raise
        except ClientError as e:
            self.logger.error(f"Failed to create S3 client due to ClientError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while trying to create S3 client: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating S3 client.")

        
    def close_s3_client(self, s3_client : client):
        s3_client.close()
    
    def generate_presigned_download_url(self, s3_client : client, bucket_name, s3_key, transaction_id, expiration=300):
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Generating presigned URL for file: {s3_key} in bucket {bucket_name}")
            response = s3_client.generate_presigned_url('get_object',
                                                      Params={'Bucket': bucket_name,
                                                              'Key': s3_key},
                                                      ExpiresIn=expiration)
            self.logger.info(f"Transaction-id: {transaction_id}, Presigned URL generated successfully for {s3_key} in bucket {bucket_name}")
            return response
        except ClientError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Failed to generate presigned URL due to ClientError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexcepted Error while trying to upload file to S3: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while generating presigned URL.")
    
    
    def generate_presigned_upload_url(self, s3_client: client, bucket_name: str, s3_key: str, transaction_id: str, file_type:str = "text/plain", expiration=300):
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Generating presigned upload URL for file: {s3_key} in bucket {bucket_name}")

            # Maximum file size in bytes for the presigned URL
            max_file_size = self.config.MAX_POST_FILE_SIZE * 1024 * 1024  # 500 MB in bytes

            # Conditions and fields for the presigned URL
            conditions = [
                ["content-length-range", 0, max_file_size],
                ["eq", "$Content-Type", file_type]
            ]
            fields = {"Content-Type": file_type}

            presigned_post = s3_client.generate_presigned_post(Bucket=bucket_name,
                                                               Key=s3_key,
                                                               Fields=fields,
                                                               Conditions=conditions,
                                                               ExpiresIn=expiration)

            self.logger.info(f"Transaction-id: {transaction_id}, Presigned upload URL generated successfully for {s3_key} in bucket {bucket_name}")
            return presigned_post
        except ClientError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Failed to generate presigned upload URL due to ClientError: {e}")
            raise 
        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexpected error while trying to generate presigned upload URL: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while generating presigned upload URL.")
        
    
    def create_mutlipart_upload_and_retrieve_upload_id(self, s3_client: client, bucket_name: str, s3_key: str, transaction_id: str):
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Creating multipart upload for file: {s3_key} in bucket {bucket_name}")
            response = s3_client.create_multipart_upload(Bucket=bucket_name, Key=s3_key)
            self.logger.info(f"Transaction-id: {transaction_id}, Multipart upload created successfully for {s3_key} in bucket {bucket_name}")
            return response['UploadId']
        except ClientError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Failed to create multipart upload due to ClientError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexpected error while trying to create multipart upload: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating multipart upload.")
        
    def upload_chunk_part_for_the_multipart_upload(self, s3_client: client, upload_id: str, part_number: int, chunk: bytes, s3_key: str, bucket_name: str, transaction_id: str):
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Uploading chunk part {part_number} for file: {s3_key} in bucket {bucket_name}")
            response = s3_client.upload_part(Bucket=bucket_name, Key=s3_key, PartNumber=part_number, UploadId=upload_id, Body=chunk)
            self.logger.info(f"Transaction-id: {transaction_id}, Chunk part {part_number} uploaded successfully for {s3_key} in bucket {bucket_name}")
            return response
        except ClientError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Failed to upload chunk part {part_number} due to ClientError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexpected error while trying to upload chunk part {part_number}: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while uploading chunk part.")
        
    def complete_multipart_upload_for_the_multipart_upload(self, s3_client: client, upload_id: str, s3_key: str, bucket_name: str, parts : list, transaction_id: str):
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Completing multipart upload for file: {s3_key} in bucket {bucket_name}")
            response = s3_client.complete_multipart_upload(Bucket=bucket_name, Key=s3_key, UploadId=upload_id, MultipartUpload={'Parts': parts})
            self.logger.info(f"Transaction-id: {transaction_id}, Multipart upload completed successfully for {s3_key} in bucket {bucket_name}")
            return response
        except ClientError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Failed to complete multipart upload due to ClientError: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexpected error while trying to complete multipart upload: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while completing multipart upload.")
        