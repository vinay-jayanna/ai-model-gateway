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

from fastapi import FastAPI
from src.models.env.env_config_DTO import EnvConfigDTO
from dotenv import load_dotenv
from src.controllers import model_controller
from src.utils.redis_feature_plugin import RedisFeaturePlugin
from src.utils.aws_feature_plugin import AWSFeaturePlugin
from prometheus_fastapi_instrumentator import Instrumentator

aws_plugin = AWSFeaturePlugin()

load_dotenv()
app = FastAPI()
config = EnvConfigDTO()

def startup_event():
    app.state.s3_client = aws_plugin.create_s3_client()

def shutdown_event():
    aws_plugin.close_s3_client(app.state.s3_client)

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

app.include_router(model_controller.router)

Instrumentator().instrument(app).expose(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)