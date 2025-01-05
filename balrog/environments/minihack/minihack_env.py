from typing import Optional
import inspect

import gym
import minihack  # NOQA: F401
from balrog.environments.nle import NLELanguageWrapper
from balrog.environments.wrappers import GymV21CompatibilityV0, NLETimeLimit

import nle_code_wrapper.bot.panics as panic_module
import nle_code_wrapper.bot.strategies as strategy_module
from nle_code_wrapper.utils.utils import get_function_by_name
from nle_code_wrapper.wrappers.nle_code_wrapper import NLECodeWrapper

MINIHACK_ENVS = []
for env_spec in gym.envs.registry.all():
    id = env_spec.id
    if id.split("-")[0] == "MiniHack":
        MINIHACK_ENVS.append(id)


def make_minihack_env(env_name, task, config, render_mode: Optional[str] = None):
    minihack_kwargs = dict(config.envs.minihack_kwargs)
    skip_more = minihack_kwargs.pop("skip_more", False)
    vlm = True if config.agent.max_image_history > 0 else False
    env = gym.make(
        task,
        observation_keys=[
            "glyphs",
            "blstats",
            "tty_chars",
            "inv_letters",
            "inv_strs",
            "tty_cursor",
            "tty_colors",
            "message",
            "tty_cursor",
            "inv_oclasses",
            "inv_glyphs",
        ],
        **minihack_kwargs,
    )
    env = NLELanguageWrapper(env, vlm=vlm, skip_more=skip_more, use_language_action=config.use_language_action)

    # wrap NLE with timeout
    env = NLETimeLimit(env)

    env = GymV21CompatibilityV0(env=env, render_mode=render_mode)

    if config.code_wrapper:
        if len(config.strategies) > 0:
            if isinstance(config.strategies[0], str):
                strategies = []
                for strategy_name in config.strategies:
                    strategy_func = get_function_by_name(config.strategies_loc, strategy_name)
                    strategies.append(strategy_func)
        else:
            strategies = [obj for name, obj in inspect.getmembers(strategy_module, inspect.isfunction)]

        if len(config.panics) > 0:
            if isinstance(config.panics[0], str):
                panics = []
                for panic_name in config.panics:
                    panic_func = get_function_by_name(config.panics_loc, panic_name)
                    panics.append(panic_func)
        else:
            panics = [obj for name, obj in inspect.getmembers(panic_module, inspect.isfunction)]

        gamma = config.gamma if hasattr(config, "gamma") else 1.0
        env = NLECodeWrapper(
            env, 
            strategies, 
            panics, 
            max_strategy_steps=config.max_strategy_steps, 
            gamma=gamma,
            add_letter_strategies=config.add_letter_strategies,
            add_direction_strategies=config.add_direction_strategies,
            add_more_strategy=config.add_more_strategy,
        )

    return env
