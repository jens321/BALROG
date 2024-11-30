import re
import copy

from balrog.agents.base import BaseAgent


class CodeCotAgent(BaseAgent):
    """An agent that generates the names of code strategies as actions."""

    def __init__(self, client_factory, prompt_builder, config):
        super().__init__(client_factory, prompt_builder)
        self.client = client_factory()
        self.strategies = config.strategies

        self.remember_cot = config.agent.remember_cot

    def act(self, obs, prev_action=None):
        """Generate the next action based on the observation and previous action.

        Args:
            obs (dict): The current observation in the environment.
            prev_action (str, optional): The previous action taken.

        Returns:
            str: The selected action from the LLM response.
        """
        if prev_action:
            self.prompt_builder.update_action(prev_action)

        self.prompt_builder.update_observation(obs)

        messages = self.prompt_builder.get_prompt()

        # Add CoT-specific instructions to the prompt
        cot_instructions = """
First think about what's the best course of action step by step.
Finally, provide a single output action at the end of the message in the form of: STRATEGY: <strategy>
        """.strip()

        messages[-1].content += "\n\n" + cot_instructions

        response = self.client.generate(messages)

        final_answer = self._extract_final_answer(response)

        return final_answer

    def _extract_final_answer(self, reasoning):
        """Extract the final action from the chain-of-thought reasoning response.

        Args:
            reasoning (LLMResponse): The response containing CoT reasoning and action.

        Returns:
            LLMResponse: The response with the extracted final action.
        """

        def filter_letters(input_string):
            return re.sub(r"[^a-zA-Z\s:_]", "", input_string)

        answer = copy.deepcopy(reasoning)
        self.prompt_builder.update_reasoning(reasoning.completion)
        answer = answer._replace(reasoning=answer.completion)
        answer = answer._replace(completion=filter_letters(answer.completion).split("STRATEGY:")[-1].strip())

        return answer
