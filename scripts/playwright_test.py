import argparse
import glob
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List

import openai
import requests
import torch
from beartype import beartype
from PIL import Image

from agent import (
    PromptAgent,
    construct_agent,
)
from agent.prompts import *

from browser_env.actions import is_equivalent
from browser_env.helper_functions import (
    RenderHelper,
    get_action_description,
)
from evaluation_harness import evaluator_router, image_utils

###
from browser_env.env_config import *

##############
from playwright.sync_api import (
    CDPSession,
    Page,
    Playwright,
    ViewportSize,
    expect,
    sync_playwright,
)


LOG_FOLDER = "log_files"
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
LOG_FILE_NAME = f"{LOG_FOLDER}/log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(0, 10000)}.log"

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_NAME)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

def initialize_settings():
    global viewport_size
    global headless
    global slow_mo
    global url
    global config_file
    global observation_type
        
    viewport_size = {"width": 1280, "height": 720}
    headless=True
    slow_mo=0
    url="http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7770"
    config_file="config_files/test_shopping/0.json"
    observation_type="html"
        
def main():
    # ------------- Setup
    context_manager = sync_playwright()
    playwright = context_manager.__enter__()
    browser = playwright.chromium.launch(
        headless=headless, 
        slow_mo=slow_mo,
    )
    #
    with open(config_file, "r") as f:
        instance_config = json.load(f)
    storage_state = instance_config.get("storage_state", None)
    start_url = instance_config.get("start_url", None)
    geolocation = instance_config.get("geolocation", None)
    # Problematic with API ptoentailly
    context = browser.new_context(
        viewport=viewport_size,
        storage_state=storage_state,
        geolocation=geolocation,
        device_scale_factor=1,
    )
    page = context.new_page()
    client = page.context.new_cdp_session(
        page
    )  # talk to chrome devtools
    text_observation_type = observation_type 
    if text_observation_type in [
        "accessibility_tree",
        "accessibility_tree_with_captioner",
    ]:
        client.send("Accessibility.enable")
    page.client = client  # type: ignore
    page.goto(url)
    # set the first page as the current page
    page = context.pages[0]
    page.bring_to_front()
    # ------------- step
    
if __name__=="__main__":
    initialize_settings()
    
    main()