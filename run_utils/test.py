import argparse
import json
import logging
from pathlib import Path

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
from browser_env import (
    Action,
    ActionTypes,
    ScriptBrowserEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)
from browser_env.actions import is_equivalent
from browser_env.helper_functions import (
    RenderHelper,
    get_action_description,
)
from evaluation_harness import image_utils
from evaluation_harness.evaluators import evaluator_router

from run_utils.logging import logger

@beartype
def test(
    args: argparse.Namespace,
    config_file_list: list[str]
) -> None:
    scores = []
    max_steps = args.max_steps

    early_stop_thresholds = {
        "parsing_failure": args.parsing_failure_th,
        "repeating_action": args.repeating_action_failure_th,
    }

    if args.observation_type in [
        "accessibility_tree_with_captioner",
        "image_som",
    ]:
        device = torch.device(args.eval_captioning_model_device)
        dtype = torch.float16 if args.eval_captioning_model_device == "cuda" else torch.float32
        caption_image_fn = image_utils.get_captioning_fn(
            device, dtype, args.captioning_model
        )
    else:
        caption_image_fn = None

    # Load a (possibly different) captioning model for running VQA evals.
    if (
        caption_image_fn
        and args.eval_captioning_model == args.captioning_model
    ):
        eval_caption_image_fn = caption_image_fn
    else:
        eval_caption_image_fn = image_utils.get_captioning_fn(
            args.eval_captioning_model_device,
            dtype,
            args.eval_captioning_model,
        )

    agent = construct_agent(
        args, captioning_fn=caption_image_fn
        if args.observation_type == "accessibility_tree_with_captioner"
        else None,
    )  
    # NOTE: captioning_fn here is used for captioning input images.

    env = ScriptBrowserEnv(
        headless=not args.render,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        current_viewport_only=args.current_viewport_only,
        viewport_size={
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        save_trace_enabled=args.save_trace_enabled,
        sleep_after_execution=args.sleep_after_execution,
        # NOTE: captioning_fn here is used for LLM + captioning baselines.
        # This can be different from the captioning model used for evals.
        captioning_fn=caption_image_fn,
    )
    logger.info(f"Configuration files:{config_file_list}")
    for config_file in config_file_list:
        try:
            render_helper = RenderHelper(
                config_file, args.result_dir, args.action_set_tag
            )

            # Load task.
            with open(config_file) as f:
                _c = json.load(f)
                intent = _c["intent"]
                task_id = _c["task_id"]
                image_paths = _c.get("image", None)
                images = []

                # Load input images for the task, if any.
                if image_paths is not None:
                    if isinstance(image_paths, str):
                        image_paths = [image_paths]
                    for image_path in image_paths:
                        # Load image either from the web or from a local path.
                        if image_path.startswith("http"):
                            input_image = Image.open(requests.get(image_path, stream=True).raw)
                        else:
                            input_image = Image.open(image_path)
                        
                        images.append(input_image)

            logger.info(f"[Config file]: {config_file}")
            logger.info(f"[Intent]: {intent}")

            agent.reset(config_file)
            trajectory: Trajectory = []
            
            obs, info = env.reset(
                options={"config_file": config_file})
            state_info: StateInfo = {
                "observation": obs, "info": info
            }
            trajectory.append(state_info)

            meta_data = {"action_history": ["None"]}
            while True:
                early_stop_flag, stop_info = early_stop(
                    trajectory, max_steps, early_stop_thresholds
                )

                if early_stop_flag:
                    action = create_stop_action(f"Early stop: {stop_info}")
                else:
                    try:
                        action = agent.next_action(
                            trajectory,
                            intent,
                            images=images,
                            meta_data=meta_data,
                        )
                    except ValueError as e:
                        # get the error message
                        action = create_stop_action(f"ERROR: {str(e)}")

                trajectory.append(action)

                action_str = get_action_description(
                    action,
                    state_info["info"]["observation_metadata"],
                    action_set_tag=args.action_set_tag,
                    prompt_constructor=agent.prompt_constructor
                    if isinstance(agent, PromptAgent)
                    else None,
                )
                render_helper.render(
                    action, state_info, meta_data, args.render_screenshot
                )
                meta_data["action_history"].append(action_str)

                if action["action_type"] == ActionTypes.STOP:
                    break

                obs, _, terminated, _, info = env.step(action)
                state_info = {"observation": obs, "info": info}
                trajectory.append(state_info)

                if terminated:
                    # add a action place holder
                    trajectory.append(create_stop_action(""))
                    break

            # NOTE: eval_caption_image_fn is used for running eval_vqa functions.
            evaluator = evaluator_router(
                config_file, 
                captioning_fn=eval_caption_image_fn
            )
            score = evaluator(
                trajectory=trajectory,
                config_file=config_file,
                page=env.page,
                client=env.get_page_client(env.page),
            )
            scores.append(score)

            if score == 1:
                logger.info(f"[Result] (PASS) {config_file}")
            else:
                logger.info(f"[Result] (FAIL) {config_file}")

            if args.save_trace_enabled:
                env.save_trace(
                    Path(args.result_dir) / "traces" / f"{task_id}.zip"
                )
        except openai.OpenAIError as e:
            logger.info(f"[OpenAI Error] {repr(e)}")
        except Exception as e:
            logger.info(f"[Unhandled Error] {repr(e)}]")
            import traceback

            # write to error file
            with open(Path(args.result_dir) / "error.txt", "a") as f:
                f.write(f"[Config file]: {config_file}\n")
                f.write(f"[Unhandled Error] {repr(e)}\n")
                f.write(traceback.format_exc())  # write stack trace to file
        render_helper.close()

    env.close()
    logger.info(f"Average score: {sum(scores) / len(scores)}")
    
@beartype
def early_stop(
    trajectory: Trajectory, max_steps: int, 
    thresholds: dict[str, int]
) -> tuple[bool, str]:
    """
    Check for early stopping conditions based on the trajectory, max steps, and thresholds.
    
    Parameters:
    - trajectory: The sequence of actions taken.
    - max_steps: The maximum number of steps allowed.
    - thresholds: A dictionary containing thresholds for different conditions.
    
    Returns:
    - A tuple containing a boolean indicating if early stopping condition is met and a message.
    """
    # reach the max step
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    last_k_actions: list[Action]
    action_seq: list[Action]

    # Case: parsing failure for k times
    k = thresholds["parsing_failure"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    if len(last_k_actions) >= k:
        if all(
            [
                action["action_type"] == ActionTypes.NONE
                for action in last_k_actions
            ]
        ):
            return True, f"Failed to parse actions for {k} times"

    # Case: same action for k times
    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    action_seq = trajectory[1::2]  # type: ignore[assignment]

    if len(action_seq) == 0:
        return False, ""

    last_action: Action = action_seq[-1]

    if last_action["action_type"] != ActionTypes.TYPE:
        if len(last_k_actions) >= k:
            if all(
                [
                    is_equivalent(action, last_action)
                    for action in last_k_actions
                ]
            ):
                return True, f"Same action for {k} times"

    else:
        # check the action sequence
        if (
            sum([is_equivalent(action, last_action) for action in action_seq])
            >= k
        ):
            return True, f"Same typing action for {k} times"

    return False, ""