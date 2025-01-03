from typing import Optional

import gym
import minihack  # NOQA: F401
from balrog.environments.nle import NLELanguageWrapper
from balrog.environments.wrappers import GymV21CompatibilityV0, NLETimeLimit

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

    strategies = []
    for strategy_name in config.strategies:
        strategy_func = get_function_by_name(config.strategies_loc, strategy_name)
        strategies.append(strategy_func)

    if config.code_wrapper:
        env = NLECodeWrapper(env, strategies)

    return env
