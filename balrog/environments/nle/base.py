import random

from nle import nle_language_obsv
from nle.language_wrapper.wrappers import nle_language_wrapper as language_wrapper
from nle.nethack import USEFUL_ACTIONS
from PIL import Image

from balrog.environments import Strings

from ..minihack import ACTIONS as MINIHACK_ACTIONS
from .progress import get_progress_system
from .render import tty_render_image
from .render_rgb import rgb_render_image


class NLELanguageWrapper(language_wrapper.NLELanguageWrapper):
    def __init__(self, env, vlm=False, skip_more=False, use_language_action: bool = True):
        super().__init__(env, use_language_action=use_language_action)
        self.nle_language = nle_language_obsv.NLELanguageObsv()
        self.language_action_space = self.create_action_space()
        self.env = env
        self.vlm = vlm
        self.done = False
        self.skip_more = skip_more

        if not vlm:
            self.prompt_mode = "hybrid"
        else:
            self.prompt_mode = "language"

        self.progress = get_progress_system(self.env)
        self.max_steps = self.env.unwrapped._max_episode_steps

    def step(self, action):
        obs, reward, done, info = super().step(action)
        self.done = done if not self.done else self.done
        self.progress.update(obs["obs"], reward, self.done, info)
        return obs, reward, self.done, info

    def post_reset(self, obsv):
        return self.post_step(obsv)

    def reset(self, **kwargs):
        self.progress = get_progress_system(self.env)
        obsv = self.env.reset(**kwargs)
        return self.post_reset(obsv)

    def post_step(self, nle_obsv):
        return self.nle_process_obsv(nle_obsv)

    @property
    def default_action(self):
        if "minihack" in self.env.spec.id.lower():
            return "north"
        else:
            return "esc"

    def get_text_action(self, action):
        return NLELanguageWrapper.all_nle_action_map[self.env.actions[action]][0]

    def nle_process_obsv(self, nle_obsv):
        img = Image.fromarray(self.render("tiles")).convert("RGB") if self.vlm else None
        text = self.nle_obsv_type(nle_obsv)

        return {
            "text": text,
            "image": img,
            "obs": nle_obsv,
        }

    def nle_obsv_type(self, nle_obsv):
        nle_obsv = self.nle_obsv_to_language(nle_obsv)
        if self.prompt_mode == "language":
            return self.render_text(nle_obsv)
        elif self.prompt_mode == "hybrid":
            return self.render_hybrid(nle_obsv)
        else:
            raise ValueError(f'"{self.prompt_mode}" is not a valid prompt mode.')

    def clean_message(self, nle_obsv):
        message = self.nle_language.text_message(nle_obsv["tty_chars"]).decode("latin-1")
        if not self.skip_more:
            while "--More--" in message and not self.done:
                message = message.replace("--More--", " ")
                message = message.replace("\n", " ")

                nle_obsv, reward, self.done, info = self.step("more")
                add = self.nle_language.text_message(nle_obsv["obs"]["tty_chars"]).decode("latin-1")
                message += add
                return message, nle_obsv["obs"]
        return message, nle_obsv

    def render(self, mode="human"):
        if mode == "tiles":
            obs = self.env.last_observation
            glyphs = obs[self.env._observation_keys.index("glyphs")]
            return rgb_render_image(glyphs)
        elif mode == "tty_image":
            obs = self.env.last_observation
            tty_chars = obs[self.env._observation_keys.index("tty_chars")]
            tty_colors = obs[self.env._observation_keys.index("tty_colors")]
            return tty_render_image(tty_chars, tty_colors)
        else:
            return super().render(mode)

    def get_stats(self):
        return self.progress.__dict__

    def create_action_space(self):
        if "minihack" in self.env.spec.id.lower():
            available_actions = {}
            for action in self.env.actions:
                action_key = NLELanguageWrapper.all_nle_action_map[action][0]
                if action_key not in MINIHACK_ACTIONS:
                    continue
                available_actions[action_key] = MINIHACK_ACTIONS[action_key]

            all_actions = [action for action, _ in available_actions.items()]

        else:
            available_actions = [
                action_strs[0]
                for action, action_strs in NLELanguageWrapper.all_nle_action_map.items()
                if action in USEFUL_ACTIONS
            ]
            single_chars = [chr(i) for i in range(ord("a"), ord("z") + 1)] + [
                chr(i) for i in range(ord("A"), ord("Z") + 1)
            ]
            single_digits = [str(i) for i in range(10)]
            double_digits = [f"{i:02d}" for i in range(100)]
            all_actions = available_actions + single_chars + single_digits + double_digits

        return Strings(all_actions)

    def ascii_render(self, chars):
        rows, cols = chars.shape
        result = ""
        for i in range(rows):
            for j in range(cols):
                entry = chr(chars[i, j])
                result += entry
            result += "\n"
        return result

    def nle_obsv_to_language(self, nle_obsv):
        """Translate NLE Observation into a language observation.
        Args:
            nle_obsv (dict): NLE observation from the base environment
        Returns:
            (dict): language observation
        """

        message, nle_obsv = self.clean_message(nle_obsv)

        glyphs = nle_obsv["glyphs"]
        blstats = nle_obsv["blstats"]
        tty_cursor = nle_obsv["tty_cursor"]
        inv_strs = nle_obsv["inv_strs"]
        inv_letters = nle_obsv["inv_letters"]

        return {
            "text_glyphs": self.nle_language.text_glyphs(glyphs, blstats).decode("latin-1"),
            "text_message": message,
            "text_blstats": self.nle_language.text_blstats(blstats).decode("latin-1"),
            "text_inventory": self.nle_language.text_inventory(inv_strs, inv_letters).decode("latin-1"),
            "text_cursor": self.nle_language.text_cursor(glyphs, blstats, tty_cursor).decode("latin-1"),
            "tty_chars": nle_obsv["tty_chars"],
            "tty_cursor": nle_obsv["tty_cursor"],
        }

    def render_text(self, nle_obsv):
        long_term_observations = [
            ("text_message", "message"),
            ("text_glyphs", "language observation"),
            ("text_cursor", "cursor"),
        ]

        short_term_observations = [
            ("text_blstats", "statistics"),
            ("text_inventory", "inventory"),
        ]

        long_term_context = "\n".join([f"{name}:\n{nle_obsv[key]}\n" for key, name in long_term_observations])
        short_term_context = "\n".join([f"{name}:\n{nle_obsv[key]}\n" for key, name in short_term_observations])

        return {
            "long_term_context": long_term_context,
            "short_term_context": short_term_context,
        }

    def render_hybrid(self, nle_obsv):
        ascii_map = self.ascii_render(nle_obsv["tty_chars"])
        cursor = nle_obsv["tty_cursor"]
        cursor = f"(x={cursor[1]}, y={cursor[0]})"
        ascii_map = "\n".join(ascii_map.split("\n")[1:])  # remove first line

        nle_obsv["map"] = ascii_map
        nle_obsv["text_cursor"] = nle_obsv["text_cursor"] + "\n" + cursor

        long_term_observations = [
            ("text_message", "message"),
            ("text_glyphs", "language observation"),
            ("text_cursor", "cursor"),
            ("map", "map"),
        ]
        short_term_observation = [
            ("text_inventory", "inventory"),
        ]

        long_term_context = "\n".join([f"{name}:\n{nle_obsv[key]}\n" for key, name in long_term_observations])
        short_term_context = "\n".join([f"{name}:\n{nle_obsv[key]}\n" for key, name in short_term_observation])

        return {
            "long_term_context": long_term_context,
            "short_term_context": short_term_context,
        }
