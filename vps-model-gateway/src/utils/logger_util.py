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

import logging
from src.models.env.env_config_DTO import EnvConfigDTO

config = EnvConfigDTO()

def setup_logger(name):
    """
    Configures and returns a logger.
    
    Args:
        name (str): Name of the logger.
    
    Returns:
        logging.Logger: Configured logger object.
    """
    logger = logging.getLogger(name)

    log_level_str = config.LOG_LEVEL.upper()  # Ensure uppercase for consistency
    log_level = getattr(logging, log_level_str, logging.INFO)  # Fallback to INFO if conversion fails
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:  # Prevent adding multiple handlers to the same logger
        logger.addHandler(ch)
    
    return logger
