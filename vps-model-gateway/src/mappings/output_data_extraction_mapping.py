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

OUTPUT_DATA_EXTRACTION_KSERVE_V1_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data["predictions"][0]

extracted_output_data = extract_prediction_output_data(output_data)
"""

OUTPUT_DATA_EXTRACTION_KSERVE_V2_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data["outputs"][0]["data"]

extracted_output_data = extract_prediction_output_data(output_data)
"""
OUTPUT_DATA_EXTRACTION_TEXT_GENERATION_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data

extracted_output_data = extract_prediction_output_data(output_data)
"""
OUTPUT_DATA_EXTRACTION_TEXT2TEXT_GENERATION_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data

extracted_output_data = extract_prediction_output_data(output_data)
"""
OUTPUT_DATA_EXTRACTION_TOKEN_CLASSIFICATION_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data

extracted_output_data = extract_prediction_output_data(output_data)
"""
OUTPUT_DATA_EXTRACTION_TEXT_CLASSIFICATION_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data

extracted_output_data = extract_prediction_output_data(output_data)
"""

OUTPUT_DATA_EXTRACTION_MLFLOW_MAPPING_SCHEMA = """
def extract_prediction_output_data(output_data):
    return output_data

extracted_output_data = extract_prediction_output_data(output_data)
"""

DEPLOYMENT_SYSTEM_TO_EXTRACTOR_MAPPING = {
    "KserveV1": OUTPUT_DATA_EXTRACTION_KSERVE_V1_MAPPING_SCHEMA,
    "KserveV2": OUTPUT_DATA_EXTRACTION_KSERVE_V2_MAPPING_SCHEMA,
    "TextGeneration": OUTPUT_DATA_EXTRACTION_TEXT_GENERATION_MAPPING_SCHEMA,
    "Text2TextGeneration": OUTPUT_DATA_EXTRACTION_TEXT2TEXT_GENERATION_MAPPING_SCHEMA,
    "TokenClassification": OUTPUT_DATA_EXTRACTION_TOKEN_CLASSIFICATION_MAPPING_SCHEMA,
    "TextClassification": OUTPUT_DATA_EXTRACTION_TEXT_CLASSIFICATION_MAPPING_SCHEMA,
    'MLFlow': OUTPUT_DATA_EXTRACTION_MLFLOW_MAPPING_SCHEMA
}


