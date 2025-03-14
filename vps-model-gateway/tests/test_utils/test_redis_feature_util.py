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

from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from src.models.env.env_config_DTO import EnvConfigDTO
from src.utils.redis_feature_plugin import RedisFeaturePlugin
from redis.exceptions import RedisError
import pytest

@pytest.fixture
def redis_feature_plugin():
    return RedisFeaturePlugin()

@pytest.fixture(autouse=True)
def mock_env_config(mocker):
    mock_config = mocker.patch("src.utils.redis_feature_plugin.EnvConfigDTO", autospec=True)
    mock_config_instance = mock_config.return_value
    mock_config_instance.REDIS_STARTUP_NODES = [
        {"host": "testserver1", "port": 6379},
        {"host": "testserver2", "port": 6379}
    ]
    mock_config_instance.MAX_RATE_LIMIT = 60
    return mock_config

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch("src.utils.redis_feature_plugin.setup_logger", autospec=True)

def test_create_redis_client_success(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster', new_callable=MagicMock) as mock_redis_cluster:
        mock_client = MagicMock()
        mock_redis_cluster.return_value = mock_client
        
        client = redis_feature_plugin.create_redis_client()
        assert client == mock_client
        mock_redis_cluster.assert_called_once_with(
            startup_nodes=redis_feature_plugin.config.REDIS_STARTUP_NODES,
            decode_responses=True
        )

def test_create_redis_client_redis_error(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster', new_callable=MagicMock) as mock_redis_cluster:
        mock_redis_cluster.side_effect = RedisError("Redis connection error")

        client = redis_feature_plugin.create_redis_client()
        assert client is None

def test_create_redis_client_unexpected_error(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster', new_callable=MagicMock) as mock_redis_cluster:
        mock_redis_cluster.side_effect = Exception("Unexpected error")

        client = redis_feature_plugin.create_redis_client()
        assert client is None

def test_close_redis_client(redis_feature_plugin):
    mock_client = MagicMock()
    
    redis_feature_plugin.close_redis_client(mock_client)
    mock_client.close.assert_called_once()

def test_check_rate_limit_not_exceeded(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster.get', new_callable=MagicMock) as mock_get, \
         patch('src.utils.redis_feature_plugin.RedisCluster.set', new_callable=MagicMock) as mock_set, \
         patch('src.utils.redis_feature_plugin.RedisCluster.incr', new_callable=MagicMock) as mock_incr, \
         patch('src.utils.redis_feature_plugin.RedisCluster.ttl', new_callable=MagicMock) as mock_ttl:

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.set = mock_set
        mock_client.incr = mock_incr
        mock_client.ttl = mock_ttl
        
        mock_get.return_value = None
        mock_ttl.return_value = -2

        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is False
        mock_set.assert_called_once_with("user1", 1, ex=60)

        mock_get.return_value = "59"
        mock_ttl.return_value = 30
        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is False
        mock_incr.assert_called_once_with("user1")

def test_check_rate_limit_exceeded(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster.get', new_callable=MagicMock) as mock_get, \
         patch('src.utils.redis_feature_plugin.RedisCluster.ttl', new_callable=MagicMock) as mock_ttl:

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.ttl = mock_ttl

        mock_get.return_value = "60"
        mock_ttl.return_value = 10

        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is True

def test_check_rate_limit_key_expired(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster.get', new_callable=MagicMock) as mock_get, \
         patch('src.utils.redis_feature_plugin.RedisCluster.ttl', new_callable=MagicMock) as mock_ttl, \
         patch('src.utils.redis_feature_plugin.RedisCluster.delete', new_callable=MagicMock) as mock_delete, \
         patch('src.utils.redis_feature_plugin.RedisCluster.set', new_callable=MagicMock) as mock_set:

        mock_client = MagicMock()
        mock_client.get = mock_get
        mock_client.ttl = mock_ttl
        mock_client.delete = mock_delete
        mock_client.set = mock_set

        mock_get.return_value = "60"
        mock_ttl.return_value = -1

        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is False
        mock_delete.assert_called_once_with("user1")
        mock_set.assert_called_once_with("user1", 1, ex=60)

def test_check_rate_limit_redis_error(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster.get', new_callable=MagicMock) as mock_get:
        mock_get.side_effect = RedisError("Redis error")

        mock_client = MagicMock()
        mock_client.get = mock_get

        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is None

def test_check_rate_limit_unexpected_error(redis_feature_plugin):
    with patch('src.utils.redis_feature_plugin.RedisCluster.get', new_callable=MagicMock) as mock_get:
        mock_get.side_effect = Exception("Unexpected error")

        mock_client = MagicMock()
        mock_client.get = mock_get

        result = redis_feature_plugin.check_rate_limit_exceeded_or_not_for_a_particular_user(mock_client, "user1", "transaction_id")
        assert result is None
