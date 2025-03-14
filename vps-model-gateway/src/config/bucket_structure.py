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

from src.utils.logger_util import setup_logger
import yaml
import os

logger = setup_logger(__name__)

class BucketStructure:
    def __init__(self, project_details):
        logger.debug(f"Initializing BucketStructure with project_details: {project_details}")
        self.bucket_structure = None
        self.intake_artifacts_details = project_details
        self.project_id = self.intake_artifacts_details.get("project_id")
        self.entity_id = self.intake_artifacts_details.get("entity_id")
        self.project_type = self.intake_artifacts_details.get("project_type")
        self.version = self.intake_artifacts_details.get("version")
        self.model_id = self.intake_artifacts_details.get("model_id")
        self.app_id = self.intake_artifacts_details.get("app_id")
        self.transformer_id = self.intake_artifacts_details.get("transformer_id")
        self.build_id = self.intake_artifacts_details.get("build_id")
        self.transaction_id = self.intake_artifacts_details.get("transaction_id")
        self.challenge_id = self.intake_artifacts_details.get("challenge_id")

        try:
            blueprint_config_file = os.path.join("/app/config", "folder_structure_blueprint.yaml")
            with open(blueprint_config_file, "r") as file:
                config_data = yaml.safe_load(file)
            # Iterate through the blueprint dictionary and replace the placeholders
            for key, value in config_data["folder_structure_blueprint"].items():
                config_data["folder_structure_blueprint"][key] = value.format(
                    entity_id=self.entity_id,
                    project_id=self.project_id,
                    project_type=self.project_type,
                    version=self.version,
                    model_id=self.model_id,
                    app_id=self.app_id,
                    transformer_id=self.transformer_id,
                    build_id=self.build_id,
                    transaction_id=self.transaction_id,
                    challenge_id=self.challenge_id
                )
            self.bucket_structure = config_data["folder_structure_blueprint"]
        except Exception as e:
            print(f"Failed to load bucket structure blueprint: {e}")
            raise e

    def get_bucket_structure(self):
        if self.bucket_structure is None:
            raise Exception("Bucket structure not initialized")
        return self.bucket_structure
