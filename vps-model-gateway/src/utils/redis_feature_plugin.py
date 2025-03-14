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

from rediscluster import RedisCluster
from redis.exceptions import RedisError
from fastapi import HTTPException
from src.models.env.env_config_DTO import EnvConfigDTO
from src.utils.logger_util import setup_logger

class RedisFeaturePlugin:
    def __init__(self):
        self.config = EnvConfigDTO()
        self.logger = setup_logger(self.__class__.__name__)

    def create_redis_client(self):
        try:
            self.logger.info(f"Connecting to Redis using startup nodes: {self.config.REDIS_STARTUP_NODES}")
            # Initialize RedisCluster with the startup nodes
            client = RedisCluster(startup_nodes=self.config.REDIS_STARTUP_NODES, decode_responses=True)
            return client
        
        except RedisError as e:
            self.logger.error(f"Failed to connect to Redis due to redis error: {e}")
            return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to Redis: {e}")
            return None

    def close_redis_client(self, client: RedisCluster):
        self.logger.info(f"Closing Redis connection")
        client.close()

    def check_rate_limit_exceeded_or_not_for_a_particular_user(self, client: RedisCluster, username: str, transaction_id: str, expire: int = 60):        
        try:
            self.logger.info(f"Transaction-id: {transaction_id}, Checking rate limit for user: {username}")
            current_count = client.get(username)
            if current_count is None:
                client.set(username, 1, ex=expire)
                return False
            else:
                ttl = client.ttl(username)
                if ttl == -1:  # Key exists but has expired
                    self.logger.info(f"Transaction-id: {transaction_id}, Rate limit key for user {username} has expired. Resetting key.")
                    # Delete the key
                    client.delete(username)
                    # Set new key with initial value and expiration
                    client.set(username, 1, ex=expire)
                    return False
                if int(current_count) < self.config.MAX_RATE_LIMIT:
                    client.incr(username)
                    self.logger.info(f"Transaction-id: {transaction_id}, Incremented rate limit count for user {username}. Current count: {int(current_count) + 1}.")
                    return False
                else:
                    self.logger.info(f"Transaction-id: {transaction_id}, Rate limit exceeded for user {username}. Current count: {current_count}.")
                    return True  # Rate limit exceeded
            
        except RedisError as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Redis error while checking rate limit: {e}")

        except Exception as e:
            self.logger.error(f"Transaction-id: {transaction_id}, Unexpected error while checking rate limit: {e}")
